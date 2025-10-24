# pages/8_Relatorio.py
import streamlit as st
import pandas as pd
import numpy as np
import io
from src.utils import set_page_config_and_style
from datetime import datetime
# Plotly não é mais necessário para a função de PDF, mas mantido para visualização no dashboard
import plotly.express as px 
# Pillow também não é mais estritamente necessário, mas mantido.
from PIL import Image 

# ... (Restante do setup e mock data) ...

# -------------------------------
# FUNÇÃO: GERA GRÁFICO PARA EXPORTAÇÃO (SIMPLIFICADA)
# -------------------------------
def generate_chart_png(df):
    # Se optamos por não ter imagens, esta função retorna None
    return None

# ... (Seções de Resumo e Download CSV mantidas) ...

# -------------------------------
# 3. DOWNLOAD PDF (Função Storytelling)
# -------------------------------
st.markdown("### 📄 Download em PDF (Relatório com Storytelling)")

def create_pdf_report(df: pd.DataFrame) -> bytes:
    """
    Função que gera um relatório PDF focado em storytelling e detalhamento textual, 
    sem depender de imagens.
    """
    try:
        from fpdf import FPDF 
        
        # 1. PRÉ-CÁLCULOS E NARRATIVA
        df_monthly = df.groupby('Mes').agg(
            Total_Investimento=('Investimento_Mil_R$', 'sum'),
            Media_CPM=('CPM_R$', 'mean'),
            Total_Reach=('Reach_Milhoes', 'sum')
        ).reset_index()
        
        df_monthly['Total_Investimento'] = df_monthly['Total_Investimento'].round(0)
        df_monthly['Media_CPM'] = df_monthly['Media_CPM'].round(2)
        df_monthly['Total_Reach'] = df_monthly['Total_Reach'].round(1)

        total_investimento = df_monthly['Total_Investimento'].sum()
        maior_investimento_mes = df_monthly.loc[df_monthly['Total_Investimento'].idxmax()]
        
        pdf = FPDF()
        pdf.add_page()
        
        # --- CONFIGURAÇÕES BÁSICAS ---
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # --- TÍTULO ---
        pdf.set_font("Arial", "B", 18) 
        pdf.cell(200, 10, "Relatório Executivo de Campanha OOH", 0, 1, "C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(200, 5, f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, "C")
        pdf.ln(10)

        # --- SEÇÃO 1: RESUMO EXECUTIVO (STORYTELLING) ---
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "1. Análise Sumária da Performance", 0, 1, "L")
        
        # Destaque em negrito e itálico
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 6, 
            f"O período de análise demonstrou um investimento total de "
            f"R$ {total_investimento:,.0f} mil. O foco principal esteve no mês de "
            f"'{maior_investimento_mes['Mes']}', que concentrou o maior volume de recursos "
            f"({maior_investimento_mes['Total_Investimento']:,.0f} mil R$). "
            f"A estratégia alcançou um total de {df_relatorio['Reach_Milhoes'].sum():,.1f} milhões de pessoas "
            f"com um custo médio por milhão (CPM) de R$ {df_relatorio['CPM_R$'].mean():.2f}."
        )
        pdf.ln(5)

        # --- SEÇÃO 2: DETALHE MENSAL (STORYTELLING) ---
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "2. Detalhamento da Evolução Mensal", 0, 1, "L")
        
        pdf.set_font("Arial", "", 11)
        
        # Geração da narrativa por mês
        for index, row in df_monthly.iterrows():
            invest = row['Total_Investimento']
            reach = row['Total_Reach']
            cpm = row['Media_CPM']
            
            # Formatação do texto com destaque em negrito
            story = (
                f"**Mês de {row['Mes']}:** O investimento atingiu R$ {invest:,.0f} mil, "
                f"resultando em um alcance de {reach:,.1f} milhões. O CPM médio foi de R$ {cpm:.2f}."
            )
            
            # Destaque para o mês de pico ou baixo desempenho (simulação)
            if row['Mes'] == maior_investimento_mes['Mes']:
                 story += " (Este mês representou o pico de investimento da campanha.)"
            elif cpm > df_monthly['Media_CPM'].mean() * 1.1:
                 story += " (Observa-se um CPM ligeiramente acima da média.)"
            
            pdf.write(5, story.replace('**', FPDF.set_font_style), link='') # Usar write para quebras de linha

            # Formatação manual de negrito (FPDF não suporta Markdown)
            pdf.set_font("Arial", "B", 11)
            pdf.write(5, f"Mês de {row['Mes']}:", link='')
            pdf.set_font("Arial", "", 11)
            pdf.write(5, story.replace(f"**Mês de {row['Mes']}:**", ''), link='')
            pdf.ln(5)

        pdf.ln(5)

        # --- SEÇÃO 3: DETALHE DA TABELA AGREGADA (RICA) ---
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "3. Tabela de Performance Consolidada (Mensal)", 0, 1, "L")

        pdf.set_font("Arial", "B", 10)
        col_widths = [40, 40, 40, 40]
        headers = ["Mês", "Investimento (R$K)", "Reach (Milhões)", "CPM Médio (R$)"]
        
        # Header da Tabela
        for col, width in zip(headers, col_widths):
            pdf.cell(width, 7, col, 1, 0, "C")
        pdf.ln()

        # Linhas de Dados
        pdf.set_font("Arial", "", 10)
        for _, row in df_monthly.iterrows():
            pdf.cell(col_widths[0], 7, row['Mes'], 1, 0)
            
            # Estilo Condicional para Investimento Alto
            if row['Total_Investimento'] == maior_investimento_mes['Total_Investimento']:
                pdf.set_font("Arial", "B", 10)
            pdf.cell(col_widths[1], 7, f"R$ {row['Total_Investimento']:,.0f}", 1, 0, "R")
            pdf.set_font("Arial", "", 10) # Reseta o negrito

            pdf.cell(col_widths[2], 7, f"{row['Total_Reach']:.1f}", 1, 0, "R")
            
            # Estilo Condicional para CPM Alto
            if row['Media_CPM'] > df_monthly['Media_CPM'].mean() * 1.1:
                pdf.set_text_color(255, 0, 0) # Cor Vermelha
            pdf.cell(col_widths[3], 7, f"R$ {row['Media_CPM']:.2f}", 1, 0, "R")
            pdf.set_text_color(0, 0, 0) # Reseta a cor para preto
            pdf.ln()

        pdf.ln(10)
        
        # --- SEÇÃO 4: DETALHE COMPLETO DA CAMPANHA ---
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "4. Detalhe Completo por Campanha", 0, 1, "L")
        
        # Aqui você pode incluir a tabela completa da campanha, se necessário.
        pdf.set_font("Arial", "I", 10)
        pdf.cell(200, 5, "Para brevidade no relatório, listamos apenas as 5 principais campanhas.", 0, 1, "L")
        pdf.ln(2)

        pdf.set_font("Arial", "B", 8)
        col_widths_detalhe = [20, 15, 20, 20, 20, 20, 20, 20]
        headers_detalhe = ["ID", "Mês", "Mídia", "Invest.(K)", "Reach(MM)", "Freq.", "CPM", "Audiência"]
        
        for col, width in zip(headers_detalhe, col_widths_detalhe):
            pdf.cell(width, 7, col, 1, 0, "C")
        pdf.ln()

        pdf.set_font("Arial", "", 7)
        for _, row in df.head(5).iterrows():
            pdf.cell(col_widths_detalhe[0], 5, row['ID_Campanha'], 1, 0)
            pdf.cell(col_widths_detalhe[1], 5, row['Mes'], 1, 0, "C")
            pdf.cell(col_widths_detalhe[2], 5, row['Tipo_Midia'], 1, 0)
            pdf.cell(col_widths_detalhe[3], 5, f"{row['Investimento_Mil_R$']:.1f}", 1, 0, "R")
            pdf.cell(col_widths_detalhe[4], 5, f"{row['Reach_Milhoes']:.1f}", 1, 0, "R")
            pdf.cell(col_widths_detalhe[5], 5, f"{row['Frequencia']:.1f}", 1, 0, "R")
            pdf.cell(col_widths_detalhe[6], 5, f"{row['CPM_R$']:.2f}", 1, 0, "R")
            pdf.cell(col_widths_detalhe[7], 5, f"{row['Audiencia_Pico_K']}", 1, 0, "R")
            pdf.ln()


        # RETORNO BINÁRIO
        buffer = io.BytesIO(pdf.output(dest='S'))
        return buffer.getvalue() 
        
    except ImportError:
        # PLACEHOLDER: fpdf2 não instalado
        st.warning("A biblioteca `fpdf2` não está instalada. O PDF gerado será um placeholder de texto.")
        
        pdf_content_str = f"RELATÓRIO EXECUTIVO OOH (Placeholder) \n\nInstale 'fpdf2' para o relatório com storytelling."
        buffer = io.BytesIO()
        buffer.write(pdf_content_str.encode('utf-8'))
        return buffer.getvalue() 

    except Exception as e:
        # TRATAMENTO DE OUTROS ERROS
        st.error(f"Erro Crítico ao gerar PDF: {type(e).__name__}: {e}")
        pdf_content_str = f"RELATÓRIO EXECUTIVO OOH (Erro Crítico) \n\nDetalhes: {type(e).__name__}: {e}"
        return pdf_content_str.encode('utf-8') 

# -------------------------------
# Botão de Download PDF
# -------------------------------
pdf_bytes = create_pdf_report(df_relatorio)

st.download_button(
    label="Baixar Relatório em PDF",
    data=pdf_bytes,
    file_name='relatorio_executivo_storytelling.pdf',
    mime='application/pdf',
    type="primary",
    help="Gera um relatório PDF detalhado com narrativa de dados e formatação condicional."
)
