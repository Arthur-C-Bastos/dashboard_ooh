# pages/7_Datas_Sazonais.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
# Importa a função de padronização
from src.utils import set_page_config_and_style 

# -------------------------------
# CONFIGURAÇÕES GERAIS E ESTILO PADRÃO
# -------------------------------
# REMOVIDAS AS LINHAS st.set_page_config, st.markdown (h1 e p)
set_page_config_and_style(
    page_title="Datas Sazonais",
    main_title="CALENDÁRIO SAZONAL & PROJEÇÃO",
    subtitle="Comparação de fluxo OOH por ano – 2024 a 2028"
)
# A função set_page_config_and_style já adiciona a linha horizontal (---)

# -------------------------------
# MAPEAMENTO DE EMOJIS (SEM NOME EM INGLÊS)
# -------------------------------
EMOJIS = {
    "party-popper": "&#x1F389;",     # Ano Novo
    "mask": "&#x1F383;",            # Carnaval
    "church": "&#x26EA;",            # Igreja
    "flag": "&#x1F1E7;&#x1F1F7;",  # Bandeira BR
    "briefcase": "&#x1F4BC;",        # Trabalho
    "baby": "&#x1F476;",             # Criança
    "candle": "&#x1F56F;",           # Vela
    "scroll": "&#x1F4DC;",           # Pergaminho
    "raised-fist": "&#x270A;",       # Punho
    "christmas-tree": "&#x1F384;",   # Natal
    "fireworks": "&#x1F386;",        # Réveillon
}

# -------------------------------
# DADOS BASE 2025 (SOMENTE PORTUGUÊS)
# -------------------------------
DADOS_BASE = [
    {"mes": "Janeiro", "data": "01/01", "evento": "Ano Novo", "tipo": "Feriado", "pedestres": 20, "onibus": 15, "nivel": 3, "detalhe": "Compras pós-festas", "icone": "party-popper"},
    {"mes": "Fevereiro/Março", "data": "03-04/03", "evento": "Carnaval", "tipo": "Feriado", "pedestres": 50, "onibus": 40, "nivel": 4, "detalhe": "Blocos e eventos", "icone": "mask"},
    {"mes": "Abril", "data": "18/04", "evento": "Sexta-Feira Santa", "tipo": "Feriado", "pedestres": 10, "onibus": 5, "nivel": 2, "detalhe": "Missas", "icone": "church"},
    {"mes": "Abril", "data": "21/04", "evento": "Tiradentes", "tipo": "Feriado", "pedestres": 15, "onibus": 10, "nivel": 2, "detalhe": "Viagens", "icone": "flag"},
    {"mes": "Maio", "data": "01/05", "evento": "Dia do Trabalho", "tipo": "Feriado", "pedestres": 25, "onibus": 20, "nivel": 3, "detalhe": "Protestos", "icone": "briefcase"},
    {"mes": "Junho", "data": "19/06", "evento": "Corpus Christi", "tipo": "Ponto Facultativo", "pedestres": 15, "onibus": 10, "nivel": 2, "detalhe": "Procissões", "icone": "church"},
    {"mes": "Setembro", "data": "07/09", "evento": "Independência", "tipo": "Feriado", "pedestres": 20, "onibus": 15, "nivel": 3, "detalhe": "Desfiles", "icone": "flag"},
    {"mes": "Outubro", "data": "12/10", "evento": "Nossa Senhora Aparecida + Dia das Crianças", "tipo": "Feriado", "pedestres": 30, "onibus": 25, "nivel": 4, "detalhe": "Compras", "icone": "baby"},
    {"mes": "Novembro", "data": "02/11", "evento": "Finados", "tipo": "Feriado", "pedestres": 10, "onibus": 8, "nivel": 1, "detalhe": "Cemitérios", "icone": "candle"},
    {"mes": "Novembro", "data": "15/11", "evento": "Proclamação da República", "tipo": "Feriado", "pedestres": 15, "onibus": 12, "nivel": 2, "detalhe": "Viagens", "icone": "scroll"},
    {"mes": "Novembro", "data": "20/11", "evento": "Consciência Negra", "tipo": "Feriado SP", "pedestres": 25, "onibus": 20, "nivel": 3, "detalhe": "Eventos", "icone": "raised-fist"},
    {"mes": "Dezembro", "data": "25/12", "evento": "Natal", "tipo": "Feriado", "pedestres": 40, "onibus": 30, "nivel": 4, "detalhe": "Compras", "icone": "christmas-tree"},
    {"mes": "Dezembro", "data": "31/12", "evento": "Réveillon", "tipo": "Ponto Facultativo", "pedestres": 50, "onibus": 40, "nivel": 4, "detalhe": "Festas", "icone": "fireworks"},
]

# -------------------------------
# FUNÇÃO PARA GERAR DADOS POR ANO
# -------------------------------
@st.cache_data
def gerar_dados_ano(ano_base=2025, crescimento_anual=0.15):
    fator = (1 + crescimento_anual) ** (ano_base - 2025)
    dados = []
    for d in DADOS_BASE:
        dados.append({
            "ano": ano_base,
            "mes": d["mes"],
            "data": d["data"],
            "evento": d["evento"],
            "tipo": d["tipo"],
            "pedestres": int(d["pedestres"] * fator),
            "onibus": int(d["onibus"] * fator),
            "nivel": d["nivel"],
            "detalhe": d["detalhe"],
            "emoji": EMOJIS[d["icone"]]  # USAR EMOJI REAL
        })
    return pd.DataFrame(dados)

# -------------------------------
# SELETOR DE ANOS
# -------------------------------
anos_disponiveis = list(range(2024, 2029))
anos_selecionados = st.multiselect(
    "Selecione os anos para comparar",
    anos_disponiveis,
    default=[2024, 2025, 2026],
    help="Escolha até 3 anos"
)

if not anos_selecionados:
    st.warning("Selecione pelo menos um ano.")
    st.stop()

dfs = [gerar_dados_ano(ano) for ano in anos_selecionados]
df_completo = pd.concat(dfs, ignore_index=True)

# -------------------------------
# CORES
# -------------------------------
CORES_ANO = {2024: "#1E90FF", 2025: "#32CD32", 2026: "#FF8C00", 2027: "#DC143C", 2028: "#9932CC"}
CORES_NIVEL = {1: "#87CEEB", 2: "#FFD700", 3: "#FF8C00", 4: "#DC143C"}

# -------------------------------
# LAYOUT (Mantido o excelente padrão de colunas)
# -------------------------------
col1, col2 = st.columns([1.3, 2.7])

with col1:
    st.markdown("### Calendário por Ano")
    ano_exibir = st.selectbox("Ver detalhes do ano", anos_selecionados)
    df_ano = df_completo[df_completo["ano"] == ano_exibir]
    
    for mes in df_ano["mes"].unique():
        with st.expander(f"**{mes} – {ano_exibir}**", expanded=False):
            for _, row in df_ano[df_ano["mes"] == mes].iterrows():
                cor = CORES_NIVEL[row["nivel"]]
                nivel_texto = ["Baixo", "Médio", "Alto", "Muito Alto"][row["nivel"]-1]
                
                # EMOJI + NOME DO FERIADO (SEM TEXTO EM INGLÊS)
                st.markdown(f"""
                <div style="background-color: {cor}20; padding: 12px; border-radius: 10px; margin: 8px 0; border-left: 5px solid {cor};">
                    <p style="margin:0; font-weight:bold; font-size:16px;">
                        <span style="font-size:20px;">{row['emoji']}</span> <strong>{row['evento']}</strong>
                    </p>
                    <p style="margin:0; font-size:14px; color:#555;">
                        {row['data']} – {row['tipo']}
                    </p>
                    <p style="margin:5px 0 0; font-size:13px;">
                        <b>Pedestres:</b> +{row['pedestres']}% | <b>Ônibus:</b> +{row['onibus']}%
                    </p>
                    <p style="margin:0; font-size:13px; color:{cor};">
                        <b>{nivel_texto}:</b> {row['detalhe']}
                    </p>
                </div>
                """, unsafe_allow_html=True)

# === GRÁFICO, MÉTRICAS E TABELA (sem mudanças no interior do col2) ===
with col2:
    st.markdown("### Comparação de Impacto por Ano")
    fig = go.Figure()
    meses_ordenados = ["Janeiro", "Fevereiro/Março", "Abril", "Maio", "Junho", "Setembro", "Outubro", "Novembro", "Dezembro"]
    
    for ano in anos_selecionados:
        df_ano = df_completo[df_completo["ano"] == ano]
        impacto = df_ano.groupby("mes")["nivel"].mean().reindex(meses_ordenados)
        fig.add_trace(go.Bar(
            x=impacto.index, y=impacto.values, name=str(ano),
            marker_color=CORES_ANO[ano], text=[f"{v:.1f}" for v in impacto.values],
            textposition='outside'
        ))
    
    fig.update_layout(
        barmode='group',
        title="Impacto Médio por Mês (1=Baixo, 4=Muito Alto)",
        xaxis_title="Mês",
        yaxis_title="Nível Médio de Impacto",
        yaxis=dict(tickmode='array', tickvals=[1,2,3,4], ticktext=['Baixo', 'Médio', 'Alto', 'Muito Alto']),
        template="simple_white",
        height=500,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # MÉTRICAS
    st.markdown("### Projeção de Crescimento")
    base = 2_800_000
    cols = st.columns(3)
    for i, ano in enumerate(anos_selecionados[:3]):
        fator = (1.15) ** (ano - 2024)
        projetado = int(base * fator)
        delta = f"+{int((fator-1)*100)}%"
        with cols[i]:
            # Mantido o HTML customizado para as métricas, pois é um design bonito.
            st.markdown(f"""
            <div style="text-align:center; padding:15px; background:{CORES_ANO[ano]}; border-radius:12px; color:white;">
                <h4 style="margin:0;">{ano}</h4>
                <h2 style="margin:8px 0;">{projetado:,}</h2>
                <p style="margin:0; font-size:14px;">{delta}</p>
            </div>
            """.replace(",", "."), unsafe_allow_html=True)

    # TABELA NATAL
    st.markdown("### Tabela Comparativa (Natal)")
    natal = df_completo[df_completo["evento"].str.contains("Natal", case=False)]
    if not natal.empty:
        tab = natal.pivot(index="evento", columns="ano", values="pedestres").reset_index()
        tab.columns.name = None
        tab_formatted = tab.copy()
        for col in tab.columns[1:]:
            tab_formatted[col] = tab_formatted[col].apply(lambda x: f"+{int(x)}%" if pd.notna(x) else "")
        st.dataframe(tab_formatted, use_container_width=True)
    else:
        st.info("Nenhum dado de Natal.")

# DICAS
st.success("""
**Dica Estratégica**: 
- 2024 → Foco em consolidação 
- 2025 → Expansão (+15%) 
- 2026 → Domínio (+32%) 
Planeje campanhas com 2 anos de antecedência!
""")
st.caption("Projeção com +15% anual (Artesp, CET-SP, tendência urbana SP)")
