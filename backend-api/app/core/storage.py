"""
Gestion du stockage local des fichiers PDF
"""
from pathlib import Path
import shutil
from typing import BinaryIO
from datetime import datetime


# Dossier de stockage
UPLOAD_DIR = Path("./uploads")
INVOICES_DIR = UPLOAD_DIR / "invoices"

# Créer les dossiers au démarrage
UPLOAD_DIR.mkdir(exist_ok=True)
INVOICES_DIR.mkdir(exist_ok=True)


def save_invoice_pdf(user_id: int, filename: str, file_content: BinaryIO) -> dict:
    """
    Sauvegarder un PDF de facture localement
    
    Args:
        user_id: ID de l'utilisateur
        filename: Nom du fichier original
        file_content: Contenu du fichier (binary)
    
    Returns:
        dict: {file_path: str, file_name: str}
    """
    # Créer dossier utilisateur (avec parents si nécessaire)
    user_dir = INVOICES_DIR / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Générer nom unique avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = Path(filename).suffix
    safe_filename = f"{Path(filename).stem}_{timestamp}{file_extension}"
    
    # Chemin complet
    file_path = user_dir / safe_filename
    
    # Sauvegarder le fichier
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file_content, f)
    
    # Retourner chemin relatif simple (pas besoin de relative_to)
    # Format: uploads/invoices/user_X/filename.pdf
    relative_path = f"uploads/invoices/user_{user_id}/{safe_filename}"
    
    return {
        "file_path": relative_path,
        "file_name": filename
    }


def get_invoice_pdf_path(file_path: str) -> Path:
    """
    Obtenir le chemin absolu d'un PDF
    """
    return Path(file_path)


def delete_invoice_pdf(file_path: str) -> bool:
    """
    Supprimer un PDF de facture
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        return False


def get_user_invoices_dir(user_id: int) -> Path:
    """
    Obtenir le dossier des factures d'un utilisateur
    """
    return INVOICES_DIR / f"user_{user_id}"

