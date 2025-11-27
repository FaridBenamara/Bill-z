from playwright.sync_api import sync_playwright
import os
import glob

def convert_html_to_pdf(html_path, pdf_path):
    """
    Convertit un fichier HTML en PDF en tenant tout sur une seule page A4,
    avec redimensionnement automatique si nécessaire.
    """
    try:
        html_abs = os.path.abspath(html_path).replace("\\", "/")
        file_url = f"file:///{html_abs}"

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            # Charger la page HTML
            page.goto(file_url)
            page.wait_for_load_state("networkidle")

            # Ajustement global du contenu pour tenir sur une seule page
            page.add_style_tag(content="""
                body {
                    margin: 0;
                    padding: 0;
                    transform-origin: top left;
                }
            """)

            # Récupérer la taille réelle du contenu
            content_height = page.evaluate("document.body.scrollHeight")

            # Taille max en pixels pour une page A4 (≈ 1122px à 96dpi)
            max_height_px = 1122

            # Calcul du facteur d'échelle
            scale = min(1, max_height_px / content_height)

            # Générer le PDF
            page.pdf(
                path=pdf_path,
                format="A4",
                print_background=True,
                scale=scale,
                margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"},
            )

            browser.close()

        print(f"PDF généré : {pdf_path}")
        return True

    except Exception as e:
        print(f"Erreur lors de la conversion : {e}")
        return False


def convert_all_html_to_pdf(input_dir="data/generated_invoices", output_dir="data/generated_invoices_pdf"):
    os.makedirs(output_dir, exist_ok=True)

    html_files = glob.glob(os.path.join(input_dir, "*.html"))
    if not html_files:
        print("Aucun fichier HTML trouvé.")
        return

    for html in html_files:
        filename = os.path.basename(html).replace(".html", ".pdf")
        pdf_path = os.path.join(output_dir, filename)
        convert_html_to_pdf(html, pdf_path)

    print("Conversion terminée !")


if __name__ == "__main__":
    convert_all_html_to_pdf()
