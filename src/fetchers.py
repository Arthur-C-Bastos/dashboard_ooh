# src/fetchers.py
import requests
import pandas as pd
from typing import Optional, List, Dict
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


# ===============================
# 1. OVERPASS – BUSCA POIs (ônibus, outdoors, etc.)
# ===============================
def fetch_pois_overpass(bbox: str, tags: List[str] = None, timeout: int = 25) -> pd.DataFrame:
    """
    Busca pontos de interesse (POIs) usando Overpass API.
    - bbox: 'minlat,minlon,maxlat,maxlon'
    - tags: lista de ['key=value']
    Retorna DataFrame com id, lat, lon e tags.
    """
    if tags is None:
        tags = ['highway=bus_stop', 'advertising=billboard']
    
    clauses = []
    for tag in tags:
        if '=' not in tag:
            continue
        k, v = tag.split('=', 1)
        clauses.append(f'node["{k}"="{v}"]({bbox});')
        clauses.append(f'way["{k}"="{v}"]({bbox});')
    
    query = f"[out:json][timeout:{timeout}];(" + "".join(clauses) + ");out center tags;"
    url = 'https://overpass-api.de/api/interpreter'
    
    try:
        response = requests.post(url, data={'data': query}, timeout=timeout)
        response.raise_for_status()
        elements = response.json().get('elements', [])
        rows = []
        for el in elements:
            lat = el.get('lat') or (el.get('center') or {}).get('lat')
            lon = el.get('lon') or (el.get('center') or {}).get('lon')
            if lat is None or lon is None:
                continue
            row = {'id': el.get('id'), 'lat': lat, 'lon': lon}
            row.update(el.get('tags', {}))
            rows.append(row)
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"[Overpass] Erro: {e}")
        return pd.DataFrame()  # Retorna vazio em erro


# ===============================
# 2. IBGE – PROJEÇÃO POPULACIONAL
# ===============================
def fetch_population_ibge(
    municipio_id: str = None,
    periodo: Optional[str] = None,
    timeout: int = 15,
    max_retries: int = 3
) -> Optional[dict]:
    """
    Busca projeção populacional do IBGE com retry automático.
    Retorna dict ou None se falhar.
    """
    base = "https://servicodados.ibge.gov.br/api/v1/projecoes/populacao"
    url = f"{base}/{municipio_id}" if municipio_id else base
    if periodo:
        url += f"?periodo={periodo}"

    session = requests.Session()
    retry = Retry(total=max_retries, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


# ===============================
# 3. IBGE – PIB MUNICIPAL (SIDRA)
# ===============================
def fetch_pib_ibge(municipio_id: str = "3550308", ano: str = "2021") -> Optional[int]:
    """
    Busca PIB municipal via SIDRA (tabela 5938).
    Retorna valor em reais (int) ou None.
    """
    url = f"https://servicodados.ibge.gov.br/api/v3/agregados/5938/periodos/{ano}/variaveis/543?localidades=MUN{municipio_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        valor = data[0]['resultados'][0]['series'][0]['serie'][ano]
        return int(float(valor) * 1_000_000)
    except Exception as e:
        print(f"[PIB IBGE] Erro: {e}")
        return None


# ===============================
# 4. INMET – DADOS DE ESTAÇÃO
# ===============================
def fetch_inmet_station_data(
    station_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[dict]:
    """
    Busca dados diários ou por período do INMET.
    Formato: 'YYYY-MM-DD'
    Retorna lista de dicionários ou [] se falhar.
    """
    if start_date and end_date:
        url = f"https://apitempo.inmet.gov.br/estacao/dados/{start_date}/{end_date}/{station_code}"
    else:
        url = f"https://apitempo.inmet.gov.br/estacao/{station_code}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[INMET] Erro: {e}")
        return []


# ===============================
# 5. SPTRANS – CLIENTE OLHO VIVO (ônibus em tempo real)
# ===============================
class SPTransClient:
    """
    Cliente para API Olho Vivo (SPTrans).
    - Autentica com token
    - Busca posições e conta linhas em operação
    """
    def __init__(self, token: str, base: str = 'http://api.olhovivo.sptrans.com.br/v2.1'):
        self.token = token.strip() if token else None
        self.base = base
        self.session = requests.Session()
        self.authenticated = False

    def authenticate(self) -> bool:
        """Autentica com token. Retorna True se sucesso."""
        if not self.token:
            return False
        url = f"{self.base}/Login/Autenticar?token={self.token}"
        try:
            r = self.session.post(url, timeout=10)
            r.raise_for_status()
            self.authenticated = (r.text.strip().lower() == 'true')
            return self.authenticated
        except Exception as e:
            print(f"[SPTrans] Falha na autenticação: {e}")
            return False

    def get_positions(self) -> Optional[dict]:
        """Retorna JSON com posições de veículos ou None."""
        if not self.authenticated:
            return None
        url = f"{self.base}/Posicao"
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[SPTrans] Erro ao buscar posições: {e}")
            return None

    def get_bus_count(self) -> int:
        """Retorna número de linhas (ônibus) em operação."""
        data = self.get_positions()
        if not data or 'l' not in data:
            return 0
        return len(data['l'])  # 'l' = lista de linhas ativas
