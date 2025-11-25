import os
from dotenv import load_dotenv
from pathlib import Path

# Chemin vers la racine du projet (le dossier contenant app.py)
ROOT_DIR = Path(__file__).resolve().parents[1]  # Ajustable selon profondeur

# Charger le .env à la racine
load_dotenv(ROOT_DIR / ".env")

CONTEXT_FILE = "Agent_facture/context.txt"
PROMPT_FILE  = "Agent_facture/prompt.txt"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME_analyse = os.getenv("MODEL_NAME_analyse")

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL_NAME_extract = os.getenv("MODEL_NAME_extract")

