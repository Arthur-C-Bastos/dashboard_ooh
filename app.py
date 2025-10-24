import streamlit as st


st.set_page_config(page_title='OOH Dashboard BR', layout = 'wide')
st.title('OHH Dashboard BR - Versão didática')
st.markdown('''
Este é um app didático que organiza várias páginas (abas) para análise OOH no Brasil.
Navegue pelas abas e conheça o projeto.
''')

st.sidebar.header('Sobre')
st.sidebar.info('Projeto educacional')

st.markdown('''Selecione uma aba para começar: Mapa Interativo, Indicadores, Mobilidade, Clima, Análise e Configurações. ''')