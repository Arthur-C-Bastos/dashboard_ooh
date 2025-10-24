# pages/1_Mapa_Interativo.py
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
from folium import FeatureGroup, LayerControl
from streamlit_folium import st_folium
# NOVO: Importa geopy para Geocoding
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError 

# ... (Restante das importações de src/ e definições de performance/utils) ...
# Mock/Simulação das importações de src para evitar erros de UI
try:
    from src.fetchers import fetch_pois_overpass
    from src.geoprocess import pois_to_gdf, create_buffers
    from src.utils import set_page_config_and_style
except ImportError:
    def fetch_pois_overpass(bbox): return pd.DataFrame()
    def pois_to_gdf(df): return df
    def create_buffers(gdf, radius_m): return gdf
    def set_page_config_and_style(page_title, main_title, subtitle):
        st.set_page_config(layout="wide", page_title=page_title)
        st.title(main_title)
        st.markdown(f"**{subtitle}**")

# -------------------------------
# CONFIGURAÇÕES DA PÁGINA
# -------------------------------
set_page_config_and_style(
    page_title="Mapa Interativo",
    main_title="MAPA TÁTICO: MÍDIAS OOH E PONTOS DE INTERESSE",
    subtitle="Análise da densidade de mídias e sua proximidade a pontos de tráfego."
)

# -------------------------------
# CONFIGURAÇÃO DE PERFORMANCE E CONSTANTES
# -------------------------------
MAX_POINTS = 1000
DELTA_DEG = 0.01
MAX_BUFFERS = 30
MAP_DEFAULT_CENTER = (-23.55, -46.63) # São Paulo

# -------------------------------
# FUNÇÃO DE GEOCODING
# -------------------------------
@st.cache_data(ttl=3600) # Cache por 1 hora
def geocode_address(address):
    """Converte endereço ou nome para coordenadas (lat/lon)."""
    # É fundamental definir um user_agent para usar o Nominatim
    geolocator = Nominatim(user_agent="ooh_analysis_app")
    try:
        # Tenta buscar a localização com timeout
        location = geolocator.geocode(address, timeout=10) 
        if location:
            return location.latitude, location.longitude
        return None, None
    except GeocoderTimedOut:
        st.sidebar.error("A pesquisa excedeu o tempo limite. Tente ser mais específico.")
        return None, None
    except GeocoderServiceError as e:
        st.sidebar.error(f"Erro no serviço de Geocoding: {e}. Tente novamente mais tarde.")
        return None, None
    except Exception:
        return None, None


# -------------------------------
# LAYOUT UI: FILTROS NA BARRA LATERAL (INÍCIO)
# -------------------------------
st.sidebar.header("🗺️ Controles do Mapa")

# NOVO BLOCO: PESQUISA POR BAIRRO/ENDEREÇO
st.sidebar.subheader("Pesquisar Local")
search_term = st.sidebar.text_input(
    "Digite Bairro, Rua ou Ponto de Referência",
    placeholder="Ex: Av. Paulista, São Paulo",
    key="search_input"
)

# Botão para iniciar a pesquisa
if st.sidebar.button("Pesquisar e Centralizar Mapa", use_container_width=True):
    if search_term:
        with st.sidebar.spinner(f"Buscando coordenadas para '{search_term}'..."):
            new_lat, new_lon = geocode_address(search_term)
            
            if new_lat and new_lon:
                # Atualiza o estado da sessão com a nova localização
                st.session_state.map_lat = new_lat
                st.session_state.map_lon = new_lon
                st.session_state.click_lat = new_lat
                st.session_state.click_lon = new_lon
                st.session_state.search_success = True
                st.sidebar.success(f"Mapa centralizado em: {search_term}")
            else:
                st.sidebar.error("Local não encontrado. Tente refinar a pesquisa (ex: adicione a cidade).")
                st.session_state.search_success = False
    else:
        st.sidebar.warning("Por favor, digite um termo de pesquisa.")

st.sidebar.markdown("---")


# FILTROS DE BUFFER (Movidos para o novo bloco)
st.sidebar.subheader("Ajustes de Análise")
buffer_m = st.sidebar.selectbox(
    "Buffer (Raio de Análise em metros)", 
    [250, 500, 1000, 1500], 
    index=1
)

show_buffers = st.sidebar.checkbox(
    "Mostrar polígonos de Buffer", 
    value=False
)
st.sidebar.markdown("---")

# -------------------------------
# INSTRUÇÃO PRINCIPAL
# -------------------------------
st.markdown("""
### 📍 Como Usar:
1.  Use a **Barra Lateral** para buscar um endereço ou para refinar o Buffer.
2.  Ou, **clique diretamente no mapa** para selecionar a região.
""")


# -------------------------------
# MAPA INICIAL/ATUALIZADO
# -------------------------------
# Usa o centro padrão ou o centro atualizado (do clique ou da pesquisa)
center_lat, center_lon = st.session_state.get("map_lat", MAP_DEFAULT_CENTER[0]), \
                         st.session_state.get("map_lon", MAP_DEFAULT_CENTER[1])


m = folium.Map(
    location=[center_lat, center_lon], 
    zoom_start=st.session_state.get("zoom_level", 13), # Mantém zoom para melhor UX
    tiles="CartoDB positron"
)

# Captura clique
map_data = st_folium(m, width=900, height=550, returned_objects=["last_clicked", "zoom"])

# Atualiza o zoom_level para manter o estado
if map_data and map_data.get("zoom") is not None:
    st.session_state.zoom_level = map_data["zoom"]

# -------------------------------
# TRATAMENTO DO CLIQUE MANUAL
# -------------------------------
# Se houver clique manual, ele sobrescreve o ponto de interesse
if map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    
    # Só atualiza se for um novo ponto (evita re-renderização desnecessária)
    if lat != st.session_state.get("click_lat") or lon != st.session_state.get("click_lon"):
        st.session_state.click_lat = lat
        st.session_state.click_lon = lon
        st.session_state.map_lat = lat
        st.session_state.map_lon = lon
        st.sidebar.success(f"Novo ponto clicado: Lat {lat:.4f}, Lon {lon:.4f}. Processando POIs...")


# -------------------------------
# CONSULTA E EXIBIÇÃO APÓS CLIQUE/PESQUISA
# -------------------------------

# O restante do código de processamento (que você já tinha) deve vir aqui.
# Ele será acionado se click_lat/lon estiver no session_state, seja por clique manual ou pesquisa.
if "click_lat" in st.session_state and "click_lon" in st.session_state:
    lat = st.session_state.click_lat
    lon = st.session_state.click_lon
    
    # ... (O restante da lógica de bbox, fetch_pois_overpass, filtros, gdf, heatmap/markers, buffers) ...
    # Usei '...' para não duplicar o código enorme, mas esta é a seção onde a sua lógica anterior deve continuar.

    # ----------------------------------------------------
    # TRECHO CRÍTICO (DEVE SER MANTIDO DA VERSÃO ANTERIOR)
    # ----------------------------------------------------
    
    # bbox ~ 2 km x 2 km
    bbox = f"{lat - DELTA_DEG},{lon - DELTA_DEG},{lat + DELTA_DEG},{lon + DELTA_DEG}"

    # ... (RESTANTE DA LÓGICA DE CONSULTA E PLOTAGEM) ...
    
    # Para fins de demonstração, simularemos a lógica de novo:
    try:
        df = fetch_pois_overpass(bbox)
        # ... (Toda a lógica de filtragem, GeoDataFrame, HeatMap, Marcadores, Buffers e LayerControl)
        # ... (que foi incluída na resposta anterior)
        # ... (e termina com o st_folium final)
        
        # Simulando o final:
        st.session_state.df_pois = df 
        #st_folium(m, width=900, height=600, key="final_map") # Se o mapa não foi renderizado antes
        
    except Exception as e:
        # Se você não tem as funções 'src' funcionando, esta seção vai falhar.
        st.error(f"Erro na execução da análise de POI: {type(e).__name__}. Verifique os arquivos 'src'.")
        
    # ----------------------------------------------------

st.markdown("---")
st.caption("Dados fornecidos pela Overpass API (OpenStreetMap) e Geocoding por Nominatim/OpenStreetMap.")
