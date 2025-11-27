from __future__ import print_function
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json
import os
import pickle
import time
import re
from datetime import datetime


SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]
CLIENT_SECRET_FILE = "client_secret.json"

def get_credentials():
    """Obtient les credentials Gmail, crée token.json si nécessaire."""
    creds = None
    token_file = 'token.json'
    token_pickle = 'token.pickle'
    
    # Essayer de charger depuis token.json (nouveau format)
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    # Sinon essayer token.pickle (ancien format)
    elif os.path.exists(token_pickle):
        with open(token_pickle, 'rb') as token:
            creds = pickle.load(token)
    
    # Si pas de credentials valides, créer un nouveau token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                raise FileNotFoundError(
                    f"{CLIENT_SECRET_FILE} introuvable. "
                    "Assurez-vous que le fichier est présent dans le répertoire."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Sauvegarder dans token.json (format JSON)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        print(f"✓ Token sauvegardé dans {token_file}")
    
    return creds


def send_mail_with_attachment(subject, message_body, to_email, pdf_path=None):
    """
    Envoie un email avec optionnellement une pièce jointe PDF.
    
    Args:
        subject: Sujet de l'email
        message_body: Corps du message
        to_email: Adresse email du destinataire
        pdf_path: Chemin vers le fichier PDF à joindre (optionnel)
    """
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    
    # Créer le message
    if pdf_path and os.path.exists(pdf_path):
        message = MIMEMultipart()
        message['to'] = to_email
        message['subject'] = subject
        
        # Ajouter le corps du message
        message.attach(MIMEText(message_body, 'plain'))
        
        # Ajouter la pièce jointe PDF
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        filename = os.path.basename(pdf_path)
        part = MIMEApplication(pdf_bytes, _subtype="pdf")
        part.add_header('Content-Disposition', 'attachment', filename=filename)
        part.add_header('Content-Type', f'application/pdf; name="{filename}"')
        message.attach(part)
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    else:
        # Message simple sans pièce jointe
        message = MIMEText(message_body)
        message['to'] = to_email
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    # Envoyer avec gestion du rate limit
    max_retries = 5
    retry_delay = 60  # Délai par défaut en secondes
    
    for attempt in range(max_retries):
        try:
            send_message = service.users().messages().send(
                userId="me", body={'raw': raw_message}).execute()
            
            print(f"✓ Email envoyé à {to_email} : {send_message.get('id')}")
            return send_message
            
        except HttpError as error:
            if error.resp.status == 429:  # Rate limit exceeded
                # Extraire le délai d'attente depuis le message d'erreur
                error_msg = str(error)
                wait_seconds = retry_delay
                
                # Chercher "Retry after" dans le message
                if "Retry after" in error_msg:
                    try:
                        # Extraire le timestamp (format: 2025-11-23T21:03:29.211Z)
                        match = re.search(r'Retry after (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)', error_msg)
                        if match:
                            retry_time_str = match.group(1)
                            # Parser le timestamp
                            retry_time = datetime.strptime(retry_time_str.replace('Z', ''), '%Y-%m-%dT%H:%M:%S.%f')
                            now = datetime.utcnow()
                            wait_seconds = max((retry_time - now).total_seconds(), 60)
                    except Exception:
                        # Si l'extraction échoue, utiliser le délai par défaut
                        wait_seconds = retry_delay
                
                if attempt < max_retries - 1:
                    minutes = int(wait_seconds // 60)
                    seconds = int(wait_seconds % 60)
                    print(f"  ⚠ Rate limit atteint. Attente {minutes} min {seconds} sec avant réessai...")
                    time.sleep(wait_seconds)
                    retry_delay = wait_seconds * 2  # Backoff exponentiel pour les prochains essais
                else:
                    raise Exception(f"Rate limit toujours actif après {max_retries} tentatives")
            else:
                # Autre erreur HTTP
                raise
        except Exception as e:
            if attempt < max_retries - 1:
                # Réessayer après un court délai
                print(f"  ⚠ Erreur (tentative {attempt + 1}/{max_retries}): {e}")
                time.sleep(5)
            else:
                raise


# Email/Destinataire par défaut
DEFAULT_RECIPIENT = "billz.project.md5@gmail.com"

def send_invoice_email(invoice_data, pdf_path, is_seller_mode, recipient_email=None):
    """
    Envoie une facture par email.
    
    Args:
        invoice_data: Données de la facture (dict)
        pdf_path: Chemin vers le PDF de la facture
        is_seller_mode: True si nous sommes le seller (on envoie au client)
        recipient_email: Email du destinataire (si None, utilise DEFAULT_EMAIL)
    """
    invoice_number = invoice_data.get("invoice_number", "N/A")
    
    if not recipient_email:
        recipient_email = DEFAULT_RECIPIENT
    
    if is_seller_mode:
        # Nous sommes le seller - Facture envoyée par nous
        subject = f"[ENVOI] Facture {invoice_number} - Altevia Solutions"
        message = f"""
Bonjour,

Vous trouverez ci-joint la facture {invoice_number} que nous avons émise.

Cette facture correspond à une vente effectuée par Altevia Solutions.

Détails de la facture :
- Numéro : {invoice_number}
- Date : {invoice_data.get("date", "N/A")}
- Client : {invoice_data.get("buyer", {}).get("name", "N/A")}
- Montant TTC : {invoice_data.get("total_ttc", 0)} €

Merci de votre confiance.

Cordialement,
Altevia Solutions
12 Rue des Entrepreneurs, 75015 Paris, France
contact@altevia.com
        """
    else:
        # Nous sommes le buyer - Facture reçue d'un fournisseur
        seller_name = invoice_data.get("seller", {}).get("name", "Fournisseur")
        seller_email = invoice_data.get("seller", {}).get("email", "")
        subject = f"[RÉCEPTION] Facture {invoice_number} - {seller_name}"
        message = f"""
Bonjour,

Vous trouverez ci-joint la facture {invoice_number} que nous avons reçue de {seller_name}.

Cette facture correspond à un achat effectué auprès de {seller_name}.

Détails de la facture :
- Numéro : {invoice_number}
- Date : {invoice_data.get("date", "N/A")}
- Fournisseur : {seller_name}
{f"- Email : {seller_email}" if seller_email else ""}
- Montant TTC : {invoice_data.get("total_ttc", 0)} €

Cordialement,
Altevia Solutions
        """
    
    return send_mail_with_attachment(subject, message.strip(), recipient_email, pdf_path)


if __name__ == '__main__':
    # Test d'envoi
    print("Test d'authentification Gmail...")
    creds = get_credentials()
    print("✓ Authentification réussie !")
    
    # Test d'envoi simple
    send_mail_with_attachment(
        subject="Test Gmail API",
        message_body="Ceci est un email automatique de test.",
        to_email=DEFAULT_RECIPIENT
    )

    