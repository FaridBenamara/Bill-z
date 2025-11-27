"""
Service de rapprochement bancaire intégré
"""
import json
from typing import Dict, List, Optional
from pathlib import Path
from groq import Groq
from app.core.config import settings


class BankReconciliationService:
    """Service de rapprochement bancaire intelligent"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        
        self.context_envoi = self._load_context("context_envoi.txt")
        self.context_reception = self._load_context("context_reception.txt")
        self.prompt_template = self._load_prompt_template()
    
    def _load_context(self, filename: str) -> str:
        """Charge un fichier de contexte"""
        context_path = Path(__file__).parent.parent.parent.parent / "Agent_banque" / filename
        try:
            with open(context_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return "Tu es un agent de rapprochement bancaire."
    
    def _load_prompt_template(self) -> str:
        """Charge le template de prompt"""
        prompt_path = Path(__file__).parent.parent.parent.parent / "Agent_banque" / "prompt.txt"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return "Facture: {{facture_json}}\n\nRelevé bancaire: {{releve_bancaire}}"
    
    def reconcile(
        self,
        invoice_data: Dict,
        bank_transactions: List[Dict],
        invoice_type: str = "reception"  # "reception" ou "envoi"
    ) -> Optional[Dict]:
        """
        Effectue le rapprochement entre une facture et des transactions bancaires
        
        Args:
            invoice_data: Données de la facture (dict)
            bank_transactions: Liste des transactions bancaires (list of dict)
            invoice_type: "reception" (facture reçue) ou "envoi" (facture émise)
        
        Returns:
            dict: Résultat du rapprochement ou None si erreur
        """
        try:
            # Choisir le bon contexte
            context = self.context_reception if invoice_type == "reception" else self.context_envoi
            
            # Préparer les données
            invoice_json = json.dumps(invoice_data, ensure_ascii=False, indent=2)
            releve_json = json.dumps(bank_transactions, ensure_ascii=False, indent=2)
            
            # Créer le prompt
            prompt = self.prompt_template.replace("{{facture_json}}", invoice_json)
            prompt = prompt.replace("{{releve_bancaire}}", releve_json)
            
            # Appel à Groq
            response = self.groq_client.chat.completions.create(
                model=settings.MODEL_NAME_analyse,
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            raw_content = response.choices[0].message.content
            result = json.loads(raw_content)
            
            return result
        
        except Exception:
            return None
    
    def auto_reconcile_invoice(
        self,
        invoice_data: Dict,
        bank_transactions: List[Dict],
        confidence_threshold: float = 0.7
    ) -> Optional[Dict]:
        """
        Tente un rapprochement automatique avec un seuil de confiance
        
        Returns:
            dict: Meilleure correspondance trouvée ou None
        """
        result = self.reconcile(invoice_data, bank_transactions)
        
        if not result or not result.get('correspondance_trouvee'):
            return None
        
        # Trouver la meilleure correspondance
        lignes = result.get('lignes_correspondantes', [])
        if not lignes:
            return None
        
        # Trier par niveau de confiance
        best_match = max(lignes, key=lambda x: x.get('niveau_confiance', 0))
        
        if best_match.get('niveau_confiance', 0) >= confidence_threshold:
            return {
                'transaction': best_match,
                'confidence': best_match.get('niveau_confiance'),
                'details': result
            }
        
        return None

