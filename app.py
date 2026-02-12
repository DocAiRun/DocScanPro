import streamlit as st
import openai
import json
import base64
import io
import os
import pandas as pd
from datetime import datetime
from collections import defaultdict

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="DocScan Pro · Extraction Documentaire IA",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }
    
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
        padding: 2rem; border-radius: 12px; color: white; margin-bottom: 2rem;
    }
    .main-header h1 { margin: 0; font-size: 2rem; font-weight: 700; }
    .main-header p { margin: 0.5rem 0 0 0; opacity: 0.85; font-size: 1rem; }
    
    .stat-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 1rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .stat-card h3 { margin: 0; color: #2d6a9f; font-size: 1.5rem; }
    .stat-card p { margin: 0.3rem 0 0 0; color: #64748b; font-size: 0.8rem; }
    
    .success-banner {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white; padding: 0.8rem 1.2rem; border-radius: 8px; margin: 0.5rem 0; font-weight: 500;
    }
    
    div[data-testid="stFileUploader"] {
        border: 2px dashed #2d6a9f; border-radius: 12px; padding: 1rem; background: #f0f7ff;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Config types
# ─────────────────────────────────────────────
TYPE_CONFIG = {
    "facture":          {"icon": "🧾", "label": "Factures"},
    "devis":            {"icon": "📝", "label": "Devis"},
    "bon_de_commande":  {"icon": "📦", "label": "Bons de commande"},
    "fiche_de_paie":    {"icon": "💰", "label": "Fiches de paie"},
    "note_de_frais":    {"icon": "🧾", "label": "Notes de frais"},
    "autre":            {"icon": "📄", "label": "Autres"},
}

# ─────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

# ─────────────────────────────────────────────
# API Key resolution
# ─────────────────────────────────────────────
def get_api_key():
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

# ─────────────────────────────────────────────
# Sidebar
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
            "Clé API OpenAI", type="password",
            help="Commence par sk-... ou configure-la dans Streamlit Secrets.",
            key="sidebar_api_key"
        )
    
    st.markdown("---")
    
    if st.session_state.history:
        st.markdown("### 👥 Clients détectés")
        clients = sorted(set(h["client"] for h in st.session_state.history))
        for c in clients:
            count = sum(1 for h in st.session_state.history if h["client"] == c)
            types_for_client = set(h["type"] for h in st.session_state.history if h["client"] == c)
            type_icons = " ".join(TYPE_CONFIG.get(t, {}).get("icon", "📄") for t in types_for_client)
            st.markdown(f"**{c}** — {count} doc(s) {type_icons}")
        
        st.markdown("---")
        st.metric("Total documents", len(st.session_state.history))
        
        if st.button("🗑️ Réinitialiser", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("Aucun document traité.")

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📄 DocScan Pro</h1>
    <p>Extraction IA · Classement auto par Client & Type · Export Excel organisé<br>
    Propulsé par GPT-4o Vision · Conçu pour La Réunion 🇷🇪</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Prompt système
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """Tu es un assistant expert en extraction de données documentaires.
On te fournit l'image d'un document professionnel.

MISSIONS :
1. IDENTIFIER le type de document
2. IDENTIFIER le client (= la personne/entreprise qui REÇOIT le document ou à qui il est adressé. Si c'est une facture, le client est le destinataire. Si c'est une fiche de paie, le client est l'employeur.)
3. EXTRAIRE toutes les informations

Réponds UNIQUEMENT avec un JSON valide (sans markdown, sans backticks) :

{
    "type_document": "facture | devis | bon_de_commande | fiche_de_paie | note_de_frais | autre",
    "confiance_type": "haute | moyenne | basse",
    "client_detecte": "Nom de l'entreprise/personne cliente identifiée",
    "emetteur": {
        "nom": "",
        "adresse": "",
        "telephone": "",
        "email": "",
        "siret": "",
        "tva_intra": ""
    },
    "destinataire": {
        "nom": "",
        "adresse": "",
        "telephone": "",
        "email": "",
        "siret": ""
    },
    "document": {
        "numero": "",
        "date_emission": "",
        "date_echeance": "",
        "reference": "",
        "objet": ""
    },
    "lignes": [
        {
            "description": "",
            "quantite": "",
            "prix_unitaire_ht": "",
            "montant_ht": "",
            "tva_pourcent": ""
        }
    ],
    "totaux": {
        "total_ht": "",
        "total_tva": "",
        "total_ttc": "",
        "devise": "EUR"
    },
    "paiement": {
        "mode": "",
        "iban": "",
        "bic": "",
        "conditions": ""
    },
    "notes": ""
}

Règles :
- Remplis UNIQUEMENT les champs trouvés dans le document, laisse "" pour les absents
- client_detecte : déduis le nom du client principal (destinataire pour facture/devis, employeur pour fiche de paie)
- Montants en string "1234.56", dates en "JJ/MM/AAAA"
- Si le type ne correspond à aucun listé, utilise "autre"
"""

# ─────────────────────────────────────────────
# Core functions
# ─────────────────────────────────────────────
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")


def extract_data(image_base64, file_type, api_key):
    client = openai.OpenAI(api_key=api_key)
    mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
    mime = mime_map.get(file_type.lower(), "image/jpeg")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": "Analyse ce document. Identifie le client, le type, et extrais toutes les données en JSON."},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_base64}", "detail": "high"}}
            ]}
        ],
        max_tokens=4096,
        temperature=0
    )
    
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
    return json.loads(raw)


def flatten_data(data):
    flat = {}
    flat["Client"] = data.get("client_detecte", "Non identifié")
    flat["Type"] = data.get("type_document", "autre")
    flat["Confiance"] = data.get("confiance_type", "")
    
    em = data.get("emetteur", {})
    flat["Émetteur"] = em.get("nom", "")
    flat["Émetteur Adresse"] = em.get("adresse", "")
    flat["Émetteur Tél"] = em.get("telephone", "")
    flat["Émetteur Email"] = em.get("email", "")
    flat["Émetteur SIRET"] = em.get("siret", "")
    
    dest = data.get("destinataire", {})
    flat["Destinataire"] = dest.get("nom", "")
    flat["Destinataire Adresse"] = dest.get("adresse", "")
    
    doc = data.get("document", {})
    flat["N° Document"] = doc.get("numero", "")
    flat["Date émission"] = doc.get("date_emission", "")
    flat["Date échéance"] = doc.get("date_echeance", "")
    flat["Référence"] = doc.get("reference", "")
    flat["Objet"] = doc.get("objet", "")
    
    tot = data.get("totaux", {})
    flat["Total HT"] = tot.get("total_ht", "")
    flat["Total TVA"] = tot.get("total_tva", "")
    flat["Total TTC"] = tot.get("total_ttc", "")
    flat["Devise"] = tot.get("devise", "EUR")
    
    paie = data.get("paiement", {})
    flat["Mode paiement"] = paie.get("mode", "")
    flat["IBAN"] = paie.get("iban", "")
    flat["Notes"] = data.get("notes", "")
    return flat


def lines_to_df(data):
    lignes = data.get("lignes", [])
    if not lignes:
        return None
    rows = []
    for l in lignes:
        rows.append({
            "Description": l.get("description", ""),
            "Quantité": l.get("quantite", ""),
            "Prix unitaire HT": l.get("prix_unitaire_ht", ""),
            "Montant HT": l.get("montant_ht", ""),
            "TVA (%)": l.get("tva_pourcent", ""),
        })
    return pd.DataFrame(rows)


def safe_sheet_name(name, max_len=31):
    for ch in ['\\', '/', '*', '?', ':', '[', ']']:
        name = name.replace(ch, '_')
    return name[:max_len]


def build_organized_excel(history):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        
        # 1. INDEX GÉNÉRAL
        all_flats = []
        for h in history:
            row = h["flat"].copy()
            row["Fichier source"] = h["filename"]
            row["Date extraction"] = h["timestamp"]
            all_flats.append(row)
        pd.DataFrame(all_flats).to_excel(writer, sheet_name="Index général", index=False)
        
        # 2. PAR CLIENT → PAR TYPE
        by_client = defaultdict(list)
        for h in history:
            by_client[h["client"]].append(h)
        
        for client_name, client_docs in sorted(by_client.items()):
            by_type = defaultdict(list)
            for doc in client_docs:
                by_type[doc["type"]].append(doc)
            
            for type_key, type_docs in sorted(by_type.items()):
                type_label = TYPE_CONFIG.get(type_key, {}).get("label", type_key)
                sheet_name = safe_sheet_name(f"{client_name} - {type_label}")
                
                rows = []
                for doc in type_docs:
                    row = doc["flat"].copy()
                    row["Fichier source"] = doc["filename"]
                    rows.append(row)
                pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Lignes détaillées
                all_lines = []
                for doc in type_docs:
                    if doc["lines_df"] is not None and not doc["lines_df"].empty:
                        ldf = doc["lines_df"].copy()
                        ldf.insert(0, "N° Document", doc["flat"].get("N° Document", ""))
                        ldf.insert(0, "Fichier", doc["filename"])
                        all_lines.append(ldf)
                
                if all_lines:
                    combined = pd.concat(all_lines, ignore_index=True)
                    lines_sheet = safe_sheet_name(f"{client_name} - {type_label} DET")
                    combined.to_excel(writer, sheet_name=lines_sheet, index=False)
    
    return output.getvalue()


def build_single_excel(flat, lines_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([flat]).to_excel(writer, sheet_name="Résumé", index=False)
        if lines_df is not None and not lines_df.empty:
            lines_df.to_excel(writer, sheet_name="Lignes détaillées", index=False)
    return output.getvalue()


# ─────────────────────────────────────────────
# UPLOAD & EXTRACTION
# ─────────────────────────────────────────────
st.markdown("## 📤 Uploader des documents")

uploaded_files = st.file_uploader(
    "Glisse tes documents ici — factures, devis, bons de commande, fiches de paie...",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
    help="Formats : PNG, JPG, JPEG, WEBP · Max 20 Mo par fichier"
)

api_key = get_api_key()

if uploaded_files and not api_key:
    st.warning("⚠️ Entre ta clé API OpenAI dans la barre latérale ou configure les Secrets Streamlit.")

if uploaded_files and api_key:
    if st.button("🚀 Lancer l'extraction", type="primary", use_container_width=True):
        
        progress = st.progress(0, text="Préparation...")
        
        for i, uploaded_file in enumerate(uploaded_files):
            progress.progress(i / len(uploaded_files), text=f"📄 Analyse de {uploaded_file.name} ({i+1}/{len(uploaded_files)})...")
            
            st.markdown(f"---\n### 📄 {uploaded_file.name}")
            col_img, col_result = st.columns([1, 1.5])
            
            with col_img:
                st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
            
            with col_result:
                with st.spinner("🔍 GPT-4o Vision analyse..."):
                    try:
                        file_ext = uploaded_file.name.rsplit(".", 1)[-1]
                        img_b64 = encode_image(uploaded_file)
                        data = extract_data(img_b64, file_ext, api_key)
                        
                        flat = flatten_data(data)
                        lines_df = lines_to_df(data)
                        
                        doc_type = data.get("type_document", "autre")
                        client_name = data.get("client_detecte", "Non identifié") or "Non identifié"
                        
                        st.session_state.history.append({
                            "filename": uploaded_file.name,
                            "raw": data,
                            "flat": flat,
                            "lines_df": lines_df,
                            "type": doc_type,
                            "client": client_name,
                            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")
                        })
                        
                        type_conf = TYPE_CONFIG.get(doc_type, TYPE_CONFIG["autre"])
                        st.markdown(
                            f'<div class="success-banner">'
                            f'✅ {type_conf["icon"]} {type_conf["label"].upper()} · Client : {client_name}'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        
                        doc_info = data.get("document", {})
                        totaux = data.get("totaux", {})
                        
                        mc1, mc2, mc3 = st.columns(3)
                        with mc1:
                            st.markdown(f'<div class="stat-card"><h3>{doc_info.get("numero", "—")}</h3><p>N° Document</p></div>', unsafe_allow_html=True)
                        with mc2:
                            st.markdown(f'<div class="stat-card"><h3>{doc_info.get("date_emission", "—")}</h3><p>Date</p></div>', unsafe_allow_html=True)
                        with mc3:
                            st.markdown(f'<div class="stat-card"><h3>{totaux.get("total_ttc", "—")} €</h3><p>Total TTC</p></div>', unsafe_allow_html=True)
                        
                        if lines_df is not None and not lines_df.empty:
                            st.markdown("**📋 Lignes :**")
                            st.dataframe(lines_df, use_container_width=True, hide_index=True)
                        
                        excel_bytes = build_single_excel(flat, lines_df)
                        st.download_button(
                            label=f"📥 Excel · {uploaded_file.name}",
                            data=excel_bytes,
                            file_name=f"{client_name}_{doc_type}_{uploaded_file.name.rsplit('.', 1)[0]}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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
# HISTORIQUE, FILTRES & EXPORT
# ─────────────────────────────────────────────
if st.session_state.history:
    st.markdown("---")
    st.markdown("## 📊 Tableau de bord")
    
    all_clients = sorted(set(h["client"] for h in st.session_state.history))
    all_types = sorted(set(h["type"] for h in st.session_state.history))
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-card"><h3>{len(st.session_state.history)}</h3><p>Documents</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card"><h3>{len(all_clients)}</h3><p>Clients</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-card"><h3>{len(all_types)}</h3><p>Types</p></div>', unsafe_allow_html=True)
    with c4:
        total = 0
        for h in st.session_state.history:
            ttc = h["raw"].get("totaux", {}).get("total_ttc", "0")
            try:
                total += float(str(ttc).replace(",", ".").replace(" ", ""))
            except (ValueError, TypeError):
                pass
        st.markdown(f'<div class="stat-card"><h3>{total:,.2f} €</h3><p>Total TTC</p></div>', unsafe_allow_html=True)
    
    st.markdown("")
    
    # Filtres
    st.markdown("### 🔍 Filtrer")
    fc1, fc2 = st.columns(2)
    with fc1:
        filter_client = st.selectbox("👤 Client", ["Tous"] + all_clients)
    with fc2:
        type_options = ["Tous"] + [f"{TYPE_CONFIG.get(t, {}).get('icon', '📄')} {TYPE_CONFIG.get(t, {}).get('label', t)}" for t in all_types]
        filter_type_display = st.selectbox("📋 Type", type_options)
    
    filtered = st.session_state.history
    if filter_client != "Tous":
        filtered = [h for h in filtered if h["client"] == filter_client]
    if filter_type_display != "Tous":
        for t_key, t_conf in TYPE_CONFIG.items():
            if t_conf["label"] in filter_type_display:
                filtered = [h for h in filtered if h["type"] == t_key]
                break
    
    if filtered:
        st.markdown(f"### 📋 Documents ({len(filtered)} résultat{'s' if len(filtered) > 1 else ''})")
        
        display_rows = []
        for h in filtered:
            type_conf = TYPE_CONFIG.get(h["type"], TYPE_CONFIG["autre"])
            display_rows.append({
                "Client": h["client"],
                "Type": f"{type_conf['icon']} {type_conf['label']}",
                "N° Document": h["flat"].get("N° Document", ""),
                "Date": h["flat"].get("Date émission", ""),
                "Émetteur": h["flat"].get("Émetteur", ""),
                "Total TTC": h["flat"].get("Total TTC", ""),
                "Fichier": h["filename"],
                "Extrait le": h["timestamp"],
            })
        st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Aucun document ne correspond aux filtres.")
    
    # Exports
    st.markdown("---")
    st.markdown("### 📥 Export organisé")
    st.caption("L'Excel contient : **Index général** + une feuille par **Client × Type** + **lignes détaillées**")
    
    exp1, exp2 = st.columns(2)
    
    with exp1:
        global_excel = build_organized_excel(st.session_state.history)
        st.download_button(
            label="📥 Export complet (tous clients, tous types)",
            data=global_excel,
            file_name=f"DocScan_Export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )
    
    with exp2:
        if filter_client != "Tous" or filter_type_display != "Tous":
            filtered_excel = build_organized_excel(filtered)
            st.download_button(
                label=f"📥 Export filtré ({filter_client})",
                data=filtered_excel,
                file_name=f"DocScan_{filter_client}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.caption("💡 Utilise les filtres pour exporter un client ou type spécifique.")

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<center style='color: #94a3b8; font-size: 0.85rem;'>"
    "DocScan Pro v2.0 · GPT-4o Vision · Classement auto Client × Type · Conçu à La Réunion 🇷🇪"
    "</center>",
    unsafe_allow_html=True
)
