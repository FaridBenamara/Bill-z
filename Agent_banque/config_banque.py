import os
from dotenv import load_dotenv
from pathlib import Path

# Chemin vers la racine du projet (le dossier contenant app.py)
ROOT_DIR = Path(__file__).resolve().parents[0]  # Ajustable selon profondeur

# Charger le .env à la racine
load_dotenv(ROOT_DIR / ".env")

CONTEXT_FILE = "context_envoi.txt"
PROMPT_FILE  = "prompt_envoi.txt"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME_analyse = os.getenv("MODEL_NAME_analyse")

