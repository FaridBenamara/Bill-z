import json
from utils_banque import lire_xlsx_en_liste_de_dicos, read_file
from groq import Groq
from config_banque import GROQ_API_KEY, MODEL_NAME_analyse


def load_prompt_and_context(invoice_json, releve_bancaire, context_file, prompt_file) -> tuple[str, str]:
    """Charge le contexte et remplace le placeholder dans le prompt."""
    context = read_file(context_file)
    prompt_template = read_file(prompt_file)

    if not context or not prompt_template:
        raise ValueError("Impossible de charger context.txt ou prompt.txt")

    prompt = prompt_template.replace("{{facture_json}}", invoice_json).replace("{{releve_bancaire}}", releve_bancaire)
    return context, prompt



    

def rapprochement(invoice_json, releve_bancaire, context_file, prompt_file) -> dict | None:
    """Appelle l'API GROQ pour analyser le code Python."""
    if not GROQ_API_KEY:
        print("[ERREUR] GROQ_API_KEY n'est pas défini.")
        return None


    context, prompt = load_prompt_and_context(invoice_json, releve_bancaire, context_file, prompt_file)

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



def afficher_rapprochement(resultat):

    facture = resultat.get("facture", {})

    print("\n=== RAPPROCHEMENT ===")

    print("\n📄 Facture")
    print(f"  • Fournisseur : {facture.get('fournisseur')}")
    print(f"  • Montant TTC : {facture.get('montant_ttc')} {facture.get('devise')}")
    print(f"  • Date : {facture.get('date')}")

    print("\n🔎 Correspondance trouvée :", resultat.get("correspondance_trouvee"))

    print("\n📌 Lignes correspondantes :")
    lignes = resultat.get("lignes_correspondantes", [])

    if lignes:
        for i, ligne in enumerate(lignes, 1):
            print(f"\n   —— Ligne {i} ——")
            print(f"   • Date relevé : {ligne.get('date')}")
            print(f"   • Montant : {ligne.get('amount')} {ligne.get('currency')}")
            print(f"   • Vendor : {ligne.get('vendor')}")
            print(f"   • Similarité fournisseur : {ligne.get('similarite_fournisseur')}")
            print(f"   • Différences : {', '.join(ligne.get('differences', []))}")

            details = ligne.get("details_differences", {})
            print("   • Détails des différences :")
            print(f"       - Montant facture : {details.get('montant_facture')}")
            print(f"       - Montant relevé : {details.get('montant_releve')}")
            print(f"       - Écart montant : {details.get('ecart_montant')}")
            print(f"       - Devise facture : {details.get('devise_facture')}")
            print(f"       - Devise relevé : {details.get('devise_releve')}")
            print(f"       - Date facture : {details.get('date_facture')}")
            print(f"       - Date relevé : {details.get('date_releve')}")
            print(f"   • Niveau de confiance : {ligne.get('niveau_confiance')}")

    else:
        print("   Aucune ligne correspondante.")

    print("\n🏁 Conclusion :")
    print(" ", resultat.get("conclusion"))
    print("\n")



if __name__ == "__main__":
    releve_bancaire = lire_xlsx_en_liste_de_dicos("releve_bancaire_08-2017.xlsx")
    invoice_json = read_file("invoice_sample.json")
    result = rapprochement(invoice_json, json.dumps(releve_bancaire))
    print(result)

