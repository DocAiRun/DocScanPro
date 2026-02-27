"""
Configuration globale de DocScan Pro.

Contient les constantes partagées : CSS, types de documents, prompt système GPT-4o.
"""

# ─────────────────────────────────────────────
# CSS personnalisé
# ─────────────────────────────────────────────
CSS: str = """
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
"""

# ─────────────────────────────────────────────
# Types de documents supportés
# ─────────────────────────────────────────────
TYPE_CONFIG: dict[str, dict[str, str]] = {
    "facture":          {"icon": "🧾", "label": "Factures"},
    "devis":            {"icon": "📝", "label": "Devis"},
    "bon_de_commande":  {"icon": "📦", "label": "Bons de commande"},
    "fiche_de_paie":    {"icon": "💰", "label": "Fiches de paie"},
    "note_de_frais":    {"icon": "🧾", "label": "Notes de frais"},
    "autre":            {"icon": "📄", "label": "Autres"},
}

# Couleurs Excel par type de document (hex sans #)
TYPE_COLORS: dict[str, str] = {
    "facture":          "2563eb",
    "devis":            "7c3aed",
    "bon_de_commande":  "db2777",
    "fiche_de_paie":    "ea580c",
    "note_de_frais":    "059669",
    "autre":            "64748b",
}

# ─────────────────────────────────────────────
# Prompt système GPT-4o Vision
# ─────────────────────────────────────────────
SYSTEM_PROMPT: str = """Tu es un assistant expert en extraction de données documentaires.
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
