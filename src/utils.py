# src/utils.py - helpers pequenos (cache, formatação)
import streamlit as st

def get_secret(key, default=None):
    """Tenta ler st.secrets, fallback para None."""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def set_page_config_and_style(page_title: str, main_title: str, subtitle: str = None):
    """
    Define a configuração básica da página (wide layout) e aplica o estilo de cabeçalho padronizado.

    Args:
        page_title (str): Título da aba do navegador.
        main_title (str): Título principal exibido na página (usando o estilo bonito).
        subtitle (str, optional): Subtítulo ou breve descrição.
    """
    # 1. Configuração da Página
    st.set_page_config(page_title=page_title, layout="wide")

    # 2. Título Principal Estilizado
    st.markdown(
        f"<h1 style='text-align: center; color: #1E90FF;'>{main_title}</h1>",
        unsafe_allow_html=True
    )

    # 3. Subtítulo Padronizado (Opcional)
    if subtitle:
        st.markdown(
            f"<p style='text-align: center; font-size: 18px;'>{subtitle}</p>",
            unsafe_allow_html=True
        )
    
    # 4. Separador (opcional, mas bom para delimitar o cabeçalho)
    st.markdown("---")

# Você também pode adicionar a função de métrica estilizada aqui, se quiser!
def styled_metric(col, title, value, color):
    """Aplica o estilo de métrica com fundo colorido e fonte branca (baseado no código de Datas Sazonais)."""
    with col:
        st.markdown(f"""
            <div style="text-align:center; padding:15px; background:{color}; border-radius:12px; color:white;">
                <h4 style="margin:0;">{title}</h4>
                <h2 style="margin:8px 0;">{value}</h2>
            </div>
            """.replace(",", "."), unsafe_allow_html=True)
