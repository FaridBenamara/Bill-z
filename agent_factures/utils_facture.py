import json
from pathlib import Path
import pdfplumber
import os
import base64
from mistralai import Mistral

def read_file(path: str | Path) -> str | None:
    try:
        with open(path, 'r', encoding='utf-8') as fp:
            return fp.read()
    except Exception as e:
        print(f"[ERREUR] Impossible de lire {path} : {e}")
        return None

#############################
#LIRE LES PIECES JOINTES PDF#
#############################
def extract_text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


##########################
#LIRE LE TEXT DANS IMAGES#
##########################
def encode_image_to_base64(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

def extract_text_with_pixtral(image_path, api_key, model):

    if not api_key:
        raise ValueError("Mettez votre MISTRAL_API_KEY dans l'environnement")
    client = Mistral(api_key=api_key)


    b64 = encode_image_to_base64(image_path)
    image_payload = f"data:image/jpeg;base64,{b64}"
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract all text from this image:"},
                {"type": "image_url", "image_url": image_payload}
            ]
        }
    ]

    response = client.chat.complete(
        model=model,
        messages=messages,
    )

    return response.choices[0].message.content



if __name__ == "__main__":
    chemin_image = "chemin/vers/votre/image.jpg"
    api_key = "jzUtiaC0wNqmsC5KUJs7BvGhK7xPU9Jy"
    model = "pixtral-12b-latest"
    texte = extract_text_with_pixtral(chemin_image, api_key, model)
    print("Texte extrait :")
    print(texte)

