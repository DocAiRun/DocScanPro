# CLAUDE.md — DocScan Pro

> Instructions pour Claude Code. Ce fichier décrit le projet, le stack existant, l'architecture cible et la roadmap de développement.

---

## 📌 Contexte du projet

**DocScan Pro** est un service d'extraction documentaire IA destiné au marché réunionnais (La Réunion, 974, France).
Il permet aux entreprises locales (BTP, commerces, artisans, cabinets comptables) de numériser, extraire et classer automatiquement leurs documents (factures, devis, bons de commande, fiches de paie, notes de frais).

**Repo GitHub** : https://github.com/DocAiRun/DocScanPro

**Double modèle économique** :
1. **SaaS self-service** — le client uploade ses documents et récupère ses données via l'interface web (abonnement Stripe)
2. **Service managé** — le fondateur utilise DocScan Pro pour numériser et classer des documents pour le compte d'entreprises locales (prestation facturée à la mission ou au volume)

---

## 🏗️ Stack actuel (v2.0)

| Composant | Technologie |
|-----------|-------------|
| Frontend / Interface | **Streamlit** (Python) |
| IA / Extraction | **GPT-4o Vision** (API OpenAI) |
| Base de données | **Supabase** (PostgreSQL) |
| Export | **openpyxl** (Excel .xlsx) |
| Déploiement | **Streamlit Cloud** (gratuit) |
| Langage | **Python 3.11+** |

### Structure actuelle du repo

```
DocScanPro/
├── .streamlit/
│   └── config.toml
├── pages/
│   ├── upload.py           # Upload + extraction (GPT-4o Vision)
│   └── dashboard.py        # Filtres + export Excel
├── modules/
│   ├── extraction.py       # Logique GPT-4o Vision (prompt + parsing)
│   └── export.py           # Export Excel organisé
├── utils/
│   ├── config.py           # CSS, TYPE_CONFIG, SYSTEM_PROMPT
│   └── helpers.py          # get_api_key()
├── app.py                  # Point d'entrée (navigation + sidebar)
├── requirements.txt
├── packages.txt
├── .gitignore
├── CLAUDE.md               # Ce fichier
└── README.md
```

### Fonctionnalités existantes (v2.0)
- Upload multi-documents (factures, devis, bons de commande, fiches de paie, notes de frais)
- Détection automatique du client via GPT-4o Vision
- Classification automatique par type de document
- Filtres dynamiques (par client, par type)
- Export Excel organisé : feuille "Index général" + une feuille par combinaison Client × Type
- Export individuel par document
- Clé API saisie par l'utilisateur ou via Streamlit Secrets

---

## 🎯 Roadmap — Features à implémenter (par ordre de priorité)

### Phase 1 : Refactorisation modulaire ✅ TERMINÉ

`app.py` monolithique (669 lignes) refactorisé en structure `modules/` + `pages/` + `utils/`.
Navigation multi-pages via `st.navigation()` (Streamlit >= 1.36.0).

---

### Phase 2 : Classement automatique avancé ⭐ PRIORITÉ HAUTE

**Objectif** : Améliorer significativement le classement et l'organisation des documents extraits.

**Spécifications** :
- Catégorisation automatique des documents par type (facture, devis, bon de commande, fiche de paie, note de frais, avoir, relance, contrat, etc.)
- Classement par fournisseur/client détecté
- Classement chronologique automatique
- Détection des doublons (même document uploadé plusieurs fois)
- Tags et métadonnées enrichis : montant total, TVA, date d'émission, date d'échéance, numéro de document, SIRET/SIREN
- Arborescence de classement automatique : `/{Client}/{Année}/{Type}/{document}`
- Recherche full-text sur les documents traités

**Stockage** : Utiliser Supabase pour persister les métadonnées et l'arborescence. Les documents originaux peuvent être stockés dans Supabase Storage.

**Points d'attention** :
- Le prompt GPT-4o Vision doit être enrichi pour extraire tous les champs de métadonnées nécessaires en un seul appel
- Prévoir un mécanisme de correction manuelle si le classement automatique se trompe
- L'arborescence doit être compatible avec l'export (ZIP organisé)

---

### Phase 3 : Tableau de bord client ⭐ PRIORITÉ HAUTE

**Objectif** : Offrir à chaque client un espace personnel avec visibilité sur ses documents et ses statistiques.

**Spécifications** :
- **Authentification** : Supabase Auth (email/password, possibilité d'ajouter OAuth plus tard)
- **Dashboard principal** :
  - Nombre total de documents traités
  - Répartition par type (graphique camembert/barres)
  - Montant total des factures (émises vs reçues)
  - TVA récupérable estimée
  - Timeline des uploads
- **Historique des documents** : Liste paginée avec filtres (date, type, client, montant)
- **Espace de stockage** : Visualisation de l'arborescence de classement
- **Multi-utilisateurs** : Un compte entreprise peut avoir plusieurs utilisateurs avec des rôles (admin, viewer)
- **Notifications** : Alerte si un document semble en doublon ou si une facture approche de l'échéance

**UI** : Rester sur Streamlit pour la cohérence, mais structurer le code avec `st.navigation` / multi-pages Streamlit.

**Points d'attention** :
- Chaque client ne voit que SES documents (Row Level Security Supabase)
- Le dashboard doit être rapide même avec des centaines de documents
- Prévoir des vues agrégées par mois/trimestre/année

---

### Phase 4 : Numérisation scan (OpenCV)

**Objectif** : Transformer une photo de document (prise au smartphone, de travers, mal éclairée) en un PDF propre et exploitable, en plus de l'extraction des données.

**Spécifications** :
- **Détection automatique des contours** du document dans l'image (OpenCV : `findContours`, `approxPolyDP`)
- **Redressement perspectif** (transformation homographique 4 points)
- **Amélioration de l'image** : binarisation adaptative, correction de contraste/luminosité, suppression du bruit
- **Génération d'un PDF propre** : rendu "scanner" en noir et blanc ou couleur optimisée
- **Double livrable** : le client reçoit (1) le PDF numérisé propre + (2) les données structurées extraites

**Librairies** :
- `opencv-python-headless` (pour Streamlit Cloud, pas de GUI)
- `numpy` pour les transformations matricielles
- `Pillow` ou `img2pdf` pour la génération PDF

**Pipeline** :
```
Image brute → Détection contours → Redressement → Nettoyage → PDF propre → GPT-4o Vision → Données structurées
```

**Points d'attention** :
- Utiliser `opencv-python-headless` (pas `opencv-python`) pour compatibilité Streamlit Cloud
- Ajouter `libgl1-mesa-glx` et `libglib2.0-0` dans `packages.txt` si nécessaire
- Prévoir un mode "manuel" où l'utilisateur peut ajuster les 4 coins si la détection automatique échoue
- Le redressement doit fonctionner sur des photos prises dans des conditions variées (lumière faible, angle prononcé, fond non uni)

---

### Phase 5 : Intégration Stripe (Paiement)

**Objectif** : Monétiser le service via des abonnements et/ou du paiement à l'usage.

**Spécifications** :
- **Plans d'abonnement** :
  - **Starter** : 9.90€/mois — 50 documents/mois
  - **Pro** : 24.90€/mois — 200 documents/mois
  - **Business** : 49.90€/mois — documents illimités + export comptable + multi-utilisateurs
  - **Pay-as-you-go** : 0.30€/document (sans abonnement)
- **Intégration Stripe** :
  - Stripe Checkout pour l'abonnement
  - Stripe Billing pour la gestion des plans et la facturation récurrente
  - Webhook Stripe → Supabase pour mettre à jour le statut d'abonnement en temps réel
  - Stripe Customer Portal pour que le client gère lui-même son abonnement
- **Gating** : vérifier les quotas avant chaque extraction (nombre de docs restants dans le plan)
- **Page pricing** intégrée à l'app Streamlit

**Librairies** : `stripe` (SDK Python)

**Points d'attention** :
- Utiliser Stripe en mode Test d'abord, basculer en Live une fois validé
- Les webhooks Stripe doivent être sécurisés (vérification de signature)
- Stocker le `stripe_customer_id` et `subscription_status` dans la table `users` Supabase
- Prévoir une période d'essai gratuite (ex : 10 documents gratuits)
- Les prix incluent la TVA (marché français)

---

## 🏛️ Architecture cible

```
DocScanPro/
├── .streamlit/
│   └── config.toml
├── pages/                      # Multi-pages Streamlit
│   ├── upload.py               # Upload + extraction + numérisation
│   ├── dashboard.py            # Tableau de bord client
│   ├── documents.py            # Historique + arborescence + recherche
│   ├── abonnement.py           # Plans Stripe + gestion abonnement
│   └── parametres.py           # Profil, clé API, préférences
├── modules/
│   ├── auth.py                 # Authentification Supabase
│   ├── extraction.py           # Logique GPT-4o Vision (prompt + parsing)
│   ├── classification.py       # Classement automatique + métadonnées
│   ├── scanner.py              # Numérisation OpenCV (redressement + nettoyage)
│   ├── storage.py              # Supabase Storage + arborescence
│   ├── export.py               # Export Excel + ZIP organisé
│   ├── stripe_billing.py       # Intégration Stripe (checkout, webhooks, quotas)
│   └── dashboard_stats.py      # Calculs stats pour le dashboard
├── utils/
│   ├── config.py               # CSS, TYPE_CONFIG, SYSTEM_PROMPT
│   ├── helpers.py              # get_api_key(), fonctions utilitaires
│   ├── supabase_client.py      # Client Supabase singleton
│   └── constants.py            # Constantes métier (TVA, devises, etc.)
├── app.py                      # Point d'entrée principal (navigation)
├── requirements.txt
├── packages.txt
├── .gitignore
├── CLAUDE.md                   # Ce fichier
└── README.md
```

---

## 🔧 Conventions de développement

### Style de code
- **Python 3.11+**
- **Type hints** sur toutes les fonctions
- **Docstrings** en français (Google style)
- Pas de variables globales, utiliser `st.session_state` pour l'état Streamlit
- Noms de variables et commentaires en **français** quand c'est du métier, en anglais pour le technique

### Gestion des erreurs
- Toujours encapsuler les appels API (OpenAI, Supabase, Stripe) dans des try/except
- Afficher des messages d'erreur user-friendly via `st.error()` / `st.warning()`
- Logger les erreurs techniques (print ou logging)

### Sécurité
- Jamais de clés API en dur dans le code
- Utiliser `st.secrets` ou variables d'environnement
- Row Level Security (RLS) activé sur toutes les tables Supabase
- Vérification de signature sur les webhooks Stripe

### Base de données Supabase — Schéma cible

```sql
-- Table utilisateurs
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    company_name TEXT,
    stripe_customer_id TEXT,
    subscription_plan TEXT DEFAULT 'free',
    subscription_status TEXT DEFAULT 'inactive',
    docs_used_this_month INTEGER DEFAULT 0,
    docs_limit INTEGER DEFAULT 10,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    original_filename TEXT,
    storage_path TEXT,
    pdf_clean_path TEXT,
    doc_type TEXT,           -- facture, devis, bon_commande, fiche_paie, note_frais, avoir, contrat
    client_name TEXT,        -- client/fournisseur détecté
    doc_number TEXT,         -- numéro du document
    doc_date DATE,
    due_date DATE,
    amount_ht DECIMAL,
    amount_ttc DECIMAL,
    tva_amount DECIMAL,
    tva_rate DECIMAL,
    siret TEXT,
    currency TEXT DEFAULT 'EUR',
    raw_extraction JSONB,    -- réponse brute GPT-4o Vision
    is_duplicate BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour la recherche et les filtres
CREATE INDEX idx_documents_user ON documents(user_id);
CREATE INDEX idx_documents_type ON documents(doc_type);
CREATE INDEX idx_documents_client ON documents(client_name);
CREATE INDEX idx_documents_date ON documents(doc_date);

-- RLS : chaque utilisateur ne voit que ses documents
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own documents" ON documents
    FOR ALL USING (auth.uid() = user_id);
```

---

## 🚨 Règles impératives

1. **Ne jamais casser les fonctionnalités existantes** — tester que l'upload + extraction + export Excel fonctionnent toujours après chaque modification
2. **Modulariser** — ne pas tout mettre dans `app.py`. Refactorer vers la structure `modules/` et `pages/`
3. **Déploiement Streamlit Cloud** — toujours vérifier la compatibilité (pas de packages système exotiques, pas de GUI)
4. **Coûts API maîtrisés** — un seul appel GPT-4o Vision par document (prompt enrichi pour tout extraire d'un coup)
5. **UX pro** — l'interface doit être clean, intuitive, prête pour une démo client. Utiliser les composants Streamlit natifs (st.metric, st.dataframe, st.tabs, etc.)
6. **Marché français** — montants en EUR, dates au format JJ/MM/AAAA, TVA française (20%, 10%, 5.5%, 2.1%)

---

## 📋 Checklist avant chaque PR

- [ ] `streamlit run app.py` fonctionne sans erreur
- [ ] Les features existantes ne sont pas cassées (upload, extraction, export)
- [ ] Pas de clés API en dur
- [ ] Type hints sur les nouvelles fonctions
- [ ] Messages d'erreur user-friendly
- [ ] Compatible Streamlit Cloud (pas de dépendances GUI)
- [ ] `requirements.txt` mis à jour si nouvelles dépendances
- [ ] `packages.txt` mis à jour si nouvelles dépendances système

---

## 💡 Notes pour Claude Code

- Le fondateur (Johan) utilise un style de développement "vibe coding" — il préfère des itérations rapides avec des résultats visibles plutôt que de longues phases de planification
- Privilégier des PRs/commits atomiques par feature plutôt qu'un gros refactoring monolithique
- En cas de doute sur un choix technique, proposer la solution la plus simple qui fonctionne sur Streamlit Cloud
- Le marché cible est La Réunion (974) — les exemples de données et l'UI doivent refléter ce contexte (entreprises locales, numéros SIRET, adresses réunionnaises)
- La facturation électronique obligatoire en France est un argument de vente majeur — garder ça en tête dans les features d'export
