"""
Fonctions utilitaires partagées entre les pages.
"""

import os
import streamlit as st


def get_api_key() -> str:
    """Récupère la clé API OpenAI depuis les Secrets, l'environnement ou la session.

    Ordre de priorité :
    1. Streamlit Secrets (OPENAI_API_KEY)
    2. Variable d'environnement (OPENAI_API_KEY)
    3. Saisie utilisateur dans la barre latérale (sidebar_api_key)

    Returns:
        La clé API ou une chaîne vide si non trouvée.
    """
    try:
        sk = st.secrets.get("OPENAI_API_KEY", "")
        if sk:
            return sk
    except Exception:
        pass

    env = os.environ.get("OPENAI_API_KEY", "")
    if env:
        return env

    return st.session_state.get("sidebar_api_key", "")
