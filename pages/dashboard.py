"""
Page Tableau de bord — DocScan Pro.

Affiche les statistiques, les filtres et les options d'export Excel
pour l'ensemble des documents traités dans la session.
"""

from datetime import datetime

import pandas as pd
import streamlit as st

from modules.export import build_organized_excel
from utils.config import TYPE_CONFIG

# ─────────────────────────────────────────────
# Garde : aucun document traité
# ─────────────────────────────────────────────
if not st.session_state.get("history"):
    st.markdown("## 📊 Tableau de bord")
    st.info(
        "💡 Aucun document traité. Rendez-vous sur la page **Upload & Extraction** pour commencer."
    )
    st.stop()

# ─────────────────────────────────────────────
# En-tête
# ─────────────────────────────────────────────
st.markdown("## 📊 Tableau de bord")

history: list[dict] = st.session_state.history
all_clients = sorted(set(h["client"] for h in history))
all_types = sorted(set(h["type"] for h in history))

# ─────────────────────────────────────────────
# Métriques globales
# ─────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f'<div class="stat-card"><h3>{len(history)}</h3><p>Documents</p></div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f'<div class="stat-card"><h3>{len(all_clients)}</h3><p>Clients</p></div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f'<div class="stat-card"><h3>{len(all_types)}</h3><p>Types</p></div>',
        unsafe_allow_html=True,
    )
with c4:
    total = 0.0
    for h in history:
        ttc = h["raw"].get("totaux", {}).get("total_ttc", "0")
        try:
            total += float(str(ttc).replace(",", ".").replace(" ", ""))
        except (ValueError, TypeError):
            pass
    st.markdown(
        f'<div class="stat-card"><h3>{total:,.2f} €</h3><p>Total TTC</p></div>',
        unsafe_allow_html=True,
    )

st.markdown("")

# ─────────────────────────────────────────────
# Filtres
# ─────────────────────────────────────────────
st.markdown("### 🔍 Filtrer")
fc1, fc2 = st.columns(2)

with fc1:
    filter_client: str = st.selectbox("👤 Client", ["Tous"] + all_clients)
with fc2:
    type_options = ["Tous"] + [
        f"{TYPE_CONFIG.get(t, {}).get('icon', '📄')} {TYPE_CONFIG.get(t, {}).get('label', t)}"
        for t in all_types
    ]
    filter_type_display: str = st.selectbox("📋 Type", type_options)

# Appliquer les filtres
filtered: list[dict] = history

if filter_client != "Tous":
    filtered = [h for h in filtered if h["client"] == filter_client]

if filter_type_display != "Tous":
    for t_key, t_conf in TYPE_CONFIG.items():
        if t_conf["label"] in filter_type_display:
            filtered = [h for h in filtered if h["type"] == t_key]
            break

# ─────────────────────────────────────────────
# Tableau des documents filtrés
# ─────────────────────────────────────────────
if filtered:
    st.markdown(
        f"### 📋 Documents ({len(filtered)} résultat{'s' if len(filtered) > 1 else ''})"
    )

    display_rows = []
    for h in filtered:
        type_conf = TYPE_CONFIG.get(h["type"], TYPE_CONFIG["autre"])
        display_rows.append(
            {
                "Client": h["client"],
                "Type": f"{type_conf['icon']} {type_conf['label']}",
                "N° Document": h["flat"].get("N° Document", ""),
                "Date": h["flat"].get("Date émission", ""),
                "Émetteur": h["flat"].get("Émetteur", ""),
                "Total TTC": h["flat"].get("Total TTC", ""),
                "Fichier": h["filename"],
                "Extrait le": h["timestamp"],
            }
        )
    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
else:
    st.info("Aucun document ne correspond aux filtres.")

# ─────────────────────────────────────────────
# Export Excel
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📥 Export organisé")
st.caption(
    "L'Excel contient : **Index général** + une feuille par **Client × Type** + **lignes détaillées**"
)

exp1, exp2 = st.columns(2)

with exp1:
    global_excel = build_organized_excel(history)
    st.download_button(
        label="📥 Export complet (tous clients, tous types)",
        data=global_excel,
        file_name=f"DocScan_Export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )

with exp2:
    if filter_client != "Tous" or filter_type_display != "Tous":
        filtered_excel = build_organized_excel(filtered)
        st.download_button(
            label=f"📥 Export filtré ({filter_client})",
            data=filtered_excel,
            file_name=f"DocScan_{filter_client}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.caption("💡 Utilise les filtres pour exporter un client ou type spécifique.")
