# pages/8_Relatorio.py
import streamlit as st
import pandas as pd
import numpy as np
import io
from src.utils import set_page_config_and_style
from datetime import datetime # CORREÇÃO: Importa a classe datetime

# OMITIDO: from fpdf import FPDF (Importação feita dentro do try/except para segurança)

# -------------------------------
# CONFIGURAÇÕES GERAIS E ESTILO PADRÃO
# -------------------------------
set_page_config_and_style(
    page_title="Relatório Executivo",
    main_title="RELATÓRIO EXECUTIVO & DOWNLOAD",
    subtitle="Resumo das análises e opções de exportação de dados"
)

# -------------------------------
# DADOS MOCK (Simulando os dados de outras abas)
# -------------------------------
@st.cache_data
def get_mock_data():
    """Gera um DataFrame unificado para download, simulando dados de análise OOH."""
    data = {
        'ID_Campanha': [f'C{i}' for i in range(101, 111)],
        'Mes': ['Jan', 'Jan', 'Fev', 'Fev', 'Mar', 'Mar', 'Abr', 'Abr', 'Maio', 'Maio'],
        'Tipo_Midia': ['Digital', 'Estática'] * 5,
        'Investimento_Mil_R$': np.random.uniform(50, 300, 10).round(1),
        'Reach_Milhoes': np.random.uniform(1.0, 5.0, 10).round(2),
        'Frequencia': np.random.uniform(4.0, 7.0, 10).round(1),
        'CPM_R$': np.random.uniform(2.5, 6.0, 10).round(2),
        'Audiencia_Pico_K': np.random.randint(50, 200, 10)
    }
    df = pd.DataFrame(data)
    return df

df_relatorio = get_mock_data()

# -------------------------------
# 1. RESUMO EXECUTIVO NA TELA
# -------------------------------
st.markdown("### Resumo das Métricas Chave")

# Cálculos Aggregados
total_investimento = df_relatorio['Investimento_Mil_R$'].sum()
media_cpm = df_relatorio['CPM_R$'].mean()
total_reach = df_relatorio['Reach_Milhoes'].sum().round(1)
num_campanhas = len(df_relatorio)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Campanhas", num_campanhas)
with col2:
    st.metric("Investimento Total (Mil R$)", f"{total_investimento:,.0f}".replace(",", "."))
with col3:
    st.metric("Reach Agregado (Milhões)", f"{total_reach:,.1f}".replace(",", "."))
with col4:
    st.metric("CPM Médio", f"R$ {media_cpm:.2f}")

st.markdown("---")

# Detalhe dos dados (opcional, para visualização rápida)
if st.checkbox("Mostrar Tabela de Dados (Detalhamento)"):
    st.dataframe(df_relatorio.head(), use_container_width=True, hide_index=True)


# -------------------------------
# 2. DOWNLOAD CSV
# -------------------------------
st.markdown("### 📥 Download em CSV")
st.info("Baixe a planilha completa de desempenho das campanhas para análise detalhada em Excel ou outra ferramenta.")

csv = df_relatorio.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Baixar Dados em CSV",
    data=csv,
    file_name='relatorio_ooh_detalhado.csv',
    mime='text/csv',
    type="primary"
)


# -------------------------------
# 3. DOWNLOAD PDF (Função simulada)
# -------------------------------
st.markdown("### 📄 Download em PDF (Relatório Visual)")

def create_pdf_report(df: pd.DataFrame) -> bytes:
    """
    Função que simula a criação de um relatório PDF.
    
    NOTA: Para funcionar de fato, você precisa instalar a biblioteca fpdf2 (pip install fpdf2).
    """
    try:
        # Importação segura: só tenta gerar PDF se a biblioteca estiver instalada.
        from fpdf import FPDF 

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "Relatório Executivo OOH", 0, 1, "C")
        
        pdf.set_font("Arial", "", 12)
        # datetime.now() está seguro graças à importação no topo
        pdf.cell(200, 10, f"Data da Geração: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1) 
        pdf.cell(200, 10, f"Total de Campanhas Analisadas: {len(df)}", 0, 1)

        # Adicionar Métrica Principal
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, f"Investimento Agregado: R$ {df['Investimento_Mil_R$'].sum():,.0f} mil", 0, 1)
        
        # Adicionar Tabela Simplificada
        pdf.set_font("Arial", "B", 10)
        col_widths = [30, 30, 30, 30, 30]
        headers = ["Campanha", "Mês", "Investimento", "Reach (MM)", "CPM (R$)"]
        
        # Header
        for col, width in zip(headers, col_widths):
            pdf.cell(width, 7, col, 1, 0, "C")
        pdf.ln()

        # Data rows (Top 5 para o PDF)
        pdf.set_font("Arial", "", 10)
        for index, row in df.head(5).iterrows():
            pdf.cell(col_widths[0], 7, row['ID_Campanha'], 1, 0)
            pdf.cell(col_widths[1], 7, row['Mes'], 1, 0)
            pdf.cell(col_widths[2], 7, f"R$ {row['Investimento_Mil_R$']:.0f}K", 1, 0)
            pdf.cell(col_widths[3], 7, f"{row['Reach_Milhoes']:.1f}", 1, 0)
            pdf.cell(col_widths[4], 7, f"R$ {row['CPM_R$']:.2f}", 1, 0)
            pdf.ln()

        # RETORNO BEM SUCEDIDO
        return pdf.output(dest='S').encode('latin-1')
        
    except ImportError:
        # Se a importação falhar, ele cai aqui, gerando o placeholder de texto com segurança.
        
        st.warning("A biblioteca `fpdf2` não está instalada. O PDF gerado será um placeholder de texto.")
        pdf_content = f"RELATÓRIO EXECUTIVO OOH (Placeholder) \n\nTotal de Campanhas: {len(df)}\nInvestimento: R$ {df['Investimento_Mil_R$'].sum():,.0f} mil\n\nInstale 'fpdf2' (pip install fpdf2) para gerar o PDF completo."
        return pdf_content.encode('utf-8')
    except Exception as e:
        # Captura outros erros (ex: erro de fonte)
        st.error(f"Erro ao gerar PDF (Instalado?): {e}")
        pdf_content = f"RELATÓRIO EXECUTIVO OOH (Erro na Geração) \n\nDetalhes: {e}"
        return pdf_content.encode('utf-8')

# -------------------------------
# Botão de Download PDF
# -------------------------------
pdf_bytes = create_pdf_report(df_relatorio)

st.download_button(
    label="Baixar Relatório em PDF",
    data=pdf_bytes,
    file_name='relatorio_executivo_ooh.pdf',
    mime='application/pdf',
    help="Gera um relatório PDF com as principais métricas e uma tabela resumida."
)
