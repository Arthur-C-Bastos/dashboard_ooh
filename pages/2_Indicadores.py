# -------------------------------------
# pages/2_Indicadores.py
# -------------------------------------
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.fetchers import (
    fetch_population_ibge,
    fetch_pib_ibge,
    fetch_idh_ibge,
    SPTransClient
)

# -------------------------------------
# CONFIGURAÇÕES INICIAIS
# -------------------------------------
MUNIC_CODE = "3550308"
MUNIC_NOME = "São Paulo"
POP_2023 = 12_325_232
TAXA_CRESCIMENTO = 0.003

# Token de acesso ao Olho Vivo (seguro)
SPTRANS_TOKEN = st.secrets.get("SPTRANS_TOKEN", "seu_token_aqui")

# Configuração de layout
st.set_page_config(page_title="Indicadores SP", layout="wide")
st.header(f"📊 INDICADORES COMPLETOS – {MUNIC_NOME}")
st.caption("População • PIB • IDH • Tráfego • Evolução 2020–2026")

# -------------------------------------
# SELEÇÃO DE ANO
# -------------------------------------
anos = [str(y) for y in range(2020, 2027)]
periodo = st.selectbox("Ano da projeção", anos, index=3)

# -------------------------------------
# INICIALIZA SESSION_STATE
# -------------------------------------
if "indicadores" not in st.session_state:
    st.session_state["indicadores"] = None

# -------------------------------------
# BOTÃO DE BUSCA
# -------------------------------------
if st.button("🔍 Buscar todos os indicadores", type="primary"):
    with st.spinner("Consultando IBGE, SPTrans e projeções..."):
        try:
            # --- 1. POPULAÇÃO ---
            pop_data = fetch_population_ibge(MUNIC_CODE, periodo=periodo)
            if pop_data is None:
                anos_diff = int(periodo) - 2023
                pop = int(POP_2023 * (1 + TAXA_CRESCIMENTO) ** anos_diff)
                pop_fonte = "Projeção (base IBGE 2023)"
            else:
                pop = (
                    pop_data.get("populacao", 0)
                    if isinstance(pop_data, dict)
                    else pop_data[0]["populacao"]
                )
                pop_fonte = "IBGE"

            # --- 2. PIB ---
            pib = fetch_pib_ibge(MUNIC_CODE, periodo)
            if pib is None:
                pib = 800_000_000_000
                pib_fonte = "Estimativa (2021)"
            else:
                pib_fonte = "IBGE (SIDRA)"

            # --- 3. IDH ---
            idh = fetch_idh_ibge(MUNIC_CODE)
            if idh is None:
                idh = 0.805
                idh_fonte = "PNUD (2010)"
            else:
                idh_fonte = "IBGE"

            # --- 4. TRÁFEGO SPTRANS ---
            client = SPTransClient(SPTRANS_TOKEN)
            if client.authenticate():
                trafego = client.get_positions() or 0
                trafego_fonte = "SPTrans (ao vivo)"
            else:
                trafego = 650
                trafego_fonte = "Estimativa"

            # Armazena os resultados no estado
            st.session_state["indicadores"] = {
                "pop": pop,
                "pib": pib,
                "idh": idh,
                "trafego": trafego,
                "pop_fonte": pop_fonte,
                "pib_fonte": pib_fonte,
                "idh_fonte": idh_fonte,
                "trafego_fonte": trafego_fonte,
                "periodo": periodo,
            }

        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")
            st.stop()

# -------------------------------------
# EXIBIÇÃO DOS RESULTADOS
# -------------------------------------
if st.session_state["indicadores"] is not None:
    data = st.session_state["indicadores"]

    # --- MÉTRICAS EM LINHA ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("População", f"{int(data['pop']):,}".replace(",", "."))
    with col2:
        st.metric("PIB", f"R$ {data['pib'] // 1_000_000_000:,} bi".replace(",", "."))
    with col3:
        st.metric("IDH", f"{data['idh']:.3f}")
    with col4:
        st.metric("Ônibus em operação", f"{data['trafego']}")

    # --- TABELA DETALHADA ---
    df = pd.DataFrame([
        {"Indicador": "População", "Valor": f"{int(data['pop']):,}".replace(",", "."),
         "Ano": data['periodo'], "Fonte": data['pop_fonte']},
        {"Indicador": "PIB", "Valor": f"R$ {data['pib'] // 1_000_000_000:,} bilhões".replace(",", "."),
         "Ano": "2021", "Fonte": data['pib_fonte']},
        {"Indicador": "IDH", "Valor": f"{data['idh']:.3f}", "Ano": "2010", "Fonte": data['idh_fonte']},
        {"Indicador": "Tráfego", "Valor": f"{data['trafego']} linhas",
         "Ano": "atual", "Fonte": data['trafego_fonte']},
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

    # --- GRÁFICO POPULACIONAL ---
    anos_num = list(range(2020, 2027))
    pop_evol = [int(POP_2023 * (1 + TAXA_CRESCIMENTO) ** (a - 2023)) for a in anos_num]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=anos_num,
        y=pop_evol,
        mode="lines+markers",
        name="População projetada",
        line=dict(color="#1f77b4", width=3)
    ))
    fig.add_trace(go.Scatter(
        x=[int(data["periodo"])],
        y=[data["pop"]],
        mode="markers",
        marker=dict(color="red", size=12, symbol="star"),
        name=f"{data['periodo']} (selecionado)"
    ))
    fig.update_layout(
        title="Evolução Populacional de São Paulo (2020–2026)",
        xaxis_title="Ano",
        yaxis_title="População",
        template="simple_white",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.success("✅ Indicadores carregados com sucesso!")
    st.caption("Fonte: IBGE, PNUD, SPTrans e projeções internas.")

else:
    st.info("Clique em **Buscar todos os indicadores** para carregar os dados.")
