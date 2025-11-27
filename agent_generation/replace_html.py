from jinja2 import Template
import os
import glob
import random
import json

def read_file(file_path):
    """Lit le contenu d'un fichier."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def _format_invoice_number(template_name, invoice_data, invoice_id):
    """Prefixe le numéro de facture par le nom de l'entreprise."""
    base_number = invoice_data.get("invoice_number") or invoice_id
    serial = base_number.split("-")[-1] if "-" in base_number else base_number
    serial = serial.strip()
    if not serial:
        serial = invoice_id.replace("invoice_", "") or "001"

    seller_name = (invoice_data.get("seller") or {}).get("name", "").strip()
    if template_name == "facture00.html":
        prefix = seller_name or "Altevia Solutions"
    else:
        prefix = seller_name or "Fournisseur"

    safe_prefix = "-".join(prefix.split()) or "FACTURE"
    formatted = f"{safe_prefix}-{serial}"
    invoice_data["invoice_number"] = formatted
    return formatted


def normalize_invoice_numbers(invoices_json, template_name):
    """
    Applique le formatage des numéros de facture pour l'ensemble des données.
    """
    if not template_name:
        return invoices_json

    for invoice_id, data in invoices_json.items():
        _format_invoice_number(template_name, data, invoice_id)

    return invoices_json


def populate_invoice(template_path, invoice_data, export_path):
    """
    Remplit un template HTML avec les données de la facture.
    
    Args:
        template_path: Chemin vers le template HTML
        invoice_data: Dictionnaire contenant les données de la facture
        export_path: Chemin où sauvegarder la facture remplie
    """
    # Lire le template
    template_content = read_file(template_path)
    
    # Créer le template Jinja2
    template = Template(template_content)
    
    # Rendre le template avec les données
    rendered_html = template.render(**invoice_data)
    
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(os.path.dirname(export_path) if os.path.dirname(export_path) else ".", exist_ok=True)
    
    # Écrire le fichier rempli
    with open(export_path, "w", encoding="utf-8") as file:
        file.write(rendered_html)
    
    print(f"Facture générée : {export_path}")


def process_all_invoices(invoices_json, template_name=None):
    """
    Prend un dictionnaire JSON de factures et remplit les templates HTML.
    
    Args:
        invoices_json: Dictionnaire contenant les factures (ex: {"invoice_1": {...}, "invoice_2": {...}})
        template_name: Nom du template à utiliser (ex: "facture1.html", "facture00.html"). 
                      Si None, utilise un template aléatoire pour chaque facture.
    """
    templates_dir = "data/html_template"
    
    # Si un template spécifique est demandé
    if template_name:
        template_path = os.path.join(templates_dir, template_name)
        if not os.path.exists(template_path):
            print(f"Template introuvable : {template_path}")
            return
        template_files = [template_path]
    else:
        # Récupérer tous les templates HTML disponibles
        template_files = glob.glob(os.path.join(templates_dir, "facture*.html"))
        if not template_files:
            print(f"Aucun template trouvé dans {templates_dir}")
            return
    
    # Créer le répertoire de sortie
    output_dir = "data/generated_invoices"
    os.makedirs(output_dir, exist_ok=True)
    
    # Pour chaque facture, créer un HTML rempli
    for invoice_id, invoice_data in invoices_json.items():
        # Utiliser le template spécifié ou un template aléatoire
        if template_name:
            template_path = template_files[0]
        else:
            template_path = random.choice(template_files)
        
        # Générer le nom du fichier de sortie
        current_template = os.path.basename(template_path)
        invoice_number = _format_invoice_number(current_template, invoice_data, invoice_id)
        output_filename = f"facture_{invoice_number.replace('/', '_')}.html"
        output_path = os.path.join(output_dir, output_filename)
        
        # Remplir le template
        populate_invoice(template_path, invoice_data, output_path)


if __name__ == "__main__":
    # Exemple d'utilisation si exécuté directement
    # En production, utilisez process_all_invoices(invoices_json) depuis main.py
    try:
        # Exemple avec des données de test
        test_invoices = {
            "invoice_1": {
                "invoice_number": "F2025-001",
                "date": "2025-11-20",
                "seller": {
                    "name": "Fournisseur Test",
                    "address": "123 Rue Test, 75000 Paris",
                    "email": "test@fournisseur.com"
                },
                "buyer": {
                    "name": "Altevia Solutions",
                    "address": "12 Rue des Entrepreneurs, 75015 Paris"
                },
                "items": [
                    {"description": "Produit A", "quantity": 2, "unit_price": 50}
                ],
                "total_ht": 100,
                "tva": 20,
                "total_ttc": 120
            }
        }
        process_all_invoices(test_invoices)
        print("\nToutes les factures ont été générées avec succès !")
    except Exception as e:
        print(f"Erreur lors de la génération : {e}")
        import traceback
        traceback.print_exc()
