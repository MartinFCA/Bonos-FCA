import streamlit as st

st.set_page_config(page_title="Estrategia de Carteras", layout="wide")

st.title("💼 Estrategia y Carteras Modelos - FCA Asset Management")
st.caption("Perspectivas de inversión y manejo de carteras")

with open("FCA_Market_Views_Agosto2026.html", "r", encoding="utf-8") as f:
    html_content = f.read()

st.components.v1.html(html_content, height=1300, scrolling=True)
