import pandas as pd
import json
import os
from datetime import datetime

def add_invoices_to_csv(json_path, template_name, is_seller_mode, csv_path="data/releve_bancaire_08-2017.xlsx"):
    """
    Ajoute les factures générées au relevé bancaire CSV.
    
    Args:
        json_path: Chemin vers le fichier JSON des factures
        template_name: Nom du template utilisé
        is_seller_mode: True si nous sommes le seller (revenus), False si buyer (dépenses)
        csv_path: Chemin vers le fichier CSV/Excel du relevé bancaire
    """
    # Lire le JSON des factures
    with open(json_path, "r", encoding="utf-8") as f:
        invoices_json = json.load(f)
    
    # Lire le CSV existant
    if os.path.exists(csv_path):
        if csv_path.endswith('.xlsx'):
            df = pd.read_excel(csv_path)
        else:
            df = pd.read_csv(csv_path)
    else:
        # Créer un nouveau DataFrame si le fichier n'existe pas
        df = pd.DataFrame(columns=['date', 'amount', 'currency', 'vendor', 'source'])
    
    # Préparer les nouvelles lignes
    new_rows = []
    
    for invoice_id, invoice_data in invoices_json.items():
        # Date complète (YYYY-MM-DD), fallback 2017-08-01
        date_str = invoice_data.get("date", "2017-08-01")
        
        # Montant : total_ttc
        total_ttc = invoice_data.get("total_ttc", 0)
        
        # Si nous sommes buyer (dépense) → montant négatif
        # Si nous sommes seller (revenu) → montant positif
        amount = total_ttc if is_seller_mode else -total_ttc
        
        # Currency : par défaut EUR (peut être modifié)
        currency = "EUR"
        
        # Vendor : 
        # - Si buyer mode → seller.name (celui qui nous vend)
        # - Si seller mode → buyer.name (celui qui nous achète)
        if is_seller_mode:
            vendor = invoice_data.get("buyer", {}).get("name", "Client")
        else:
            vendor = invoice_data.get("seller", {}).get("name", "Fournisseur")
        
        # Source : nom du fichier facture
        invoice_number = invoice_data.get("invoice_number", invoice_id)
        source = f"facture_{invoice_number.replace('/', '_')}.pdf"
        
        new_rows.append({
            'date': date_str,
            'amount': round(amount, 2),
            'currency': currency,
            'vendor': vendor,
            'source': source
        })
    
    # Créer un DataFrame avec les nouvelles lignes
    new_df = pd.DataFrame(new_rows)
    
    # Ajouter au DataFrame existant
    df = pd.concat([df, new_df], ignore_index=True)
    
    # Sauvegarder avec gestion d'erreur si le fichier est ouvert
    try:
        if csv_path.endswith('.xlsx'):
            df.to_excel(csv_path, index=False)
        else:
            df.to_csv(csv_path, index=False)
        
        print(f"✓ {len(new_rows)} transactions ajoutées au relevé bancaire")
        print(f"  - Mode: {'Revenus (+)' if is_seller_mode else 'Dépenses (-)'}")
        print(f"  - Template: {template_name}")
    except PermissionError:
        # Si le fichier est ouvert, sauvegarder dans un fichier temporaire
        temp_path = csv_path.replace('.xlsx', '_new.xlsx').replace('.csv', '_new.csv')
        if csv_path.endswith('.xlsx'):
            df.to_excel(temp_path, index=False)
        else:
            df.to_csv(temp_path, index=False)
        
        print(f"⚠ ATTENTION : Le fichier {csv_path} est ouvert dans Excel.")
        print(f"  Les {len(new_rows)} transactions ont été sauvegardées dans : {temp_path}")
        print(f"  Veuillez fermer le fichier Excel et copier le contenu de {temp_path} dans {csv_path}")
        raise  # Relancer l'erreur pour que main.py sache qu'il y a eu un problème


if __name__ == "__main__":
    # Exemple d'utilisation
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python add_to_csv.py <json_path> <template_name> <is_seller_mode>")
        print("Exemple: python add_to_csv.py data/generated_invoices_json/invoices_facture1.json facture1.html False")
        sys.exit(1)
    
    json_path = sys.argv[1]
    template_name = sys.argv[2]
    is_seller_mode = sys.argv[3].lower() == 'true'
    
    add_invoices_to_csv(json_path, template_name, is_seller_mode)

