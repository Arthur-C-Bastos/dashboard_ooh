# src/utils.py - helpers pequenos (cache, formatação)
import streamlit as st

def get_secret(key, default=None):
    """Tenta ler st.secrets, fallback para None."""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default
