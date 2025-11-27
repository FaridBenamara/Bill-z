"""
Routes API pour les transactions bancaires
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import io
import json
from datetime import datetime
import uuid

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.models.invoice import Invoice
from app.schemas.transaction import TransactionResponse, ReconciliationResult
from app.services.bank_reconciliation import BankReconciliationService

router = APIRouter()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_transactions(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload un fichier CSV ou Excel de transactions bancaires
    
    Format attendu:
    - date (YYYY-MM-DD ou DD/MM/YYYY)
    - amount (float, négatif = dépense)
    - vendor (string, optionnel)
    - description (string, optionnel)
    """
    try:
        # Lire le fichier
        contents = await file.read()
        
        # Déterminer le type de fichier
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format non supporté. Utilisez CSV ou Excel (.xlsx, .xls)"
            )
        
        # Vérifier les colonnes requises
        required_columns = ['date', 'amount']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Colonnes manquantes: {', '.join(missing)}"
            )
        
        # Générer un ID de batch pour ce lot d'import
        batch_id = str(uuid.uuid4())
        
        # Importer les transactions
        transactions_created = 0
        for _, row in df.iterrows():
            try:
                # Parser la date
                if isinstance(row['date'], str):
                    # Essayer différents formats
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y']:
                        try:
                            transaction_date = datetime.strptime(row['date'], fmt).date()
                            break
                        except ValueError:
                            continue
                    else:
                        continue
                else:
                    transaction_date = pd.to_datetime(row['date']).date()
                
                # Créer la transaction
                transaction = Transaction(
                    user_id=current_user.id,
                    date=transaction_date,
                    amount=float(row['amount']),
                    vendor=str(row.get('vendor', '')) if pd.notna(row.get('vendor')) else None,
                    description=str(row.get('description', '')) if pd.notna(row.get('description')) else None,
                    category=str(row.get('category', '')) if pd.notna(row.get('category')) else None,
                    source_file=file.filename,
                    import_batch_id=batch_id
                )
                
                db.add(transaction)
                transactions_created += 1
            
            except Exception as e:
                continue
        
        db.commit()
        
        return {
            "message": f"{transactions_created} transactions importées",
            "batch_id": batch_id,
            "transactions_count": transactions_created
        }
    
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier est vide"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'import: {str(e)}"
        )


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    reconciled_only: bool = False
):
    """
    Récupérer les transactions de l'utilisateur
    """
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    
    if reconciled_only:
        query = query.filter(Transaction.is_reconciled == True)
    
    transactions = query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()
    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer une transaction spécifique
    """
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction non trouvée"
        )
    
    return transaction


@router.post("/reconcile-all")
async def reconcile_all_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lance le rapprochement bancaire automatique pour toutes les factures non rapprochées
    
    Retourne:
    - Liste des rapprochements effectués
    - Statistiques
    """
    # Récupérer toutes les factures de l'utilisateur
    invoices = db.query(Invoice).filter(Invoice.user_id == current_user.id).all()
    
    if not invoices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune facture trouvée"
        )
    
    # Récupérer les transactions non rapprochées
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.is_reconciled == False
    ).all()
    
    if not transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune transaction disponible pour le rapprochement"
        )
    
    
    service = BankReconciliationService()
    results = []
    stats = {
        "total_invoices": len(invoices),
        "processed": 0,
        "matched": 0,
        "auto_confirmed": 0,
        "manual_review": 0,
        "no_match": 0
    }
    
    for invoice in invoices:
        # Vérifier si déjà rapprochée
        already_reconciled = db.query(Transaction).filter(
            Transaction.user_id == current_user.id,
            Transaction.invoice_id == invoice.id,
            Transaction.is_reconciled == True
        ).first()
        
        if already_reconciled:
            continue
        
        stats["processed"] += 1
        
        # Préparer les données
        invoice_data = {
            "fournisseur": invoice.supplier.get('name') if isinstance(invoice.supplier, dict) else str(invoice.supplier),
            "montant_ttc": invoice.amounts.get('ttc') if isinstance(invoice.amounts, dict) else 0,
            "date": str(invoice.invoice_date),
            "invoice_number": invoice.invoice_number
        }
        
        # Récupérer les transactions non rapprochées (mise à jour à chaque itération)
        available_transactions = db.query(Transaction).filter(
            Transaction.user_id == current_user.id,
            Transaction.is_reconciled == False
        ).all()
        
        if not available_transactions:
            break
        
        bank_transactions = [
            {
                "date": str(t.date),
                "amount": t.amount,
                "vendor": t.vendor or "",
                "description": t.description or "",
                "transaction_id": t.id
            }
            for t in available_transactions
        ]
        
        # Effectuer le rapprochement
        result = service.reconcile(
            invoice_data=invoice_data,
            bank_transactions=bank_transactions,
            invoice_type="reception" if invoice.invoice_type == "entrante" else "envoi"
        )
        
        if result and result.get('correspondance_trouvee'):
            lignes = result.get('lignes_correspondantes', [])
            if lignes:
                # Prendre la meilleure correspondance
                best_match = max(lignes, key=lambda x: x.get('niveau_confiance', 0))
                confidence = best_match.get('niveau_confiance', 0)
                
                # Retrouver l'ID de la transaction
                for t in available_transactions:
                    if (str(t.date)[:7] == best_match.get('date') and 
                        abs(t.amount - best_match.get('amount', 0)) < 0.01 and 
                        (t.vendor or "") == best_match.get('vendor', '')):
                        best_match['transaction_id'] = t.id
                        break
                
                if 'transaction_id' in best_match:
                    stats["matched"] += 1
                    
                    # Auto-confirmer si confiance >= 0.85 (85%)
                    if confidence >= 0.85:
                        transaction = db.query(Transaction).filter(
                            Transaction.id == best_match['transaction_id']
                        ).first()
                        
                        if transaction:
                            transaction.is_reconciled = True
                            transaction.invoice_id = invoice.id
                            transaction.reconciliation_confidence = confidence
                            transaction.reconciliation_details = {
                                "invoice_number": invoice.invoice_number,
                                "auto_confirmed": True,
                                "confirmed_at": str(datetime.now())
                            }
                            db.commit()
                            stats["auto_confirmed"] += 1
                        else:
                            stats["manual_review"] += 1
                    else:
                        stats["manual_review"] += 1
                    
                    results.append({
                        "invoice_id": invoice.id,
                        "invoice_number": invoice.invoice_number,
                        "transaction_id": best_match.get('transaction_id'),
                        "confidence": confidence,
                        "auto_confirmed": confidence >= 0.85,
                        "details": best_match
                    })
                else:
                    stats["no_match"] += 1
            else:
                stats["no_match"] += 1
        else:
            stats["no_match"] += 1
    
    
    return {
        "success": True,
        "message": f"{stats['auto_confirmed']} rapprochement(s) confirmé(s) automatiquement",
        "stats": stats,
        "results": results
    }


@router.post("/reconcile/{invoice_id}")
async def reconcile_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lance le rapprochement bancaire pour une facture
    """
    # Récupérer la facture
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facture non trouvée"
        )
    
    # Récupérer les transactions non rapprochées
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.is_reconciled == False
    ).all()
    
    if not transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune transaction disponible pour le rapprochement"
        )
    
    # Créer un mapping transaction_id -> transaction pour retrouver les IDs
    transaction_map = {
        f"{t.date}_{t.amount}_{t.vendor}": t.id
        for t in transactions
    }
    
    # Préparer les données pour le rapprochement
    invoice_data = {
        "fournisseur": invoice.supplier.get('name') if isinstance(invoice.supplier, dict) else str(invoice.supplier),
        "montant_ttc": invoice.amounts.get('ttc') if isinstance(invoice.amounts, dict) else 0,
        "date": str(invoice.invoice_date),
        "invoice_number": invoice.invoice_number
    }
    
    bank_transactions = [
        {
            "date": str(t.date),
            "amount": t.amount,
            "vendor": t.vendor or "",
            "description": t.description or "",
            "transaction_id": t.id  # Ajouter l'ID pour le retrouver
        }
        for t in transactions
    ]
    
    # Effectuer le rapprochement
    service = BankReconciliationService()
    result = service.reconcile(
        invoice_data=invoice_data,
        bank_transactions=bank_transactions,
        invoice_type="reception" if invoice.invoice_type == "entrante" else "envoi"
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du rapprochement"
        )
    
    # Ajouter les transaction_ids aux lignes correspondantes
    if result.get('lignes_correspondantes'):
        for ligne in result['lignes_correspondantes']:
            # Extraire les valeurs avec plusieurs variantes possibles
            ligne_date = (
                ligne.get('date') or 
                ligne.get('date_releve') or 
                ligne.get('details_differences', {}).get('date_releve') or 
                ''
            )
            
            ligne_amount = (
                ligne.get('amount') or 
                ligne.get('montant_releve') or 
                ligne.get('details_differences', {}).get('montant_releve') or 
                0
            )
            
            ligne_vendor = (
                ligne.get('vendor') or 
                ligne.get('fournisseur') or 
                ''
            )
            
            # Chercher la transaction correspondante
            matched = False
            
            # Stratégie 1: Match exact (date + montant + vendor)
            for t in transactions:
                transaction_date_prefix = str(t.date)[:7] if ligne_date else str(t.date)
                
                date_match = transaction_date_prefix == ligne_date if ligne_date else True
                amount_match = abs(t.amount - ligne_amount) < 0.01
                vendor_match = (t.vendor or "").strip().lower() == ligne_vendor.strip().lower()
                
                if date_match and amount_match and vendor_match:
                    ligne['transaction_id'] = t.id
                    matched = True
                    break
            
            # Stratégie 2: Match par montant + date (vendor peut différer légèrement)
            if not matched:
                for t in transactions:
                    transaction_date_prefix = str(t.date)[:7] if ligne_date else str(t.date)
                    date_match = transaction_date_prefix == ligne_date if ligne_date else True
                    amount_match = abs(t.amount - ligne_amount) < 0.01
                    
                    if date_match and amount_match:
                        ligne['transaction_id'] = t.id
                        matched = True
                        break
            
            # Stratégie 3: Match par montant seul (dernier recours)
            if not matched and ligne_amount != 0:
                for t in transactions:
                    if abs(t.amount - ligne_amount) < 0.01:
                        ligne['transaction_id'] = t.id
                        matched = True
                        break
    
    return result


@router.post("/reconcile/{invoice_id}/confirm/{transaction_id}")
async def confirm_reconciliation(
    invoice_id: int,
    transaction_id: int,
    confidence: float = 1.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirme le rapprochement entre une facture et une transaction
    
    Args:
        invoice_id: ID de la facture
        transaction_id: ID de la transaction
        confidence: Niveau de confiance (0-1), par défaut 1.0 pour confirmation manuelle
    """
    # Vérifier que la facture et la transaction appartiennent à l'utilisateur
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not invoice or not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facture ou transaction non trouvée"
        )
    
    # Vérifier si la transaction n'est pas déjà rapprochée
    if transaction.is_reconciled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette transaction est déjà rapprochée"
        )
    
    # Préparer les détails du rapprochement
    reconciliation_details = {
        "invoice_number": invoice.invoice_number,
        "invoice_date": str(invoice.invoice_date),
        "supplier": invoice.supplier.get('name') if isinstance(invoice.supplier, dict) else str(invoice.supplier),
        "amount_invoice": invoice.amounts.get('ttc') if isinstance(invoice.amounts, dict) else 0,
        "amount_transaction": transaction.amount,
        "confirmed_at": str(datetime.now()),
        "confirmed_by": "user"
    }
    
    # Marquer la transaction comme rapprochée
    transaction.is_reconciled = True
    transaction.invoice_id = invoice_id
    transaction.reconciliation_confidence = confidence
    transaction.reconciliation_details = reconciliation_details
    
    db.commit()
    db.refresh(transaction)
    
    return {
        "success": True,
        "message": "Rapprochement confirmé avec succès",
        "transaction_id": transaction_id,
        "invoice_id": invoice_id,
        "confidence": confidence,
        "details": reconciliation_details
    }


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer une transaction
    """
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction non trouvée"
        )
    
    db.delete(transaction)
    db.commit()
    
    return None

