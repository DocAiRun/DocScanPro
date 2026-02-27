"""
Module de classification et détection de doublons — DocScan Pro.

Fournit des outils pour calculer l'empreinte unique d'un document
et détecter les doublons dans l'historique de session.
"""

import hashlib


def calculer_fingerprint(data: dict) -> str:
    """Calcule une empreinte unique (fingerprint) pour un document extrait.

    Basée sur la concaténation normalisée de :
    - Nom de l'émetteur
    - Numéro de document
    - Total TTC
    - Date d'émission

    Si tous ces champs sont vides, retourne "" (pas de détection possible).

    Args:
        data: Dictionnaire JSON retourné par GPT-4o Vision.

    Returns:
        Chaîne hexadécimale de 8 caractères (SHA-256 tronqué), ou "".
    """
    emetteur_nom = data.get("emetteur", {}).get("nom", "").strip().lower()
    doc_numero = data.get("document", {}).get("numero", "").strip()
    total_ttc = data.get("totaux", {}).get("total_ttc", "").strip()
    date_emission = data.get("document", {}).get("date_emission", "").strip()

    # Pas assez d'informations pour une empreinte fiable
    if not any([emetteur_nom, doc_numero, total_ttc]):
        return ""

    chaine = f"{emetteur_nom}|{doc_numero}|{total_ttc}|{date_emission}"
    return hashlib.sha256(chaine.encode("utf-8")).hexdigest()[:8]


def detecter_doublon(data: dict, history: list[dict]) -> dict | None:
    """Détecte si un document est déjà présent dans l'historique de session.

    Deux niveaux de détection :
    - **Exact** : même empreinte SHA-256 (même émetteur + numéro + montant + date)
    - **Probable** : même client + même type + même total TTC (sans numéro de doc)

    Args:
        data: Dictionnaire JSON du nouveau document (retourné par GPT-4o Vision).
        history: Liste des documents déjà traités (st.session_state.history).

    Returns:
        Dictionnaire du document en doublon avec une clé "match" ("exact" ou "probable"),
        ou None si aucun doublon détecté.
    """
    if not history:
        return None

    fingerprint = calculer_fingerprint(data)

    # 1. Match exact par fingerprint
    if fingerprint:
        for doc in history:
            if doc.get("fingerprint") == fingerprint:
                return {**doc, "match": "exact"}

    # 2. Match probable : même client + même type + même total TTC non vide
    client_nouveau = (data.get("client_detecte") or "").strip().lower()
    type_nouveau = data.get("type_document", "")
    ttc_nouveau = (data.get("totaux", {}).get("total_ttc") or "").strip()

    if client_nouveau and type_nouveau and ttc_nouveau:
        for doc in history:
            client_hist = doc.get("client", "").strip().lower()
            type_hist = doc.get("type", "")
            ttc_hist = (doc.get("flat", {}).get("Total TTC") or "").strip()

            if (
                client_hist == client_nouveau
                and type_hist == type_nouveau
                and ttc_hist == ttc_nouveau
            ):
                return {**doc, "match": "probable"}

    return None
