"""
Génère un relevé bancaire simple :
- chaque ligne du CSV devient une opération dans le relevé
- les champs du template sont remplis avec des valeurs fixes

Usage :
    python generate_statement.py \
        --csv data/releve_bancaire_08-2017.xlsx \
        --output data/generated_statements/releve_aout_2017.html
"""

import argparse
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype
from jinja2 import Template

from html_to_pdf import convert_html_to_pdf

DEFAULT_CSV = "data/releve_bancaire_08-2017.xlsx"
DEFAULT_TEMPLATE = "data/html_template/relevee1.html"
OUTPUT_DIR = "data/generated_statements"


def read_template(path: str) -> Template:
    with open(path, "r", encoding="utf-8") as f:
        return Template(f.read())


DATE_COLUMN_CANDIDATES = [
    "date",
    "transaction_date",
    "date_transaction",
    "dateoperation",
    "operation_date",
    "date opé",
    "date opération",
]


def detect_date_column(df: pd.DataFrame) -> Optional[str]:
    columns = list(df.columns)
    for candidate in DATE_COLUMN_CANDIDATES:
        if candidate in columns:
            return candidate
    for column in columns:
        if "date" in column:
            return column
    return None


def read_csv(path: str) -> pd.DataFrame:
    if path.endswith(".xlsx"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    df = df.rename(columns=str.lower)

    date_column = detect_date_column(df)
    if date_column:
        date_series = df[date_column]
        if not is_datetime64_any_dtype(date_series):
            cleaned = (
                date_series.astype(str)
                .str.replace(r"[\u202a\u202c]", "", regex=True)
                .str.strip()
            )
            cleaned = cleaned.replace({"": pd.NA, "nan": pd.NA, "NaT": pd.NA})
            date_series = pd.to_datetime(
                cleaned,
                errors="coerce",
                dayfirst=False,
            )
        df["date"] = date_series
        df = df.sort_values("date", na_position="last")
    else:
        df["date"] = pd.NaT  # keep column to avoid template errors

    return df


def format_currency(value: float) -> str:
    return f"{value:,.2f} €".replace(",", " ").replace(".", ",")


def format_date(value) -> str:
    if value is None or pd.isna(value):
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    try:
        dt = pd.to_datetime(value)
        if pd.isna(dt):
            return "-"
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(value)


def build_operations(df: pd.DataFrame, opening_balance: float) -> Tuple[List[Dict], float]:
    balance = opening_balance
    operations = []

    for _, row in df.iterrows():
        amount = float(row.get("amount", 0))
        vendor = str(row.get("vendor", "Opération"))
        source = row.get("source", "")
        date_str = format_date(row.get("date"))

        balance += amount

        op_label = vendor.strip()
        if not op_label:
            op_label = "OPÉRATION"

        operations.append({
            "date": date_str,
            "label": op_label.upper(),
            "debit": format_currency(abs(amount)) if amount < 0 else "–",
            "credit": format_currency(amount) if amount > 0 else "–",
            "balance": format_currency(balance)
        })

    return operations, balance


def render_statement(csv_path: str,
                     template_path: str,
                     output_html: str,
                     opening_balance: float = 0.0) -> str:
    template = read_template(template_path)
    df = read_csv(csv_path)

    operations, closing_balance = build_operations(df, opening_balance)

    summary = {
        "date_start": format_date(df["date"].min()) if "date" in df.columns else "",
        "date_end": format_date(df["date"].max()) if "date" in df.columns else "",
        "opening_balance": format_currency(opening_balance),
        "closing_balance": format_currency(closing_balance),
        "total_debits": format_currency(df[df["amount"] < 0]["amount"].sum()),
        "total_credits": format_currency(df[df["amount"] > 0]["amount"].sum()),
    }

    context = {
        "bank": {
            "name": "BANQUE ALT",
            "address": "21 Rue des Financiers",
            "city": "75008 PARIS"
        },
        "statement": {
            "title": "RELEVÉ DE COMPTE",
            "period_start": summary["date_start"],
            "period_end": summary["date_end"],
            "generated_at": datetime.now().strftime("%d/%m/%Y")
        },
        "holder": {
            "name": "ALTEVIA SOLUTIONS",
            "account_number": "0000 0000 0000",
            "address": "12 Rue des Entrepreneurs, 75015 Paris, France",
            "iban": "FR76 3000 3000 0000 0000 0000 123"
        },
        "summary": summary,
        "operations": operations,
        "footer_note": "Document généré automatiquement – relevé bancaire de synthèse"
    }

    os.makedirs(os.path.dirname(output_html), exist_ok=True)
    rendered_html = template.render(**context)
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    return output_html


def main():
    parser = argparse.ArgumentParser(description="Génère un relevé bancaire simple à partir du CSV")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Chemin du CSV/XLSX du relevé")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, help="HTML template à utiliser")
    parser.add_argument("--output", help="Chemin du fichier HTML généré")
    parser.add_argument("--opening-balance", type=float, default=0.0, help="Solde d'ouverture")
    parser.add_argument("--no-pdf", action="store_true", help="Ne pas convertir en PDF")
    args = parser.parse_args()

    output_html = args.output
    if not output_html:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_html = os.path.join(OUTPUT_DIR, "releve_generé.html")

    print("📄 Génération du relevé...")
    html_path = render_statement(
        csv_path=args.csv,
        template_path=args.template,
        output_html=output_html,
        opening_balance=args.opening_balance
    )
    print(f"✓ Relevé HTML généré : {html_path}")

    if not args.no_pdf:
        pdf_path = output_html.replace(".html", ".pdf")
        convert_html_to_pdf(html_path, pdf_path)
        print(f"✓ PDF généré : {pdf_path}")


if __name__ == "__main__":
    main()

