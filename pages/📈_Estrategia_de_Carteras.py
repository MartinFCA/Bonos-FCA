import streamlit as st

st.set_page_config(page_title="Estrategia de Carteras", layout="wide")

st.title("💼 Estrategia de Carteras - FCA Asset Management")
st.caption("Perspectivas de inversión y manejo de carteras")

with open("FCA_Market_Views_Junio2026_5.html", "r", encoding="utf-8") as f:
    html_content = f.read()

st.components.v1.html(html_content, height=1000, scrolling=True)
