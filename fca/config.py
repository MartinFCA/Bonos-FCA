"""Configuración central: rutas de datos e identidad visual de FCA.

Todo lo que dependa del entorno (rutas, colores, nombres de archivo) vive acá,
para que cambiar de origen de datos o de dominio no obligue a tocar las páginas.
"""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

BONOS_XLSX = DATA_DIR / "bonos.xlsx"
ETFS_XLSX = DATA_DIR / "etfs.xlsx"
MARKET_VIEWS_DIR = DATA_DIR / "market_views"

# Tiempo máximo que un archivo queda en caché aunque no cambie (segundos).
CACHE_TTL = 3600

# Identidad visual (la misma de los reportes Market Views).
BRAND = {
    "navy": "#1C2B4A",
    "navy_light": "#2E4470",
    "gold": "#C9A84C",
    "bg": "#F5F6F8",
    "card": "#FFFFFF",
    "border": "#DDE1EA",
    "muted": "#6B7489",
    "text": "#1A1F2B",
    "font": "'Source Sans', 'Source Sans Pro', 'Segoe UI', sans-serif",
}

# Colores por segmento de crédito.
SEGMENT_COLORS = {"IG": "#2E5C9A", "HY": "#C9A84C"}
SEGMENT_LABELS = {"IG": "Investment Grade", "HY": "High Yield"}

# Buy = comprar, Hold = mantener, Done = cerrado (se excluye del dashboard).
DECISION_COLORS = {"Buy": "#1E8E5A", "Hold": "#C99A2E", "Done": "#8A93A6", "Sell": "#FF2C2C"}
DECISION_EXCLUIDA = "Done"
