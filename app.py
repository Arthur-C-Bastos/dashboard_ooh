import streamlit as st
import pandas as pd
st.set_page_config(
    page_title="OOH Dashboard BR",
    layout="wide"
)

# Versão 1: Profissional e Focado em Valor
st.title("📊 OOH Dashboard BR – Plataforma de Análise Tática e Sazonal")

st.markdown("""
Bem-vindo à **Versão Didática** do seu painel de Out-Of-Home (OOH) para o mercado brasileiro.

Este aplicativo foi arquitetado para transformar dados geográficos e contextuais em **inteligência de mídia**, otimizando a seleção de locais e a estratégia de investimento. Navegue pelas seções para explorar diferentes dimensões da análise OOH:
""")

# Simula uma tabela formatada em Streamlit para melhor visualização
data = {
    'Seção': ['🗺️ Mapa Interativo', '📈 Indicadores', '🚗 Mobilidade', '🌤️ Clima', '🔍 Análise', '⚙️ Configurações'],
    'Foco Principal': [
        'Visualize a densidade de mídias e o entorno de Pontos de Interesse (POIs).',
        'Acompanhe métricas chave de performance e investimento em OOH.',
        'Analise dados de tráfego, fluxo de pessoas e audiência de rotas.',
        'Entenda a influência de fatores climáticos na exposição de suas mídias.',
        'Gere relatórios consolidados e projeções de performance sazonal.',
        'Defina o período de análise e personalize os parâmetros do projeto.'
    ]
}

df_nav = pd.DataFrame(data)

# st.table é simples, st.dataframe é mais interativo, mas um markdown formatado pode ser mais estético
# st.dataframe(df_nav, hide_index=True)

st.markdown("---")
st.header("Selecione uma aba no menu lateral para começar sua análise.")
