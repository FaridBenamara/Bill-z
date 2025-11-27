from groq import Groq
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
import os
import json
load_dotenv()

def read_file(file_path):
    with open(file_path, "r") as file:
        return file.read()

# Vérifier si GROQ_KEY existe
groq_key = os.getenv("GROQ_KEY")
if not groq_key:
    raise ValueError(
        "GROQ_KEY n'est pas définie. Veuillez créer un fichier .env dans ce répertoire avec: GROQ_KEY=votre_cle_api"
    )

client = Groq(api_key=groq_key)

ALTEVIA_SIRET = "123 456 789 00012"
ALTEVIA_VAT = "FR12 345678900"
DUE_DATE_OFFSET_DAYS = 30


def _compute_due_date(invoice_date):
    if not invoice_date:
        return ""
    try:
        parsed = datetime.strptime(invoice_date, "%Y-%m-%d")
        return (parsed + timedelta(days=DUE_DATE_OFFSET_DAYS)).strftime("%Y-%m-%d")
    except ValueError:
        return ""


def _ensure_invoice_fields(invoices_json, is_seller_mode):
    """
    Injecte les champs obligatoires lorsque le modèle ne les fournit pas
    et force les valeurs fixes d'Altevia.
    """
    for invoice in invoices_json.values():
        buyer = invoice.get("buyer", {})
        seller = invoice.get("seller", {})

        # Supplier info
        if is_seller_mode:
            invoice.setdefault("supplier_siret", ALTEVIA_SIRET)
            invoice.setdefault("supplier_vat", ALTEVIA_VAT)
        else:
            invoice.setdefault("supplier_siret", seller.get("siret", ""))
            invoice.setdefault("supplier_vat", seller.get("vat", ""))

        # Client info (Altevia côté achats)
        if buyer.get("name") == "Altevia Solutions":
            invoice["client_siret"] = ALTEVIA_SIRET
            invoice["client_vat"] = ALTEVIA_VAT
        else:
            invoice.setdefault("client_siret", buyer.get("siret", ""))
            invoice.setdefault("client_vat", buyer.get("vat", ""))

        # Due date
        invoice.setdefault("due_date", _compute_due_date(invoice.get("date")))

def _apply_template_rules(invoices_json, template_rules):
    if not template_rules:
        return invoices_json

    seller_info = template_rules.get("seller", {})
    supplier_siret = template_rules.get("supplier_siret")
    supplier_vat = template_rules.get("supplier_vat")

    for invoice in invoices_json.values():
        seller = invoice.setdefault("seller", {})
        seller.update({k: v for k, v in seller_info.items() if v})

        if supplier_siret:
            invoice["supplier_siret"] = supplier_siret
        if supplier_vat:
            invoice["supplier_vat"] = supplier_vat

    return invoices_json


def generate_invoice_mail(is_seller_mode=False, template_rules=None, template_name=None):
    """
    Génère des factures via l'API Groq.
    
    Args:
        is_seller_mode: Si True, nous sommes le seller (facture00.html). 
                       Si False, nous sommes le buyer (facture1-5.html).
    """
    # Choisir le contexte et le prompt selon le mode
    context_file = "context_seller.txt" if is_seller_mode else "context.txt"
    prompt_file = "prompt_seller.txt" if is_seller_mode else "prompt.txt"
    
    # Vérifier si les fichiers existent
    if not os.path.exists(context_file):
        print(f"Attention: {context_file} introuvable, utilisation de context.txt")
        context_file = "context.txt"
    if not os.path.exists(prompt_file):
        print(f"Attention: {prompt_file} introuvable, utilisation de prompt.txt")
        prompt_file = "prompt.txt"
    
    prompt_text = read_file(file_path=prompt_file)
    if template_rules:
        suffix = template_rules.get("prompt_suffix")
        domain = template_rules.get("domain")
        seller = template_rules.get("seller", {})
        if suffix or seller:
            extra = "\n\nRÈGLES SPÉCIFIQUES À CE TEMPLATE :\n"
            if domain:
                extra += f"- Domaine ciblé : {domain}. Tous les items doivent refléter ce domaine.\n"
            if seller:
                extra += (
                    "- Fournisseur fixe : "
                    f"{seller.get('name')} ({seller.get('address')}, {seller.get('email')}). "
                    "Toutes les factures doivent conserver exactement cette identité fournisseur.\n"
                )
            if template_name:
                extra += f"- Template utilisé : {template_name}.\n"
            if suffix:
                extra += f"- Consigne détaillée : {suffix}\n"
            prompt_text += extra

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": read_file(file_path=context_file)
            },
            {
                "role": "user",
                "content": prompt_text
            }
        ],
        temperature=0.5,
        response_format={"type": "json_object"},
        model="llama-3.3-70b-versatile" if random.randint(0, 1) else "openai/gpt-oss-20b"
    )
    result = json.loads(response.choices[0].message.content)
    _ensure_invoice_fields(result, is_seller_mode)
    result = _apply_template_rules(result, template_rules)

    return result


if __name__ == "__main__":
    ticket_response = generate_invoice_mail()
    for id_invoice, invoice in ticket_response.items():
        print(id_invoice)
        print(invoice)
        print("_"*20)

