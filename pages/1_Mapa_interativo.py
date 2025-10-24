# pages/1_Mapa_Interativo.py
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
from folium import FeatureGroup, LayerControl
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError 

# -------------------------------
# CONFIGURAÇÕES DE PERFORMANCE E CONSTANTES
# -------------------------------
MAX_POINTS = 1000        # limite de POIs exibidos
DELTA_DEG = 0.01         # ~1 km em cada direção (para a bbox do Overpass)
MAX_BUFFERS = 30         # evita poluição visual de buffers
MAP_DEFAULT_CENTER = (-23.55, -46.63) # São Paulo (Latitude, Longitude)

# -------------------------------
# MOCKS/SIMULAÇÃO E UTILS (GARANTIR QUE O CÓDIGO RODE)
# -------------------------------
# Assegure-se de que seus arquivos 'src/' contenham as implementações REAIS dessas funções.
try:
    from src.fetchers import fetch_pois_overpass
    from src.geoprocess import pois_to_gdf, create_buffers
    # Tenta importar uma função de estilo se existir
    from src.utils import set_page_config_and_style
except ImportError:
    # Mocks para desenvolvimento da UI
    def fetch_pois_overpass(bbox): return pd.DataFrame()
    def pois_to_gdf(df): return df
    def create_buffers(gdf, radius_m): return gdf
    def set_page_config_and_style(page_title, main_title, subtitle):
        st.set_page_config(layout="wide", page_title=page_title)
        st.title(main_title)
        st.markdown(f"**{subtitle}**")

# -------------------------------
# FUNÇÕES DE CACHE
# -------------------------------
@st.cache_data(ttl=3600) 
def geocode_address(address):
    """Converte endereço ou nome para coordenadas (lat/lon) usando Nominatim."""
    geolocator = Nominatim(user_agent="ooh_analysis_app")
    try:
        location = geolocator.geocode(address, timeout=10) 
        if location:
            return location.latitude, location.longitude
        return None, None
    except GeocoderTimedOut:
        # Não podemos usar st.sidebar.error aqui, a exceção será tratada no corpo principal
        return None, None
    except GeocoderServiceError:
        return None, None
    except Exception:
        return None, None


# -------------------------------
# CONFIGURAÇÕES DA PÁGINA
# -------------------------------
set_page_config_and_style(
    page_title="Mapa Interativo",
    main_title="MAPA TÁTICO: MÍDIAS OOH E PONTOS DE INTERESSE",
    subtitle="Análise da densidade de mídias e sua proximidade a pontos de tráfego."
)


# -------------------------------
# LAYOUT UI: FILTROS NA BARRA LATERAL
# -------------------------------
st.sidebar.header("🗺️ Controles do Mapa")

# NOVO BLOCO: PESQUISA POR BAIRRO/ENDEREÇO
st.sidebar.subheader("1. Pesquisar Local")
search_term = st.sidebar.text_input(
    "Digite Bairro, Rua ou Ponto de Referência",
    placeholder="Ex: Av. Paulista, São Paulo",
    key="search_input"
)

# Variável de estado para controlar a ação do botão
if 'run_search' not in st.session_state:
    st.session_state.run_search = False

if st.sidebar.button("Pesquisar e Centralizar Mapa", use_container_width=True):
    st.session_state.run_search = True
    
if st.session_state.run_search and st.session_state.search_input:
    # Lógica de Geocoding (agora no corpo principal para evitar o erro de spinner)
    # A atualização do mapa e a busca de POIs ocorrerá depois.
    pass # Deixamos o spinner e a lógica para o corpo principal

st.sidebar.markdown("---")


# FILTROS DE BUFFER
st.sidebar.subheader("2. Ajustes de Análise")
buffer_m = st.sidebar.selectbox(
    "Buffer (Raio de Análise em metros)", 
    [250, 500, 1000, 1500], 
    index=1,
    key='buffer_map'
)

show_buffers = st.sidebar.checkbox(
    "Mostrar polígonos de Buffer", 
    value=False,
    key='show_buffers_map'
)
st.sidebar.markdown("---")


# -------------------------------
# LÓGICA DE GEOCODING NO CORPO PRINCIPAL (CORREÇÃO DO ERRO)
# -------------------------------
if st.session_state.run_search and st.session_state.search_input:
    # O spinner agora está no CORPO PRINCIPAL
    with st.spinner(f"Buscando coordenadas para '{st.session_state.search_input}'..."):
        new_lat, new_lon = geocode_address(st.session_state.search_input)
        
        # Reseta o estado
        st.session_state.run_search = False 
        
        if new_lat and new_lon:
            # Atualiza o estado da sessão
            st.session_state.map_lat = new_lat
            st.session_state.map_lon = new_lon
            st.session_state.click_lat = new_lat
            st.session_state.click_lon = new_lon
            st.success(f"Mapa centralizado em: **{st.session_state.search_input}**.")
            st.info("O sistema iniciará a busca de POIs na nova localização.")
        else:
            st.error("Local não encontrado ou houve um erro no serviço de pesquisa. Tente refinar a pesquisa.")
            
# -------------------------------
# INSTRUÇÃO PRINCIPAL
# -------------------------------
st.markdown("""
### 💡 Como Usar:
1.  Use a **Barra Lateral** para pesquisar um local (bairro/rua).
2.  Ou, **clique diretamente no mapa** (onde diz "Leaflet") para selecionar a região de interesse.
""")


# -------------------------------
# MAPA INICIAL/ATUALIZADO (FOLIUM)
# -------------------------------
center_lat, center_lon = st.session_state.get("map_lat", MAP_DEFAULT_CENTER[0]), \
                         st.session_state.get("map_lon", MAP_DEFAULT_CENTER[1])
if "zoom_level" not in st.session_state:
    st.session_state.zoom_level = 13

m = folium.Map(
    location=[center_lat, center_lon], 
    zoom_start=st.session_state.zoom_level,
    tiles="CartoDB positron" 
)

# Captura clique
map_data = st_folium(m, width=900, height=550, returned_objects=["last_clicked", "zoom"], key="initial_map_view")

# Atualiza o zoom_level para manter o estado
if map_data and map_data.get("zoom") is not None:
    st.session_state.zoom_level = map_data["zoom"]

# -------------------------------
# TRATAMENTO DO CLIQUE MANUAL
# -------------------------------
if map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    
    # Só atualiza se for um novo ponto
    if lat != st.session_state.get("click_lat") or lon != st.session_state.get("click_lon"):
        st.session_state.click_lat = lat
        st.session_state.click_lon = lon
        st.session_state.map_lat = lat
        st.session_state.map_lon = lon
        st.info(f"Novo ponto clicado: Lat {lat:.4f}, Lon {lon:.4f}. Iniciando consulta de POIs...")


# -------------------------------
# CONSULTA E EXIBIÇÃO APÓS CLIQUE/PESQUISA (LÓGICA COMPLETA)
# -------------------------------

if "click_lat" in st.session_state and "click_lon" in st.session_state:
    lat = st.session_state.click_lat
    lon = st.session_state.click_lon

    bbox = f"{lat - DELTA_DEG},{lon - DELTA_DEG},{lat + DELTA_DEG},{lon + DELTA_DEG}"

    with st.container():
        st.markdown("---")
        st.subheader(f"Resultados de POIs na Região (BBox ~4km²)")
        
        with st.spinner(f"Consultando Overpass API ao redor de {lat:.4f}, {lon:.4f}..."):
            try:
                df = fetch_pois_overpass(bbox)
                
                if df.empty:
                    st.info("Nenhum Ponto de Interesse (POI) relevante encontrado nesta área.")
                    st.stop()
                    
                # 1. Determina tipos de POI para filtro
                poi_types = set()
                if "advertising" in df.columns:
                    poi_types.update(df["advertising"].dropna().unique())
                if "highway" in df.columns:
                    poi_types.update(df["highway"].dropna().unique())

                poi_types = sorted(list(poi_types))
                
                # UI para filtrar tipos de POI
                col_type_filter, col_metrics = st.columns([2, 1])
                
                with col_type_filter:
                    selected_types = st.multiselect(
                        "Filtrar Tipos de Ponto de Interesse (POI)", 
                        poi_types, 
                        default=[t for t in poi_types if t in ['bus_stop', 'billboard', 'poster_box']]
                    )

                # Aplica o filtro
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

                # Checa se o filtro resultou em algo
                total_encontrado = len(df_filtered)
                if total_encontrado == 0:
                    st.warning("O filtro selecionado não resultou em nenhum POI. Ajuste os filtros.")
                    st.stop()
                
                # Exibe métricas
                with col_metrics:
                    st.metric("Total de POIs Encontrados", f"{total_encontrado:,}")
                
                # Limite de pontos
                if total_encontrado > MAX_POINTS:
                    st.warning(f"Exibindo apenas {MAX_POINTS:,} aleatórios para performance.")
                    df_filtered = df_filtered.sample(MAX_POINTS, random_state=42)
                
                
                # 2. Processamento geográfico
                gdf = pois_to_gdf(df_filtered)
                gdf_buf = create_buffers(gdf, radius_m=buffer_m)


                # 3. RE-CRIAÇÃO DO MAPA PARA PLOTAGEM DE DADOS
                m_plot = folium.Map(
                    location=[lat, lon], 
                    zoom_start=st.session_state.zoom_level if st.session_state.zoom_level > 12 else 14,
                    tiles="CartoDB positron"
                )
                
                if len(gdf) > 500:
                    # HeatMap para grandes volumes
                    heat_data = [[row.lat, row.lon] for _, row in gdf.iterrows() if pd.notna(row.lat) and pd.notna(row.lon)]
                    HeatMap(heat_data, radius=15).add_to(m_plot)
                    st.info("HeatMap ativado devido ao grande volume de POIs.")
                else:
                    # Marcadores e Clusters para menor volume
                    layers = {}
                    for poi_type in selected_types:
                        layer_name = poi_type.replace("_", " ").title()
                        layers[poi_type] = FeatureGroup(name=layer_name).add_to(m_plot)
                        cluster = MarkerCluster().add_to(layers[poi_type])

                        subset = gdf[
                            (gdf.get("advertising") == poi_type) |
                            (gdf.get("highway") == poi_type)
                        ]
                        
                        for _, r in subset.iterrows():
                            lat_r, lon_r = r.lat, r.lon
                            if pd.isna(lat_r) or pd.isna(lon_r): continue

                            # Define cor
                            if poi_type == "bus_stop" or r.get("highway") == "bus_stop":
                                color = "green"
                            elif poi_type in ["billboard", "poster_box", "column"] or r.get("advertising") in ["billboard", "poster_box", "column"]:
                                color = "red"
                            else:
                                color = "blue"

                            folium.CircleMarker(
                                location=[lat_r, lon_r], radius=5, color=color, fill=True, fill_color=color, fill_opacity=0.8, weight=2,
                                popup=folium.Popup(f"<b>{poi_type.replace('_', ' ').title()}</b><br>Nome: {r.get('name', 'N/A')}", max_width=300)
                            ).add_to(cluster)
                
                # Buffers
                if show_buffers and len(gdf_buf) > 0:
                    buf_subset = gdf_buf.head(MAX_BUFFERS)
                    if len(gdf_buf) > MAX_BUFFERS:
                        st.info(f"Mostrando apenas {MAX_BUFFERS} de {len(gdf_buf)} buffers.")
                    
                    buffer_group = FeatureGroup(name=f"Buffers ({buffer_m}m)", show=True).add_to(m_plot)
                    for _, r in buf_subset.iterrows():
                        folium.GeoJson(
                            r.geometry.__geo_interface__,
                            style_function=lambda x: {"color": "darkred", "fillOpacity": 0.05, "weight": 1.5},
                        ).add_to(buffer_group)

                # Controle de camadas e exibição final
                LayerControl().add_to(m_plot)
                st.session_state.df_pois = df_filtered
                st_folium(m_plot, width=900, height=600, key="final_map")

            except Exception as e:
                st.error(f"Erro na análise de POI: {type(e).__name__}: {e}")
                st.info("Certifique-se de que as funções em 'src/' e as bibliotecas Geopy/GeoPandas estão corretas.")

# -------------------------------
# Rodapé informativo
# -------------------------------
st.markdown("---")
st.caption("Dados fornecidos pela Overpass API (OpenStreetMap) e Geocoding por Nominatim/OpenStreetMap.")
