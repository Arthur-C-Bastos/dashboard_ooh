# pages/8_Relatorio.py
# -*- coding: utf-8 -*- 
import streamlit as st
import pandas as pd
import numpy as np
import io
# Importe 'set_page_config_and_style' se o arquivo 'src/utils.py' existir.
try:
    from src.utils import set_page_config_and_style
except ImportError:
    def set_page_config_and_style(page_title, main_title, subtitle):
        st.set_page_config(layout="wide", page_title=page_title)
        st.title(main_title)
        st.markdown(f"**{subtitle}**")

from datetime import datetime
import plotly.express as px 
from PIL import Image 
from fpdf import FPDF 

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
    incluindo uma projeção futura.
    """
    try:
        # 1. PRÉ-CÁLCULOS E ANÁLISE DOS MELHORES PONTOS
        
        # Agregação Mensal
        df_monthly = df.groupby('Mes').agg(
            Total_Investimento=('Investimento_Mil_R$', 'sum'),
            Media_CPM=('CPM_R$', 'mean'),
            Total_Reach=('Reach_Milhoes', 'sum')
        ).reset_index()
        
        # Agregação por Mídia para Projeção
        df_media = df.groupby('Tipo_Midia').agg(
            Media_CPM=('CPM_R$', 'mean'),
            Total_Reach=('Reach_Milhoes', 'sum'),
            Total_Investimento=('Investimento_Mil_R$', 'sum')
        ).reset_index()

        # Encontrar o Melhor Ponto de Eficiência (menor CPM)
        melhor_midia = df_media.loc[df_media['Media_CPM'].idxmin()]
        cpm_base = melhor_midia['Media_CPM']
        
        # Dados da Projeção (Aumento de 20% no Investimento)
        aumento_investimento = 0.20
        novo_investimento = melhor_midia['Total_Investimento'] * (1 + aumento_investimento)
        
        # Novo Reach Projetado (mantendo a eficiência do CPM base)
        # CPM = Custo / Reach (Milhares) -> Reach = Custo / CPM (Mantendo CPM constante)
        novo_reach_proj_milhoes = (novo_investimento * 1000) / cpm_base / 1000
        novo_reach_proj_milhoes = novo_reach_proj_milhoes.round(1) # Arredondado para 1 casa
        
        
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
            f"R$ {total_investimento_geral:,.0f} mil. O foco principal esteve no mês de "
            f"'{maior_investimento_mes['Mes']}', que concentrou o maior volume de recursos "
            f"({maior_investimento_mes['Total_Investimento']:,.0f} mil R$). "
            f"A estratégia alcançou um total de {df.loc[:, 'Reach_Milhoes'].sum():,.1f} milhões de pessoas "
            f"com um custo médio por milhão (CPM) de R$ {df.loc[:, 'CPM_R$'].mean():.2f}."
        )
        pdf.ln(5)

        # --- SEÇÃO 2: DETALHE MENSAL (STORYTELLING) ---
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "2. Detalhamento da Evolução Mensal", 0, 1, "L")
        
        for index, row in df_monthly.iterrows():
            invest = row['Total_Investimento']
            reach = row['Total_Reach']
            cpm = row['Media_CPM']
            
            pdf.set_font("Arial", "B", 11)
            pdf.write(5, f"Mês de {row['Mes']}:", link='')
            
            pdf.set_font("Arial", "", 11)
            
            story_part = f" O investimento atingiu R$ {invest:,.0f} mil, resultando em um alcance de {reach:,.1f} milhões. O CPM médio foi de R$ {cpm:.2f}."
            
            if row['Mes'] == maior_investimento_mes['Mes']:
                 story_part += " (Pico de investimento da campanha.)"
            elif cpm > df_monthly['Media_CPM'].mean() * 1.1:
                 story_part += " (CPM ligeiramente acima da média.)"
            
            pdf.write(5, story_part, link='')
            pdf.ln(5) 

        pdf.ln(5)
        
        # ------------------------------------------------------------------
        # --- SEÇÃO 3: PROJEÇÃO ESTRATÉGICA (NOVA SEÇÃO) ---
        # ------------------------------------------------------------------
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "3. Projeção Estratégica: Otimizando o Investimento", 0, 1, "L")
        
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 6, 
            f"Baseado na performance histórica, a mídia **{melhor_midia['Tipo_Midia']}** se destacou com o melhor custo-benefício, apresentando um CPM médio de "
            f"R$ {cpm_base:.2f}. Recomendamos focar recursos nesta categoria."
        )
        pdf.ln(3)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 6, f"Cenário Projetado: Aumento de {aumento_investimento*10
