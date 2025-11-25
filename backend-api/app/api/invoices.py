"""
Routes API pour les factures
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import json
from pathlib import Path

from app.core.database import get_db
from app.core.storage import save_invoice_pdf, delete_invoice_pdf
from app.api.auth import get_current_user
from app.models.user import User
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceResponse
from app.services.agent_runner import run_invoice_agent

router = APIRouter()


@router.post("/upload", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    file: UploadFile = File(...),
    extracted_data: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload une facture PDF avec ses données extraites par l'agent
    
    - **file**: PDF de la facture
    - **extracted_data**: JSON des données extraites
    """
    # Vérifier que c'est un PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Parser les données extraites
    try:
        data = json.loads(extracted_data)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in extracted_data"
        )
    
    # Sauvegarder le PDF
    file_info = save_invoice_pdf(
        user_id=current_user.id,
        filename=file.filename,
        file_content=file.file
    )
    
    # Créer l'entrée en base
    new_invoice = Invoice(
        user_id=current_user.id,
        invoice_number=data.get("invoice_number"),
        invoice_date=data.get("invoice_date"),
        due_date=data.get("due_date"),
        supplier=data.get("supplier"),
        client=data.get("client"),
        amounts=data.get("amounts"),
        category=data.get("category"),
        anomalies=data.get("anomalies", []),
        confidence_global=data.get("confidence_global", 0.0),
        file_path=file_info["file_path"],
        file_name=file_info["file_name"],
        email_id=data.get("email_id"),
        email_subject=data.get("email_subject"),
        invoice_type="entrante"
    )
    
    db.add(new_invoice)
    db.commit()
    db.refresh(new_invoice)
    
    return new_invoice


@router.get("/", response_model=List[InvoiceResponse])
async def get_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les factures de l'utilisateur
    """
    invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user.id
    ).order_by(Invoice.created_at.desc()).all()
    
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer une facture spécifique
    """
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return invoice


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Télécharger le PDF d'une facture
    """
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    file_path = Path(invoice.file_path)
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found"
        )
    
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=invoice.file_name
    )


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer une facture et son PDF
    """
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Supprimer le fichier PDF
    delete_invoice_pdf(invoice.file_path)
    
    # Supprimer de la base
    db.delete(invoice)
    db.commit()
    
    return None


@router.post("/scan")
async def scan_gmail_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lance l'agent facture pour scanner Gmail et extraire les factures
    """
    from app.core.security import create_access_token
    
    # Générer un token pour l'agent
    token = create_access_token(data={"sub": current_user.email})
    
    # Lancer l'agent
    result = run_invoice_agent(user_token=token)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Erreur lors de l'exécution de l'agent")
        )
    
    return {
        "message": "Scan terminé",
        "invoices_processed": result["invoices_processed"],
        "invoices_uploaded": result["invoices_uploaded"]
    }

