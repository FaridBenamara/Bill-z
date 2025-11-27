"""
Service d'optimisation fiscale et analyse comptable intégré
"""
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from groq import Groq
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.invoice import Invoice
from app.models.transaction import Transaction


class OptimisationService:
    """Service d'analyse et d'optimisation comptable"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        
        self.context = self._load_context()
        self.prompt_template = self._load_prompt_template()
    
    def _load_context(self) -> str:
        """Charge le contexte pour l'analyse"""
        context_path = Path(__file__).parent.parent.parent.parent / "Agent_optimisation" / "context.txt"
        try:
            with open(context_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return "Tu es un agent d'optimisation comptable."
    
    def _load_prompt_template(self) -> str:
        """Charge le template de prompt"""
        prompt_path = Path(__file__).parent.parent.parent.parent / "Agent_optimisation" / "prompt.txt"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return "Factures: {{factures_json}}\n\nRapprochements: {{rapprochements_json}}"
    
    def _prepare_facture_data(self, invoice: Invoice) -> Dict:
        """Prépare les données d'une facture pour l'analyse"""
        return {
            "id": str(invoice.id),
            "numero": invoice.invoice_number or "N/A",
            "fournisseur": invoice.supplier.get('name') if isinstance(invoice.supplier, dict) else str(invoice.supplier),
            "date": str(invoice.invoice_date) if invoice.invoice_date else None,
            "date_echeance": str(invoice.due_date) if invoice.due_date else None,
            "montant_ttc": invoice.amounts.get('ttc') if isinstance(invoice.amounts, dict) else 0,
            "devise": invoice.amounts.get('currency', 'EUR') if isinstance(invoice.amounts, dict) else 'EUR',
            "categorie": invoice.category or "non catégorisé",
            "invoice_type": "reçue" if invoice.invoice_type == "entrante" else "envoyée" if invoice.invoice_type == "sortante" else None,
            "anomalies": invoice.anomalies or [],
            "confiance": invoice.confidence_global or 0.0
        }
    
    def _prepare_rapprochement_data(self, invoice: Invoice, transaction: Optional[Transaction]) -> Dict:
        """Prépare les données de rapprochement pour l'analyse"""
        if transaction and transaction.is_reconciled:
            return {
                "facture_id": str(invoice.id),
                "rapprochee": True,
                "date_paiement": str(transaction.date)[:7] if transaction.date else None,  # YYYY-MM
                "ecart_montant": abs(invoice.amounts.get('ttc', 0) - abs(transaction.amount)) if isinstance(invoice.amounts, dict) else 0,
                "ecart_jours": (transaction.date - invoice.invoice_date).days if transaction.date and invoice.invoice_date else 0,
                "niveau_confiance": transaction.reconciliation_confidence or 0.0
            }
        else:
            return {
                "facture_id": str(invoice.id),
                "rapprochee": False,
                "date_paiement": None,
                "ecart_montant": None,
                "ecart_jours": None,
                "niveau_confiance": 0.0
            }
    
    def analyze(self, user_id: int, db: Session) -> Optional[Dict]:
        """
        Analyse comptable complète pour un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            db: Session de base de données
        
        Returns:
            dict: Résultat de l'analyse ou None si erreur
        """
        try:
            # Récupérer toutes les factures de l'utilisateur
            invoices = db.query(Invoice).filter(Invoice.user_id == user_id).all()
            
            if not invoices:
                return {
                    "statistiques_globales": {
                        "nombre_factures_total": 0,
                        "nombre_factures_reçues": 0,
                        "nombre_factures_envoyées": 0,
                        "total_factures": 0.0,
                        "total_rapproché": 0.0,
                        "total_non_rapproché": 0.0,
                        "taux_rapprochement": 0.0,
                        "nombre_fournisseurs": 0
                    },
                    "rapprochements": {
                        "factures_rapprochées": [],
                        "factures_non_rapprochées": []
                    },
                    "analyse_fournisseurs": [],
                    "anomalies": [],
                    "optimisations": ["Aucune facture à analyser. Commencez par scanner vos emails ou importer des factures."],
                    "résumé": "Aucune donnée comptable disponible pour l'analyse."
                }
            
            # Récupérer les transactions rapprochées
            transactions = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.is_reconciled == True
            ).all()
            
            # Créer un mapping invoice_id -> transaction
            transaction_map = {t.invoice_id: t for t in transactions if t.invoice_id}
            
            # Préparer les données
            factures_data = []
            rapprochements_data = []
            
            for invoice in invoices:
                factures_data.append(self._prepare_facture_data(invoice))
                transaction = transaction_map.get(invoice.id)
                rapprochements_data.append(self._prepare_rapprochement_data(invoice, transaction))
            
            # Convertir en JSON
            factures_json = json.dumps(factures_data, ensure_ascii=False, indent=2)
            rapprochements_json = json.dumps(rapprochements_data, ensure_ascii=False, indent=2)
            
            # Créer le prompt avec la date du jour
            today = datetime.now().strftime("%Y-%m-%d")
            prompt = self.prompt_template.replace("{{date_aujourdhui}}", today)
            prompt = prompt.replace("{{factures_json}}", factures_json)
            prompt = prompt.replace("{{rapprochements_json}}", rapprochements_json)
            
            # Appel à Groq
            response = self.groq_client.chat.completions.create(
                model=settings.MODEL_NAME_analyse,
                messages=[
                    {"role": "system", "content": self.context},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            raw_content = response.choices[0].message.content
            result = json.loads(raw_content)
            
            return result
        
        except Exception:
            return None
    
    def get_tva_analysis(self, user_id: int, db: Session) -> Dict:
        """
        Analyse spécifique de la TVA
        
        Returns:
            dict: Analyse de la TVA
        """
        try:
            invoices = db.query(Invoice).filter(Invoice.user_id == user_id).all()
            
            tva_collectee = 0.0  # TVA sur factures émises
            tva_deductible = 0.0  # TVA sur factures reçues
            
            for invoice in invoices:
                if isinstance(invoice.amounts, dict):
                    tva = invoice.amounts.get('tva', 0)
                    if invoice.invoice_type == "sortante":
                        tva_collectee += tva
                    elif invoice.invoice_type == "entrante":
                        tva_deductible += tva
            
            tva_a_payer = tva_collectee - tva_deductible
            
            return {
                "tva_collectee": round(tva_collectee, 2),
                "tva_deductible": round(tva_deductible, 2),
                "tva_a_payer": round(tva_a_payer, 2),
                "conseil": "Pensez à déclarer votre TVA avant la date limite." if tva_a_payer > 0 else "Vous êtes en crédit de TVA."
            }
        
        except Exception:
            return {
                "tva_collectee": 0.0,
                "tva_deductible": 0.0,
                "tva_a_payer": 0.0,
                "conseil": "Erreur lors du calcul de la TVA"
            }

