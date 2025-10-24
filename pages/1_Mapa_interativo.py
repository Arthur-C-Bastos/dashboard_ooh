# pages/1_Mapa_Interativo.py

import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
from folium import FeatureGroup, LayerControl
from streamlit_folium import st_folium

from src.fetchers import fetch_pois_overpass
from src.geoprocess import pois_to_gdf, create_buffers

# -------------------------------
# Configurações de performance
# -------------------------------
MAX_POINTS = 1000      # limite de POIs exibidos
DELTA_DEG = 0.01       # ~1 km em cada direção
MAX_BUFFERS = 30       # evita poluição visual

# -------------------------------
# Cabeçalho
# -------------------------------
st.header("Mapa Interativo – Pontos OOH e Paradas de Ônibus")
st.markdown("""
Clique no mapa para selecionar a região.  
O sistema buscará POIs ao redor do ponto clicado.  
Use filtros, buffers e HeatMap para grandes volumes.
""")

# -------------------------------
# Inputs
# -------------------------------
buffer_m = st.selectbox("Buffer (metros)", [250, 500, 1000], index=1)
show_buffers = st.checkbox("Mostrar buffers", value=True)

# -------------------------------
# Mapa inicial
# -------------------------------
center_lat, center_lon = -23.55, -46.63  # São Paulo
if "map_lat" not in st.session_state:
    st.session_state.map_lat = center_lat
    st.session_state.map_lon = center_lon

m = folium.Map(location=[st.session_state.map_lat, st.session_state.map_lon], zoom_start=12)

# Captura clique
map_data = st_folium(m, width=700, height=500, returned_objects=["last_clicked"])

if map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.session_state.click_lat = lat
    st.session_state.click_lon = lon
    st.session_state.map_lat = lat
    st.session_state.map_lon = lon

# -------------------------------
# Consulta e processamento (após clique)
# -------------------------------
if "click_lat" in st.session_state and "click_lon" in st.session_state:
    lat = st.session_state.click_lat
    lon = st.session_state.click_lon

    # bbox ~ 2 km x 2 km
    bbox = f"{lat - DELTA_DEG},{lon - DELTA_DEG},{lat + DELTA_DEG},{lon + DELTA_DEG}"

    with st.spinner("Consultando Overpass API..."):
        try:
            df = fetch_pois_overpass(bbox)
            if df.empty:
                st.info("Nenhum POI encontrado nesta área.")
            else:
                # -------------------------------
                # Determina tipos de POI (advertising + highway)
                # -------------------------------
                poi_types = set()

                if "advertising" in df.columns:
                    poi_types.update(df["advertising"].dropna().unique())
                if "highway" in df.columns:
                    poi_types.update(df["highway"].dropna().unique())

                if not poi_types:
                    poi_types = {"unknown"}

                poi_types = sorted(list(poi_types))
                selected_types = st.multiselect(
                    "Filtrar tipos de POI", poi_types, default=poi_types
                )

                # -------------------------------
                # Filtra DataFrame com segurança
                # -------------------------------
                conditions = []
                if "advertising" in df.columns:
                    conditions.append(df["advertising"].isin(selected_types))
                if "highway" in df.columns:
                    conditions.append(df["highway"].isin(selected_types))

                if conditions:
                    mask = pd.concat(conditions, axis=1).any(axis=1)
                    df_filtered = df[mask]
                else:
                    df_filtered = df.copy()

                # Limite de pontos
                if len(df_filtered) > MAX_POINTS:
                    st.warning(f"Muitos POIs. Exibindo apenas {MAX_POINTS} aleatórios.")
                    df_filtered = df_filtered.sample(MAX_POINTS, random_state=42)

                # GeoDataFrame + buffers
                gdf = pois_to_gdf(df_filtered)
                gdf_buf = create_buffers(gdf, radius_m=buffer_m)

                # -------------------------------
                # HeatMap para muitos pontos
                # -------------------------------
                if len(gdf) > 500:
                    heat_data = [[row.lat, row.lon] for _, row in gdf.iterrows() if pd.notna(row.lat) and pd.notna(row.lon)]
                    HeatMap(heat_data, radius=15).add_to(m)
                    st.info("HeatMap ativado (muitos pontos).")
                else:
                    # -------------------------------
                    # Marcadores com cores corretas
                    # -------------------------------
                    layers = {}
                    for poi_type in selected_types:
                        layer_name = poi_type.replace("_", " ").title()
                        layers[poi_type] = FeatureGroup(name=layer_name).add_to(m)
                        cluster = MarkerCluster().add_to(layers[poi_type])

                        # Subset seguro
                        subset = gdf[
                            (gdf.get("advertising") == poi_type) |
                            (gdf.get("highway") == poi_type)
                        ]

                        for _, r in subset.iterrows():
                            lat_r, lon_r = r.lat, r.lon
                            if pd.isna(lat_r) or pd.isna(lon_r):
                                continue

                            # Define cor
                            if poi_type == "bus_stop" or r.get("highway") == "bus_stop":
                                color = "green"
                            elif poi_type in ["billboard", "poster_box", "column"] or r.get("advertising") in ["billboard", "poster_box", "column"]:
                                color = "red"
                            else:
                                color = "blue"

                            folium.CircleMarker(
                                location=[lat_r, lon_r],
                                radius=5,
                                popup=folium.Popup(
                                    f"<b>{poi_type.replace('_', ' ').title()}</b><br>"
                                    f"Nome: {r.get('name', 'N/A')}<br>"
                                    f"ID: {r.get('id', 'N/A')}",
                                    max_width=300
                                ),
                                color=color,
                                fill=True,
                                fill_color=color,
                                fill_opacity=0.8,
                                weight=2,
                            ).add_to(cluster)

                # -------------------------------
                # Buffers (limitados)
                # -------------------------------
                if show_buffers and len(gdf_buf) > 0:
                    buf_subset = gdf_buf.head(MAX_BUFFERS)
                    if len(gdf_buf) > MAX_BUFFERS:
                        st.info(f"Mostrando apenas {MAX_BUFFERS} buffers.")
                    for _, r in buf_subset.iterrows():
                        folium.GeoJson(
                            r.geometry.__geo_interface__,
                            style_function=lambda x: {"color": "blue", "fillOpacity": 0.03, "weight": 1},
                        ).add_to(m)

                # Controle de camadas
                LayerControl().add_to(m)

                # Salva para uso futuro
                st.session_state.df_pois = df_filtered

                # Exibe mapa final
                st_folium(m, width=900, height=600)

        except Exception as e:
            st.error(f"Erro ao consultar Overpass: {e}")
