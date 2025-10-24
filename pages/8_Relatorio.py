# pages/8_Relatorio.py
import streamlit as st
import pandas as pd
import numpy as np
import io
from src.utils import set_page_config_and_style
from datetime import datetime
import plotly.express as px
from PIL import Image # Importado para manipulação, caso necessário, mas principalmente para clareza

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
    return pd.DataFrame(data)

df_relatorio = get_mock_data()
total_investimento = df_relatorio['Investimento_Mil_R$'].sum()
media_cpm = df_relatorio['CPM_R$'].mean()
total_reach = df_relatorio['Reach_Milhoes'].sum().round(1)
num_campanhas = len(df_relatorio)

# -------------------------------
# FUNÇÃO: GERA GRÁFICO PARA EXPORTAÇÃO
# -------------------------------
def generate_chart_png(df):
    """Cria um gráfico Plotly e o retorna como bytes PNG."""
    df_agg = df.groupby('Mes')['Investimento_Mil_R$'].sum().reset_index()
    mes_order = ['Jan', 'Fev', 'Mar', 'Abr', 'Maio']
    df_agg['Mes'] = pd.Categorical(df_agg['Mes'], categories=mes_order, ordered=True)
    df_agg = df_agg.sort_values('Mes')
    
    fig = px.bar(
        df_agg, 
        x='Mes', 
        y='Investimento_Mil_R$', 
        title='Investimento Agregado por Mês (R$ Mil)',
        labels={'Investimento_Mil_R$': 'Investimento (R$ Mil)'},
        color_discrete_sequence=['#1E90FF']
    )
    fig.update_layout(plot_bgcolor='white', margin=dict(t=50, b=0, l=0, r=0))
    
    try:
        # TENTA EXPORTAR DIRETAMENTE COMO BYTES PNG
        # Requer 'kaleido' para a renderização limpa
        img_bytes = fig.to_image(format="png", width=700, height=400)
        
        return img_bytes
        
    except Exception as e:
        # Se Plotly/Kaleido falhar (por falta de navegador ou outra razão)
        st.error(f"Erro ao gerar imagem PNG do gráfico: {e}")
        return None

# -------------------------------
# 1. RESUMO EXECUTIVO NA TELA
# -------------------------------
st.markdown("### Resumo das Métricas Chave")
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Total de Campanhas", num_campanhas)
with col2: st.metric("Investimento Total (Mil R$)", f"{total_investimento:,.0f}".replace(",", "."))
with col3: st.metric("Reach Agregado (Milhões)", f"{total_reach:,.1f}".replace(",", "."))
with col4: st.metric("CPM Médio", f"R$ {media_cpm:.2f}")

st.markdown("---")

# Visualização do gráfico no dashboard (opcional)
if st.checkbox("Mostrar Gráfico de Investimento (Visão Dashboard)"):
    df_agg = df_relatorio.groupby('Mes')['Investimento_Mil_R$'].sum().reset_index()
    mes_order = ['Jan', 'Fev', 'Mar', 'Abr', 'Maio']
    df_agg['Mes'] = pd.Categorical(df_agg['Mes'], categories=mes_order, ordered=True)
    df_agg = df_agg.sort_values('Mes')
    fig_dash = px.bar(
        df_agg, 
        x='Mes', 
        y='Investimento_Mil_R$', 
        title='Investimento Agregado por Mês (R$ Mil)',
        color_discrete_sequence=['#1E90FF']
    )
    st.plotly_chart(fig_dash, use_container_width=True)

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
# 3. DOWNLOAD PDF (Função RICA)
# -------------------------------
st.markdown("### 📄 Download em PDF (Relatório Visual Rico)")

def create_pdf_report(df: pd.DataFrame) -> bytes:
    """
    Função que gera um relatório PDF rico com imagem.
    Garante que o retorno seja sempre bytes para o Streamlit.
    """
    try:
        from fpdf import FPDF 
        
        # 1. GERA O GRÁFICO COMO IMAGEM BINÁRIA
        chart_png_bytes = generate_chart_png(df)
        
        pdf = FPDF()
        pdf.add_page()
        
        # --- CABEÇALHO ---
        pdf.set_font("Arial", "B", 16) 
        pdf.cell(200, 10, "Relatório Executivo OOH", 0, 1, "C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(200, 10, f"Data da Geração: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1) 
        pdf.ln(5)

        # --- SEÇÃO 1: MÉTRICAS CHAVE ---
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "Métricas Consolidadas", 0, 1, "L")
        pdf.set_font("Arial", "", 12)
        pdf.cell(50, 7, "Total Campanhas:", 0, 0)
        pdf.cell(50, 7, str(len(df)), 0, 1)
        pdf.cell(50, 7, "Investimento Total:", 0, 0)
        pdf.cell(50, 7, f"R$ {df['Investimento_Mil_R$'].sum():,.0f} mil", 0, 1)
        pdf.cell(50, 7, "Reach Agregado:", 0, 0)
        pdf.cell(50, 7, f"{df['Reach_Milhoes'].sum():,.1f} milhões", 0, 1)
        pdf.ln(5)
        
        # --- SEÇÃO 2: GRÁFICO DE INVESTIMENTO ---
        if chart_png_bytes:
            pdf.set_font("Arial", "B", 14)
            pdf.cell(200, 10, "Visualização de Investimento Mensal", 0, 1, "L")
            
            # Adiciona a imagem do buffer
            pdf.image(
                name=io.BytesIO(chart_png_bytes), 
                type='PNG', 
                w=pdf.w - 20 # Largura da página menos margens
            )
            pdf.ln(10)
        else:
            pdf.set_font("Arial", "I", 10)
            pdf.cell(200, 5, "Gráfico não disponível (Erro de Exportação)", 0, 1, "C")
            pdf.ln(5)


        # --- SEÇÃO 3: DETALHE DA TABELA (Top 5) ---
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "Detalhe das Campanhas (Top 5)", 0, 1, "L")

        pdf.set_font("Arial", "B", 10)
        col_widths = [30, 20, 35, 30, 30, 30]
        headers = ["Campanha", "Mês", "Investimento(K)", "Reach (MM)", "Frequência", "CPM (R$)"]
        
        for col, width in zip(headers, col_widths):
            pdf.cell(width, 7, col, 1, 0, "C")
        pdf.ln()

        pdf.set_font("Arial", "", 8) # Fonte menor para tabela
        for _, row in df.head(5).iterrows():
            pdf.cell(col_widths[0], 7, row['ID_Campanha'], 1, 0)
            pdf.cell(col_widths[1], 7, row['Mes'], 1, 0)
            pdf.cell(col_widths[2], 7, f"R$ {row['Investimento_Mil_R$']:.1f}", 1, 0, "R")
            pdf.cell(col_widths[3], 7, f"{row['Reach_Milhoes']:.1f}", 1, 0, "R")
            pdf.cell(col_widths[4], 7, f"{row['Frequencia']:.1f}", 1, 0, "R")
            pdf.cell(col_widths[5], 7, f"R$ {row['CPM_R$']:.2f}", 1, 0, "R")
            pdf.ln()

        # RETORNO BINÁRIO (garantido via buffer)
        buffer = io.BytesIO(pdf.output(dest='S'))
        return buffer.getvalue() 
        
    except ImportError:
        # PLACEHOLDER: fpdf2 não instalado
        st.warning("A biblioteca `fpdf2` não está instalada. O PDF gerado será um placeholder de texto.")
        
        pdf_content_str = f"RELATÓRIO EXECUTIVO OOH (Placeholder) \n\nInstale 'fpdf2' e 'kaleido' para o relatório visual rico."
        buffer = io.BytesIO()
        buffer.write(pdf_content_str.encode('utf-8'))
        return buffer.getvalue() 

    except Exception as e:
        # TRATAMENTO DE OUTROS ERROS
        st.error(f"Erro ao gerar PDF: {type(e).__name__}: {e}")
        pdf_content_str = f"RELATÓRIO EXECUTIVO OOH (Erro Crítico) \n\nDetalhes: {type(e).__name__}: {e}"
        return pdf_content_str.encode('utf-8') 

# -------------------------------
# Botão de Download PDF
# -------------------------------
pdf_bytes = create_pdf_report(df_relatorio)

st.download_button(
    label="Baixar Relatório em PDF",
    data=pdf_bytes,
    file_name='relatorio_executivo_ooh_rico.pdf',
    mime='application/pdf',
    type="primary",
    help="Gera um relatório PDF com métricas, gráfico de investimento e tabela."
)
