# pages/2_Indicadores.py
import streamlit as st
import pandas as pd
from src.fetchers import fetch_population_ibge

MUNIC_CODE = "3550308"
MUNIC_NOME = "São Paulo"
POP_2023_OFICIAL = 12_325_232  # IBGE 2023

st.header(f"INDICADORES – {MUNIC_NOME}")
st.markdown("Projeção populacional oficial do IBGE com fallback robusto.")

periodo = st.selectbox("Ano da projeção", ["2020", "2021", "2022", "2023", "2024", "2025", "2026"], index=3)

if st.button("Buscar dados do IBGE", type="primary"):
    with st.spinner("Consultando IBGE..."):
        data = fetch_population_ibge(MUNIC_CODE, periodo=periodo)

    # -------------------------------
    # SÓ usa fallback se IBGE falhar
    # -------------------------------
    if data is None:
        st.error("Servidor do IBGE indisponível (erro 503 ou falha de rede).")
        st.info("**Usando projeção realista com base em 2023**")

        taxa_crescimento = 0.003  # 0.3% ao ano
        anos_diff = int(periodo) - 2023
        pop_projetada = int(POP_2023_OFICIAL * (1 + taxa_crescimento) ** anos_diff)

        data = [{
            "municipio": MUNIC_NOME,
            "populacao": pop_projetada,
            "ano": periodo,
            "fonte": "Projeção (base IBGE 2023)"
        }]
        fonte_final = "Projeção (base IBGE 2023)"
    else:
        st.success(f"Dados oficiais do IBGE para {periodo}")
        if isinstance(data, dict):
            data = [data]
        fonte_final = "IBGE (projeção oficial)"

    # -------------------------------
    # Exibição
    # -------------------------------
    df = pd.DataFrame(data)
    pop = df["populacao"].iloc[0]
    pop_str = f"{int(pop):,}".replace(",", ".")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("População", pop_str)
    with col2:
        st.metric("Ano", periodo)

    df_display = df[["ano", "populacao", "fonte"]].copy()
    df_display["populacao"] = df_display["populacao"].apply(lambda x: f"{int(x):,}".replace(",", "."))
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.caption(f"Fonte: {fonte_final}")

else:
    st.info("Clique em **Buscar dados do IBGE** para carregar.")
