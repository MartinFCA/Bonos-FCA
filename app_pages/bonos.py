import pandas as pd
import streamlit as st

from fca import charts, ui
from fca.config import SEGMENT_LABELS
from fca.data import DataError, load_bonds, load_etfs, trend_curve

ui.page_setup("Bonos corporativos", "Curva de rendimiento · IG y HY")

try:
    universo = load_bonds()
except DataError as e:
    st.error(str(e), icon=":material/error:")
    st.stop()

df = universo.df

# ── Filtros ──────────────────────────────────────────────────────────────────
f1, f2, f3, f4 = st.columns([1, 1, 2, 1.4])
segmentos = f1.pills(
    "Segmento", options=sorted(df["segment"].dropna().unique()), selection_mode="multi",
    default=sorted(df["segment"].dropna().unique()), format_func=lambda s: SEGMENT_LABELS.get(s, s),
)
decisiones = None
if universo.tiene_decision:
    opciones = sorted(df["decision"].fillna("Sin decisión").unique())
    decisiones = f2.pills("Decisión", options=opciones, selection_mode="multi", default=opciones)
emisores = f3.multiselect(
    "Emisores", options=sorted(df["emisor"].unique()), placeholder="Todos los emisores",
)
anio_min, anio_max = int(df["maturity"].dt.year.min()), int(df["maturity"].dt.year.max())
anios = f4.slider("Vencimiento", anio_min, anio_max, (anio_min, anio_max)) if anio_min < anio_max else (anio_min, anio_max)

mask = df["segment"].isin(segmentos or []) & df["maturity"].dt.year.between(*anios)
if emisores:
    mask &= df["emisor"].isin(emisores)
if decisiones is not None:
    mask &= df["decision"].fillna("Sin decisión").isin(decisiones)
sel = df[mask]

# ── Resumen ──────────────────────────────────────────────────────────────────
ig, hy = sel[sel["segment"] == "IG"], sel[sel["segment"] == "HY"]
ui.kpis([
    ("Bonos", f"{len(sel)}", f"de {len(df)} en el universo"),
    ("YTW promedio", ui.fmt_pct(sel["ytw"].mean()), f"IG {ui.fmt_pct(ig['ytw'].mean())} · HY {ui.fmt_pct(hy['ytw'].mean())}"),
    ("Cupón promedio", ui.fmt_pct(sel["coupon"].mean()) if "coupon" in sel else "—", "Sobre bonos con cupón informado"),
    ("Spread HY − IG", f"{(hy['ytw'].mean() - ig['ytw'].mean()) * 100:.0f} pb" if len(ig) and len(hy) else "—", "Diferencia de YTW promedio"),
    ("Δ YTW 1 mes", ui.fmt_pp(sel["ytw_change"].mean()) if "ytw_change" in sel else "—", "Promedio vs. mes anterior"),
])

if universo.avisos:
    with st.expander(f"Avisos de calidad de datos ({len(universo.avisos)})", icon=":material/info:"):
        for aviso in universo.avisos:
            st.markdown(f"- {aviso}")

if sel.empty:
    st.info("No hay bonos que cumplan los filtros seleccionados.", icon=":material/filter_alt_off:")
    st.stop()

# ── Pestañas ─────────────────────────────────────────────────────────────────
tab_curva, tab_decision, tab_tabla, tab_etf = st.tabs(
    [":material/show_chart: Curva", ":material/fact_check: Decisiones", ":material/table: Datos", ":material/stacked_line_chart: ETFs"]
)

with tab_curva:
    st.altair_chart(charts.yield_curve(sel, trend_curve(sel)), theme=None, width="stretch")
    st.caption("Puntos: bonos individuales · Líneas: tendencia cuadrática por segmento. "
               "Clic en la leyenda para aislar un segmento; Shift + rueda del mouse para hacer zoom, arrastrar para desplazar, doble clic para restablecer.")
    if "ytw_change" in sel and sel["ytw_change"].notna().any():
        ui.section("Mayores movimientos del mes")
        st.altair_chart(charts.ytw_movers(sel), theme=None, width="stretch")

with tab_decision:
    if not universo.tiene_decision:
        st.info("Agregá una columna **Decisión** (Buy / Hold / Done) al Excel para activar esta sección.")
    else:
        orden = st.segmented_control(
            "Ordenar por", ["Vencimiento", "YTW", "Emisor"], default="Vencimiento", label_visibility="collapsed",
        )
        clave = {"Vencimiento": ("maturity", True), "YTW": ("ytw", False), "Emisor": ("issuer", True)}[orden or "Vencimiento"]
        ui.bond_cards(sel.sort_values(clave[0], ascending=clave[1]))

with tab_tabla:
    columnas = {
        "issuer": "Emisor", "industry": "Industria", "segment": "IG/HY", "rating": "Rating",
        "coupon": "Cupón %", "maturity": "Vencimiento", "price": "Precio", "ytw": "YTW %",
        "ytw_prev": "YTW mes ant. %", "ytw_change": "Δ YTW (pp)", "gspread": "G-spread (pb)",
        "min_settlement": "Mínimo", "outstanding": "Outstanding US$", "isin": "ISIN", "decision": "Decisión",
    }
    tabla = sel[[c for c in columnas if c in sel]].rename(columns=columnas)
    st.dataframe(
        tabla, hide_index=True, height=560,
        column_config={
            "Vencimiento": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Cupón %": st.column_config.NumberColumn(format="%.2f%%"),
            "YTW %": st.column_config.NumberColumn(format="%.2f%%"),
            "YTW mes ant. %": st.column_config.NumberColumn(format="%.2f%%"),
            "Δ YTW (pp)": st.column_config.NumberColumn(format="%+.2f"),
            "Precio": st.column_config.NumberColumn(format="%.2f"),
            "G-spread (pb)": st.column_config.NumberColumn(format="%.0f"),
            "Mínimo": st.column_config.NumberColumn(format="$%,.0f"),
            "Outstanding US$": st.column_config.NumberColumn(format="compact"),
        },
    )
    st.download_button(
        "Descargar selección (CSV)", tabla.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"bonos_fca_{pd.Timestamp.today():%Y%m%d}.csv", mime="text/csv", icon=":material/download:",
    )

with tab_etf:
    try:
        etfs = load_etfs()
    except DataError as e:
        st.warning(str(e), icon=":material/warning:")
    else:
        if {"vto", "ytw"} <= set(etfs.columns) and etfs["vto"].notna().any():
            ui.section("ETFs de vencimiento fijo")
            st.altair_chart(charts.etf_curve(etfs), theme=None, width="stretch")
        ui.section("Universo de ETFs")
        st.dataframe(
            etfs.rename(columns={"ticker": "Ticker", "tipo": "Tipo", "segment": "IG/HY", "vto": "Vencimiento",
                                 "ter": "TER %", "ytw": "YTW %", "link": "Ficha"}),
            hide_index=True,
            column_config={
                "Vencimiento": st.column_config.NumberColumn(format="%d"),
                "TER %": st.column_config.NumberColumn(format="%.2f%%"),
                "YTW %": st.column_config.NumberColumn(format="%.2f%%"),
                "Ficha": st.column_config.LinkColumn(display_text="Ver producto"),
            },
        )

ui.footer(f"Datos: {len(df)} bonos válidos de {universo.total_archivo} filas")
