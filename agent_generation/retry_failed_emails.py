"""
Script pour relancer l'envoi des emails qui ont échoué.
Utilisation: python retry_failed_emails.py
"""
from mail_management import send_invoice_email, DEFAULT_EMAIL
import json
import os
import glob
import time

# Liste des factures qui ont échoué (d'après les logs)
FAILED_INVOICE_NUMBERS = [
    "F2025-030", "F2025-031", "F2025-032", "F2025-033", "F2025-034",
    "F2025-035", "F2025-036", "F2025-037", "F2025-038", "F2025-039",
    "F2025-040", "F2025-041", "F2025-042", "F2025-043", "F2025-044",
    "F2025-045", "F2025-046", "F2025-047", "F2025-048", "F2025-049",
    "F2025-050"
]

def retry_failed_emails():
    """
    Relance l'envoi des emails pour les factures qui ont échoué.
    """
    # Chemin du JSON (facture00.html = facture00)
    json_path = "data/generated_invoices_json/invoices_facture00.json"
    
    if not os.path.exists(json_path):
        print(f"⚠ Fichier JSON introuvable : {json_path}")
        return
    
    # Lire le JSON des factures
    print(f"📖 Lecture de {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        invoices_json = json.load(f)
    
    # Créer un mapping invoice_number -> invoice_data
    invoice_map = {invoice_data.get("invoice_number"): invoice_data 
                   for invoice_data in invoices_json.values()}
    
    # Créer un mapping invoice_number -> pdf_path
    pdf_dir = "data/generated_invoices_pdf"
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    pdf_map = {}
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        if filename.startswith("facture_") and filename.endswith(".pdf"):
            invoice_num = filename.replace("facture_", "").replace(".pdf", "")
            pdf_map[invoice_num] = pdf_path
    
    print(f"\n🔄 Relance de l'envoi pour {len(FAILED_INVOICE_NUMBERS)} facture(s)...\n")
    
    # Réessayer l'envoi
    success_count = 0
    failed_count = 0
    is_seller_mode = True  # facture00.html = seller mode
    
    for i, invoice_number in enumerate(FAILED_INVOICE_NUMBERS, 1):
        invoice_data = invoice_map.get(invoice_number)
        pdf_path = pdf_map.get(invoice_number)
        
        if not invoice_data:
            print(f"  ⚠ [{i}/{len(FAILED_INVOICE_NUMBERS)}] Facture {invoice_number} introuvable dans le JSON")
            failed_count += 1
            continue
        
        if not pdf_path:
            print(f"  ⚠ [{i}/{len(FAILED_INVOICE_NUMBERS)}] PDF introuvable pour {invoice_number}")
            failed_count += 1
            continue
        
        try:
            print(f"  📧 [{i}/{len(FAILED_INVOICE_NUMBERS)}] Envoi de {invoice_number}...", end=" ")
            send_invoice_email(invoice_data, pdf_path, is_seller_mode, DEFAULT_EMAIL)
            success_count += 1
            print("✓")
            
            # Pause de 3 secondes entre chaque email pour éviter le rate limit
            if i < len(FAILED_INVOICE_NUMBERS):
                time.sleep(3)
                
        except Exception as e:
            failed_count += 1
            error_msg = str(e)
            if "429" in error_msg or "rate limit" in error_msg.lower():
                print(f"⚠ Rate limit toujours actif")
                # Le mail_management.py gère déjà le rate limit avec retry automatique
                # Si on arrive ici, c'est que tous les retries ont échoué
                print(f"\n  → {success_count} email(s) envoyé(s) avec succès")
                print(f"  → Rate limit toujours actif après plusieurs tentatives")
                print(f"  → Relancez ce script dans 5-10 minutes pour continuer")
                break
            else:
                print(f"✗ Erreur: {e}")
    
    print(f"\n{'='*60}")
    print(f"✓ Résultat : {success_count}/{len(FAILED_INVOICE_NUMBERS)} emails envoyés")
    if failed_count > 0:
        print(f"⚠ {failed_count} email(s) toujours en échec")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("="*60)
    print("Relance de l'envoi des emails non envoyés")
    print("="*60)
    print(f"\nFactures à relancer ({len(FAILED_INVOICE_NUMBERS)}):")
    print(f"  {', '.join(FAILED_INVOICE_NUMBERS[:10])}...")
    print(f"  ... et {len(FAILED_INVOICE_NUMBERS) - 10} autres\n")
    
    retry_failed_emails()

