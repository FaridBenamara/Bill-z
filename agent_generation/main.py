from invoice_agent import generate_invoice_mail
from replace_html import process_all_invoices, normalize_invoice_numbers
from html_to_pdf import convert_all_html_to_pdf
import json
import os

# ============================================
# CONFIGURATION - Changez cette ligne pour chaque exécution
# ============================================
# Options disponibles :
# - "facture00.html" : Nous sommes le seller (ventes)
# - "facture1.html" : Nous sommes le buyer (achats)
# - "facture2.html" : Nous sommes le buyer (achats)
# - "facture3.html" : Nous sommes le buyer (achats)
# - "facture4.html" : Nous sommes le buyer (achats)
# - "facture5.html" : Nous sommes le buyer (achats)
TEMPLATE_NAME = "facture5.html"  # <-- CHANGEZ ICI AVANT CHAQUE EXÉCUTION
# ============================================


TEMPLATE_RULES = {
    "facture1.html": {
        "domain": "services cloud & SaaS",
        "seller": {
            "name": "NebulaOps Solutions",
            "address": "4 Avenue de la République, 75011 Paris, France",
            "email": "contact@nebulaops.fr",
        },
        "supplier_siret": "732 829 320 00047",
        "supplier_vat": "FR39 732829320",
        "prompt_suffix": (
            "Les 5 factures concernent un fournisseur cloud/SaaS nommé NebulaOps Solutions. "
            "Décris des abonnements logiciels, hébergement cloud, supervision et services DevOps."
        ),
    },
    "facture2.html": {
        "domain": "ingénierie industrielle",
        "seller": {
            "name": "HexaFactory Industries",
            "address": "91 Rue de Gerland, 69007 Lyon, France",
            "email": "facturation@hexafactory.fr",
        },
        "supplier_siret": "512 907 654 00021",
        "supplier_vat": "FR66 512907654",
        "prompt_suffix": (
            "Les 5 factures concernent HexaFactory Industries, un équipementier industriel. "
            "Facture des pièces mécaniques, maintenance d'ateliers, capteurs IoT industriels, robots, etc."
        ),
    },
    "facture3.html": {
        "domain": "marketing digital",
        "seller": {
            "name": "Pixelia Marketing",
            "address": "27 Boulevard Vauban, 59800 Lille, France",
            "email": "billing@pixelia.marketing",
        },
        "supplier_siret": "418 204 998 00015",
        "supplier_vat": "FR08 418204998",
        "prompt_suffix": (
            "Les 5 factures proviennent de Pixelia Marketing pour des campagnes publicitaires, "
            "SEO, production de contenu et analytics marketing."
        ),
    },
    "facture4.html": {
        "domain": "infrastructures & énergie",
        "seller": {
            "name": "Energrid Facilities",
            "address": "12 Quai Gustave Flaubert, 76000 Rouen, France",
            "email": "gestion@energrid.fr",
        },
        "supplier_siret": "602 118 450 00033",
        "supplier_vat": "FR71 602118450",
        "prompt_suffix": (
            "Les 5 factures sont émises par Energrid Facilities pour des travaux électriques, "
            "maintenance d'installations énergétiques et gestion de bâtiments."
        ),
    },
    "facture5.html": {
        "domain": "cybersécurité & réseaux",
        "seller": {
            "name": "SentinelSec Defense",
            "address": "18 Rue de Tivoli, 31000 Toulouse, France",
            "email": "finance@sentinelsec.fr",
        },
        "supplier_siret": "903 552 187 00018",
        "supplier_vat": "FR48 903552187",
        "prompt_suffix": (
            "Les 5 factures émanent de SentinelSec Defense et couvrent audits de sécurité, "
            "SOC-as-a-Service, firewalls et services réseau critiques."
        ),
    },
}
# ============================================

def generate_invoices_for_template(template_name):
    """
    Génère 50 factures pour un template spécifique.
    
    Args:
        template_name: Nom du template à utiliser (ex: "facture1.html", "facture00.html")
    """
    print(f"\n{'='*60}")
    print(f"Génération des factures pour le template : {template_name}")
    print(f"{'='*60}\n")
    
    # Déterminer si nous sommes en mode seller (uniquement facture00.html)
    is_seller_mode = (template_name == "facture00.html")
    template_rules = TEMPLATE_RULES.get(template_name)
    if not is_seller_mode and not template_rules:
        raise ValueError(f"Aucune règle spécifique définie pour {template_name}.")
    
    try:
        # 1. Générer les factures via l'API
        print("Étape 1/4 : Génération des factures via l'API Groq...")
        invoices_json = generate_invoice_mail(
            is_seller_mode=is_seller_mode,
            template_rules=template_rules,
            template_name=template_name,
        )
        invoices_json = normalize_invoice_numbers(invoices_json, template_name)
        print(f"✓ {len(invoices_json)} factures générées\n")
        
        # Sauvegarder le JSON pour l'ajout au CSV
        json_output_dir = "data/generated_invoices_json"
        os.makedirs(json_output_dir, exist_ok=True)
        json_filename = f"invoices_{template_name.replace('.html', '')}.json"
        json_path = os.path.join(json_output_dir, json_filename)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(invoices_json, f, indent=2, ensure_ascii=False)
        print(f"✓ JSON sauvegardé : {json_path}\n")
        
        # 2. Remplir les templates HTML
        print("Étape 2/4 : Remplissage des templates HTML...")
        process_all_invoices(invoices_json, template_name=template_name)
        print("✓ Templates HTML remplis\n")
        
        # 3. Convertir en PDF
        print("Étape 3/5 : Conversion HTML vers PDF...")
        convert_all_html_to_pdf()
        print("✓ PDFs générés\n")
        
        # 4. Envoyer les factures par email
        print("Étape 4/5 : Envoi des factures par email...")
        try:
            from mail_management import send_invoice_email, DEFAULT_RECIPIENT
            import glob
            
            pdf_dir = "data/generated_invoices_pdf"
            
            # Créer un mapping invoice_number -> pdf_path
            pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
            pdf_map = {}
            for pdf_path in pdf_files:
                # Extraire le numéro de facture du nom de fichier
                # Format: facture_F2017-001.pdf -> F2017-001
                filename = os.path.basename(pdf_path)
                if filename.startswith("facture_") and filename.endswith(".pdf"):
                    invoice_num = filename.replace("facture_", "").replace(".pdf", "")
                    pdf_map[invoice_num] = pdf_path
            
            sent_count = 0
            for invoice_id, invoice_data in invoices_json.items():
                invoice_number = invoice_data.get("invoice_number", "")
                pdf_path = pdf_map.get(invoice_number)
                
                if not pdf_path:
                    print(f"  ⚠ PDF introuvable pour {invoice_number}")
                    continue
                
                # Destinataire par défaut (configuré dans mail_management.DEFAULT_RECIPIENT)
                recipient_email = DEFAULT_RECIPIENT
                
                try:
                    send_invoice_email(invoice_data, pdf_path, is_seller_mode, recipient_email)
                    sent_count += 1
                except Exception as e:
                    print(f"  ⚠ Erreur envoi {invoice_number}: {e}")
            
            print(f"✓ {sent_count}/{len(invoices_json)} emails envoyés\n")
        except Exception as e:
            print(f"⚠ Erreur lors de l'envoi des emails : {e}\n")
            print("  Les factures ont été générées, mais l'envoi d'emails a échoué.\n")
        
        # 5. Ajouter au CSV (optionnel, peut être fait séparément)
        print("Étape 5/5 : Ajout au relevé bancaire...")
        try:
            from add_to_csv import add_invoices_to_csv
            add_invoices_to_csv(json_path, template_name, is_seller_mode)
            print("✓ Transactions ajoutées au CSV\n")
        except PermissionError:
            print("⚠ Le fichier Excel est ouvert. Fermez-le et relancez le script ou utilisez add_to_csv.py séparément.\n")
            print("  Les factures ont été générées avec succès, seul l'ajout au CSV a échoué.\n")
        
        print(f"{'='*60}")
        print(f"✓ Traitement terminé pour {template_name} !")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Erreur lors du traitement de {template_name} : {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Générer les factures pour le template spécifié
    generate_invoices_for_template(TEMPLATE_NAME)
    
    print("\n" + "="*60)
    print("Pour générer pour un autre template, modifiez TEMPLATE_NAME dans main.py")
    print("="*60)
