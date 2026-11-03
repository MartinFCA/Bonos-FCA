"""Limpieza tolerante a datos cargados a mano en Excel.

Funciones puras (sin Streamlit) para poder reutilizarlas el día que los datos
vengan de una base de datos o una API en vez de un Excel.
"""
import re
import unicodedata

import pandas as pd


class DataError(Exception):
    """Error de datos con un mensaje apto para mostrarle al usuario."""


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Unifica encabezados: Unicode NFC, sin saltos de línea ni espacios dobles."""
    df = df.copy()
    df.columns = [
        re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(c))).strip()
        for c in df.columns
    ]
    return df


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Devuelve la primera columna que coincida (sin distinguir mayúsculas)."""
    by_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in by_lower:
            return by_lower[cand.lower()]
    return None


def to_number(series: pd.Series) -> pd.Series:
    """Convierte a número; '5,25', '5.25%' o ' 5 ' funcionan y el texto inválido queda NaN."""
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    cleaned = (
        series.astype("string")
        .str.replace("%", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce").astype(float)


def to_percent(series: pd.Series) -> pd.Series:
    """Número en puntos porcentuales: si la columna viene en decimales (0.05) la pasa a 5.

    La escala se decide con la mediana (un valor atípico no cambia toda la columna) y
    solo se escalan los valores que sí parecen decimales: '5,25%' o 5.25 cargados a mano
    en una columna decimal no se multiplican por 100.
    """
    values = to_number(series)
    with_sign = series.astype("string").str.contains("%", regex=False, na=False)
    median = values[~with_sign].abs().median()
    if pd.notna(median) and median <= 1.0:
        decimal = ~with_sign & (values.abs() <= 1.0)
        values = values.where(~decimal, values * 100)
    return values


def to_date(series: pd.Series) -> pd.Series:
    """Fechas mezcladas (datetime de Excel y texto dd/mm/aaaa) a datetime; lo inválido queda NaT."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    parsed = pd.to_datetime(series.where(series.map(lambda v: not isinstance(v, str))), errors="coerce")
    text = series.where(series.map(lambda v: isinstance(v, str))).str.strip()
    parsed_text = pd.to_datetime(text, format="%d/%m/%Y", errors="coerce")
    parsed_text = parsed_text.fillna(pd.to_datetime(text, dayfirst=True, errors="coerce"))
    return parsed.fillna(parsed_text)


def to_text(series: pd.Series) -> pd.Series:
    """Texto limpio; vacíos y guiones sueltos quedan como NA."""
    out = series.astype("string").str.strip()
    return out.mask(out.isin(["", "-", "nan", "None"]))
