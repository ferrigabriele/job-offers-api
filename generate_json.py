import requests
import pandas as pd
from io import BytesIO
import os
import json

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

    # Converte le date nel formato GG/MM/AAAA
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%d/%m/%Y')

    # Converte NaN in None per avere JSON valido (null)
    return df.where(pd.notnull(df), None).to_dict(orient='records')

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
