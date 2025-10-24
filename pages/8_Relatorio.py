# pages/8_Relatorio.py
import streamlit as st
import pandas as pd
import numpy as np
import io
from src.utils import set_page_config_and_style
from datetime import datetime

# -------------------------------
# CONFIGURAÇÕES GERAIS E DADOS (Omitido por brevidade, sem alterações)
# -------------------------------
set_page_config_and_style(
    page_title="Relatório Executivo",
    main_title="RELATÓRIO EXECUTIVO & DOWNLOAD",
    subtitle="Resumo das análises e opções de exportação de dados"
)

# ... (função get_mock_data e cálculos de métricas mantidos)

@st.cache_data
def get_mock_data():
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
    return pd.DataFrame(data)

df_relatorio = get_mock_data()
total_investimento = df_relatorio['Investimento_Mil_R$'].sum()
media_cpm = df_relatorio['CPM_R$'].mean()
total_reach = df_relatorio['Reach_Milhoes'].sum().round(1)
num_campanhas = len(df_relatorio)

# ... (Seções de Resumo e Download CSV mantidas)

st.markdown("### Resumo das Métricas Chave")
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Total de Campanhas", num_campanhas)
with col2: st.metric("Investimento Total (Mil R$)", f"{total_investimento:,.0f}".replace(",", "."))
with col3: st.metric("Reach Agregado (Milhões)", f"{total_reach:,.1f}".replace(",", "."))
with col4: st.metric("CPM Médio", f"R$ {media_cpm:.2f}")

st.markdown("---")

if st.checkbox("Mostrar Tabela de Dados (Detalhamento)"):
    st.dataframe(df_relatorio.head(), use_container_width=True, hide_index=True)

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
    Função que gera um relatório PDF. Usa io.BytesIO para garantir retorno binário.
    """
    try:
        from fpdf import FPDF 

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16) 
        pdf.cell(200, 10, "Relatório Executivo OOH", 0, 1, "C")
        
        pdf.set_font("Arial", "", 12)
        pdf.cell(200, 10, f"Data da Geração: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1) 
        pdf.cell(200, 10, f"Total de Campanhas Analisadas: {len(df)}", 0, 1)

        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, f"Investimento Agregado: R$ {df['Investimento_Mil_R$'].sum():,.0f} mil", 0, 1)
        
        pdf.set_font("Arial", "B", 10)
        col_widths = [30, 30, 30, 30, 30]
        headers = ["Campanha", "Mês", "Investimento", "Reach (MM)", "CPM (R$)"]
        
        for col, width in zip(headers, col_widths):
            pdf.cell(width, 7, col, 1, 0, "C")
        pdf.ln()

        pdf.set_font("Arial", "", 10)
        for _, row in df.head(5).iterrows():
            pdf.cell(col_widths[0], 7, row['ID_Campanha'], 1, 0)
            pdf.cell(col_widths[1], 7, row['Mes'], 1, 0)
            pdf.cell(col_widths[2], 7, f"R$ {row['Investimento_Mil_R$']:.0f}K", 1, 0)
            pdf.cell(col_widths[3], 7, f"{row['Reach_Milhoes']:.1f}", 1, 0)
            pdf.cell(col_widths[4], 7, f"R$ {row['CPM_R$']:.2f}", 1, 0)
            pdf.ln()

        # ALTERAÇÃO CHAVE: Usar io.BytesIO para garantir a tipagem 'bytes'
        pdf_output = pdf.output(dest='S')
        buffer = io.BytesIO(pdf_output)
        
        return buffer.getvalue() 
        
    except ImportError:
        # PLACEHOLDER: Retorno binário forçado para o placeholder
        st.warning("A biblioteca `fpdf2` não está instalada. O PDF gerado será um placeholder de texto.")
        
        pdf_content_str = f"RELATÓRIO EXECUTIVO OOH (Placeholder) \n\nTotal de Campanhas: {len(df)}\nInvestimento: R$ {df['Investimento_Mil_R$'].sum():,.0f} mil\n\nInstale 'fpdf2' (pip install fpdf2) para gerar o PDF completo."
        
        buffer = io.BytesIO()
        buffer.write(pdf_content_str.encode('utf-8'))
        
        return buffer.getvalue() 

    except Exception as e:
        # TRATAMENTO DE OUTROS ERROS: Retorna bytes com a mensagem de erro
        st.error(f"Erro ao gerar PDF: {type(e).__name__}: {e}")
        pdf_content_str = f"RELATÓRIO EXECUTIVO OOH (Erro na Geração) \n\nDetalhes: {type(e).__name__}: {e}"
        
        # Converte a string de erro para bytes antes de retornar
        return pdf_content_str.encode('utf-8') 

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
