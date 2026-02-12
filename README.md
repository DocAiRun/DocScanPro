# 📄 DocScan Pro v2.0 — Extraction Documentaire IA

> Extraction intelligente + Classement auto par **Client** & **Type** + Export Excel organisé  
> Propulsé par GPT-4o Vision · Conçu pour La Réunion 🇷🇪

## 🚀 Fonctionnalités

- **Upload multi-documents** : Factures, devis, bons de commande, fiches de paie, notes de frais...
- **Détection automatique du client** : GPT-4o identifie à qui appartient chaque document
- **Classification automatique** : Le type de document est détecté (facture, devis, fiche de paie, etc.)
- **Filtres dynamiques** : Filtrer par client, par type, ou les deux
- **Export Excel organisé** :
  - 📊 Feuille "Index général" (tous les documents)
  - 📁 Une feuille par combinaison **Client × Type** (ex: "SFR - Factures")
  - 📋 Lignes détaillées séparées pour chaque catégorie
- **Export individuel** : Chaque document peut aussi être téléchargé seul
- **Interface pro** : Design épuré, prêt pour démo client

## 📦 Déploiement sur Streamlit Cloud (GRATUIT)

### Étape 1 : Crée un repo GitHub

1. Va sur [github.com](https://github.com) → **New repository** (ex: `docscan-pro`)
2. Upload cette structure :
   ```
   docscan-pro/
   ├── app.py
   ├── requirements.txt
   └── .streamlit/
       └── config.toml
   ```

### Étape 2 : Configure ta clé API (optionnel mais recommandé)

Pour ne pas avoir à la saisir à chaque fois :
1. Sur Streamlit Cloud, va dans **Settings > Secrets**
2. Ajoute :
   ```toml
   OPENAI_API_KEY = "sk-ta-clé-ici"
   ```
3. Ça y est, la clé est chargée automatiquement !

### Étape 3 : Déploie

1. Va sur [share.streamlit.io](https://share.streamlit.io)
2. Connecte ton GitHub → Sélectionne le repo
3. **Main file** : `app.py` → **Deploy**
4. En 2-3 min, t'as ton URL publique !

## 💰 Coûts

| Composant | Coût |
|-----------|------|
| Streamlit Cloud | **Gratuit** |
| GPT-4o Vision | ~0.01-0.03€/document |
| 100 docs/mois | ~1-3€ |

## 🔒 Sécurité

- Clé API : saisie utilisateur ou Streamlit Secrets (jamais dans le code)
- Aucune donnée stockée côté serveur
- Documents envoyés directement à l'API OpenAI

## 🛠️ Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

*Fait avec ❤️ à La Réunion 🇷🇪*
