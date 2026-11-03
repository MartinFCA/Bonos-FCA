import streamlit as st

from fca import ui
from fca.data import DataError, list_reports, load_bonds

ui.page_setup("Plataforma de inversiones", "Análisis de renta fija y estrategia")

try:
    universo = load_bonds()
    df = universo.df
    ui.kpis([
        ("Bonos en seguimiento", f"{len(df)}", f"{df['emisor'].nunique()} emisores"),
        ("YTW promedio", ui.fmt_pct(df["ytw"].mean()), "Universo completo"),
        ("Investment Grade", f"{(df['segment'] == 'IG').sum()}", ui.fmt_pct(df.loc[df["segment"] == "IG", "ytw"].mean()) + " YTW"),
        ("High Yield", f"{(df['segment'] == 'HY').sum()}", ui.fmt_pct(df.loc[df["segment"] == "HY", "ytw"].mean()) + " YTW"),
    ])
except DataError as e:
    st.warning(str(e), icon=":material/warning:")

ui.section("Secciones")
c1, c2, c3 = st.columns(3)
with c1:
    ui.tile("Bonos corporativos", "Curva de rendimiento IG y HY, decisiones de inversión, tabla de datos y ETFs de renta fija.")
    st.page_link("app_pages/bonos.py", label="Abrir dashboard", icon=":material/arrow_forward:")
with c2:
    reportes = list_reports()
    ultimo = reportes[0].label if reportes else "sin reportes"
    ui.tile("Market Views y carteras", f"Visión de mercado y carteras modelo del comité. Último reporte: {ultimo}.")
    st.page_link("app_pages/estrategia.py", label="Ver reporte", icon=":material/arrow_forward:")
with c3:
    ui.tile("Recursos", "Historial de reportes y descargas de datos para uso interno.")
    st.page_link("app_pages/recursos.py", label="Ir a recursos", icon=":material/arrow_forward:")

ui.footer()
