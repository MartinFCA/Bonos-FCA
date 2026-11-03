"""Catálogo de reportes Market Views (HTML) guardados en data/market_views/."""
import re
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from fca.config import CACHE_TTL, MARKET_VIEWS_DIR

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
    "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}
# FCA_Market_Views_<Mes><espacio opcional><Año>[_<versión>].html
PATRON = re.compile(r"Market_Views_([A-Za-zÁÉÍÓÚáéíóú]+)\s*(\d{4})(?:_(\d+))?$", re.IGNORECASE)


@dataclass(frozen=True)
class Report:
    path: Path
    year: int
    month: int
    version: int
    label: str


def _parse(path: Path) -> Report | None:
    m = PATRON.search(path.stem)
    if not m or m.group(1).lower() not in MESES:
        return None
    mes = m.group(1).lower()
    version = int(m.group(3) or 0)
    label = f"{mes.capitalize()} {m.group(2)}" + (f" · v{version}" if version else "")
    return Report(path, int(m.group(2)), MESES[mes], version, label)


def list_reports(folder: Path = MARKET_VIEWS_DIR) -> list[Report]:
    """Reportes ordenados del más reciente al más antiguo."""
    if not folder.exists():
        return []
    reports = [r for p in folder.glob("*.html") if (r := _parse(p))]
    return sorted(reports, key=lambda r: (r.year, r.month, r.version), reverse=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _read(path: str, mtime: float) -> str:
    return Path(path).read_text(encoding="utf-8")


def read_report(report: Report) -> str:
    return _read(str(report.path), report.path.stat().st_mtime)
