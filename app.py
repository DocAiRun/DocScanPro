"""
DocScan Pro — Point d'entrée principal.

Configure la page, injecte le CSS global, gère la sidebar partagée
et lance la navigation multi-pages via st.navigation().
"""

import streamlit as st

from utils.config import CSS, TYPE_CONFIG

# ─────────────────────────────────────────────
# Configuration de la page (doit être le 1er appel Streamlit)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="DocScan Pro · Extraction Documentaire IA",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS global (partagé par toutes les pages)
st.markdown(CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Initialisation du session state
# ─────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

# ─────────────────────────────────────────────
# Sidebar partagée (visible sur toutes les pages)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    has_secret = False
    try:
        has_secret = bool(st.secrets.get("OPENAI_API_KEY", ""))
    except Exception:
        pass

    if has_secret:
        st.success("✅ Clé API chargée via Secrets")
    else:
        st.text_input(
            "Clé API OpenAI",
            type="password",
            help="Commence par sk-... ou configure-la dans Streamlit Secrets.",
            key="sidebar_api_key",
        )

    st.markdown("---")

    if st.session_state.history:
        st.markdown("### 👥 Clients détectés")
        clients = sorted(set(h["client"] for h in st.session_state.history))
        for cl in clients:
            count = sum(1 for h in st.session_state.history if h["client"] == cl)
            types_for_client = set(
                h["type"] for h in st.session_state.history if h["client"] == cl
            )
            type_icons = " ".join(
                TYPE_CONFIG.get(t, {}).get("icon", "📄") for t in types_for_client
            )
            st.markdown(f"**{cl}** — {count} doc(s) {type_icons}")

        st.markdown("---")
        st.metric("Total documents", len(st.session_state.history))

        if st.button("🗑️ Réinitialiser", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("Aucun document traité.")

# ─────────────────────────────────────────────
# Navigation multi-pages
# ─────────────────────────────────────────────
upload_page = st.Page(
    "pages/upload.py",
    title="Upload & Extraction",
    icon="📤",
    default=True,
)
dashboard_page = st.Page(
    "pages/dashboard.py",
    title="Tableau de bord",
    icon="📊",
)

nav = st.navigation([upload_page, dashboard_page])
nav.run()
