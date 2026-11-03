"""Componentes visuales compartidos por todas las páginas.

Cualquier texto que venga de los datos pasa por `esc()` antes de entrar al HTML,
para que una celda del Excel no pueda inyectar código en la página.
"""
from datetime import date
from html import escape

import pandas as pd
import streamlit as st

from fca.config import BRAND, DECISION_COLORS, SEGMENT_COLORS, SEGMENT_LABELS

B = BRAND

_CSS = f"""
<style>

#MainMenu, footer, [data-testid="stDecoration"] {{ display: none; }}
.block-container {{ padding-top: 4.5rem; padding-bottom: 3rem; max-width: 1680px; padding-left: 2.5rem; padding-right: 2.5rem; }}

.fca-header {{
  background: {B['navy']}; border-radius: 6px; overflow: hidden; margin-bottom: 1.25rem;
  box-shadow: 0 4px 18px rgba(28, 43, 74, .14);
}}
.fca-header__inner {{
  display: flex; align-items: center; justify-content: space-between; gap: 24px;
  padding: 22px 28px; flex-wrap: wrap;
}}
.fca-logo {{ color: #fff; font-size: 28px; font-weight: 700; letter-spacing: .05em; line-height: 1; }}
.fca-logo span {{
  display: block; color: {B['gold']}; font-size: 9px; font-weight: 400;
  letter-spacing: .28em; text-transform: uppercase; margin-top: 4px;
}}
.fca-header__title {{ text-align: right; }}
.fca-header__title h1 {{
  color: #fff !important; font-size: 22px !important; font-weight: 600 !important;
  margin: 0 !important; padding: 0 !important; letter-spacing: .01em;
}}
.fca-header__title p {{
  color: {B['gold']}; font-size: 11px; letter-spacing: .16em; text-transform: uppercase; margin: 6px 0 0;
}}
.fca-gold-bar {{ height: 3px; background: {B['gold']}; }}

.fca-section {{
  display: flex; align-items: center; gap: 12px; margin: 1.6rem 0 .8rem;
  color: {B['gold']}; font-size: 11px; font-weight: 700; letter-spacing: .18em; text-transform: uppercase;
}}
.fca-section::after {{ content: ''; flex: 1; height: 1px; background: {B['gold']}; opacity: .35; }}

.fca-kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }}
.fca-kpi {{
  background: {B['card']}; border: 1px solid {B['border']}; border-top: 3px solid {B['navy']};
  border-radius: 4px; padding: 14px 16px;
}}
.fca-kpi__label {{ color: {B['muted']}; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; }}
.fca-kpi__value {{ color: {B['navy']}; font-size: 26px; font-weight: 700; line-height: 1.25; margin-top: 4px; }}
.fca-kpi__note {{ color: {B['muted']}; font-size: 12px; margin-top: 2px; }}

.fca-cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }}
.fca-card {{
  background: {B['card']}; border: 1px solid {B['border']}; border-radius: 4px; padding: 14px 16px;
  border-left: 4px solid var(--accent);
}}
.fca-card__top {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }}
.fca-card__name {{ color: {B['navy']}; font-weight: 700; font-size: 15px; line-height: 1.25; }}
.fca-card__sub {{ color: {B['muted']}; font-size: 12px; margin-top: 2px; }}
.fca-pill {{
  display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 11px; font-weight: 700;
  letter-spacing: .04em; color: #fff; background: var(--pill); white-space: nowrap;
}}
.fca-card__grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-top: 12px; }}
.fca-card__grid div span {{ display: block; color: {B['muted']}; font-size: 10px; text-transform: uppercase; letter-spacing: .06em; }}
.fca-card__grid div b {{ color: {B['text']}; font-size: 14px; font-weight: 600; }}
.up {{ color: #B5473A !important; }} .down {{ color: #1E8E5A !important; }}

.fca-tile {{
  background: {B['card']}; border: 1px solid {B['border']}; border-top: 3px solid {B['gold']};
  border-radius: 4px; padding: 18px 20px; height: 100%;
}}
.fca-tile h3 {{ color: {B['navy']}; font-size: 17px; margin: 0 0 6px; padding: 0; }}
.fca-tile p {{ color: {B['muted']}; font-size: 14px; margin: 0; }}

.fca-footer {{
  margin-top: 3rem; padding-top: 14px; border-top: 1px solid {B['border']};
  display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;
  color: {B['muted']}; font-size: 12px;
}}

[data-testid="stTabs"] button[role="tab"] p {{ font-weight: 600; }}
[data-testid="stSidebar"] {{ border-right: 1px solid {B['border']}; }}
@media (max-width: 640px) {{
  .fca-header__title {{ text-align: left; }}
  .fca-card__grid {{ grid-template-columns: repeat(2, 1fr); }}
}}
</style>
"""


def esc(value) -> str:
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return "—"
    return escape(str(value))


def fmt_pct(value) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.2f}%"


def fmt_pp(value) -> str:
    """Variación en puntos porcentuales; evita mostrar '-0.00'."""
    if value is None or pd.isna(value):
        return "—"
    value = round(value, 2) + 0.0
    return f"{value:+.2f} pp"


def fmt_date(value) -> str:
    return value.strftime("%d/%m/%Y") if pd.notna(value) else "—"


def apply_theme() -> None:
    st.html(_CSS)


def header(title: str, subtitle: str = "") -> None:
    st.html(f"""
    <div class="fca-header">
      <div class="fca-header__inner">
        <div class="fca-logo">FCA<span>Asset Management</span></div>
        <div class="fca-header__title"><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>
      </div>
      <div class="fca-gold-bar"></div>
    </div>""")


def section(label: str) -> None:
    st.html(f'<div class="fca-section">{esc(label)}</div>')


def kpis(items: list[tuple[str, str, str]]) -> None:
    """items = [(etiqueta, valor, nota), ...]"""
    cells = "".join(
        f'<div class="fca-kpi"><div class="fca-kpi__label">{esc(l)}</div>'
        f'<div class="fca-kpi__value">{esc(v)}</div><div class="fca-kpi__note">{esc(n)}</div></div>'
        for l, v, n in items
    )
    st.html(f'<div class="fca-kpis">{cells}</div>')


def bond_cards(df: pd.DataFrame) -> None:
    """Tarjetas de decisión en una sola grilla HTML (mucho más liviano que un widget por bono)."""
    cards = []
    for row in df.itertuples(index=False):
        decision = getattr(row, "decision", None)
        decision_txt = decision if isinstance(decision, str) else "Sin decisión"
        pill = DECISION_COLORS.get(decision_txt, B["muted"])
        accent = SEGMENT_COLORS.get(row.segment, B["navy"])
        change = getattr(row, "ytw_change", None)
        change_cls = "" if change is None or pd.isna(change) or round(change, 2) == 0 else ("up" if change > 0 else "down")
        sub = f"{SEGMENT_LABELS.get(row.segment, row.segment)} · {esc(row.rating)}"
        cards.append(f"""
        <div class="fca-card" style="--accent:{accent}">
          <div class="fca-card__top">
            <div><div class="fca-card__name">{esc(row.issuer)}</div><div class="fca-card__sub">{sub}</div></div>
            <span class="fca-pill" style="--pill:{pill}">{esc(decision_txt)}</span>
          </div>
          <div class="fca-card__grid">
            <div><span>YTW</span><b>{fmt_pct(row.ytw)}</b></div>
            <div><span>Cupón</span><b>{fmt_pct(row.coupon) if hasattr(row, 'coupon') else '—'}</b></div>
            <div><span>Vence</span><b>{fmt_date(row.maturity)}</b></div>
            <div><span>Δ YTW 1M</span><b class="{change_cls}">{fmt_pp(change)}</b></div>
          </div>
        </div>""")
    st.html(f'<div class="fca-cards">{"".join(cards)}</div>')


def tile(title: str, text: str) -> None:
    st.html(f'<div class="fca-tile"><h3>{esc(title)}</h3><p>{esc(text)}</p></div>')


def footer(note: str = "") -> None:
    st.html(f"""
    <div class="fca-footer">
      <span>© {date.today().year} FCA Asset Management · Uso interno. No constituye recomendación de inversión.</span>
      <span>{esc(note)}</span>
    </div>""")


def page_setup(title: str, subtitle: str = "") -> None:
    """Tema + encabezado; se llama al principio de cada página."""
    apply_theme()
    header(title, subtitle)
