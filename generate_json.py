import requests
import pandas as pd
from io import BytesIO
import os
import json
import numpy as np

FILE_URL = "https://docs.google.com/spreadsheets/d/1eg4h5A0ToocKoMhOnEeSDa97IXMwY0hb/export?format=xlsx"
OUTPUT_PATH = "data/data.json"

def download_excel(url):
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)

def convert_excel_to_json(excel_bytes):
    df = pd.read_excel(excel_bytes)

    # Rimuove righe completamente vuote
    df.dropna(how='all', inplace=True)

    # Converte DataInserimento e DataScadenza in datetime (se esistono)
    for col in ["DataInserimento", "DataScadenza"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

            # Aggiunge colonna ISO (es. DataInserimentoISO)
            df[f"{col}ISO"] = df[col].dt.strftime('%Y-%m-%d')

            # Sovrascrive la colonna originale con formato italiano
            df[col] = df[col].dt.strftime('%d/%m/%Y')

    # Ordina per DataInserimento decrescente (più recenti in alto)
    if "DataInserimentoISO" in df.columns:
        df.sort_values(by="DataInserimentoISO", ascending=False, inplace=True)

    # Sostituisce tutti i NaN con None
    data = df.to_dict(orient='records')
    cleaned_data = [
        {k: (None if pd.isna(v) or isinstance(v, float) and np.isnan(v) else v) for k, v in row.items()}
        for row in data
    ]

    return cleaned_data

def save_json(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    print("📥 Scarico il file Excel da Google Drive...")
    excel_file = download_excel(FILE_URL)

    print("📊 Converto in JSON...")
    json_data = convert_excel_to_json(excel_file)

    print(f"💾 Salvo in {OUTPUT_PATH}...")
    save_json(json_data, OUTPUT_PATH)

    print("✅ Completato.")

if __name__ == "__main__":
    main()
