"""Carga de ETFs de renta fija."""
from pathlib import Path

import pandas as pd
import streamlit as st

from fca.config import CACHE_TTL, ETFS_XLSX
from fca.data.cleaning import DataError, find_column, normalize_columns, to_number, to_percent, to_text

COLUMNS = {
    "ticker": ["Ticker"],
    "tipo": ["Duration", "Tipo"],
    "segment": ["IG/HY", "IG - HY", "Segmento"],
    "vto": ["Vto", "Vencimiento", "Maturity"],
    "ter": ["TER"],
    "ytw": ["YTW", "YTW %"],
    "link": ["Link", "URL"],
}


def _prepare(raw: pd.DataFrame) -> pd.DataFrame:
    raw = normalize_columns(raw)
    mapping = {n: c for n, cands in COLUMNS.items() if (c := find_column(raw, cands)) is not None}
    if "ticker" not in mapping:
        raise DataError("El Excel de ETFs no tiene la columna 'Ticker'.")

    df = pd.DataFrame({n: raw[c] for n, c in mapping.items()})
    for col in ("ticker", "tipo", "segment", "link"):
        if col in df:
            df[col] = to_text(df[col])
    if "segment" in df:
        df["segment"] = df["segment"].str.upper()
    if "vto" in df:
        df["vto"] = to_number(df["vto"]).astype("Int64")
    for col in ("ter", "ytw"):
        if col in df:
            df[col] = to_percent(df[col])
    if "link" in df:
        # Solo se muestran enlaces web; cualquier otro esquema (javascript:, file:) se descarta.
        df["link"] = df["link"].where(df["link"].str.match(r"^https?://", na=False))
    return df.dropna(subset=["ticker"]).reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _load_cached(path: str, mtime: float) -> pd.DataFrame:
    return _prepare(pd.read_excel(path))


def load_etfs(path: Path = ETFS_XLSX) -> pd.DataFrame:
    if not path.exists():
        raise DataError(f"No se encontró el archivo de ETFs ({path.name}) en la carpeta data/.")
    return _load_cached(str(path), path.stat().st_mtime)
