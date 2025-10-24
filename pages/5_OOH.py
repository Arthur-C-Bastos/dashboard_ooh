import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils import set_page_config_and_style # Importa a função de padronização
import numpy as np

# -------------------------------
# CONFIGURAÇÕES GERAIS E ESTILO PADRÃO
# -------------------------------
set_page_config_and_style(
    page_title="Análise de Desempenho OOH",
    main_title="ANÁLISE DE DESEMPENHO OOH",
    subtitle="Simulação de KPIs (Key Performance Indicators) de Campanhas"
)

# -------------------------------
# FUNÇÃO SIMULADA DE GERAÇÃO DE DADOS
# -------------------------------
@st.cache_data(ttl=3600)
def generate_campaign_data():
    """Gera dados simulados de várias campanhas OOH."""
    data = {
        'Campanha': [f'Campanha {i}' for i in range(1, 11)],
        'Investimento (R$)': np.random.randint(50000, 300000, 10),
        'Reach (Milhões)': np.random.uniform(0.8, 4.5, 10).round(2),
        'Impressões (Milhões)': np.random.uniform(5.0, 30.0, 10).round(1),
        'Frequência Média': np.random.uniform(4.0, 7.0, 10).round(1),
        'Tipo de Mídia': ['Digital', 'Estática'] * 5,
        'Mês': ['Jan', 'Fev', 'Mar', 'Abr', 'Maio'] * 2
    }
    df = pd.DataFrame(data)
    
    # Calcular CPM (Custo por Mil Impressões)
    df['CPM (R$)'] = (df['Investimento (R$)'] / df['Impressões (Milhões)']) / 1000
    df['CPM (R$)'] = df['CPM (R$)'].round(2)
    
    # Calcular CPP (Custo por Ponto de Audiência, simplificado)
    df['CPP (R$)'] = df['Investimento (R$)'] / (df['Reach (Milhões)'] * 1000000)
    df['CPP (R$)'] = df['CPP (R$)'].round(2)
    
    return df

df_campanhas = generate_campaign_data()

# -------------------------------
# CONTROLES (Filtros)
# -------------------------------
st.markdown("### Filtros de Análise")
col_mes, col_tipo_midia, col_cpm_min = st.columns(3)

with col_mes:
    meses_selecionados = st.multiselect("Filtrar por Mês", df_campanhas['Mês'].unique(), default=df_campanhas['Mês'].unique())

with col_tipo_midia:
    tipos_selecionados = st.multiselect("Filtrar por Tipo de Mídia", df_campanhas['Tipo de Mídia'].unique(), default=df_campanhas['Tipo de Mídia'].unique())

with col_cpm_min:
    cpm_max = st.slider("CPM Máximo (R$)", min_value=1.0, max_value=df_campanhas['CPM (R$)'].max() + 5, value=df_campanhas['CPM (R$)'].max(), step=0.5)

# Aplicar Filtros
df_filtrado = df_campanhas[
    (df_campanhas['Mês'].isin(meses_selecionados)) &
    (df_campanhas['Tipo de Mídia'].isin(tipos_selecionados)) &
    (df_campanhas['CPM (R$)'] <= cpm_max)
].copy()

# -------------------------------
# 1. MÉTRICAS CHAVE (Key Performance Indicators)
# -------------------------------
st.markdown("### KPIs Consolidados")
if not df_filtrado.empty:
    
    # Cálculos Consolidados
    total_investimento = df_filtrado['Investimento (R$)'].sum()
    media_cpm = df_filtrado['CPM (R$)'].mean()
    total_reach = df_filtrado['Reach (Milhões)'].sum() # Soma simples
    total_impressoes = df_filtrado['Impressões (Milhões)'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Investido", f"R$ {total_investimento:,.0f}".replace(",", "."))
    with col2:
        st.metric("Média CPM", f"R$ {media_cpm:.2f}")
    with col3:
        st.metric("Reach Total", f"{total_reach:,.1f} milhões".replace(",", "."))
    with col4:
        st.metric("Total Impressões", f"{total_impressoes:,.1f} milhões".replace(",", "."))
    
    st.markdown("---")

    # -------------------------------
    # 2. GRÁFICOS DE DESEMPENHO
    # -------------------------------
    col_cpm, col_frequencia = st.columns(2)
    
    with col_cpm:
        st.markdown("##### CPM por Campanha")
        fig_cpm = px.bar(
            df_filtrado, 
            x='Campanha', 
            y='CPM (R$)', 
            color='Tipo de Mídia',
            title='Custo por Mil Impressões (CPM)',
            template='simple_white'
        )
        fig_cpm.update_layout(xaxis={'categoryorder': 'total descending'}, height=400)
        st.plotly_chart(fig_cpm, use_container_width=True)
        
    with col_frequencia:
        st.markdown("##### Reach vs. Frequência")
        fig_freq = px.scatter(
            df_filtrado,
            x='Reach (Milhões)',
            y='Frequência Média',
            size='Investimento (R$)',
            color='Tipo de Mídia',
            hover_name='Campanha',
            title='Alcance (Reach) x Frequência Média',
            template='simple_white'
        )
        fig_freq.update_layout(height=400)
        st.plotly_chart(fig_freq, use_container_width=True)

    # -------------------------------
    # 3. TABELA DETALHADA
    # -------------------------------
    st.markdown("### Tabela de Campanhas Detalhada")
    df_display = df_filtrado.copy()
    
    # Formatação de valores para exibição
    df_display['Investimento (R$)'] = df_display['Investimento (R$)'].apply(lambda x: f"R$ {x:,.0f}".replace(",", "."))
    df_display['Reach (Milhões)'] = df_display['Reach (Milhões)'].apply(lambda x: f"{x:,.1f}".replace(",", "."))
    df_display['Impressões (Milhões)'] = df_display['Impressões (Milhões)'].apply(lambda x: f"{x:,.1f}".replace(",", "."))
    
    st.dataframe(
        df_display[['Campanha', 'Mês', 'Tipo de Mídia', 'Investimento (R$)', 'Reach (Milhões)', 'Frequência Média', 'CPM (R$)', 'CPP (R$)']],
        use_container_width=True, 
        hide_index=True
    )
    
    st.markdown("---")
    st.success("Análise de desempenho carregada. Use os filtros para refinar os resultados.")
    st.caption("Fonte: Dados simulados baseados em métricas comuns de OOH.")

else:
    st.warning("Nenhuma campanha encontrada com os filtros selecionados.")
