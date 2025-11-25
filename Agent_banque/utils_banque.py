import pandas as pd
from pathlib import Path

def lire_xlsx_en_liste_de_dicos(chemin_fichier):
    df = pd.read_excel(chemin_fichier)
    return df.to_dict(orient="records")

def read_file(path: str | Path) -> str | None:
    try:
        with open(path, 'r', encoding='utf-8') as fp:
            return fp.read()
    except Exception as e:
        print(f"[ERREUR] Impossible de lire {path} : {e}")
        return None   



if __name__ == "__main__":
    releve_path = "releve_bancaire_08-2017.xlsx"
    liste_transactions = lire_xlsx_en_liste_de_dicos(releve_path)
    print(liste_transactions)