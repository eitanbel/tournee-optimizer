# Configuration de l'application - supporte .env (local) et st.secrets (Streamlit Cloud)
import os
from dotenv import load_dotenv

load_dotenv()

def _get_secret(key: str, default: str = "") -> str:
    """Lit d'abord les secrets Streamlit Cloud, puis le fichier .env local."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)

GOOGLE_MAPS_API_KEY = _get_secret("GOOGLE_MAPS_API_KEY")
DEFAULT_START_ADDRESS = _get_secret("DEFAULT_START_ADDRESS", "1 Rue de Rivoli, 75001 Paris, France")

# Timeout pour le solveur OR-Tools (en secondes)
SOLVER_TIMEOUT = 30
