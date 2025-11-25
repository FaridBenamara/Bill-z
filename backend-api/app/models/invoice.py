"""
Modèle Invoice pour stocker les factures extraites
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Identifiants facture
    invoice_number = Column(String, index=True, nullable=True)
    invoice_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    
    # Fournisseur (JSON)
    supplier = Column(JSON, nullable=False)  # {name, siret, vat}
    
    # Client (JSON)
    client = Column(JSON, nullable=False)  # {name, siret, vat}
    
    # Montants (JSON)
    amounts = Column(JSON, nullable=False)  # {ht, tva, tva_rate, ttc, currency}
    
    # Catégorie
    category = Column(String, nullable=True)
    
    # Anomalies détectées (JSON array)
    anomalies = Column(JSON, nullable=True, default=[])
    
    # Confiance de l'extraction
    confidence_global = Column(Float, default=0.0)
    
    # Fichier PDF
    file_path = Column(String, nullable=False)  # Chemin relatif du PDF
    file_name = Column(String, nullable=False)  # Nom original
    
    # Email source
    email_id = Column(String, nullable=True)  # ID email Gmail
    email_subject = Column(String, nullable=True)
    
    # Type de facture
    invoice_type = Column(String, default="entrante")  # entrante/sortante
    
    # Statut
    is_validated = Column(Boolean, default=False)
    is_paid = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

