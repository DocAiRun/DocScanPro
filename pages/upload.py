"""
Page Upload & Extraction — DocScan Pro.

Permet d'uploader des documents (PDF, images) ou de prendre une photo directement
via la caméra, puis d'analyser chaque document via GPT-4o Vision et de télécharger
les données extraites au format Excel.
"""

import json
from datetime import datetime

import openai
import streamlit as st
from pdf2image import convert_from_bytes

from modules.classification import calculer_fingerprint, detecter_doublon
from modules.export import build_single_excel
from modules.extraction import (
    encode_image,
    extract_data,
    flatten_data,
    lines_to_df,
    pdf_to_image_b64,
)
from utils.config import TYPE_CONFIG
from utils.helpers import get_api_key

# ─────────────────────────────────────────────
# En-tête
# ─────────────────────────────────────────────
st.markdown(
    """
<div class="main-header">
    <h1>📄 DocScan Pro</h1>
    <p>Extraction IA · Classement auto par Client & Type · Export Excel organisé<br>
    Propulsé par GPT-4o Vision · Conçu pour La Réunion 🇷🇪</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("## 📤 Ajouter des documents")

# ─────────────────────────────────────────────
# Saisie : fichiers ou caméra (onglets)
# ─────────────────────────────────────────────
tab_fichier, tab_camera = st.tabs(["📁 Fichiers", "📷 Photo directe"])

with tab_fichier:
    uploaded_files = st.file_uploader(
        "Glisse tes documents ici — factures, devis, bons de commande, fiches de paie...",
        type=["png", "jpg", "jpeg", "webp", "pdf"],
        accept_multiple_files=True,
        help="Formats : PNG, JPG, JPEG, WEBP, PDF · Max 20 Mo par fichier",
    )

with tab_camera:
    st.caption("Pointe ta caméra vers le document, puis clique sur le bouton de capture.")
    camera_photo = st.camera_input("Capturer un document", label_visibility="collapsed")

# ─────────────────────────────────────────────
# Normalisation des sources en une liste commune
# Chaque item : {"file": obj, "name": str, "ext": str}
# ─────────────────────────────────────────────
fichiers_a_traiter: list[dict] = []

if uploaded_files:
    for f in uploaded_files:
        fichiers_a_traiter.append(
            {
                "file": f,
                "name": f.name,
                "ext": f.name.rsplit(".", 1)[-1].lower(),
            }
        )

if camera_photo:
    nom_photo = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    fichiers_a_traiter.append(
        {
            "file": camera_photo,
            "name": nom_photo,
            "ext": "jpeg",
        }
    )

# ─────────────────────────────────────────────
# Vérification clé API
# ─────────────────────────────────────────────
api_key = get_api_key()

if fichiers_a_traiter and not api_key:
    st.warning(
        "⚠️ Entre ta clé API OpenAI dans la barre latérale ou configure les Secrets Streamlit."
    )

# ─────────────────────────────────────────────
# Extraction
# ─────────────────────────────────────────────
if fichiers_a_traiter and api_key:
    if st.button("🚀 Lancer l'extraction", type="primary", use_container_width=True):

        progress = st.progress(0, text="Préparation...")

        for i, item in enumerate(fichiers_a_traiter):
            fichier = item["file"]
            nom = item["name"]
            ext = item["ext"]

            progress.progress(
                i / len(fichiers_a_traiter),
                text=f"📄 Analyse de {nom} ({i+1}/{len(fichiers_a_traiter)})...",
            )

            st.markdown(f"---\n### 📄 {nom}")
            col_img, col_result = st.columns([1, 1.5])

            with col_img:
                if ext == "pdf":
                    try:
                        preview_images = convert_from_bytes(
                            fichier.getvalue(), first_page=1, last_page=1, dpi=150
                        )
                        st.image(
                            preview_images[0],
                            caption=nom,
                            use_container_width=True,
                        )
                    except Exception:
                        st.info(f"📄 Fichier PDF : {nom}")
                else:
                    st.image(fichier, caption=nom, use_container_width=True)

            with col_result:
                with st.spinner("🔍 GPT-4o Vision analyse..."):
                    try:
                        if ext == "pdf":
                            img_b64 = pdf_to_image_b64(fichier)
                            send_ext = "png"
                        else:
                            img_b64 = encode_image(fichier)
                            send_ext = ext

                        data = extract_data(img_b64, send_ext, api_key)

                        flat = flatten_data(data)
                        lines_df = lines_to_df(data)

                        doc_type = data.get("type_document", "autre")
                        client_name = (
                            data.get("client_detecte", "Non identifié") or "Non identifié"
                        )

                        # Détection de doublons
                        fingerprint = calculer_fingerprint(data)
                        doublon = detecter_doublon(data, st.session_state.history)
                        if doublon:
                            qualif = "exact" if doublon.get("match") == "exact" else "probable"
                            st.warning(
                                f"⚠️ Doublon **{qualif}** détecté — ce document ressemble à "
                                f"**{doublon['filename']}** (extrait le {doublon['timestamp']}). "
                                f"Ajouté quand même."
                            )

                        st.session_state.history.append(
                            {
                                "filename": nom,
                                "raw": data,
                                "flat": flat,
                                "lines_df": lines_df,
                                "type": doc_type,
                                "client": client_name,
                                "fingerprint": fingerprint,
                                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            }
                        )

                        type_conf = TYPE_CONFIG.get(doc_type, TYPE_CONFIG["autre"])
                        st.markdown(
                            f'<div class="success-banner">'
                            f'✅ {type_conf["icon"]} {type_conf["label"].upper()} · Client : {client_name}'
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                        doc_info = data.get("document", {})
                        totaux = data.get("totaux", {})

                        mc1, mc2, mc3 = st.columns(3)
                        with mc1:
                            st.markdown(
                                f'<div class="stat-card"><h3>{doc_info.get("numero", "—")}</h3><p>N° Document</p></div>',
                                unsafe_allow_html=True,
                            )
                        with mc2:
                            st.markdown(
                                f'<div class="stat-card"><h3>{doc_info.get("date_emission", "—")}</h3><p>Date</p></div>',
                                unsafe_allow_html=True,
                            )
                        with mc3:
                            st.markdown(
                                f'<div class="stat-card"><h3>{totaux.get("total_ttc", "—")} €</h3><p>Total TTC</p></div>',
                                unsafe_allow_html=True,
                            )

                        if lines_df is not None and not lines_df.empty:
                            st.markdown("**📋 Lignes :**")
                            st.dataframe(
                                lines_df, use_container_width=True, hide_index=True
                            )

                        excel_bytes = build_single_excel(flat, lines_df)
                        st.download_button(
                            label=f"📥 Excel · {nom}",
                            data=excel_bytes,
                            file_name=f"{client_name}_{doc_type}_{nom.rsplit('.', 1)[0]}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )

                        with st.expander("🔧 JSON brut"):
                            st.json(data)

                    except json.JSONDecodeError as e:
                        st.error(f"❌ Erreur parsing JSON : {e}")
                    except openai.AuthenticationError:
                        st.error("❌ Clé API invalide.")
                        break
                    except Exception as e:
                        st.error(f"❌ Erreur : {str(e)}")

        progress.progress(1.0, text="✅ Extraction terminée !")

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<center style='color: #94a3b8; font-size: 0.85rem;'>"
    "DocScan Pro v2.0 · GPT-4o Vision · Classement auto Client × Type · Conçu à La Réunion 🇷🇪"
    "</center>",
    unsafe_allow_html=True,
)
