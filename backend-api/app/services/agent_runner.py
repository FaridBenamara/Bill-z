"""
Service pour lancer l'agent facture depuis le backend
"""
import subprocess
import os
from pathlib import Path
from typing import Dict, List


def run_invoice_agent(user_token: str) -> Dict:
    """
    Lance l'agent facture pour scanner Gmail et extraire les factures
    
    Args:
        user_token: Token JWT de l'utilisateur
    
    Returns:
        dict: Résultat de l'exécution
    """
    # Chemin vers l'agent
    agent_dir = Path(__file__).resolve().parents[3] / "agent_factures"
    agent_script = agent_dir / "agent_facture.py"
    
    if not agent_script.exists():
        return {
            "success": False,
            "error": "Agent facture non trouvé",
            "invoices_processed": 0
        }
    
    try:
        # Créer l'environnement avec le token
        env = os.environ.copy()
        env["USER_TOKEN"] = user_token
        
        # Lancer l'agent en subprocess
        result = subprocess.run(
            ["python", str(agent_script)],
            cwd=str(agent_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        # Parser la sortie pour compter les factures
        output = result.stdout
        invoices_count = output.count("[OK] Analyse terminee")
        uploaded_count = output.count("[UPLOAD] Envoyee au backend")
        
        # Log pour debug
        print(f"[AGENT] Return code: {result.returncode}")
        print(f"[AGENT] STDOUT: {result.stdout}")
        print(f"[AGENT] STDERR: {result.stderr}")
        
        return {
            "success": result.returncode == 0,
            "invoices_processed": invoices_count,
            "invoices_uploaded": uploaded_count,
            "output": output,
            "error": result.stderr if result.returncode != 0 else None
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Timeout: l'agent a pris trop de temps",
            "invoices_processed": 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "invoices_processed": 0
        }

