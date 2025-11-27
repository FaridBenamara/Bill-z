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
from app.services.invoice_scanner import InvoiceScanner

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


def _scan_invoices_task(user_id: int, db: Session):
    """Tâche de scan en arrière-plan"""
    try:
        scanner = InvoiceScanner(user_id=user_id, db=db)
        stats = scanner.scan_and_process(max_emails=50)
    except Exception:
        pass
    finally:
        db.close()


@router.post("/scan")
async def scan_gmail_invoices(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lance le scan Gmail pour extraire les factures
    Le scan s'exécute en arrière-plan pour ne pas bloquer le serveur
    """
    # Lancer le scan en arrière-plan
    background_tasks.add_task(_scan_invoices_task, current_user.id, db)
    
    return {
        "message": "Scan Gmail lancé en arrière-plan. Les factures apparaîtront progressivement.",
        "status": "processing"
    }

