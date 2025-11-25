from __future__ import print_function
import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from utils_facture import extract_text_from_pdf
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def recup_mail(folder):
    """
    Récupère tous les emails INBOX ou SENT avec pièces jointes.
    Gère la pagination (nextPageToken) pour dépasser la limite des 100 mails.
    """
    import os, base64
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    creds = None

    # Chargement du token OAuth existant
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Authentification si besoin
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Connexion à Gmail
    service = build('gmail', 'v1', credentials=creds)

    # Label cible
    label = "INBOX" if folder == "inbox" else "SENT"

    # --- Récupération de tous les messages avec pagination ---
    all_messages = []
    next_page = None

    while True:
        query = service.users().messages().list(
            userId='me',
            labelIds=[label],
            pageToken=next_page,
            maxResults=100
        ).execute()

        msgs = query.get('messages', [])
        all_messages.extend(msgs)

        next_page = query.get('nextPageToken')
        if not next_page:
            break

    mails = []

    for msg in all_messages:
        msg_id = msg["id"]

        # Récupération du message complet
        data = service.users().messages().get(
            userId='me', id=msg_id, format="full"
        ).execute()

        headers = data.get("payload", {}).get("headers", [])

        get_header = lambda name: next(
            (h["value"] for h in headers if h["name"] == name), ""
        )

        subject = get_header("Subject")

        payload = data.get("payload", {})
        attachments = []

        # Fonction interne pour analyser les parties récursivement
        def explore_parts(parts_list):
            for part in parts_list:
                filename = part.get("filename")
                if filename:
                    body = part.get("body", {})
                    att_id = body.get("attachmentId")
                    if att_id:
                        att = service.users().messages().attachments().get(
                            userId='me',
                            messageId=msg_id,
                            id=att_id
                        ).execute()

                        file_data = base64.urlsafe_b64decode(att["data"])
                        attachments.append({
                            "filename": filename,
                            "data": file_data
                        })

                if part.get("parts"):
                    explore_parts(part["parts"])

        if payload.get("parts"):
            explore_parts(payload["parts"])

        mails.append({
            "id": msg_id,
            "from": get_header("From"),
            "subject": subject,
            "date": get_header("Date"),
            "attachments": attachments
        })

    return mails




#############################
#LIRE LES PIECES JOINTES PDF#
#############################
def lire_pieces_jointes_pdf(mail, output_folder="pdfs"):
    os.makedirs(output_folder, exist_ok=True)
    textes_pdf = []  # → pour retourner les textes si besoin

    for att in mail["attachments"]:
        filename = att["filename"]

        # On cible uniquement les PDF
        if filename.lower().endswith(".pdf"):
            path = os.path.join(output_folder, filename)

            # Sauvegarde du PDF
            with open(path, "wb") as f:
                f.write(att["data"])
            print(f"\t📁 PDF enregistré : {path}")

            # Lecture du PDF
            texte = extract_text_from_pdf(path)
            textes_pdf.append((filename, texte))

            # Affichage
            print(f"\n\t📄 Contenu de {filename} :\n")
            print(texte)
            print("\n" + "-"*50 + "\n")

    return textes_pdf

def print_mails(mails):
    for i, mail in enumerate(mails, start=1):
        print(f"Mail numéro {i}")
        print(f"\tFROM    : {mail['from']}")
        print(f"\tDATE    : {mail['date']}")

        if mail["attachments"]:
            print("\t📎 Pièces jointes :")
            for att in mail["attachments"]:
                print(f"\t\t- {att['filename']}")

            # 🔥 Lire automatiquement les PDF
            lire_pieces_jointes_pdf(mail)

        else:
            print("\tAucune pièce jointe.")

        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    print("📥 INBOX :")
    inbox = recup_mail("inbox")
    print_mails(inbox)

    print("\n📤 SENT :")
    sent = recup_mail("sent")
    print_mails(sent)
