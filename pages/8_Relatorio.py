# pages/8_Relatorio.py
# -*- coding: utf-8 -*- 
import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
import plotly.express as px 
from PIL import Image 
from fpdf import FPDF 

# Tenta importar a função utilitária. Se falhar, define um fallback.
try:
    from src.utils import set_page_config_and_style
except ImportError:
    def set_page_config_and_style(page_title, main_title, subtitle):
        st.set_page_config(layout="wide", page_title=page_title)
        st.title(main_title)
        st.markdown(f"**{subtitle}**")

# -------------------------------
# CONFIGURAÇÕES GERAIS E ESTILO PADRÃO
# -------------------------------
set_page_config_and_style(
    page_title="Relatório Executivo",
    main_title="RELATÓRIO EXECUTIVO & DOWNLOAD",
    subtitle="Resumo das análises e projeções estratégicas"
)

# -------------------------------
# DADOS MOCK E CÁLCULOS (AUMENTO DE DADOS E SAZONALIDADE)
# -------------------------------
@st.cache_data
def get_mock_data():
    """Gera um DataFrame unificado simulando 100 campanhas ao longo de 12 meses."""
    N_CAMPANHAS = 100
    np.random.seed(42) 

    meses_full = ['Jan', 'Fev', 'Mar', 'Abr', 'Maio', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    # Probabilidade (sazonalidade)
    meses = np.random.choice(meses_full, N_CAMPANHAS, p=[0.06, 0.07, 0.08, 0.07, 0.08, 0.08, 0.08, 0.07, 0.08, 0.09, 0.10, 0.14])
    
    tipos_midia = np.random.choice(['Digital', 'Estática'], N_CAMPANHAS, p=[0.6, 0.4])
    
    investimentos = np.random.uniform(50, 400, N_CAMPANHAS).round(1)
    for i, mes in enumerate(meses):
        if mes == 'Dez':
            investimentos[i] *= 1.5 

    reach = (investimentos * np.random.uniform(0.015, 0.025, N_CAMPANHAS)).round(2) 
    
    cpm = np.random.uniform(2.0, 7.0, N_CAMPANHAS).round(2)
    cpm[tipos_midia == 'Digital'] *= 0.8 

    frequencia = np.random.uniform(3.0, 8.0, N_CAMPANHAS).round(1)

    data = {
        'ID_Campanha': [f'C{i:03d}' for i in range(1, N_CAMPANHAS + 1)],
        'Mes': meses,
        'Tipo_Midia': tipos_midia,
        'Investimento_Mil_R$': investimentos,
        'Reach_Milhoes': reach,
        'Frequencia': frequencia,
        'CPM_R$': cpm,
        'Audiencia_Pico_K': np.random.randint(70, 300, N_CAMPANHAS)
    }
    return pd.DataFrame(data)

# Variáveis Globais
df_relatorio = get_mock_data()
total_investimento = df_relatorio['Investimento_Mil_R$'].sum()
media_cpm = df_relatorio['CPM_R$'].mean()
total_reach = df_relatorio['Reach_Milhoes'].sum().round(1)
num_campanhas = len(df_relatorio)

# -------------------------------
# 1. RESUMO EXECUTIVO NA TELA (Mantido)
# -------------------------------
st.markdown("### Resumo das Métricas Chave (100 Campanhas)")
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Total de Campanhas", num_campanhas)
with col2: st.metric("Investimento Total (Mil R$)", f"{total_investimento:,.0f}".replace(",", "."))
with col3: st.metric("Reach Agregado (Milhões)", f"{total_reach:,.1f}".replace(",", "."))
with col4: st.metric("CPM Médio", f"R$ {media_cpm:.2f}")

st.markdown("---")

# Visualização do gráfico no dashboard (opcional)
if st.checkbox("Mostrar Gráfico de Investimento (Visão Dashboard)"):
    df_agg = df_relatorio.groupby('Mes')['Investimento_Mil_R$'].sum().reset_index()
    mes_order = ['Jan', 'Fev', 'Mar', 'Abr', 'Maio', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_agg['Mes'] = pd.Categorical(df_agg['Mes'], categories=mes_order, ordered=True)
    df_agg = df_agg.sort_values('Mes')
    fig_dash = px.bar(
        df_agg, 
        x='Mes', 
        y='Investimento_Mil_R$', 
        title='Investimento Agregado por Mês (R$ Mil)',
        color_discrete_sequence=['#1E90FF']
    )
    st.plotly_chart(fig_dash, use_container_width=True)

# -------------------------------
# 2. DOWNLOAD CSV (Mantido)
# -------------------------------
st.markdown("### 📥 Download em CSV")
csv = df_relatorio.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Baixar Dados em CSV",
    data=csv,
    file_name='relatorio_ooh_detalhado.csv',
    mime='text/csv',
    type="primary"
)


# -------------------------------
# 3. DOWNLOAD PDF (Função Storytelling) - COM CONTROLES
# -------------------------------
st.markdown("### 📄 Configuração da Projeção para o PDF")

# CONTROLES INTERATIVOS PARA PROJEÇÃO
meses_disponiveis = ['Jan', 'Fev', 'Mar', 'Abr', 'Maio', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
col_proj1, col_proj2 = st.columns(2)

with col_proj1:
    projecao_mes_selecionado = st.selectbox(
        "Mês Sazonal Alvo para Projeção",
        options=meses_disponiveis,
        index=meses_disponiveis.index('Dez'),
        help="Selecione o mês onde você planeja focar o próximo investimento sazonal."
    )

with col_proj2:
    aumento_investimento_percent = st.slider(
        "Aumento de Investimento Proposto (%)",
        min_value=5,
        max_value=100,
        value=25,
        step=5,
        help="Defina o percentual de aumento do investimento para simulação da projeção."
    )
    # Converte o percentual para decimal (ex: 25 -> 0.25)
    aumento_investimento_decimal = aumento_investimento_percent / 100.0


def create_pdf_report(df: pd.DataFrame, projecao_mes: str, aumento_investimento_percent: float) -> bytes:
    """
    Função que gera um relatório PDF focado em storytelling, detalhamento e projeção futura
    baseada na sazonalidade, utilizando parâmetros interativos.
    """
    try:
        # 1. PRÉ-CÁLCULOS
        
        # Agregação Mensal Completa
        mes_order = ['Jan', 'Fev', 'Mar', 'Abr', 'Maio', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        df['Mes'] = pd.Categorical(df['Mes'], categories=mes_order, ordered=True)
        df_monthly = df.groupby('Mes', observed=True).agg(
            Total_Investimento=('Investimento_Mil_R$', 'sum'),
            Media_CPM=('CPM_R$', 'mean'),
            Total_Reach=('Reach_Milhoes', 'sum'),
            Media_Frequencia=('Frequencia', 'mean') 
        ).reset_index()
        df_monthly = df_monthly.sort_values('Mes') 

        df_monthly['Media_Frequencia'] = df_monthly['Media_Frequencia'].round(1)
        df_monthly['Media_CPM'] = df_monthly['Media_CPM'].round(2)
        df_monthly['Total_Reach'] = df_monthly['Total_Reach'].round(1)
        df_monthly['Total_Investimento'] = df_monthly['Total_Investimento'].round(0)

        # Agregação por Mídia para Detalhe
        df_media = df.groupby('Tipo_Midia').agg(
            Media_CPM=('CPM_R$', 'mean'),
            Total_Reach=('Reach_Milhoes', 'sum'),
            Total_Investimento=('Investimento_Mil_R$', 'sum'),
            Media_Frequencia=('Frequencia', 'mean')
        ).reset_index()
        df_media['Media_Frequencia'] = df_media['Media_Frequencia'].round(1)
        df_media['Media_CPM'] = df_media['Media_CPM'].round(2)
        df_media['Total_Reach'] = df_media['Total_Reach'].round(1)
        df_media['Total_Investimento'] = df_media['Total_Investimento'].round(0)

        # ENCONTRAR MÉTRICAS CHAVE GERAIS
        melhor_midia_cpm = df_media.loc[df_media['Media_CPM'].idxmin()]
        total_investimento_geral = df_monthly['Total_Investimento'].sum()
        maior_investimento_mes = df_monthly.loc[df_monthly['Total_Investimento'].idxmax()]
        
        # 2. DEFINIÇÃO DA PROJEÇÃO
        df_mes_projecao = df_monthly[df_monthly['Mes'] == projecao_mes]
        
        if df_mes_projecao.empty:
            cpm_base_projecao = df_monthly['Media_CPM'].mean()
            investimento_base = df_monthly['Total_Investimento'].mean()
            reach_base = df_monthly['Total_Reach'].mean()
            narrativa_sazonal = "Média Geral"
        else:
            cpm_base_projecao = df_mes_projecao['Media_CPM'].iloc[0]
            investimento_base = df_mes_projecao['Total_Investimento'].iloc[0]
            reach_base = df_mes_projecao['Total_Reach'].iloc[0]
            narrativa_sazonal = f"Performance Histórica de {projecao_mes}"

        # CÁLCULO DA PROJEÇÃO
        novo_investimento = investimento_base * (1 + aumento_investimento_percent)
        novo_reach_proj_milhoes = (novo_investimento * 1000) / cpm_base_projecao / 1000
        
        
        pdf = FPDF()
        pdf.add_page()
        
        # --- CONFIGURAÇÕES BÁSICAS ---
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # --- TÍTULO ---
        pdf.set_font("Arial", "B", 18) 
        pdf.cell(200, 10, "Relatório Executivo de Performance OOH", 0, 1, "C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(200, 5, f"Período Analisado: 12 Meses | Projeção para: {projecao_mes} | Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, "C")
        pdf.ln(10)

        # ------------------------------------------------------------------
        # --- SEÇÃO 1: RESUMO EXECUTIVO (STORYTELLING) ---
        # ------------------------------------------------------------------
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "1. Análise Sumária do Período", 0, 1, "L")
        
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 6, 
            f"O período analisado (Total de {num_campanhas} campanhas) demonstrou um investimento total de "
            f"R$ {total_investimento_geral:,.0f} mil. O alcance total foi de {df.loc[:, 'Reach_Milhoes'].sum():,.1f} milhões, com um CPM médio de R$ {df.loc[:, 'CPM_R$'].mean():.2f}. "
            f"O mês com maior investimento foi **{maior_investimento_mes['Mes']}** (R$ {maior_investimento_mes['Total_Investimento']:,.0f} mil)."
        )
        pdf.ln(5)

        # ------------------------------------------------------------------
        # --- SEÇÃO 2: PERFORMANCE CONSOLIDADA POR MÍDIA (NARRATIVA) ---
        # ------------------------------------------------------------------
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "2. Performance Tática por Tipo de Mídia", 0, 1, "L")
        
        pdf.set_font("Arial", "", 12)
        
        cpm_digital = df_media[df_media['Tipo_Midia'] == 'Digital']['Media_CPM'].iloc[0]
        cpm_estatica = df_media[df_media['Tipo_Midia'] == 'Estática']['Media_CPM'].iloc[0]
        
        reach_digital = df_media[df_media['Tipo_Midia'] == 'Digital']['Total_Reach'].iloc[0]
        freq_digital = df_media[df_media['Tipo_Midia'] == 'Digital']['Media_Frequencia'].iloc[0]
        
        narrativa_midia = (
            f"A mídia **Digital** se estabeleceu como a opção mais eficiente, com um CPM médio de R$ {cpm_digital:.2f} (vs. R$ {cpm_estatica:.2f} da Estática). "
            f"Esta eficiência resultou em um Reach total de {reach_digital:.1f} milhões, acompanhado por uma alta frequência média ({freq_digital:.1f} exposições). "
            f"Recomendamos uma alocação prioritária em mídias com o menor custo por resultado para maximizar o alcance por real investido."
        )
        pdf.multi_cell(0, 6, narrativa_midia)
        
        pdf.ln(5)

        # ------------------------------------------------------------------
        # --- SEÇÃO 3: ANÁLISE REACH vs. FREQUÊNCIA (NOVO DETALHE) ---
        # ------------------------------------------------------------------
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "3. Análise: O Equilíbrio entre Alcance (Reach) e Frequência", 0, 1, "L")
        
        pdf.set_font("Arial", "", 12)
        
        frequencia_geral = df['Frequencia'].mean()
        if frequencia_geral > 5.5:
            foco_estrategico = "A estratégia da campanha se inclinou para garantir uma **Frequência** elevada, com média de {frequencia_geral:.1f} exposições por pessoa, otimizando a memorização da mensagem. A manutenção deste nível de frequência requer um investimento constante."
        else:
            foco_estrategico = "A estratégia foi balanceada, com maior foco no **Reach** (alcance) e uma frequência média de {frequencia_geral:.1f}. O próximo passo pode ser otimizar campanhas específicas para aumentar a frequência em segmentos-chave."
            
        pdf.multi_cell(0, 6, foco_estrategico.format(frequencia_geral=frequencia_geral))
        
        pdf.ln(5)
        
        # Quebra de página para começar a projeção e detalhamento na próxima folha
        pdf.add_page()
        
        # ------------------------------------------------------------------
        # --- SEÇÃO 4: PROJEÇÃO SAZONAL ---
        # ------------------------------------------------------------------
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, f"4. Projeção Estratégica: Campanha Sazonal {projecao_mes}", 0, 1, "L")
        
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 6, 
            f"Focando no próximo período sazonal de **{projecao_mes}**, que historicamente demonstrou alta demanda (Base de Performance: **{narrativa_sazonal}**), esta projeção simula o potencial de alcance com um aumento de **{aumento_investimento_percent*100:.0f}%** no investimento."
        )
        pdf.ln(3)

        # Tabela de Projeção
        pdf.set_font("Arial", "B", 11)
        col_widths_proj = [50, 40, 40, 40]
        headers_proj = ["Métrica", "Cenário Histórico", "Cenário Projetado", "Incremento"]
        
        for col, width in zip(headers_proj, col_widths_proj):
            pdf.cell(width, 7, col, 1, 0, "C")
        pdf.ln()

        pdf.set_font("Arial", "", 10)

        # Linha Investimento
        incremento_investimento = novo_investimento - investimento_base
        pdf.cell(col_widths_proj[0], 7, "Investimento (R$K)", 1, 0)
        pdf.cell(col_widths_proj[1], 7, f"R$ {investimento_base:,.0f}", 1, 0, "R")
        pdf.set_font("Arial", "B", 10)
        pdf.cell(col_widths_proj[2], 7, f"R$ {novo_investimento:,.0f}", 1, 0, "R")
        pdf.set_font("Arial", "", 10)
        pdf.cell(col_widths_proj[3], 7, f"R$ {incremento_investimento:,.0f}", 1, 0, "R")
        pdf.ln()

        # Linha Reach
        incremento_reach = novo_reach_proj_milhoes - reach_base
        pdf.cell(col_widths_proj[0], 7, "Reach (Milhões)", 1, 0)
        pdf.cell(col_widths_proj[1], 7, f"{reach_base:.1f}", 1, 0, "R")
        pdf.set_font("Arial", "B", 10)
        pdf.cell(col_widths_proj[2], 7, f"{novo_reach_proj_milhoes:.1f}", 1, 0, "R")
        pdf.set_font("Arial", "", 10)
        pdf.cell(col_widths_proj[3], 7, f"{incremento_reach:.1f}", 1, 0, "R")
        pdf.ln()
        
        pdf.ln(8)
        
        # ------------------------------------------------------------------
        # --- SEÇÃO 5: PERFORMANCE CONSOLIDADA POR MÍDIA (TABELA) ---
        # ------------------------------------------------------------------
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "5. Detalhe Consolidado por Tipo de Mídia", 0, 1, "L")
        
        pdf.set_font("Arial", "B", 10)
        col_widths_media = [40, 40, 40, 40, 30]
        headers_media = ["Mídia", "Investimento (R$K)", "Reach (Milhões)", "CPM Médio (R$)", "Freq. Média"]
        
        for col, width in zip(headers_media, col_widths_media):
            pdf.cell(width, 7, col, 1, 0, "C")
        pdf.ln()

        pdf.set_font("Arial", "", 10)
        for _, row in df_media.iterrows():
            pdf.cell(col_widths_media[0], 7, row['Tipo_Midia'], 1, 0)
            pdf.cell(col_widths_media[1], 7, f"R$ {row['Total_Investimento']:,.0f}", 1, 0, "R")
            pdf.cell(col_widths_media[2], 7, f"{row['Total_Reach']:.1f}", 1, 0, "R")
            
            if row['Media_CPM'] == melhor_midia_cpm['Media_CPM']:
                pdf.set_font("Arial", "B", 10)
            pdf.cell(col_widths_media[3], 7, f"R$ {row['Media_CPM']:.2f}", 1, 0, "R")
            pdf.set_font("Arial", "", 10) 
            
            pdf.cell(col_widths_media[4], 7, f"{row['Media_Frequencia']:.1f}", 1, 0, "R")
            pdf.ln()
        
        pdf.ln(5)

        # ------------------------------------------------------------------
        # --- SEÇÃO 6: TABELA DE PERFORMANCE MENSAL ---
        # ------------------------------------------------------------------
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "6. Detalhe Completo de Evolução Mensal", 0, 1, "L")
        
        pdf.set_font("Arial", "B", 9)
        col_widths = [30, 35, 35, 35, 35]
        headers = ["Mês", "Investimento (R$K)", "Reach (Milhões)", "CPM Médio (R$)", "Freq. Média"] 
        
        for col, width in zip(headers, col_widths):
            pdf.cell(width, 7, col, 1, 0, "C")
        pdf.ln()

        pdf.set_font("Arial", "", 9)
        for _, row in df_monthly.iterrows():
            pdf.cell(col_widths[0], 7, row['Mes'], 1, 0)
            pdf.cell(col_widths[1], 7, f"R$ {row['Total_Investimento']:,.0f}", 1, 0, "R")
            pdf.cell(col_widths[2], 7, f"{row['Total_Reach']:.1f}", 1, 0, "R")
            
            if row['Media_CPM'] > df_monthly['Media_CPM'].mean() * 1.1:
                pdf.set_text_color(255, 0, 0) # Alto CPM
            pdf.cell(col_widths[3], 7, f"R$ {row['Media_CPM']:.2f}", 1, 0, "R")
            pdf.set_text_color(0, 0, 0) 
            
            pdf.cell(col_widths[4], 7, f"{row['Media_Frequencia']:.1f}", 1, 0, "R") 
            pdf.ln()

        pdf.ln(10)
        
        # Quebra de página para a última tabela
        pdf.add_page()

        # ------------------------------------------------------------------
        # --- SEÇÃO 7: DETALHE COMPLETO DA CAMPANHA (TOP 10) ---
        # ------------------------------------------------------------------
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "7. Detalhe Tático por Campanha (Top 10 em Investimento)", 0, 1, "L")
        
        pdf.set_font("Arial", "I", 10)
        pdf.cell(200, 5, "Análise detalhada das 10 campanhas com maior investimento no período.", 0, 1, "L")
        pdf.ln(2)

        pdf.set_font("Arial", "B", 7) 
        col_widths_detalhe = [18, 15, 20, 20, 20, 20, 20, 20]
        headers_detalhe = ["ID", "Mês", "Mídia", "Invest.(K)", "Reach(MM)", "Freq.", "CPM", "Audiência(K)"]
        
        for col, width in zip(headers_detalhe, col_widths_detalhe):
            pdf.cell(width, 7, col, 1, 0, "C")
        pdf.ln()

        pdf.set_font("Arial", "", 7)
        df_detail = df.sort_values(by='Investimento_Mil_R$', ascending=False).head(10)
        
        for _, row in df_detail.iterrows():
            pdf.cell(col_widths_detalhe[0], 5, row['ID_Campanha'], 1, 0)
            pdf.cell(col_widths_detalhe[1], 5, row['Mes'], 1, 0, "C")
            pdf.cell(col_widths_detalhe[2], 5, row['Tipo_Midia'], 1, 0)
            pdf.cell(col_widths_detalhe[3], 5, f"{row['Investimento_Mil_R$']:.1f}", 1, 0, "R")
            pdf.cell(col_widths_detalhe[4], 5, f"{row['Reach_Milhoes']:.1f}", 1, 0, "R")
            pdf.cell(col_widths_detalhe[5], 5, f"{row['Frequencia']:.1f}", 1, 0, "R")
            pdf.cell(col_widths_detalhe[6], 5, f"{row['CPM_R$']:.2f}", 1, 0, "R")
            pdf.cell(col_widths_detalhe[7], 5, f"{row['Audiencia_Pico_K']}", 1, 0, "R")
            pdf.ln()

        # RETORNO BINÁRIO
        buffer = io.BytesIO(pdf.output(dest='S'))
        return buffer.getvalue() 
        
    except ImportError:
        st.error("Erro: A biblioteca `fpdf` não foi encontrada. Certifique-se de que está instalada (pip install fpdf2).")
        return b"ERRO: Instale 'fpdf2' para gerar o PDF."

    except Exception as e:
        st.error(f"Erro Crítico ao gerar PDF: {type(e).__name__}: {e}")
        return f"ERRO CRÍTICO NA GERAÇÃO DO PDF: {type(e).__name__}: {e}".encode('utf-8')

# -------------------------------
# Botão de Download PDF (chama a função com os parâmetros interativos)
# -------------------------------
st.markdown("---")
pdf_bytes = create_pdf_report(df_relatorio, projecao_mes_selecionado, aumento_investimento_decimal)

st.download_button(
    label="Baixar Relatório em PDF",
    data=pdf_bytes,
    file_name=f'relatorio_executivo_projecao_{projecao_mes_selecionado}.pdf',
    mime='application/pdf',
    type="primary",
    help="Gera um relatório PDF detalhado com análise sazonal e projeção de investimento futura."
)
