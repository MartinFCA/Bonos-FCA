import streamlit as st

from fca import ui
from fca.data import list_reports, read_report

ui.page_setup("Recursos", "Reportes y documentación")

ui.section("Historial de Market Views")
reportes = list_reports()
if not reportes:
    st.info("No hay reportes disponibles.", icon=":material/info:")
for r in reportes:
    with st.container(border=True):
        c1, c2 = st.columns([4, 1], vertical_alignment="center")
        c1.markdown(f"**Market Views · {r.label}**")
        c2.download_button(
            "Descargar", read_report(r).encode("utf-8"), file_name=r.path.name, mime="text/html",
            icon=":material/download:", key=f"dl-{r.path.name}", width="stretch",
        )

ui.footer()
