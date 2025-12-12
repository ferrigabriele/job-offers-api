import requests
import pandas as pd
from io import BytesIO
import os
import json
import numpy as np

FILE_URL = "https://docs.google.com/spreadsheets/d/1eg4h5A0ToocKoMhOnEeSDa97IXMwY0hb/export?format=xlsx"
OUTPUT_PATH_FULL = "data/data.json"
OUTPUT_PATH_MIN = "data/data_min.json"
OUTPUT_PATH_PUBLISHED = "data/data_published.json"

# --- Helpers ---------------------------------------------------------------

def download_excel(url: str) -> BytesIO:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return BytesIO(response.content)


def _normalize_colname(c) -> str:
    """Normalizza i nomi colonna per gestire piccoli cambi (spazi, newline, ecc.)."""
    if c is None:
        return ""
    c = str(c)
    c = c.replace("\n", " ").replace("\t", " ")
    c = " ".join(c.split())
    return c.strip()


def _find_header_row(excel_bytes: BytesIO, probe_rows: int = 20) -> int:
    """Trova dinamicamente la riga header cercando il campo ID_Richiesta.

    L'Excel può avere 1+ righe "di titolo" sopra la tabella.
    """
    excel_bytes.seek(0)
    raw = pd.read_excel(excel_bytes, header=None, nrows=probe_rows)

    # Cerca nelle prime colonne una cella esattamente uguale a ID_Richiesta
    for i in range(len(raw)):
        row = raw.iloc[i].astype(str)
        if any(_normalize_colname(v) == "ID_Richiesta" for v in row.values):
            return i

    # Fallback: se non trovato, usa la prima riga (comportamento precedente)
    return 0


def _apply_column_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Applica alias per gestire rinominazioni frequenti."""
    aliases = {
        "ID Richiesta": "ID_Richiesta",
        "ID richiesta": "ID_Richiesta",
        "Id_Richiesta": "ID_Richiesta",
        "Comune Sede Lavoro": "ComuneSedeLavoro",
        "Comune sede lavoro": "ComuneSedeLavoro",
        "N. lavoratori richiesti": "NumeroLavoratoriRichiesti",
        "Numero lavoratori richiesti": "NumeroLavoratoriRichiesti",
        "Link pubblicazione offerta": "LinkPubblicazioneOfferta",
        "Link Pubblicazione Offerta": "LinkPubblicazioneOfferta",
    }

    renamed = {}
    for c in df.columns:
        cn = _normalize_colname(c)
        renamed[c] = aliases.get(cn, cn)

    df = df.rename(columns=renamed)
    return df


def convert_excel_to_json(excel_bytes: BytesIO):
    # 1) Trova header row e rileggi il file con header corretto
    header_row = _find_header_row(excel_bytes)

    excel_bytes.seek(0)
    df = pd.read_excel(excel_bytes, header=header_row)

    # 2) Pulizia base
    df.columns = [_normalize_colname(c) for c in df.columns]
    df.dropna(how="all", inplace=True)
    df = _apply_column_aliases(df)

    # 3) Filtri di business (come in versione precedente)
    if "TipoPreselezione" in df.columns:
        df = df[df["TipoPreselezione"].astype(str).str.strip() == "Standard"]

    # 4) Date + ISO
    for col in ["DataInserimento", "DataScadenza"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df[f"{col}ISO"] = df[col].dt.strftime("%Y-%m-%d")
            df[col] = df[col].dt.strftime("%d/%m/%Y")

    if "DataInserimentoISO" in df.columns:
        df.sort_values(by="DataInserimentoISO", ascending=False, inplace=True)

    # 5) Derivazioni riservatezza (compatibile con versioni precedenti)
    if "PreselezioneRiservata" in df.columns:
        df["PreselezioneRiservataDiversamenteAbili"] = df["PreselezioneRiservata"].apply(
            lambda x: "SI" if isinstance(x, str) and "art 1" in x.lower() else "NO"
        )
        df["PreselezioneRiservataCategorieProtette"] = df["PreselezioneRiservata"].apply(
            lambda x: "SI" if isinstance(x, str) and "art 18" in x.lower() else "NO"
        )

    # 6) Selezione campi di output (come prima)
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
        "LinkPubblicazioneOfferta",
    ]

    # (mantiene solo i campi presenti per non rompersi se qualcosa manca)
    df = df[[c for c in campi_finali if c in df.columns]]

    # 7) Serializzazione pulita (NaN -> None)
    data = df.to_dict(orient="records")
    cleaned_data = [
        {
            k: (None if (pd.isna(v) or (isinstance(v, float) and np.isnan(v))) else v)
            for k, v in row.items()
        }
        for row in data
    ]
    return cleaned_data


def convert_minimal_json(data):
    offerte_con_link = [o for o in data if o.get("LinkPubblicazioneOfferta")]
    return offerte_con_link[:60]


def convert_published_json(data):
    return [o for o in data if o.get("LinkPubblicazioneOfferta")]


def save_json(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    json_finale = {
        "meta": {
            "progetto": "SOFIA - Prototipo di assistente virtuale per i Centri per l’Impiego",
            "versione": "test",
            "ultimo_aggiornamento": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "avviso": "⚠️ Questo file JSON è generato a scopo di test. I dati non sono ufficiali e possono contenere errori o essere incompleti. Usare solo per prototipazione tecnica interna.",
        },
        "offerte": data,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_finale, f, ensure_ascii=False, indent=2)


def main():
    print("📥 Scarico il file Excel da Google Drive...")
    excel_file = download_excel(FILE_URL)

    print("📊 Converto in JSON...")
    json_data_full = convert_excel_to_json(excel_file)

    print(f"📀 Salvo in {OUTPUT_PATH_FULL}...")
    save_json(json_data_full, OUTPUT_PATH_FULL)

    print("📊 Creo anche la versione ridotta...")
    json_data_min = convert_minimal_json(json_data_full)
    print(f"📀 Salvo in {OUTPUT_PATH_MIN}...")
    save_json(json_data_min, OUTPUT_PATH_MIN)

    print("📊 Creo anche la versione pubblicata...")
    json_data_published = convert_published_json(json_data_full)
    print(f"📀 Salvo in {OUTPUT_PATH_PUBLISHED}...")
    save_json(json_data_published, OUTPUT_PATH_PUBLISHED)

    print("✅ Completato.")


if __name__ == "__main__":
    main()
