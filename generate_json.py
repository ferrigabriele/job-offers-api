import requests
import pandas as pd
from io import BytesIO
import os
import json
import numpy as np

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
FILE_URL = "https://docs.google.com/spreadsheets/d/1eg4h5A0ToocKoMhOnEeSDa97IXMwY0hb/export?format=xlsx"
OUTPUT_PATH_FULL = "data/data.json"
OUTPUT_PATH_MIN = "data/data_min.json"
OUTPUT_PATH_PUBLISHED = "data/data_published.json"

# Debug
DEBUG = True
# Se l'Excel ha più fogli e l'ordine cambia, imposta qui il nome ESATTO del foglio corretto.
# Esempio: FORCE_SHEET_NAME = "PreselezioniAttive"
FORCE_SHEET_NAME = None

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def download_excel(url: str) -> BytesIO:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return BytesIO(response.content)


def _normalize_colname(c) -> str:
    """Normalizza i nomi colonna per gestire piccoli cambi (spazi, newline, NBSP, ecc.)."""
    if c is None:
        return ""
    c = str(c)
    c = c.replace("\u00a0", " ")  # NBSP
    c = c.replace("\n", " ").replace("\t", " ")
    c = " ".join(c.split())
    return c.strip()


def _find_header_row(excel_bytes: BytesIO, probe_rows: int = 40) -> int:
    """Trova dinamicamente la riga header cercando ID_Richiesta (o varianti)."""
    excel_bytes.seek(0)
    raw = pd.read_excel(excel_bytes, header=None, nrows=probe_rows)

    targets = {"id_richiesta", "id richiesta", "idrichiesta"}
    for i in range(len(raw)):
        row = raw.iloc[i].astype(str).values
        for v in row:
            s = _normalize_colname(v).lower()
            if s in targets:
                return i
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
        "Modo evasione richiesta": "ModoEvasioneRichiesta",
        "Modo Evasione Richiesta": "ModoEvasioneRichiesta",
        "Modo evasione Richiesta": "ModoEvasioneRichiesta",
        "CategoriaRiserva": "CategoriaRiserva",
        "Categoria Riserva": "CategoriaRiserva",
        "Categoria riserva": "CategoriaRiserva",
    }

    renamed = {}
    for c in df.columns:
        cn = _normalize_colname(c)
        renamed[c] = aliases.get(cn, cn)

    return df.rename(columns=renamed)


def _debug_print_columns(df: pd.DataFrame):
    if not DEBUG:
        return
    cols = list(df.columns)
    print("DEBUG | Numero colonne:", len(cols))
    print("DEBUG | Prime 50 colonne:", cols[:50])
    # Mostra SOLO quelle che contengono 'Categoria' per diagnosi rapida
    categoria_cols = [c for c in cols if "categoria" in str(c).lower()]
    print("DEBUG | Colonne che contengono 'Categoria':", [repr(c) for c in categoria_cols])
    print("DEBUG | Ha CategoriaRiserva?:", "CategoriaRiserva" in cols)
    # Gestione eventuali duplicati / suffissi .1
    similari = [c for c in cols if str(c).startswith("CategoriaRiserva")]
    if similari:
        print("DEBUG | Colonne che iniziano con 'CategoriaRiserva':", [repr(c) for c in similari])


def _pick_categoria_riserva_column(df: pd.DataFrame) -> str | None:
    """Sceglie la colonna da usare per la riserva.

    Preferenza:
    1) 'CategoriaRiserva' esatta
    2) una colonna che inizia con 'CategoriaRiserva' (es. duplicati o header strani)
    3) una colonna che contiene entrambe le parole 'Categoria' e 'Riserva'
    """
    cols = list(df.columns)
    if "CategoriaRiserva" in cols:
        return "CategoriaRiserva"

    starts = [c for c in cols if str(c).startswith("CategoriaRiserva")]
    if starts:
        # se c'è 'CategoriaRiserva.1' preferiamo comunque la prima
        return starts[0]

    contains = [c for c in cols if ("categoria" in str(c).lower() and "riserva" in str(c).lower())]
    if contains:
        return contains[0]

    return None


def _map_riserva(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    s = str(v).strip()
    if not s or s.lower() in {"nan", "none"}:
        return None

    sl = s.lower()

    # Caso "entrambi"
    if "entrambi" in sl or ("art 1" in sl and "art 18" in sl):
        return "Disabili art 1 Legge 68/99; Categorie protette art 18 Legge 68/99"
    if "art 1" in sl:
        return "Disabili art 1 Legge 68/99"
    if "art 18" in sl:
        return "Categorie protette art 18 Legge 68/99"

    return s


# ---------------------------------------------------------------------------
# CORE
# ---------------------------------------------------------------------------

def convert_excel_to_json(excel_bytes: BytesIO):
    # 1) Header row detection + sheet selection
    header_row = _find_header_row(excel_bytes)

    excel_bytes.seek(0)
    xl = pd.ExcelFile(excel_bytes)

    if DEBUG:
        print("DEBUG | Sheets disponibili:", xl.sheet_names)
        print("DEBUG | Header row rilevata:", header_row)

    sheet_to_use = FORCE_SHEET_NAME if FORCE_SHEET_NAME else 0
    if DEBUG:
        print("DEBUG | Sheet usato:", sheet_to_use)

    excel_bytes.seek(0)
    df = pd.read_excel(excel_bytes, header=header_row, sheet_name=sheet_to_use)

    # 2) Pulizia base
    df.columns = [_normalize_colname(c) for c in df.columns]
    df.dropna(how="all", inplace=True)
    df = _apply_column_aliases(df)

    if DEBUG:
        _debug_print_columns(df)

    # 3) Filtri di business
    if "TipoPreselezione" in df.columns:
        before = len(df)
        df = df[df["TipoPreselezione"].astype(str).str.strip() == "Standard"]
        if DEBUG:
            print("DEBUG | Filtro TipoPreselezione=Standard:", before, "->", len(df))
    else:
        if DEBUG:
            print("DEBUG | ATTENZIONE: colonna TipoPreselezione non trovata")

    # 3b) Anonimizzazione azienda
    if "ModoEvasioneRichiesta" in df.columns and "Azienda" in df.columns:
        mask_anon = (
            df["ModoEvasioneRichiesta"].astype(str).str.strip().str.lower()
            == "pubblicazione anonima con preselezione"
        )
        if DEBUG:
            print("DEBUG | Righe con pubblicazione anonima:", int(mask_anon.sum()))
        df.loc[mask_anon, "Azienda"] = "Azienda riservata"
    else:
        if DEBUG:
            print("DEBUG | INFO: non posso anonimizzare (manca ModoEvasioneRichiesta o Azienda)")

    # 4) Date + ISO
    for col in ["DataInserimento", "DataScadenza"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df[f"{col}ISO"] = df[col].dt.strftime("%Y-%m-%d")
            df[col] = df[col].dt.strftime("%d/%m/%Y")
        else:
            if DEBUG:
                print(f"DEBUG | INFO: colonna {col} non trovata")

    if "DataInserimentoISO" in df.columns:
        df.sort_values(by="DataInserimentoISO", ascending=False, inplace=True)

    # 5) Preselezione Riservata (da CategoriaRiserva)
    categoria_col = _pick_categoria_riserva_column(df)
    if DEBUG:
        print("DEBUG | Colonna scelta per riserva:", categoria_col)

    if categoria_col:
        df["Preselezione Riservata"] = df[categoria_col].apply(_map_riserva)
        if DEBUG:
            # esempi (prime 10 righe)
            cols_to_show = [categoria_col, "Preselezione Riservata"] if categoria_col in df.columns else ["Preselezione Riservata"]
            print("DEBUG | Esempi riserva (prime 10):", df[cols_to_show].head(10).to_dict(orient="records"))
    else:
        if DEBUG:
            print("DEBUG | ATTENZIONE: nessuna colonna CategoriaRiserva trovata (o equivalente)")

    # 6) Selezione campi di output
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
        "Preselezione Riservata",
        "DataInserimentoISO",
        "DataScadenzaISO",
        "LinkPubblicazioneOfferta",
    ]

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

    if DEBUG:
        if cleaned_data:
            print("DEBUG | Campi del primo record JSON:", list(cleaned_data[0].keys()))
        else:
            print("DEBUG | NESSUNA OFFERTA in output")

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
            "versione": "debug",
            "ultimo_aggiornamento": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "avviso": "⚠️ Questo file JSON è generato a scopo di test/debug. I dati non sono ufficiali e possono contenere errori o essere incompleti. Usare solo per prototipazione tecnica interna.",
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
