"""Carga y normalización del universo de bonos corporativos."""
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from fca.config import BONOS_XLSX, CACHE_TTL, DECISION_EXCLUIDA
from fca.data.cleaning import (
    DataError, find_column, normalize_columns, to_date, to_number, to_percent, to_text,
)

# Nombre interno -> encabezados aceptados en el Excel (en orden de preferencia).
COLUMNS = {
    "emisor": ["Guarantor/Organization", "Emisor", "Issuer"],
    "issuer": ["Issuer", "Emisor"],
    "industry": ["Industry", "Industria", "Sector"],
    "segment": ["IG - HY", "IG/HY", "Segmento"],
    "rating": ["Rating", "Calificación"],
    "coupon": ["Coupon %", "Coupon", "Cupón %", "Cupón"],
    "maturity": ["Maturity", "Vencimiento"],
    "price": ["Price", "Precio"],
    "ytw": ["YTW %", "YTW"],
    "ytw_prev": ["Prev month YTW%", "Prev month YTW %", "YTW mes anterior"],
    "ytw_t15": ["YTW% t-15", "YTW % t-15"],
    "gspread": ["Gspread", "G-spread", "G spread"],
    "min_settlement": ["Minimum Settlement", "Mínimo"],
    "outstanding": ["Outstanding US$", "Outstanding"],
    "isin": ["ISIN"],
    "decision": ["Decisión", "Decision", "Recomendados", "Recomendado", "Recomendación", "Recomend"],
}
REQUIRED = ["emisor", "segment", "maturity", "ytw"]
PERCENT = ["coupon", "ytw", "ytw_prev", "ytw_t15"]
NUMERIC = ["price", "gspread", "min_settlement", "outstanding"]
TEXT = ["emisor", "issuer", "industry", "rating", "isin", "decision"]


@dataclass
class BondUniverse:
    df: pd.DataFrame
    avisos: list[str] = field(default_factory=list)
    total_archivo: int = 0

    @property
    def tiene_decision(self) -> bool:
        return "decision" in self.df.columns


def _prepare(raw: pd.DataFrame) -> BondUniverse:
    raw = normalize_columns(raw)
    mapping = {}
    for name, candidates in COLUMNS.items():
        col = find_column(raw, candidates)
        if col is not None and col not in mapping.values():
            mapping[name] = col

    missing = [COLUMNS[n][0] for n in REQUIRED if n not in mapping]
    if missing:
        raise DataError(
            "Faltan columnas en el Excel de bonos: " + ", ".join(missing)
            + ". Columnas encontradas: " + ", ".join(map(str, raw.columns))
        )

    df = pd.DataFrame({name: raw[col] for name, col in mapping.items()})
    avisos = []

    for col in TEXT:
        if col in df:
            df[col] = to_text(df[col])
    if "issuer" not in df:
        df["issuer"] = df["emisor"]
    df["segment"] = to_text(df["segment"]).str.upper()
    df["maturity"] = to_date(df["maturity"])

    for col in PERCENT + NUMERIC:
        if col in df:
            original = df[col]
            df[col] = to_percent(original) if col in PERCENT else to_number(original)
            invalid = int((df[col].isna() & to_text(original.astype("string")).notna()).sum())
            if invalid:
                avisos.append(f"{invalid} valor(es) no numérico(s) en '{mapping[col]}' se dejaron vacíos.")

    total = len(df)
    df = df.dropna(subset=["maturity", "ytw", "emisor"])
    if len(df) < total:
        avisos.append(f"{total - len(df)} fila(s) sin vencimiento, YTW o emisor válidos se omitieron.")

    if "decision" in df:
        df = df[df["decision"].fillna("").str.casefold() != DECISION_EXCLUIDA.casefold()]

    if "ytw_prev" in df:
        df["ytw_change"] = df["ytw"] - df["ytw_prev"]

    df = df.sort_values("maturity").reset_index(drop=True)
    if df.empty:
        raise DataError("El Excel de bonos no tiene filas válidas para mostrar.")
    return BondUniverse(df=df, avisos=avisos, total_archivo=total)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _load_cached(path: str, mtime: float) -> BondUniverse:
    # `mtime` es parte de la clave del caché: si el Excel cambia, se vuelve a leer.
    return _prepare(pd.read_excel(path))


def load_bonds(path: Path = BONOS_XLSX) -> BondUniverse:
    if not path.exists():
        raise DataError(f"No se encontró el archivo de bonos ({path.name}) en la carpeta data/.")
    return _load_cached(str(path), path.stat().st_mtime)


def trend_curve(df: pd.DataFrame, points: int = 120) -> pd.DataFrame:
    """Curva de tendencia cuadrática de YTW contra vencimiento, por segmento."""
    curves = []
    for segment, grp in df.groupby("segment"):
        grp = grp.groupby("maturity", as_index=False)["ytw"].mean()
        if len(grp) < 3:
            continue
        x = grp["maturity"].map(pd.Timestamp.toordinal).to_numpy(dtype=float)
        coefs = np.polyfit(x, grp["ytw"].to_numpy(), 2)
        xs = np.linspace(x.min(), x.max(), points)
        curves.append(pd.DataFrame({
            "maturity": [pd.Timestamp.fromordinal(int(v)) for v in xs],
            "ytw": np.polyval(coefs, xs),
            "segment": segment,
        }))
    return pd.concat(curves, ignore_index=True) if curves else pd.DataFrame(columns=["maturity", "ytw", "segment"])
