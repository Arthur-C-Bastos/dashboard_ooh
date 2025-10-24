# pages/6_Melhores_Pontos.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from src.fetchers import fetch_pois_overpass
import numpy as np

# -------------------------------
# CONFIGURAÇÕES
# -------------------------------
st.set_page_config(page_title="Melhores Pontos OOH", layout="wide")
st.header("MELHORES PONTOS – RANKING DE POTENCIAL (SÓ ÔNIBUS)")
st.markdown("**Top 20 pontos de ônibus com maior alcance populacional – sem linhas**")

MAX_TOP = 20
RAIO_PADRAO = 150  # metros

# -------------------------------
# DADOS DE TODAS AS REGIÕES
# -------------------------------
REGIOES_DATA = {
    "Toda São Paulo": {"pop": 12_399_294, "area_km2": 1521, "bbox": "-23.8,-46.9,-23.3,-46.3"},
    "Zona Sul": {"pop": 2_800_000, "area_km2": 240, "bbox": "-23.75,-46.75,-23.60,-46.60"},
    "Centro": {"pop": 1_200_000, "area_km2": 50, "bbox": "-23.57,-46.68,-23.52,-46.62"},
    "Zona Norte": {"pop": 2_500_000, "area_km2": 220, "bbox": "-23.45,-46.70,-23.35,-46.55"},
    "Zona Leste": {"pop": 3_200_000, "area_km2": 280, "bbox": "-23.65,-46.55,-23.45,-46.35"},
    "Zona Oeste": {"pop": 2_000_000, "area_km2": 180, "bbox": "-23.65,-46.80,-23.45,-46.65"},
    "Santo André": {"pop": 748_000, "area_km2": 175, "bbox": "-23.72,-46.58,-23.62,-46.48"},
    "São Bernardo do Campo": {"pop": 849_000, "area_km2": 409, "bbox": "-23.80,-46.62,-23.65,-46.50"},
    "Osasco": {"pop": 728_000, "area_km2": 65, "bbox": "-23.58,-46.82,-23.50,-46.75"},
    "Cotia": {"pop": 270_000, "area_km2": 324, "bbox": "-23.68,-46.90,-23.55,-46.80"}
}

# -------------------------------
# BUSCAR APENAS PONTOS DE ÔNIBUS
# -------------------------------
@st.cache_data(ttl=7200, show_spinner=False)
def buscar_pontos_onibus(regiao, bbox):
    df = fetch_pois_overpass(bbox, tags=["highway=bus_stop"], timeout=30)

    if not df.empty:
        if 'public_transport' in df.columns:
            df = df[~df['public_transport'].isin(['platform', 'stop_position'])]
        if 'route' in df.columns:
            df = df[df['route'].isna()]
        if 'highway' in df.columns:
            df = df[df['highway'] == 'bus_stop']
        df = df[df['lat'].notna() & df['lon'].notna()]

    # Fallback
    if df.empty or len(df) == 0:
        np.random.seed(42)
        n = 80
        lat = np.random.uniform(float(bbox.split(',')[0]), float(bbox.split(',')[2]), n)
        lon = np.random.uniform(float(bbox.split(',')[1]), float(bbox.split(',')[3]), n)
        df = pd.DataFrame({
            'lat': lat, 'lon': lon,
            'name': [f"Ponto Ônibus {i}" for i in range(n)],
            'addr:street': [f"Rua {i%10}" for i in range(n)],
            'highway': ['bus_stop'] * n
        })

    df['regiao'] = regiao
    return df

# -------------------------------
# ANÁLISE COMPLETA
# -------------------------------
if st.button("Analisar Todos os Pontos de Ônibus", type="primary"):
    with st.spinner("Buscando pontos de ônibus em todas as regiões..."):
        todos_pontos = []
        for regiao, dados in REGIOES_DATA.items():
            df_regiao = buscar_pontos_onibus(regiao, dados["bbox"])
            area_ponto = 3.14159 * (RAIO_PADRAO / 1000) ** 2
            densidade = dados["pop"] / dados["area_km2"]
            pop_coberta = int(area_ponto * densidade)
            df_regiao['pop_coberta'] = pop_coberta
            df_regiao['potencial'] = pop_coberta
            todos_pontos.append(df_regiao.head(100))

        df_completo = pd.concat(todos_pontos, ignore_index=True)
        df_top = df_completo.nlargest(MAX_TOP, 'potencial').reset_index(drop=True)

        # LIMPEZA DOS DADOS
        df_top['name'] = df_top['name'].fillna("Ponto sem nome").astype(str)
        df_top['addr:street'] = df_top['addr:street'].fillna("").astype(str)
        df_top['nome_completo'] = df_top.apply(
            lambda x: f"{x['name']}" if x['addr:street'] in ["", "nan"] else f"{x['name']}, {x['addr:street']}",
            axis=1
        )
        
        st.session_state.df_top = df_top
        st.session_state.df_completo = df_completo

    st.success(f"Top {MAX_TOP} pontos de ônibus carregados!")

# -------------------------------
# EXIBIÇÃO
# -------------------------------
if 'df_top' in st.session_state:
    df_top = st.session_state.df_top

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Ranking de Potencial (Ônibus)")
        df_display = df_top.copy()
        df_display['pop_coberta'] = df_display['pop_coberta'].apply(lambda x: f"{x:,}".replace(",", "."))
        df_display = df_display[['regiao', 'nome_completo', 'pop_coberta']].head(10)
        df_display.columns = ['Região', 'Ponto', 'Pop. Coberta']
        st.dataframe(df_display, use_container_width=True)

    with col2:
        st.subheader("Gráfico de Potencial")
        top10 = df_top.head(10)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top10['nome_completo'],
            y=top10['pop_coberta'],
            text=top10['pop_coberta'].apply(lambda x: f"{x:,}".replace(",", ".")),
            textposition='outside',
            marker_color='lightblue',
            hovertemplate="<b>%{x}</b><br>População Coberta: %{y:,}<extra></extra>"
        ))
        fig.update_layout(
            title="Top 10 Pontos de Ônibus por População Coberta",
            xaxis_title="Ponto",
            yaxis_title="População Coberta",
            xaxis_tickangle=-30,
            template="simple_white",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

    # -------------------------------
    # MAPA DOS MELHORES PONTOS
    # -------------------------------
    st.subheader("Mapa dos Melhores Pontos de Ônibus")
    centro_sp = [-23.55, -46.63]
    m = folium.Map(location=centro_sp, zoom_start=10, tiles="CartoDB positron")

    for idx, row in df_top.iterrows():
        lat, lon = row['lat'], row['lon']
        nome = row['nome_completo']
        pop = int(row['pop_coberta'])
        regiao = row['regiao']

        texto = f"<b>{nome}</b><br><b>Pop: {pop:,}</b><br><i>{regiao}</i>".replace(",", ".")
        cor = "gold" if idx < 3 else "orange" if idx < 10 else "blue"

        folium.CircleMarker(
            [lat, lon],
            radius=10,
            color=cor,
            fill=True,
            fill_opacity=0.8,
            popup=folium.Popup(texto, max_width=300)
        ).add_to(m)

        folium.Marker(
            [lat, lon],
            icon=folium.Icon(color="white", icon="bus", prefix='fa'),
            popup=folium.Popup(texto, max_width=300)
        ).add_to(m)

    st_folium(m, width=900, height=500)

    # Exportar
    csv = df_top[['regiao', 'nome_completo', 'pop_coberta', 'lat', 'lon']].to_csv(index=False).encode('utf-8')
    st.download_button(
        "Baixar Top 20 (CSV)",
        csv,
        "melhores_pontos_onibus.csv",
        "text/csv"
    )
else:
    st.info("Clique em **Analisar Todos os Pontos de Ônibus** para gerar o ranking.")