import streamlit as st
import streamlit.components.v1 as components

from fca import ui
from fca.data import list_reports, read_report

ui.page_setup("Market Views y carteras modelo", "Perspectivas de inversión del comité")

reportes = list_reports()
if not reportes:
    st.info("Todavía no hay reportes en data/market_views/.", icon=":material/info:")
    st.stop()

elegido = st.selectbox(
    "Reporte", reportes, format_func=lambda r: r.label + ("  (más reciente)" if r == reportes[0] else ""),
)
# El reporte se muestra dentro de un iframe aislado: su HTML y CSS no afectan al resto del sitio.
components.html(read_report(elegido), height=1300, scrolling=True)

ui.footer(f"Reporte: {elegido.label}")
