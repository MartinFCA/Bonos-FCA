"""Punto de entrada de la plataforma FCA Asset Management.

Ejecutar con:  streamlit run Inicio.py

Las páginas viven en app_pages/. Para sumar una sección nueva, crear el archivo
ahí y agregarlo a PAGES; el menú se arma solo.
"""
import streamlit as st

st.set_page_config(
    page_title="FCA Asset Management",
    page_icon=":material/account_balance:",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"Get help": None, "Report a bug": None, "About": "FCA Asset Management · Plataforma de análisis"},
)

PAGES = {
    "": [
        st.Page("app_pages/inicio.py", title="Inicio", icon=":material/home:", default=True),
    ],
    "Renta fija": [
        st.Page("app_pages/bonos.py", title="Bonos corporativos", icon=":material/show_chart:", url_path="bonos"),
    ],
    "Estrategia": [
        st.Page("app_pages/estrategia.py", title="Market Views y carteras", icon=":material/insights:", url_path="estrategia"),
        st.Page("app_pages/recursos.py", title="Recursos", icon=":material/folder_open:", url_path="recursos"),
    ],
}

st.navigation(PAGES, position="top").run()
