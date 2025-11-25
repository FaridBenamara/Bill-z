"""
Schémas Pydantic pour Invoice
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class SupplierClient(BaseModel):
    """Informations fournisseur/client"""
    name: str
    siret: Optional[str] = None
    vat: Optional[str] = None


class Amounts(BaseModel):
    """Montants de la facture"""
    ht: float
    tva: float
    tva_rate: float
    ttc: float
    currency: str = "EUR"


class InvoiceCreate(BaseModel):
    """
    Création d'une facture (données extraites par l'agent)
    """
    invoice_number: str
    invoice_date: str  # Format: "YYYY-MM-DD"
    due_date: Optional[str] = None
    supplier: dict
    client: dict
    amounts: dict
    category: Optional[str] = None
    anomalies: List[str] = []
    confidence_global: float = 0.0
    email_id: Optional[str] = None
    email_subject: Optional[str] = None


class InvoiceResponse(BaseModel):
    """
    Réponse API avec une facture
    """
    id: int
    user_id: int
    invoice_number: Optional[str]
    invoice_date: Optional[date]
    due_date: Optional[date]
    supplier: dict
    client: dict
    amounts: dict
    category: Optional[str]
    anomalies: List[str]
    confidence_global: float
    file_path: str
    file_name: str
    email_id: Optional[str]
    email_subject: Optional[str]
    invoice_type: str
    is_validated: bool
    is_paid: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

