import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.utils import set_page_config_and_style # Importa a função de padronização
import requests
from datetime import datetime

# -------------------------------
# CONFIGURAÇÕES GERAIS E ESTILO PADRÃO
# -------------------------------
MUNIC_NOME = "São Paulo"
API_WEATHER_URL = "SUA_API_DE_CLIMA_AQUI" # Substitua pela URL da sua API de Clima

set_page_config_and_style(
    page_title="Condições Climáticas",
    main_title=f"IMPACTO CLIMÁTICO OOH – {MUNIC_NOME}",
    subtitle="Previsão horária, volume de chuva e seu impacto no fluxo de pedestres"
)

# -------------------------------
# FUNÇÃO SIMULADA DE FETCH (para o exemplo)
# -------------------------------
@st.cache_data(ttl=3600)
def fetch_weather_data(cidade: str):
    """
    Simula a busca de dados climáticos (você pode integrar com OpenWeatherMap, etc.)
    Retorna uma previsão horária simulada para 24h.
    """
    # Dados de exemplo: 24 horas simuladas
    data_base = datetime.now().replace(minute=0, second=0, microsecond=0)
    
    dados = []
    for h in range(24):
        hora = data_base + pd.Timedelta(hours=h)
        temp = 18 + (h % 10) # Variação de temperatura
        chuva = 0
        condicao = "Sol"
        
        if 14 <= h <= 18 and h % 2 == 0:
            chuva = 2 + (h / 4) # Chuva na tarde
            condicao = "Chuva Forte" if chuva > 4 else "Chuvisco"
        elif 6 <= h <= 9:
            condicao = "Nublado"
        
        # Fator de Redução de Fluxo (impacto no OOH)
        fator_reducao = 1.0 - (chuva * 0.05) - ((temp - 25) * 0.01 if temp > 25 else 0)
        fator_reducao = max(0.8, fator_reducao) # Mínimo de 20% de fluxo
        
        dados.append({
            "Hora": hora,
            "Temperatura (°C)": temp,
            "Chuva (mm/h)": chuva,
            "Condição": condicao,
            "Fluxo OOH Redução (%)": f"{int((1 - fator_reducao) * 100)}%",
            "Fluxo OOH Fator": fator_reducao,
        })
        
    return pd.DataFrame(dados)

# -------------------------------
# CONTROLES E BOTÃO
# -------------------------------
# Usando duas colunas para o seletor de cidade e o botão
col_cidade, col_btn = st.columns([2, 1])

with col_cidade:
    cidade_selecionada = st.selectbox("Selecione a cidade para previsão", [MUNIC_NOME, "Rio de Janeiro", "Belo Horizonte"])

with col_btn:
    # Pequeno espaço para alinhar o botão
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(f"Atualizar Previsão para {cidade_selecionada}", type="primary", use_container_width=True):
        st.session_state['carregar_clima'] = True
    else:
        # Inicializa o estado se for a primeira vez
        if 'carregar_clima' not in st.session_state:
            st.session_state['carregar_clima'] = False

# -------------------------------
# RENDERIZAÇÃO DOS DADOS
# -------------------------------
if st.session_state.get('carregar_clima'):
    
    with st.spinner(f"Buscando dados climáticos para {cidade_selecionada}..."):
        df_clima = fetch_weather_data(cidade_selecionada)
    
    # --- 1. MÉTRICAS CHAVE ---
    st.markdown("### Condições Atuais e Impacto Máximo (Próximas 24h)")
    
    max_chuva = df_clima["Chuva (mm/h)"].max()
    max_reducao = df_clima["Fluxo OOH Redução (%)"].max()
    temp_atual = df_clima.iloc[0]["Temperatura (°C)"]
    condicao_atual = df_clima.iloc[0]["Condição"]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Temperatura Atual", f"{temp_atual}°C", delta=None)
    with col2:
        st.metric("Condição Atual", condicao_atual)
    with col3:
        st.metric("Chuva Máxima (24h)", f"{max_chuva:.1f} mm/h", delta_color="inverse")
    with col4:
        st.metric("Redução Máxima OOH", max_reducao, delta_color="inverse")
        
    st.markdown("---")
    
    # --- 2. GRÁFICOS E TABELA ---
    col_grafico, col_tabela = st.columns([2, 1])
    
    with col_grafico:
        st.markdown("##### Previsão Horária e Fator de Risco no Fluxo")
        
        fig = go.Figure()
        
        # Eixo Y1: Temperatura
        fig.add_trace(go.Scatter(
            x=df_clima["Hora"].dt.hour, y=df_clima["Temperatura (°C)"],
            name="Temperatura (°C)", mode='lines+markers', yaxis='y1',
            line=dict(color='orange', width=2)
        ))
        
        # Eixo Y2: Chuva
        fig.add_trace(go.Bar(
            x=df_clima["Hora"].dt.hour, y=df_clima["Chuva (mm/h)"],
            name="Chuva (mm/h)", yaxis='y2', marker_color='lightblue'
        ))

        # Eixo Y3: Redução OOH (secundário)
        fig.add_trace(go.Scatter(
            x=df_clima["Hora"].dt.hour, y=df_clima["Fluxo OOH Fator"],
            name="Fator de Fluxo OOH", yaxis='y3', mode='lines',
            line=dict(color='red', dash='dash')
        ))

        fig.update_layout(
            title="Previsão 24h: Temperatura, Chuva e Impacto OOH",
            template="simple_white",
            height=500,
            xaxis=dict(title="Hora do Dia"),
            yaxis=dict(title="Temp. (°C)", side='left', showgrid=False, range=[10, 35]),
            yaxis2=dict(title="Chuva (mm/h)", side='right', overlaying='y', showgrid=False, range=[0, 10]),
            yaxis3=dict(title="Fator OOH (1=Sem Redução)", side='right', overlaying='y', showgrid=False, range=[0.7, 1.05], anchor="free", position=0.95),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col_tabela:
        st.markdown("##### Detalhe das Próximas Horas")
        df_display = df_clima[["Hora", "Temperatura (°C)", "Condição", "Fluxo OOH Redução (%)"]].copy()
        df_display["Hora"] = df_display["Hora"].dt.strftime("%H:%M")
        
        st.dataframe(df_display.head(10), use_container_width=True, hide_index=True)
        
    st.markdown("---")
    st.success("Dados climáticos e projeção de impacto OOH atualizados.")
    st.caption("Fonte: Dados simulados/Estimativas internas. Integre sua API de clima para dados reais.")

else:
    st.info(f"Clique em **Atualizar Previsão** para carregar os dados climáticos de {MUNIC_NOME} e o impacto projetado no fluxo OOH.")
    st.session_state['carregar_clima'] = False
