# pages/8_Relatorio.py
# -*- coding: utf-8 -*- 
import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
import plotly.express as px 
from PIL import Image 
from fpdf import FPDF 

# Tenta importar a função utilitária. Se falhar, define um fallback.
try:
    from src.utils import set_page_config_and_style
except ImportError:
    def set_page_config_and_style(page_title, main_title, subtitle):
        st.set_page_config(layout="wide", page_title=page_title)
        st.title(main_title)
        st.markdown(f"**{subtitle}**")

# -------------------------------
# CONFIGURAÇÕES GERAIS E ESTILO PADRÃO
# -------------------------------
set_page_config_and_style(
    page_title="Relatório Executivo",
    main_title="RELATÓRIO EXECUTIVO & DOWNLOAD",
    subtitle="Resumo das análises e opções de exportação de dados"
)

# -------------------------------
# DADOS MOCK E CÁLCULOS
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

# Variáveis Globais
df_relatorio = get_mock_data()
total_investimento = df_relatorio['Investimento_Mil_R$'].sum()
media_cpm = df_relatorio['CPM_R$'].mean()
total_reach = df_relatorio['Reach_Milhoes'].sum().round(1)
num_campanhas = len(df_relatorio)

def generate_chart_png(df):
    """Retorna None, desativando a inclusão de imagens no PDF."""
    return None

# -------------------------------
# 1. RESUMO EXECUTIVO NA TELA (Mantido)
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
# 2. DOWNLOAD CSV (Mantido)
# -------------------------------
st.markdown("### 📥 Download em CSV")
csv = df_relatorio.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Baixar Dados em CSV",
    data=csv,
    file_name='relatorio_ooh_detalhado.csv',
    mime='text/csv',
    type="primary"
)


# -------------------------------
# 3. DOWNLOAD PDF (Função Storytelling)
# -------------------------------
st.markdown("### 📄 Download em PDF (Relatório com Storytelling)")

def create_pdf_report(df: pd.DataFrame) -> bytes:
    """
    Função que gera um relatório PDF focado em storytelling e detalhamento textual, 
    incluindo projeção futura e detalhe por mídia.
    """
    try:
        # 1. PRÉ-CÁLCULOS E ANÁLISE DOS MELHORES PONTOS
        
        # Agregação Mensal
        df_monthly = df.groupby('Mes').agg(
            Total_Investimento=('Investimento_Mil_R$', 'sum'),
            Media_CPM=('CPM_R$', 'mean'),
            Total_Reach=('Reach_Milhoes', 'sum'),
            Media_Frequencia=('Frequencia', 'mean') # Adicionado Média de Frequência
        ).reset_index()
        df_monthly['Media_Frequencia'] = df_monthly['Media_Frequencia'].round(1)

        # Agregação por Mídia para Projeção e Detalhe
        df_media = df.groupby('Tipo_Midia').agg(
            Media_CPM=('CPM_R$', 'mean'),
            Total_Reach=('Reach_Milhoes', 'sum'),
            Total_Investimento=('Investimento_Mil_R$', 'sum'),
            Media_Frequencia=('Frequencia', 'mean') # Adicionado Média de Frequência
        ).reset_index()
        df_media['Media_Frequencia'] = df_media['Media_Frequencia'].round(1)
        df_media['Media_CPM'] = df_media['Media_CPM'].round(2)
        df_media['Total_Reach'] = df_media['Total_Reach'].round(1)
        df_media['Total_Investimento'] = df_media['Total_Investimento'].round(0)


        # ENCONTRAR MÉTRICAS CHAVE PARA STORYTELLING E PROJEÇÃO
        melhor_midia = df_media.loc[df_media['Media_CPM'].idxmin()]
        cpm_base = melhor_midia['Media_CPM']
        
        # Dados da Projeção (Aumento de 20% no Investimento)
        aumento_investimento = 0.20
        novo_investimento = melhor_midia['Total_Investimento'] * (1 + aumento_investimento)
        
        # Novo Reach Projetado (mantendo a eficiência do CPM base)
        novo_reach_proj_milhoes = (novo_investimento * 1000) / cpm_base / 1000
        novo_reach_proj_milhoes = novo_reach_proj_milhoes.round(1)
        
        
        # Dados do Sumário
        total_investimento_geral = df_monthly['Total_Investimento'].sum()
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
        
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 6, 
            f"O período de análise demonstrou um investimento total de "
            f"R$ {total_investimento_geral:,.0f} mil, alcançando um total de {df.loc[:, 'Reach_Milhoes'].sum():,.1f} milhões de pessoas. "
            f"O custo médio por milhão (CPM) ficou em R$ {df.loc[:, 'CPM_R$'].mean():.2f}, com uma frequência média de exposição de {df.loc[:, 'Frequencia'].mean():.1f} vezes."
        )
        pdf.ln(5)

        # --- SEÇÃO 2: DETALHE MENSAL (STORYTELLING) ---
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "2. Detalhamento da Evolução Mensal", 0, 1, "L")
        
        for index, row in df_monthly.iterrows():
            invest = row['Total_Investimento']
            reach = row['Total_Reach']
            cpm = row['Media_CPM']
            freq = row['Media_Frequencia']
            
            pdf.set_font("Arial", "B", 11)
            pdf.write(5, f"Mês de {row['Mes']}:", link='')
            
            pdf.set_font("Arial", "", 11)
            
            story_part = f" O investimento atingiu R$ {invest:,.0f} mil, gerando {reach:,.1f} milhões de alcance e frequência média de {freq:.1f}. O CPM médio foi de R$ {cpm:.2f}."
            
            if row['Mes'] == maior_investimento_mes['Mes']:
                 story_part += " (Pico de investimento.)"
            elif cpm > df_monthly['Media_CPM'].mean() * 1.1:
                 story_part += " (CPM ligeiramente acima da média.)"
            
            pdf.write(5, story_part, link='')
            pdf.ln(5) 

        pdf.ln(5)

        # ------------------------------------------------------------------
        # --- SEÇÃO 3: ANÁLISE CONSOLIDADA POR MÍDIA (NOVA TABELA) ---
        # ------------------------------------------------------------------
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "3. Performance Consolidada por Tipo de Mídia", 0, 1, "L")
        
        pdf.set_font("Arial", "B", 10)
        col_widths_media = [40, 40, 40, 40, 30]
        headers_media = ["Mídia", "Investimento (R$K)", "Reach (Milhões)", "CPM Médio (R$)", "Freq. Média"]
        
        # Header da Tabela
        for col, width in zip(headers_media, col_widths_media):
            pdf.cell(width, 7, col, 1, 0, "C")
        pdf.ln()

        # Linhas de Dados
        pdf.set_font("Arial", "", 10)
        for _, row in df_media.iterrows():
            pdf.cell(col_widths_media[0], 7, row['Tipo_Midia'], 1, 0)
            
            pdf.cell(col_widths_media[1], 7, f"R$ {row['Total_Investimento']:,.0f}", 1, 0, "R")
            pdf.cell(col_widths_media[2], 7, f"{row['Total_Reach']:.1f}", 1, 0, "R")
            
            # Destaque para o melhor CPM
            if row['Media_CPM'] == melhor_midia['Media_CPM']:
                pdf.set_font("Arial", "B", 10)
            pdf.cell(col_widths_media[3], 7, f"R$ {row['Media_CPM']:.2f}", 1, 0, "R")
            pdf.set_font("Arial", "", 10) 
            
            pdf.cell(col_widths_media[4], 7, f"{row['Media_Frequencia']:.1f}", 1, 0, "R")
            pdf.ln()
        
        pdf.ln(5)
        
        # --- SEÇÃO 4: PROJEÇÃO ESTRATÉGICA (Agora é a Seção 4) ---
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "4. Projeção Estratégica: Otimizando o Investimento", 0, 1, "L")
        
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 6, 
            f"Baseado na análise de eficiência, a mídia **{melhor_midia['Tipo_Midia']}** se destacou com o melhor custo-benefício (CPM de R$ {cpm_base:.2f}). "
            f"A projeção abaixo demonstra o resultado esperado ao realocar {aumento_investimento*100:.0f}% de investimento adicional mantendo a mesma eficiência."
        )
        pdf.ln(3)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 6, f"Cenário Projetado: Aumento de {aumento_investimento*100:.0f}% (Investimento focado em {melhor_midia['Tipo_Midia']})", 0, 1, "L")
        pdf.ln(1)
        
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 6,
            f"- **Investimento Base em {melhor_midia['Tipo_Midia']}:** R$ {melhor_midia['Total_Investimento']:,.0f} mil \n"
            f"- **Novo Investimento Projetado:** R$ {novo_investimento:,.0f} mil \n"
            f"- **Alcance Projetado:** {novo_reach_proj_milhoes:,.1f} milhões (Aumento de Reach de {novo_reach_proj_milhoes - melhor_midia['Total_Reach']:,.1f} milhões)."
        )
        pdf.ln(5)

        # Adiciona quebra de página se não houver espaço suficiente para a próxima seção
        if pdf.get_y() > 250:
             pdf.add_page()
        
        # --- SEÇÃO 5: TABELA AGREGADA (Mensal) (Agora é a Seção 5) ---
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "5. Tabela de Performance Consolidada (Mensal)", 0, 1, "L")

        pdf.set_font("Arial", "B", 10)
        col_widths = [35, 35, 35, 35, 35]
        headers = ["Mês", "Investimento (R$K)", "Reach (Milhões)", "CPM Médio (R$)", "Freq. Média"] # Adicionado Frequência
        
        for col, width in zip(headers, col_widths):
            pdf.cell(width, 7, col, 1, 0, "C")
        pdf.ln()

        pdf.set_font("Arial", "", 10)
        for _, row in df_monthly.iterrows():
            pdf.cell(col_widths[0], 7, row['Mes'], 1, 0)
            
            if row['Total_Investimento'] == maior_investimento_mes['Total_Investimento']:
                pdf.set_font("Arial", "B", 10)
            pdf.cell(col_widths[1], 7, f"R$ {row['Total_Investimento']:,.0f}", 1, 0, "R")
            pdf.set_font("Arial", "", 10) 

            pdf.cell(col_widths[2], 7, f"{row['Total_Reach']:.1f}", 1, 0, "R")
            
            if row['Media_CPM'] > df_monthly['Media_CPM'].mean() * 1.1:
                pdf.set_text_color(255, 0, 0) 
            pdf.cell(col_widths[3], 7, f"R$ {row['Media_CPM']:.2f}", 1, 0, "R")
            pdf.set_text_color(0, 0, 0) 
            
            pdf.cell(col_widths[4], 7, f"{row['Media_Frequencia']:.1f}", 1, 0, "R") # Exibindo Frequência
            pdf.ln()

        pdf.ln(10)

        # Adiciona quebra de página antes da última seção (para garantir a 2ª folha)
        pdf.add_page()
        
        # --- SEÇÃO 6: DETALHE COMPLETO DA CAMPANHA (Agora é a Seção 6) ---
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "6. Detalhe Completo por Campanha (Top 5 em Investimento)", 0, 1, "L")
        
        pdf.set_font("Arial", "I", 10)
        pdf.cell(200, 5, "Detalhe das 5 campanhas com maior investimento no período.", 0, 1, "L")
        pdf.ln(2)

        pdf.set_font("Arial", "B", 8)
        col_widths_detalhe = [20, 15, 20, 20, 20, 20, 20, 20]
        headers_detalhe = ["ID", "Mês", "Mídia", "Invest.(K)", "Reach(MM)", "Freq.", "CPM", "Audiência"]
        
        for col, width in zip(headers_detalhe, col_widths_detalhe):
            pdf.cell(width, 7, col, 1, 0, "C")
        pdf.ln()

        pdf.set_font("Arial", "", 7)
        df_detail = df.sort_values(by='Investimento_Mil_R$', ascending=False).head(5)
        
        for _, row in df_detail.iterrows():
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
        # TRATAMENTO DE ERRO: fpdf2 não instalado
        st.error("Erro: A biblioteca `fpdf` não foi encontrada. Certifique-se de que está instalada (pip install fpdf2).")
        pdf_content_str = "ERRO: Instale 'fpdf2' para gerar o PDF."
        buffer = io.BytesIO()
        buffer.write(pdf_content_str.encode('utf-8'))
        return buffer.getvalue() 

    except Exception as e:
        # TRATAMENTO DE OUTROS ERROS DE EXECUÇÃO
        st.error(f"Erro Crítico ao gerar PDF: {type(e).__name__}: {e}")
        pdf_content_str = f"ERRO CRÍTICO NA GERAÇÃO DO PDF: {type(e).__name__}: {e}"
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
    help="Gera um relatório PDF detalhado com narrativa de dados, detalhe por mídia e projeções estratégicas."
)
