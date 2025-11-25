import time
import json
import os
from utils_facture import read_file, extract_text_from_pdf, extract_text_with_pixtral
from groq import Groq
from recup_mail import recup_mail
from config_facture import CONTEXT_FILE, PROMPT_FILE, GROQ_API_KEY, MODEL_NAME_analyse, MISTRAL_API_KEY, MODEL_NAME_extract
from send_to_backend import send_invoice_to_backend


def load_prompt_and_context(invoice: str) -> tuple[str, str]:
    """Charge le contexte et remplace le placeholder dans le prompt."""
    context = read_file(CONTEXT_FILE)
    prompt_template = read_file(PROMPT_FILE)

    if not context or not prompt_template:
        raise ValueError("Impossible de charger context.txt ou prompt.txt")

    prompt = prompt_template.replace("{{FACTURE_BRUTE}}", invoice)
    return context, prompt


def prepare_invoice_text(attachement) -> str:
    """Prépare le texte de la facture pour l'analyse."""
    
    # Création du dossier temp si inexistant
    os.makedirs("temp", exist_ok=True)

    filename = attachement["filename"].lower()
    path = f"temp/{attachement['filename']}"

    if filename.endswith(".pdf"):
        # Extraction du texte depuis le PDF
        with open(path, "wb") as f:
            f.write(attachement["data"])
        text = extract_text_from_pdf(path)

    else:
        # Extraction du texte depuis l'image via Pixtral
        with open(path, "wb") as f:
            f.write(attachement["data"])
        text = extract_text_with_pixtral(path, MISTRAL_API_KEY, MODEL_NAME_extract)

    return text.strip()

        

def analyze_text(invoice: str) -> dict | None:
    """Appelle l'API GROQ pour analyser le code Python."""
    if not GROQ_API_KEY:
        print("[ERREUR] GROQ_API_KEY n'est pas défini.")
        return None

    context, prompt = load_prompt_and_context(invoice)

    client = Groq(api_key=GROQ_API_KEY)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME_analyse,
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        raw_content = response.choices[0].message.content

        try:
            return json.loads(raw_content)
        except json.JSONDecodeError:
            print("[ERREUR] Réponse GROQ non JSON :")
            print(raw_content)
            return None

    except Exception as e:
        print(f"[ERREUR] Appel API GROQ : {e}")
        return None

def print_results_analysis(result: dict):
    print("\n===== 📄 ANALYSE FACTURE =====\n")

    # Numéro et dates
    print(f"🧾 Numéro facture : {result.get('invoice_number')}")
    print(f"📅 Date facture : {result.get('invoice_date')}")
    print(f"⏳ Échéance : {result.get('due_date')}\n")

    # Fournisseur
    supplier = result.get("supplier", {})
    print("🏢 Fournisseur :")
    print(f"   - Nom   : {supplier.get('name')}")
    print(f"   - SIRET : {supplier.get('siret')}")

    # Montants
    amounts = result.get("amounts", {})
    print("💶 Montants :")
    print(f"   - HT       : {amounts.get('ht')}")
    print(f"   - TVA      : {amounts.get('tva')} (taux {amounts.get('tva_rate')}%)")
    print(f"   - TTC      : {amounts.get('ttc')}")
    print(f"   - Devise   : {amounts.get('currency')}\n")

    # Catégorie détectée
    print(f"🏷️ Catégorie détectée : {result.get('category')}\n")

    # Anomalies
    anomalies = result.get("anomalies", [])
    if anomalies:
        print("⚠️ Anomalies détectées :")
        for a in anomalies:
            print(f"   - {a}")
        print()
    else:
        print("✔️ Aucune anomalie détectée\n")

    # Confiance globale
    print(f"📊 Confiance analyse : {result.get('confidence_global')}\n")

    print("===== ✔ FIN ANALYSE =====\n")



if __name__ == "__main__":
    # Forcer l'encodage UTF-8 pour Windows
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Token utilisateur (passé par le backend ou dans .env)
    # IMPORTANT: Récupérer AVANT load_dotenv() pour que le backend puisse le passer
    USER_TOKEN = os.getenv("USER_TOKEN", "")
    
    # Si pas de token dans l'environnement, charger depuis .env local
    if not USER_TOKEN:
        from dotenv import load_dotenv
        load_dotenv()
        USER_TOKEN = os.getenv("USER_TOKEN", "")
    
    if not USER_TOKEN:
        print("WARNING: USER_TOKEN non défini dans .env")
        print("    L'agent va analyser les factures mais ne les enverra pas au backend.")
        print("    Pour activer l'envoi, ajoutez USER_TOKEN=votre_token dans .env\n")
    
    mails = recup_mail("inbox")
    for mail in mails:
        print(f"\nMail de {mail['from']} reçu le {mail['date']}")
        for att in mail["attachments"]:
            print(f"  - Pièce jointe : {att['filename']}")
            
            # Préparer le texte de la facture
            invoice_text = prepare_invoice_text(att)
            print("    Analyse en cours...")
            
            # Analyser avec LLM
            analysis = analyze_text(invoice_text)
            
            if analysis:
                print("    [OK] Analyse terminee")
                print(f"       Facture: {analysis.get('invoice_number')}")
                print(f"       Montant TTC: {analysis.get('amounts', {}).get('ttc')} EUR")
                
                # Envoyer au backend si token disponible
                if USER_TOKEN:
                    pdf_path = f"temp/{att['filename']}"
                    result = send_invoice_to_backend(
                        pdf_path=pdf_path,
                        analysis_data=analysis,
                        email_id=mail['id'],
                        email_subject=mail['subject'],
                        user_token=USER_TOKEN
                    )
                    
                    if result:
                        print(f"       [UPLOAD] Envoyee au backend (ID: {result.get('id')})")
                    
                    # Nettoyer le fichier temp après envoi
                    try:
                        os.remove(pdf_path)
                        print(f"       [CLEAN] Fichier temp supprime")
                    except:
                        pass
                else:
                    print("       [WARNING] Non envoyee (pas de token)")
            else:
                print("    [ERROR] Analyse echouee")
            
            time.sleep(2)  # Pour éviter de surcharger l'API
        