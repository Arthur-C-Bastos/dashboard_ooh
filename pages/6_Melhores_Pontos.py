import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.utils import set_page_config_and_style # Importa a função de padronização

# -------------------------------
# CONFIGURAÇÕES GERAIS E ESTILO PADRÃO
# -------------------------------
set_page_config_and_style(
    page_title="Melhores Pontos OOH",
    main_title="CLASSIFICAÇÃO DOS MELHORES PONTOS OOH",
    subtitle="Análise Geográfica de Ativos e Ranking por Desempenho (Score)"
)

# -------------------------------
# FUNÇÃO SIMULADA DE GERAÇÃO DE DADOS
# -------------------------------
@st.cache_data(ttl=3600)
def generate_ooh_points():
    """Gera dados simulados de pontos OOH (Out-of-Home) em São Paulo."""
    
    # Coordenadas aproximadas de pontos centrais e estratégicos de SP
    data = {
        'ID_Ponto': [f'OOH-{i:03}' for i in range(1, 26)],
        'Latitude': [
            -23.5505, -23.5430, -23.5614, -23.5520, -23.5630, # Centro/Paulista
            -23.5850, -23.6000, -23.5780, -23.5700, -23.5480, # Zona Oeste/Sul
            -23.5200, -23.5000, -23.4800, -23.4700, -23.4500, # Zona Norte
            -23.6500, -23.6300, -23.6100, -23.5900, -23.5300, # Zona Sul/Marginal
            -23.5400, -23.5350, -23.5450, -23.5550, -23.5650, # Outros
        ],
        'Longitude': [
            -46.6333, -46.6500, -46.6667, -46.6833, -46.6200,
            -46.6900, -46.6700, -46.6550, -46.6450, -46.6350,
            -46.6100, -46.5900, -46.5700, -46.5500, -46.5300,
            -46.6000, -46.5800, -46.5600, -46.5400, -46.6400,
            -46.6700, -46.6800, -46.6600, -46.6550, -46.6450,
        ],
        'Audiência Diária (Milhares)': np.random.randint(20, 150, 25),
        'Custo Mensal (R$ Mil)': np.random.uniform(5.0, 50.0, 25).round(1),
        'Tipo': ['Digital', 'Estático'] * 12 + ['Digital'],
        'Zona': ['Centro', 'Oeste', 'Sul', 'Norte', 'Leste'] * 5
    }
    df = pd.DataFrame(data)
    
    # --- Cálculo do Score (Métrica principal para ranking) ---
    # Score é Audiência * (1 / Custo) * Fator de Impacto
    df['Custo por Audiência (R$/mil)'] = (df['Custo Mensal (R$ Mil)'] * 1000) / df['Audiência Diária (Milhares)']
    df['Fator de Impacto'] = np.random.uniform(0.8, 1.2, 25).round(2)
    
    # Exemplo simples de Score: quanto maior, melhor
    df['Score OOH'] = (df['Audiência Diária (Milhares)'] / df['Custo por Audiência (R$/mil)']) * df['Fator de Impacto']
    df['Score OOH'] = df['Score OOH'].rank(ascending=False).astype(int)
    
    return df

df_pontos = generate_ooh_points()

# -------------------------------
# CONTROLES E FILTROS
# -------------------------------
st.markdown("### Seleção e Filtros de Pontos")
col_tipo, col_zona, col_custo = st.columns(3)

with col_tipo:
    tipos_selecionados = st.multiselect("Filtrar por Tipo de Mídia", df_pontos['Tipo'].unique(), default=df_pontos['Tipo'].unique())

with col_zona:
    zonas_selecionadas = st.multiselect("Filtrar por Zona", df_pontos['Zona'].unique(), default=df_pontos['Zona'].unique())

with col_custo:
    custo_max = st.slider("Custo Mensal Máximo (R$ Mil)", 
                          min_value=5.0, 
                          max_value=df_pontos['Custo Mensal (R$ Mil)'].max().round() + 5, 
                          value=df_pontos['Custo Mensal (R$ Mil)'].max().round(), 
                          step=1.0)

# Aplicar Filtros
df_filtrado = df_pontos[
    (df_pontos['Tipo'].isin(tipos_selecionados)) &
    (df_pontos['Zona'].isin(zonas_selecionadas)) &
    (df_pontos['Custo Mensal (R$ Mil)'] <= custo_max)
].copy()

# Ordenar por Score para o ranking
df_ranking = df_filtrado.sort_values(by='Score OOH', ascending=True)

# -------------------------------
# 1. MAPA (Esquerda) e RANKING (Direita)
# -------------------------------
st.markdown("---")
col_mapa, col_ranking = st.columns([2, 1])

if not df_filtrado.empty:
    
    # --- 1.1 MAPA INTERATIVO (PLANO DE FUNDO) ---
    with col_mapa:
        st.markdown("##### Visualização Geográfica dos Ativos")
        # O mapa de dispersão do Plotly é melhor para visualização interativa do que st.map
        fig_mapa = px.scatter_mapbox(
            df_filtrado,
            lat="Latitude",
            lon="Longitude",
            color="Score OOH", 
            size="Audiência Diária (Milhares)",
            color_continuous_scale=px.colors.cyclical.IceFire,
            zoom=10, 
            height=600,
            mapbox_style="carto-positron", # Estilo claro e profissional
            hover_data={
                'ID_Ponto': True,
                'Audiência Diária (Milhares)': ':.1f',
                'Custo Mensal (R$ Mil)': ':.1f',
                'Score OOH': True,
                'Latitude': False,
                'Longitude': False,
            }
        )
        # Centralizar no ponto médio (São Paulo)
        fig_mapa.update_layout(
            mapbox_center={"lat": -23.5505, "lon": -46.6333},
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        st.plotly_chart(fig_mapa, use_container_width=True)


    # --- 1.2 RANKING DE PONTOS (TABELA) ---
    with col_ranking:
        st.markdown(f"##### Ranking (Top {min(5, len(df_ranking))})")
        
        # Métrica de ponto de melhor performance (Top 1)
        top_ponto = df_ranking.iloc[-1]
        st.info(f"""
            **Melhor Ponto:** {top_ponto['ID_Ponto']} ({top_ponto['Zona']})  
            **Score:** {top_ponto['Score OOH']}  
            **Audiência:** {top_ponto['Audiência Diária (Milhares)']} mil/dia
        """)
        
        # Tabela de Ranking
        df_ranking_display = df_ranking.tail(5)[['ID_Ponto', 'Score OOH', 'Audiência Diária (Milhares)', 'Custo Mensal (R$ Mil)']].copy()
        
        df_ranking_display.rename(columns={
            'Audiência Diária (Milhares)': 'Audiência (mil)',
            'Custo Mensal (R$ Mil)': 'Custo (R$ mil)'
        }, inplace=True)
        
        st.dataframe(
            df_ranking_display.sort_values(by='Score OOH', ascending=False),
            use_container_width=True, 
            hide_index=True
        )

    # -------------------------------
    # 2. MÉTRICAS CONSOLIDADAS
    # -------------------------------
    st.markdown("---")
    st.markdown("### Métricas de Performance do Portfólio Selecionado")
    
    total_audiencia = df_filtrado['Audiência Diária (Milhares)'].sum()
    total_custo = df_filtrado['Custo Mensal (R$ Mil)'].sum()
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Total de Ativos", len(df_filtrado))
    with col_b:
        st.metric("Audiência Diária Total", f"{total_audiencia:,.0f} mil".replace(",", "."))
    with col_c:
        st.metric("Custo Mensal Agregado", f"R$ {total_custo:,.0f} mil".replace(",", "."))
        
    st.caption("Score OOH é uma métrica interna calculada para otimização de custo e audiência. Quanto menor o Score, maior a prioridade de revisão do ponto.")

else:
    st.warning("Nenhum ponto OOH encontrado com os filtros selecionados. Ajuste os critérios.")
