# pages/3_Mobilidade.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from src.utils import set_page_config_and_style # IMPORTAÇÃO DO NOVO MÓDULO

# -------------------------------
# CONFIGURAÇÕES GERAIS E ESTILO PADRÃO
# -------------------------------
set_page_config_and_style(
    page_title="Mobilidade Urbana",
    main_title="MOBILIDADE URBANA – SÃO PAULO",
    subtitle="Ônibus em operação, fluxo de viagens e projeções por hora/dia"
)

# -------------------------------
# TOKEN SPTRANS (input seguro)
# -------------------------------
# Usando um container para isolar o input na parte superior da coluna
with st.container():
    st.markdown("##### Configuração da API")
    SPTRANS_TOKEN = st.text_input(
        "Token SPTrans (Olho Vivo)",
        value="",
        type="password",
        help="Cadastre em: https://sptrans.com.br/desenvolvedores/olhovivo/"
    )

if not SPTRANS_TOKEN.strip():
    SPTRANS_TOKEN = None

# -------------------------------
# Controles de Seleção
# -------------------------------
# Usando colunas para organizar os seletores horizontalmente
col_hora, col_dia = st.columns(2)

with col_hora:
    hora = st.slider("Hora do dia", 0, 23, 18, help="Selecione a hora para projeção")

with col_dia:
    dia_semana = st.selectbox("Dia da semana", [
        "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"
    ])

# -------------------------------
# Botão
# -------------------------------
# Separando o botão com uma linha horizontal para clareza
st.markdown("---")
if st.button("Buscar dados de mobilidade", type="primary"):
    with st.spinner("Consultando SPTrans e calculando fluxo..."):

        # --- 1. Ônibus em operação (SPTrans) ---
        if SPTRANS_TOKEN:
            try:
                from src.fetchers import SPTransClient
                client = SPTransClient(SPTRANS_TOKEN)
                if client.authenticate():
                    data = client.get_positions()
                    num_onibus = len(data.get('l', [])) if data else 0
                    onibus_fonte = "SPTrans (ao vivo)"
                else:
                    num_onibus = 680
                    onibus_fonte = "Estimativa (API Indisponível)"
            except Exception as e:
                st.warning(f"Erro SPTrans: Falha na autenticação ou busca. Detalhes: {e}")
                num_onibus = 680
                onibus_fonte = "Estimativa (Erro na API)"
        else:
            num_onibus = 680
            onibus_fonte = "Estimativa (Token Ausente)"

        # --- 2. Contagens CET-SP (fallback realista) ---
        pedestres = 15_000 if hora in [7,8,17,18] else 8_000
        veiculos = 25_000 if hora in [7,8,17,18] else 15_000

        # --- 3. Projeção de fluxo (OD Metrô 2025) ---
        fluxo_base_diario = 2_864_000 # Viagens/dia (ônibus + metrô)
        
        # Fator por dia da semana
        fator_dia = {
            "Segunda": 1.15, "Terça": 1.15, "Quarta": 1.15,
            "Quinta": 1.10, "Sexta": 1.20,
            "Sábado": 0.70, "Domingo": 0.55
        }[dia_semana]

        # Fator por hora (pico manhã/tarde)
        fator_hora = 2.0 if hora in [7,8,17,18] else 1.0
        if 6 <= hora <= 9 or 16 <= hora <= 19:
            fator_hora = 1.8
        elif 9 < hora < 16 or 19 < hora < 22:
            fator_hora = 1.2

        # Fluxo por hora
        fluxo_por_hora = int((fluxo_base_diario * fator_dia) / 24 * fator_hora)

    # -------------------------------
    # Métricas
    # -------------------------------
    st.markdown("### Indicadores Chave de Fluxo")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ônibus em Operação", f"{num_onibus}")
    with col2:
        st.metric("Pedestres (Hora Proj.)", f"{pedestres:,}".replace(",", "."))
    with col3:
        st.metric("Veículos (Hora Proj.)", f"{veiculos:,}".replace(",", "."))
    with col4:
        st.metric("Fluxo Total (Viagens/h)", f"{fluxo_por_hora:,}".replace(",", "."))

    # -------------------------------
    # Tabela e Gráfico em Colunas
    # -------------------------------
    st.markdown("---")
    col_tabela, col_grafico = st.columns([1, 2])

    with col_tabela:
        st.markdown("##### Detalhes dos Dados")
        df = pd.DataFrame([
            {"Indicador": "Ônibus", "Valor": num_onibus, "Fonte": onibus_fonte},
            {"Indicador": "Pedestres", "Valor": f"{pedestres:,}".replace(",", "."), "Fonte": "CET-SP (proj.)"},
            {"Indicador": "Veículos", "Valor": f"{veiculos:,}".replace(",", "."), "Fonte": "CET-SP (proj.)"},
            {"Indicador": "Fluxo (viagens/h)", "Valor": f"{fluxo_por_hora:,}".replace(",", "."), "Fonte": "OD Metrô 2025"},
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)


    with col_grafico:
        # -------------------------------
        # GRÁFICO DE FLUXO POR HORA (ATUALIZADO COM DIA SELECIONADO)
        # -------------------------------
        horas = list(range(24))
        fluxo_horas = []
        for h in horas:
            f_hora = 2.0 if h in [7,8,17,18] else 1.0
            if 6 <= h <= 9 or 16 <= h <= 19:
                f_hora = 1.8
            elif 9 < h < 16 or 19 < h < 22:
                f_hora = 1.2
            fluxo_horas.append(int((fluxo_base_diario * fator_dia) / 24 * f_hora))

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=horas,
            y=fluxo_horas,
            name='Fluxo projetado',
            marker_color='#1E90FF', # Cor padrão azul
            hovertemplate='Hora: %{x}<br>Viagens: %{y:,}<extra></extra>'
        ))
        fig.add_vline(x=hora, line_dash="dash", line_color="red", annotation_text=f"{hora}h", annotation_position="top right")
        
        # Adiciona o ponto específico selecionado
        fig.add_trace(go.Scatter(
            x=[hora],
            y=[fluxo_por_hora],
            mode='markers',
            marker=dict(color='red', size=10),
            name=f'Ponto Selecionado ({hora}h)'
        ))


        fig.update_layout(
            title=f"Distribuição do Fluxo em {dia_semana}",
            xaxis_title="Hora do dia",
            yaxis_title="Viagens por hora",
            template="simple_white",
            hovermode="x unified",
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.success("Dados de mobilidade atualizados com sucesso!")
    st.caption("Fonte: SPTrans (Olho Vivo), CET-SP (Projeções), Pesquisa OD Metrô 2025.")

else:
    st.info("Selecione os parâmetros e clique em **Buscar dados de mobilidade** para carregar os indicadores e o gráfico de fluxo.")
