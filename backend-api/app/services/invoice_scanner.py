"""
Service intégré pour scanner Gmail et extraire les factures
Remplace l'agent externe pour une meilleure intégration
"""
import os
import json
import base64
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from groq import Groq
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.core.config import settings
from app.core.storage import save_invoice_pdf
from app.models.invoice import Invoice
from sqlalchemy.orm import Session


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class InvoiceScanner:
    """Scanner de factures Gmail intégré"""
    
    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        self.context = self._load_context()
        self.prompt_template = self._load_prompt_template()
    
    def _load_context(self) -> str:
        """Charge le contexte pour l'analyse"""
        context_path = Path(__file__).parent.parent.parent.parent / "agent_factures" / "context.txt"
        try:
            with open(context_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return "Tu es un agent spécialisé dans l'analyse de factures."
    
    def _load_prompt_template(self) -> str:
        """Charge le template de prompt"""
        prompt_path = Path(__file__).parent.parent.parent.parent / "agent_factures" / "prompt.txt"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return "Analyse cette facture: {{FACTURE_BRUTE}}"
    
    def _get_gmail_service(self):
        """Authentifie et retourne le service Gmail"""
        creds = None
        
        # Chercher token.json d'abord dans backend-api/, puis dans agent_factures/
        backend_token_path = Path(__file__).parent.parent.parent / "token.json"
        agent_token_path = Path(__file__).parent.parent.parent.parent / "agent_factures" / "token.json"
        
        token_path = backend_token_path if backend_token_path.exists() else agent_token_path
        
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Chercher credentials.json d'abord dans backend-api/, puis dans agent_factures/
                backend_creds_path = Path(__file__).parent.parent.parent / "credentials.json"
                agent_creds_path = Path(__file__).parent.parent.parent.parent / "agent_factures" / "credentials.json"
                
                credentials_path = backend_creds_path if backend_creds_path.exists() else agent_creds_path
                
                if not credentials_path.exists():
                    raise FileNotFoundError(
                        "credentials.json non trouvé. "
                        "Placez-le dans backend-api/ ou agent_factures/"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Sauvegarder le token dans backend-api/
            save_token_path = Path(__file__).parent.parent.parent / "token.json"
            with open(save_token_path, 'w') as token:
                token.write(creds.to_json())
        
        return build('gmail', 'v1', credentials=creds)
    
    def _extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """Extrait le texte d'un PDF"""
        import io
        try:
            from pypdf import PdfReader
            pdf_file = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception:
            return ""
    
    def _analyze_invoice_text(self, invoice_text: str) -> Optional[Dict]:
        """Analyse le texte de la facture avec Groq"""
        if not invoice_text or not invoice_text.strip():
            return None
        
        try:
            prompt = self.prompt_template.replace("{{FACTURE_BRUTE}}", invoice_text)
            
            response = self.groq_client.chat.completions.create(
                model=settings.MODEL_NAME_analyse,
                messages=[
                    {"role": "system", "content": self.context},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            raw_content = response.choices[0].message.content
            return json.loads(raw_content)
        
        except Exception:
            return None
    
    def _get_gmail_messages(self, service, max_results: int = 50) -> List[Dict]:
        """Récupère les messages Gmail avec pièces jointes (INBOX + SENT)"""
        try:
            emails = []
            
            # Scanner INBOX (factures reçues)
            inbox_results = service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                q='has:attachment',
                maxResults=max_results
            ).execute()
            
            inbox_messages = inbox_results.get('messages', [])
            
            for msg in inbox_messages:
                msg_id = msg['id']
                
                # Récupérer le message complet
                message = service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()
                
                headers = message.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                # Extraire les pièces jointes
                attachments = self._extract_attachments(service, msg_id, message.get('payload', {}))
                
                if attachments:
                    emails.append({
                        'id': msg_id,
                        'subject': subject,
                        'from': from_email,
                        'date': date,
                        'type': 'entrante',  # Facture reçue
                        'attachments': attachments
                    })
            
            # Scanner SENT (factures envoyées)
            sent_results = service.users().messages().list(
                userId='me',
                labelIds=['SENT'],
                q='has:attachment',
                maxResults=max_results
            ).execute()
            
            sent_messages = sent_results.get('messages', [])
            
            for msg in sent_messages:
                msg_id = msg['id']
                
                # Récupérer le message complet
                message = service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()
                
                headers = message.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                to_email = next((h['value'] for h in headers if h['name'] == 'To'), '')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                # Extraire les pièces jointes
                attachments = self._extract_attachments(service, msg_id, message.get('payload', {}))
                
                if attachments:
                    emails.append({
                        'id': msg_id,
                        'subject': subject,
                        'from': to_email,  # Pour les envoyées, le destinataire
                        'date': date,
                        'type': 'sortante',  # Facture envoyée
                        'attachments': attachments
                    })
            
            return emails
        
        except Exception:
            return []
    
    def _extract_attachments(self, service, msg_id: str, payload: Dict) -> List[Dict]:
        """Extrait les pièces jointes d'un message"""
        attachments = []
        
        def explore_parts(parts):
            for part in parts:
                filename = part.get('filename', '')
                if filename and filename.lower().endswith('.pdf'):
                    body = part.get('body', {})
                    att_id = body.get('attachmentId')
                    
                    if att_id:
                        try:
                            attachment = service.users().messages().attachments().get(
                                userId='me',
                                messageId=msg_id,
                                id=att_id
                            ).execute()
                            
                            file_data = base64.urlsafe_b64decode(attachment['data'])
                            attachments.append({
                                'filename': filename,
                                'data': file_data
                            })
                        except Exception:
                            pass
                
                if part.get('parts'):
                    explore_parts(part['parts'])
        
        if payload.get('parts'):
            explore_parts(payload['parts'])
        
        return attachments
    
    def scan_and_process(self, max_emails: int = 50) -> Dict:
        """
        Scanne Gmail et traite les factures
        
        Returns:
            dict: Statistiques de traitement
        """
        stats = {
            'emails_scanned': 0,
            'invoices_found': 0,
            'invoices_processed': 0,
            'invoices_saved': 0,
            'errors': []
        }
        
        try:
            service = self._get_gmail_service()
            emails = self._get_gmail_messages(service, max_results=max_emails)
            stats['emails_scanned'] = len(emails)
            
            # Traiter chaque email
            for email in emails:
                for attachment in email['attachments']:
                    stats['invoices_found'] += 1
                    filename = attachment['filename']
                    
                    try:
                        # Vérifier si déjà traité (via email_id)
                        existing = self.db.query(Invoice).filter(
                            Invoice.user_id == self.user_id,
                            Invoice.email_id == email['id']
                        ).first()
                        
                        if existing:
                            continue
                        
                        # Extraire le texte
                        invoice_text = self._extract_text_from_pdf(attachment['data'])
                        
                        if not invoice_text:
                            stats['errors'].append(f"{filename}: Extraction texte échouée")
                            continue
                        
                        # Analyser avec LLM
                        analysis = self._analyze_invoice_text(invoice_text)
                        
                        if not analysis:
                            stats['errors'].append(f"{filename}: Analyse LLM échouée")
                            continue
                        
                        stats['invoices_processed'] += 1
                        
                        # Sauvegarder le PDF
                        import io
                        file_info = save_invoice_pdf(
                            user_id=self.user_id,
                            filename=filename,
                            file_content=io.BytesIO(attachment['data'])
                        )
                        
                        # Créer l'entrée en base
                        invoice_type = email.get('type', 'entrante')
                        
                        new_invoice = Invoice(
                            user_id=self.user_id,
                            invoice_number=analysis.get('invoice_number'),
                            invoice_date=analysis.get('invoice_date'),
                            due_date=analysis.get('due_date'),
                            supplier=analysis.get('supplier', {}),
                            client=analysis.get('client', {}),
                            amounts=analysis.get('amounts', {}),
                            category=analysis.get('category'),
                            anomalies=analysis.get('anomalies', []),
                            confidence_global=analysis.get('confidence_global', 0.0),
                            file_path=file_info['file_path'],
                            file_name=file_info['file_name'],
                            email_id=email['id'],
                            email_subject=email['subject'],
                            invoice_type=invoice_type
                        )
                        
                        self.db.add(new_invoice)
                        self.db.commit()
                        self.db.refresh(new_invoice)
                        
                        stats['invoices_saved'] += 1
                    
                    except Exception as e:
                        stats['errors'].append(f"{filename}: {str(e)}")
                        self.db.rollback()
            
            return stats
        
        except Exception as e:
            stats['errors'].append(f"Erreur globale: {str(e)}")
            return stats
            return stats

