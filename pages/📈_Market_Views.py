import streamlit as st

st.set_page_config(page_title="Market Views", layout="wide")

st.title("📈 Market Views - FCA Asset Management")
st.caption("Perspectivas de inversión y análisis de mercado")

with open("FCA_Market_Views_Junio2026_1.html", "r", encoding="utf-8") as f:
    html_content = f.read()

st.components.v1.html(html_content, height=900, scrolling=True)
