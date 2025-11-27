"""
Envoie en série tous les PDF d'un dossier via Gmail.

Usage :
    python send_all_pdfs.py \
        --dir data/generated_invoices_pdf \
        --to fareshafiane20@gmail.com \
        --sleep 2
"""

import argparse
import glob
import os
import time

from mail_management import send_mail_with_attachment

DEFAULT_TARGET_EMAIL = "fareshafiane20@gmail.com"


def main():
    parser = argparse.ArgumentParser(description="Envoie tous les PDF d'un dossier par email.")
    parser.add_argument(
        "--dir",
        default="data/generated_invoices_pdf",
        help="Dossier contenant les PDF à envoyer",
    )
    parser.add_argument(
        "--to",
        default=DEFAULT_RECIPIENT,
        help=f"Adresse email destinataire (défaut : {DEFAULT_RECIPIENT})",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=2.0,
        help="Pause (en secondes) entre chaque envoi pour éviter le rate limit",
    )
    args = parser.parse_args()

    pdf_dir = args.dir
    recipient = args.to
    pause = max(args.sleep, 0)

    pdf_files = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))
    if not pdf_files:
        print(f"⚠ Aucun PDF trouvé dans {pdf_dir}")
        return

    print(f"📬 Envoi de {len(pdf_files)} PDF à {recipient} ...")
    sent = 0

    for index, pdf_path in enumerate(pdf_files, start=1):
        filename = os.path.basename(pdf_path)
        invoice_number = filename.replace("facture_", "").replace(".pdf", "")

        subject = f"Facture {invoice_number}"
        body = (
            f"Bonjour,\n\nVeuillez trouver ci-joint la facture {invoice_number}.\n\n"
            f"Cordialement,\nAltevia Solutions"
        )

        try:
            print(f"  [{index}/{len(pdf_files)}] Envoi de {filename} ...", end=" ")
            send_mail_with_attachment(subject, body, recipient, pdf_path)
            sent += 1
            print("✓")
            if pause > 0 and index < len(pdf_files):
                time.sleep(pause)
        except Exception as e:
            print(f"✗ Erreur : {e}")

    print(f"\n✓ {sent}/{len(pdf_files)} emails envoyés.")


if __name__ == "__main__":
    main()

