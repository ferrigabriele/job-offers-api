import requests
import pandas as pd
from io import BytesIO
import os
import json
import numpy as np

FILE_URL = "https://docs.google.com/spreadsheets/d/1eg4h5A0ToocKoMhOnEeSDa97IXMwY0hb/export?format=xlsx"
OUTPUT_PATH_FULL = "data/data.json"
OUTPUT_PATH_MIN = "data/data_min.json"

def download_excel(url):
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)

def convert_excel_to_json(excel_bytes):
    df = pd.read_excel(excel_bytes)
    df.dropna(how='all', inplace=True)

    if "TipoPreselezione" in df.columns:
        df = df[df["TipoPreselezione"] == "Standard"]

    for col in ["DataInserimento", "DataScadenza"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df[f"{col}ISO"] = df[col].dt.strftime('%Y-%m-%d')
            df[col] = df[col].dt.strftime('%d/%m/%Y')

    if "DataInserimentoISO" in df.columns:
        df.sort_values(by="DataInserimentoISO", ascending=False, inplace=True)

    campi_finali = [
        "CPI",
        "ID_Richiesta",
        "DataInserimento",
        "DataScadenza",
        "Azienda",
        "NumeroLavoratoriRichiesti",
        "Qualifica",
        "Mansioni",
        "ComuneSedeLavoro",
        "TipoContratto",
        "PreselezioneRiservataDiversamenteAbili",
        "PreselezioneRiservataCategorieProtette",
        "DataInserimentoISO",
        "DataScadenzaISO",
        "LinkPubblicazioneOfferta"
    ]
    df = df[[col for col in campi_finali if col in df.columns]]

    data = df.to_dict(orient='records')
    cleaned_data = [
        {k: (None if pd.isna(v) or isinstance(v, float) and np.isnan(v) else v) for k, v in row.items()}
        for row in data
    ]

    return cleaned_data

def convert_minimal_json(data):
    offerte_con_link = [o for o in data if o.get("LinkPubblicazioneOfferta")]
    return offerte_con_link[:60]

def save_json(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    json_finale = {
        "meta": {
            "progetto": "SOFIA - Prototipo di assistente virtuale per i Centri per l’Impiego",
            "versione": "test",
            "ultimo_aggiornamento": pd.Timestamp.now().strftime('%Y-%m-%d'),
            "avviso": "⚠️ Questo file JSON è generato a scopo di test. I dati non sono ufficiali e possono contenere errori o essere incompleti. Usare solo per prototipazione tecnica interna."
        },
        "offerte": data
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_finale, f, ensure_ascii=False, indent=2)

def main():
    print("📥 Scarico il file Excel da Google Drive...")
    excel_file = download_excel(FILE_URL)

    print("📊 Converto in JSON...")
    json_data_full = convert_excel_to_json(excel_file)

    print(f"💾 Salvo in {OUTPUT_PATH_FULL}...")
    save_json(json_data_full, OUTPUT_PATH_FULL)

    print("📊 Creo anche la versione ridotta...")
    json_data_min = convert_minimal_json(json_data_full)
    print(f"💾 Salvo in {OUTPUT_PATH_MIN}...")
    save_json(json_data_min, OUTPUT_PATH_MIN)

    print("✅ Completato.")

if __name__ == "__main__":
    main()
