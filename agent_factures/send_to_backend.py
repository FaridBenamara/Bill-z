"""
Module pour envoyer les factures au backend
"""
import requests
import json
from pathlib import Path


def send_invoice_to_backend(
    pdf_path: str,
    analysis_data: dict,
    email_id: str,
    email_subject: str,
    user_token: str,
    backend_url: str = "http://127.0.0.1:8000"
) -> dict:
    """
    Envoie une facture PDF + données JSON au backend
    
    Args:
        pdf_path: Chemin vers le PDF
        analysis_data: Dictionnaire JSON de l'analyse
        email_id: ID de l'email Gmail
        email_subject: Sujet de l'email
        user_token: Token JWT de l'utilisateur
        backend_url: URL du backend
    
    Returns:
        dict: Réponse du backend ou None si erreur
    """
    # Ajouter les infos email dans les données
    analysis_data["email_id"] = email_id
    analysis_data["email_subject"] = email_subject
    
    try:
        # Ouvrir le PDF
        with open(pdf_path, 'rb') as pdf_file:
            files = {
                'file': (Path(pdf_path).name, pdf_file, 'application/pdf')
            }
            
            data = {
                'extracted_data': json.dumps(analysis_data)
            }
            
            headers = {
                'Authorization': f'Bearer {user_token}'
            }
            
            # Envoyer au backend
            response = requests.post(
                f"{backend_url}/api/invoices/upload",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                print(f"[OK] Facture {analysis_data.get('invoice_number')} envoyee au backend")
                return response.json()
            else:
                print(f"[ERROR] Erreur backend ({response.status_code}): {response.text}")
                return None
                
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Erreur connexion backend: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Erreur envoi facture: {e}")
        return None

