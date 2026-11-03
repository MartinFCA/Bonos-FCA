"""Gráficos con Altair (Vega-Lite).

Altair ya viene con Streamlit: no suma dependencias, se renderiza en el navegador
y arranca mucho más rápido que Plotly. Todos los gráficos comparten el mismo estilo.
"""
import altair as alt
import pandas as pd

from fca.config import BRAND, SEGMENT_COLORS, SEGMENT_LABELS

_SEGMENTS = list(SEGMENT_COLORS)
_SEGMENT_SCALE = alt.Scale(domain=_SEGMENTS, range=[SEGMENT_COLORS[s] for s in _SEGMENTS])
_SEGMENT_LEGEND = alt.Legend(
    title=None, orient="top", direction="horizontal", symbolType="circle",
    labelExpr="".join(f"datum.label == '{k}' ? '{v}' : " for k, v in SEGMENT_LABELS.items()) + "datum.label",
)


def _style(chart: alt.TopLevelMixin, height: int) -> alt.TopLevelMixin:
    font = "Source Sans, Source Sans Pro, Segoe UI, sans-serif"
    return (
        chart.properties(height=height, background="transparent")
        .configure(font=font)
        .configure_view(stroke=None)
        .configure_axis(
            labelColor=BRAND["muted"], titleColor=BRAND["muted"], labelFontSize=12, titleFontSize=12,
            titleFontWeight=600, gridColor="#E9ECF2", domainColor=BRAND["border"], tickColor=BRAND["border"],
        )
        .configure_legend(labelColor=BRAND["text"], labelFontSize=13, symbolSize=120, padding=4)
    )


def yield_curve(bonds: pd.DataFrame, curve: pd.DataFrame, height: int = 520) -> alt.TopLevelMixin:
    """Bonos individuales (puntos) y tendencia cuadrática por segmento (líneas)."""
    seleccion = alt.selection_point(fields=["segment"], bind="legend")
    # Zoom solo con Shift + rueda, para no interferir con el scroll de la página.
    zoom = alt.selection_interval(bind="scales", encodings=["x", "y"], zoom="wheel![event.shiftKey]")
    opacidad = alt.condition(seleccion, alt.value(1), alt.value(0.12))
    color = alt.Color("segment:N", scale=_SEGMENT_SCALE, legend=_SEGMENT_LEGEND)
    x = alt.X("maturity:T", title="Vencimiento", axis=alt.Axis(format="%Y", tickCount="year"))
    y = alt.Y("ytw:Q", title="YTW (%)", scale=alt.Scale(zero=False), axis=alt.Axis(format=".1f"))

    lineas = (
        alt.Chart(curve).mark_line(strokeWidth=2.5, interpolate="monotone")
        .encode(x=x, y=y, color=color, opacity=opacidad)
    )

    tooltip = [
        alt.Tooltip("issuer:N", title="Emisor"),
        alt.Tooltip("rating:N", title="Rating"),
        alt.Tooltip("ytw:Q", title="YTW %", format=".2f"),
        alt.Tooltip("coupon:Q", title="Cupón %", format=".2f"),
        alt.Tooltip("maturity:T", title="Vencimiento", format="%d/%m/%Y"),
    ]
    for col, title, fmt in [("price", "Precio", ".2f"), ("ytw_change", "Δ YTW 1M (pp)", "+.2f"), ("decision", "Decisión", None)]:
        if col in bonds:
            tooltip.append(alt.Tooltip(f"{col}:{'N' if fmt is None else 'Q'}", title=title, **({"format": fmt} if fmt else {})))

    puntos = (
        alt.Chart(bonds).mark_circle(size=90, stroke="white", strokeWidth=1.2)
        .encode(x=x, y=y, color=color, opacity=opacidad, tooltip=tooltip)
    )

    return _style((lineas + puntos).add_params(seleccion, zoom), height)


def ytw_movers(bonds: pd.DataFrame, n: int = 12, height: int = 380) -> alt.TopLevelMixin:
    """Bonos con mayor variación de YTW contra el mes anterior."""
    df = bonds.dropna(subset=["ytw_change"]).copy()
    df["abs_change"] = df["ytw_change"].abs()
    df = df.nlargest(n, "abs_change")
    df["etiqueta"] = df["emisor"] + " " + df["maturity"].dt.strftime("%m/%y")

    return _style(
        alt.Chart(df).mark_bar(cornerRadiusEnd=3, height=16)
        .encode(
            x=alt.X("ytw_change:Q", title="Variación de YTW vs. mes anterior (pp)", axis=alt.Axis(format="+.2f")),
            y=alt.Y("etiqueta:N", title=None, sort=alt.EncodingSortField("ytw_change", order="descending")),
            color=alt.condition("datum.ytw_change > 0", alt.value("#B5473A"), alt.value("#1E8E5A")),
            tooltip=[
                alt.Tooltip("issuer:N", title="Emisor"),
                alt.Tooltip("ytw_prev:Q", title="YTW mes anterior %", format=".2f"),
                alt.Tooltip("ytw:Q", title="YTW actual %", format=".2f"),
                alt.Tooltip("ytw_change:Q", title="Variación (pp)", format="+.2f"),
            ],
        ),
        height,
    )


def etf_curve(etfs: pd.DataFrame, height: int = 360) -> alt.TopLevelMixin:
    """YTW de los ETFs de vencimiento fijo según año de vencimiento."""
    df = etfs.dropna(subset=["vto", "ytw"])
    base = alt.Chart(df).encode(
        x=alt.X("vto:O", title="Año de vencimiento", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("ytw:Q", title="YTW (%)", scale=alt.Scale(zero=False), axis=alt.Axis(format=".1f")),
        color=alt.Color("segment:N", scale=_SEGMENT_SCALE, legend=_SEGMENT_LEGEND),
    )
    lineas = base.mark_line(strokeWidth=2.5)
    puntos = base.mark_circle(size=110, stroke="white", strokeWidth=1.2).encode(
        tooltip=[
            alt.Tooltip("ticker:N", title="Ticker"),
            alt.Tooltip("ytw:Q", title="YTW %", format=".2f"),
            alt.Tooltip("ter:Q", title="TER %", format=".2f"),
        ]
    )
    etiquetas = base.mark_text(dy=-14, fontSize=11, fontWeight=600).encode(text="ticker:N")
    return _style(lineas + puntos + etiquetas, height)
