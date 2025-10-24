# pages/1_Mapa_Interativo.py
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
from folium import FeatureGroup, LayerControl
# Importação simulada (assumindo que estas bibliotecas e arquivos existem)
from streamlit_folium import st_folium

# Mock/Simulação das importações de src para evitar erros de UI
# Na vida real, você PRECISARIA dessas funções funcionando:
try:
    from src.fetchers import fetch_pois_overpass
    from src.geoprocess import pois_to_gdf, create_buffers
    
    # Adicionar uma função utilitária de estilo se existir
    from src.utils import set_page_config_and_style
except ImportError:
    # Apenas para que o código da UI não quebre se as fontes não existirem
    def fetch_pois_overpass(bbox): return pd.DataFrame()
    def pois_to_gdf(df): return df
    def create_buffers(gdf, radius_m): return gdf
    def set_page_config_and_style(page_title, main_title, subtitle):
        st.set_page_config(layout="wide", page_title=page_title)
        st.title(main_title)
        st.markdown(f"**{subtitle}**")
        
# -------------------------------
# CONFIGURAÇÕES DA PÁGINA (Melhor UX)
# -------------------------------
set_page_config_and_style(
    page_title="Mapa Interativo",
    main_title="MAPA TÁTICO: MÍDIAS OOH E PONTOS DE INTERESSE",
    subtitle="Análise da densidade de mídias e sua proximidade a pontos de tráfego (Ex: Paradas de Ônibus)."
)


# -------------------------------
# Configurações de performance (Mantidas)
# -------------------------------
MAX_POINTS = 1000        # limite de POIs exibidos
DELTA_DEG = 0.01         # ~1 km em cada direção
MAX_BUFFERS = 30         # evita poluição visual

# -------------------------------
# LAYOUT UI: FILTROS NA BARRA LATERAL
# -------------------------------
st.sidebar.header("🗺️ Controles do Mapa")

# Coluna 1: Buffer
buffer_m = st.sidebar.selectbox(
    "Buffer (Raio de Análise em metros)", 
    [250, 500, 1000, 1500], 
    index=1,
    help="Define o raio de proximidade para calcular a intersecção de mídias com POIs."
)

# Coluna 2: Buffers On/Off
show_buffers = st.sidebar.checkbox(
    "Mostrar polígonos de Buffer", 
    value=False,
    help=f"Exibe os círculos de {buffer_m}m de raio ao redor dos POIs (Limite: {MAX_BUFFERS} buffers)."
)

# Instrução principal (Visível e Destacada)
st.markdown("""
### 📍 Como Usar:
1.  **Clique em qualquer ponto do mapa** (ex: no centro da cidade).
2.  O sistema buscará Mídias OOH e Paradas de Ônibus (POIs) em um raio de 2km ao redor.
3.  Use os **Filtros na Barra Lateral** para refinar a visualização.
""")


# -------------------------------
# Mapa inicial (Melhor visualização do Folium)
# -------------------------------
center_lat, center_lon = -23.55, -46.63  # São Paulo
if "map_lat" not in st.session_state:
    st.session_state.map_lat = center_lat
    st.session_state.map_lon = center_lon

# Adicionando um tileset mais limpo para melhor visualização OOH
m = folium.Map(
    location=[st.session_state.map_lat, st.session_state.map_lon], 
    zoom_start=13,
    tiles="CartoDB positron" # Tiles mais claros e focados em dados
)

# Captura clique
map_data = st_folium(m, width=900, height=550, returned_objects=["last_clicked"])

# -------------------------------
# Processamento e Lógica (Mantendo a lógica existente)
# -------------------------------
if map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    
    # Atualiza o estado da sessão com o novo ponto clicado
    st.session_state.click_lat = lat
    st.session_state.click_lon = lon
    st.session_state.map_lat = lat
    st.session_state.map_lon = lon

    st.sidebar.success(f"Novo ponto selecionado: Lat {lat:.4f}, Lon {lon:.4f}. Processando POIs...")


# -------------------------------
# CONSULTA E EXIBIÇÃO APÓS CLIQUE
# -------------------------------

if "click_lat" in st.session_state and "click_lon" in st.session_state:
    lat = st.session_state.click_lat
    lon = st.session_state.click_lon

    # bbox ~ 2 km x 2 km
    bbox = f"{lat - DELTA_DEG},{lon - DELTA_DEG},{lat + DELTA_DEG},{lon + DELTA_DEG}"

    # Usando um container com o spinner
    with st.container():
        st.markdown("---")
        st.subheader(f"Resultados de POIs na Região (BBox ~4km²)")
        
        with st.spinner(f"Consultando Overpass API ao redor de {lat:.4f}, {lon:.4f}..."):
            try:
                # 1. Busca os dados
                df = fetch_pois_overpass(bbox)
                
                if df.empty:
                    st.info("Nenhum Ponto de Interesse (POI) relevante encontrado nesta área ou a API Overpass não retornou dados.")
                    st.stop()
                    
                # 2. Determina e filtra tipos de POI (UI mais integrada)
                poi_types = set()

                # Adiciona tipos de advertising e highway se existirem nas colunas
                if "advertising" in df.columns:
                    poi_types.update(df["advertising"].dropna().unique())
                if "highway" in df.columns:
                    poi_types.update(df["highway"].dropna().unique())

                if not poi_types:
                    poi_types = {"unknown"}

                poi_types = sorted(list(poi_types))
                
                # UI para filtrar tipos de POI (Melhor posicionado)
                col_type_filter, col_metrics = st.columns([2, 1])
                
                with col_type_filter:
                    selected_types = st.multiselect(
                        "Filtrar Tipos de Ponto de Interesse (POI)", 
                        poi_types, 
                        default=[t for t in poi_types if t in ['bus_stop', 'billboard', 'poster_box']] # Sugestão de default
                    )

                # Aplica o filtro de DataFrame (mantido da lógica original)
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

                # 3. Limite de pontos e geoprocessamento
                total_encontrado = len(df_filtered)
                if total_encontrado == 0:
                    st.warning("O filtro selecionado não resultou em nenhum POI. Ajuste os filtros.")
                    st.stop()
                
                # Limite de pontos
                if total_encontrado > MAX_POINTS:
                    with col_metrics:
                         st.metric("Total de POIs Encontrados", f"{total_encontrado:,}")
                         st.warning(f"Exibindo apenas {MAX_POINTS:,} aleatórios para performance.")
                    df_filtered = df_filtered.sample(MAX_POINTS, random_state=42)
                else:
                     with col_metrics:
                         st.metric("Total de POIs Encontrados", f"{total_encontrado:,}")
                
                
                # Processamento geográfico
                gdf = pois_to_gdf(df_filtered)
                gdf_buf = create_buffers(gdf, radius_m=buffer_m)


                # 4. EXIBIÇÃO NO MAPA (Lógica mantida)
                
                # Configurações do mapa final (movendo o mapa para o centro do clique)
                m = folium.Map(
                    location=[lat, lon], 
                    zoom_start=14, # Zoom in após o clique
                    tiles="CartoDB positron"
                )
                
                if len(gdf) > 500:
                    # HeatMap para grandes volumes
                    heat_data = [[row.lat, row.lon] for _, row in gdf.iterrows() if pd.notna(row.lat) and pd.notna(row.lon)]
                    HeatMap(heat_data, radius=15).add_to(m)
                    st.info("O mapa está exibindo a densidade (HeatMap) de POIs devido ao grande volume de dados.")
                else:
                    # Marcadores e Clusters para menor volume
                    layers = {}
                    # ... (Lógica de Marcadores e Clusters exatamente como no código original) ...
                    for poi_type in selected_types:
                        layer_name = poi_type.replace("_", " ").title()
                        layers[poi_type] = FeatureGroup(name=layer_name).add_to(m)
                        cluster = MarkerCluster().add_to(layers[poi_type])

                        subset = gdf[
                            (gdf.get("advertising") == poi_type) |
                            (gdf.get("highway") == poi_type)
                        ]
                        
                        for _, r in subset.iterrows():
                            lat_r, lon_r = r.lat, r.lon
                            if pd.isna(lat_r) or pd.isna(lon_r):
                                continue

                            # Define cor (Lógica de cores mantida)
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
                
                # Buffers (limitados)
                if show_buffers and len(gdf_buf) > 0:
                    buf_subset = gdf_buf.head(MAX_BUFFERS)
                    if len(gdf_buf) > MAX_BUFFERS:
                        st.info(f"Mostrando apenas {MAX_BUFFERS} buffers de {len(gdf_buf)} totais.")
                    
                    buffer_group = FeatureGroup(name=f"Buffers ({buffer_m}m)", show=True).add_to(m)
                    for _, r in buf_subset.iterrows():
                        folium.GeoJson(
                            r.geometry.__geo_interface__,
                            style_function=lambda x: {"color": "darkred", "fillOpacity": 0.05, "weight": 1.5},
                        ).add_to(buffer_group)

                # Controle de camadas
                LayerControl().add_to(m)
                
                # Salva para uso futuro
                st.session_state.df_pois = df_filtered

                # Exibe mapa final (O mapa será renderizado aqui, dentro do container)
                st_folium(m, width=900, height=600, key="final_map")

            except Exception as e:
                # Trata erros que possam surgir do geoprocessamento ou Overpass
                st.error(f"Erro ao processar ou exibir os dados: {type(e).__name__}: {e}")
                st.info("Verifique se as bibliotecas `geopandas` e `shapely` estão instaladas e se as funções em `src/` estão corretas.")

# -------------------------------
# Rodapé informativo
# -------------------------------
st.markdown("---")
st.caption("Dados fornecidos pela Overpass API (OpenStreetMap). A disponibilidade e precisão dos POIs podem variar.")
