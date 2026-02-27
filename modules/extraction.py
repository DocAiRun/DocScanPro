"""
Module d'extraction documentaire via GPT-4o Vision.

Gère l'encodage des fichiers, l'appel API OpenAI et le parsing des résultats.
"""

import base64
import io
import json

import openai
import pandas as pd
from pdf2image import convert_from_bytes

from utils.config import SYSTEM_PROMPT


def encode_image(uploaded_file) -> str:
    """Encode un fichier image en base64.

    Args:
        uploaded_file: Fichier uploadé via st.file_uploader.

    Returns:
        Chaîne base64 de l'image.
    """
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")


def pdf_to_image_b64(uploaded_file) -> str:
    """Convertit la première page d'un PDF en image base64 (PNG, 200 DPI).

    Args:
        uploaded_file: Fichier PDF uploadé via st.file_uploader.

    Returns:
        Chaîne base64 de la première page en PNG.
    """
    images = convert_from_bytes(
        uploaded_file.getvalue(), first_page=1, last_page=1, dpi=200
    )
    buf = io.BytesIO()
    images[0].save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def extract_data(image_base64: str, file_type: str, api_key: str) -> dict:
    """Envoie l'image à GPT-4o Vision et retourne les données extraites.

    Args:
        image_base64: Image encodée en base64.
        file_type: Extension du fichier (png, jpg, jpeg, webp).
        api_key: Clé API OpenAI.

    Returns:
        Dictionnaire JSON avec les données extraites du document.

    Raises:
        json.JSONDecodeError: Si la réponse GPT-4o n'est pas un JSON valide.
        openai.AuthenticationError: Si la clé API est invalide.
    """
    client = openai.OpenAI(api_key=api_key)

    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    }
    mime = mime_map.get(file_type.lower(), "image/png")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyse ce document. Identifie le client, le type, et extrais toutes les données en JSON.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{image_base64}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
        max_tokens=4096,
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()

    # Nettoyer les éventuels blocs markdown ```json ... ```
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    return json.loads(raw)


def flatten_data(data: dict) -> dict:
    """Aplatit la structure JSON imbriquée en un dictionnaire plat pour l'export.

    Args:
        data: Dictionnaire JSON retourné par GPT-4o Vision.

    Returns:
        Dictionnaire plat avec toutes les métadonnées du document.
    """
    flat: dict = {}

    flat["Client"] = data.get("client_detecte", "Non identifié")
    flat["Type"] = data.get("type_document", "autre")
    flat["Confiance"] = data.get("confiance_type", "")
    flat["Taux TVA principal (%)"] = data.get("taux_tva_principal", "")

    em = data.get("emetteur", {})
    flat["Émetteur"] = em.get("nom", "")
    flat["Émetteur Adresse"] = em.get("adresse", "")
    flat["Émetteur Tél"] = em.get("telephone", "")
    flat["Émetteur Email"] = em.get("email", "")
    flat["Émetteur SIRET"] = em.get("siret", "")
    flat["Émetteur TVA Intra"] = em.get("tva_intra", "")

    dest = data.get("destinataire", {})
    flat["Destinataire"] = dest.get("nom", "")
    flat["Destinataire Adresse"] = dest.get("adresse", "")
    flat["Destinataire SIRET"] = dest.get("siret", "")
    flat["Destinataire TVA Intra"] = dest.get("tva_intra", "")

    doc = data.get("document", {})
    flat["N° Document"] = doc.get("numero", "")
    flat["Date émission"] = doc.get("date_emission", "")
    flat["Date échéance"] = doc.get("date_echeance", "")
    flat["Référence"] = doc.get("reference", "")
    flat["Objet"] = doc.get("objet", "")

    # Année extraite de la date d'émission (format JJ/MM/AAAA → 4 derniers chars)
    date_em = doc.get("date_emission", "")
    flat["Année"] = date_em[-4:] if len(date_em) >= 4 and date_em[-4:].isdigit() else ""

    tot = data.get("totaux", {})
    flat["Total HT"] = tot.get("total_ht", "")
    flat["Total TVA"] = tot.get("total_tva", "")
    flat["Total TTC"] = tot.get("total_ttc", "")
    flat["Devise"] = tot.get("devise", "EUR")

    paie = data.get("paiement", {})
    flat["Mode paiement"] = paie.get("mode", "")
    flat["IBAN"] = paie.get("iban", "")
    flat["BIC"] = paie.get("bic", "")
    flat["Conditions paiement"] = paie.get("conditions", "")
    flat["Notes"] = data.get("notes", "")

    return flat


def lines_to_df(data: dict) -> pd.DataFrame | None:
    """Convertit les lignes de détail d'un document en DataFrame pandas.

    Args:
        data: Dictionnaire JSON retourné par GPT-4o Vision.

    Returns:
        DataFrame des lignes de détail, ou None si aucune ligne.
    """
    lignes = data.get("lignes", [])
    if not lignes:
        return None

    rows = []
    for ligne in lignes:
        rows.append(
            {
                "Description": ligne.get("description", ""),
                "Quantité": ligne.get("quantite", ""),
                "Prix unitaire HT": ligne.get("prix_unitaire_ht", ""),
                "Montant HT": ligne.get("montant_ht", ""),
                "TVA (%)": ligne.get("tva_pourcent", ""),
            }
        )
    return pd.DataFrame(rows)
