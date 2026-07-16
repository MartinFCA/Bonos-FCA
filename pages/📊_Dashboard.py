import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# ⚙️ CONFIGURACIÓN DE LA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Dashboard de Bonos",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None,
)

st.markdown(
    """
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #111;
            color: #fff;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        div[data-testid="stMetric"] {text-align: center;}
        div[data-testid="stMetricValue"] {font-size: 28px; font-weight: bold;}
        div[data-testid="stMetricLabel"] {font-size: 12px; text-transform: uppercase; color: #ffffff;}

        button[data-baseweb="tab"] {
            background: linear-gradient(135deg, #0E1117 100%, #ffffff 100%);
            border-radius: 9px 9px 0 0;
            color: #FFFFFF !important;
            font-weight: 500 !important;
        }

        ::-webkit-scrollbar {width: 8px;}
        ::-webkit-scrollbar-track {background: #f1f1f1;}
        ::-webkit-scrollbar-thumb {background: #888; border-radius: 4px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# 🎨 CONFIGURACIÓN VISUAL Y TEMA
# ============================================================================
TEMA = {
    'bg_principal': '#F8F9FA',
    'color_IG': '#1F77B4',      # Azul profesional
    'color_HY': '#FF9944',      # Naranja Claro profesional
    'color_grid': '#E0E0E0',
    'color_texto': '#222222',
    'color_border': '#CCCCCC',
    'font_principal': 'Arial, sans-serif'
}

RATING_COLORS = {
    'AAA': '#00A651', 'AA': '#00C7B7', 'A': '#FFC107',
    'A-': '#FFD54F', 'BBB': '#FF9800', 'BBB-': '#FFB74D',
    'BB': '#F44336', 'BB+': '#EF5350', 'B': '#C62828', 'B-': '#B71C1C',
    'CCC': '#880E4F', 'CC': '#4A0E4E', 'C': '#1A0033',
    'D': '#000000'
}

# Colores de la tarjeta de decisión: Buy = comprar, Hold = mantener, Done = cerrado/ejecutado
DECISION_COLORS = {
    'Buy': '#00A651',
    'Hold': '#FFC107',
    'Done': '#6C757D',
}
DECISION_ICONS = {
    'Buy': '🟢',
    'Hold': '🟡',
    'Done': '⚪',
}

NOMBRE_ARCHIVO_EXCEL = "Bonos Ejemplo.xlsx"
NOMBRE_ARCHIVO_ETF = "ETF.xlsx"

# Nombres posibles de la columna de decisión, en orden de preferencia
CANDIDATOS_COL_DECISION = ['Decisión', 'Decision', 'Recomendados', 'Recomendado', 'Recomendación', 'Recomend']


# ============================================================================
# 📦 CAPA DE DATOS
# ============================================================================
class BondRepository:
    """Carga, valida y prepara los datos de bonos desde el Excel de origen."""

    COLUMNAS_REQUERIDAS = ['Maturity', 'YTW %', 'Coupon %', 'IG - HY', 'Rating']
    COLUMNAS_PORCENTAJE = ['YTW %', 'Coupon %', 'Prev month YTW%', 'YTW% t-15']

    def __init__(self, ruta_excel):
        self.ruta_excel = ruta_excel
        self.df = None
        self.col_emisor = None
        self.col_decision = None

    @staticmethod
    @st.cache_data(ttl=300)
    def _leer_excel(ruta):
        df = pd.read_excel(ruta)
        # Normaliza saltos de línea que suelen venir en los encabezados del Excel
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
        return df

    def cargar(self):
        """Carga el Excel y prepara el DataFrame. Detiene la app en caso de error."""
        try:
            df = self._leer_excel(self.ruta_excel)
        except FileNotFoundError:
            st.error(f"❌ No se encontró el archivo '{self.ruta_excel}'")
            st.info("Asegúrate de que el archivo esté en la misma carpeta que el script.")
            st.stop()
        except Exception as e:
            st.error(f"❌ Error al cargar datos: {str(e)}")
            st.stop()

        df = self._validar_y_preparar(df)
        if df is None or df.empty:
            st.stop()

        self.df = df
        self.col_emisor = self._detectar_col_emisor(df)
        if not self.col_emisor:
            st.error("❌ No se encontró columna de emisores en el Excel")
            st.info("Columnas detectadas: " + ", ".join(df.columns.tolist()))
            st.stop()

        self.col_decision = self._detectar_col_decision(df)
        return self

    def _validar_y_preparar(self, df):
        faltantes = [col for col in self.COLUMNAS_REQUERIDAS if col not in df.columns]
        if faltantes:
            st.error(f"❌ **Columnas faltantes en Excel:**\n{', '.join(faltantes)}")
            st.info("Tu Excel debe contener estas columnas: " + ", ".join(self.COLUMNAS_REQUERIDAS))
            st.write("**Columnas disponibles en tu archivo:**")
            st.code(", ".join(df.columns.tolist()))
            return None

        try:
            df = df.copy()
            df['Maturity'] = pd.to_datetime(df['Maturity'], errors='coerce')

            for col in self.COLUMNAS_PORCENTAJE:
                if col in df.columns and pd.to_numeric(df[col], errors='coerce').max() <= 1.0:
                    df[col] = df[col] * 100

            df = df.dropna(subset=['Maturity', 'YTW %'])

            if df.empty:
                st.warning("⚠️ No hay datos válidos después de limpiar filas vacías.")
                return None

            return df
        except Exception as e:
            st.error(f"❌ Error preparando datos: {str(e)}")
            return None

    @staticmethod
    def _detectar_col_emisor(df):
        for col in ['Guarantor/Organization', 'Issuer', 'Emisor', 'issuer']:
            if col in df.columns:
                return col
        for col in df.columns:
            if df[col].dtype == 'object' and col not in ['IG - HY', 'Rating']:
                return col
        return None

    @staticmethod
    def _detectar_col_decision(df):
        for col in CANDIDATOS_COL_DECISION:
            if col in df.columns:
                return col
        return None

    def filtrar(self, emisores_seleccionados, tipos_seleccionados):
        df = self.df
        return df[
            (df[self.col_emisor].isin(emisores_seleccionados)) &
            (df['IG - HY'].isin(tipos_seleccionados))
        ]


class ETFRepository:
    """Carga los datos de ETFs de renta fija."""

    def __init__(self, ruta_excel):
        self.ruta_excel = ruta_excel

    @st.cache_data(ttl=300)
    def cargar(_self):
        df = pd.read_excel(_self.ruta_excel)
        for col in ['TER', 'YTW']:
            if col in df.columns and df[col].max() <= 1.0:
                df[col] = df[col] * 100
        return df


# ============================================================================
# 📈 CONSTRUCCIÓN DEL GRÁFICO
# ============================================================================
class YieldCurveChartBuilder:
    """Construye el gráfico interactivo de curvas de rendimiento (YTW)."""

    def __init__(self, tema, col_emisor):
        self.tema = tema
        self.col_emisor = col_emisor

    def construir(self, df_filtrado):
        fig = go.Figure()

        for tipo, color in [('IG', self.tema['color_IG']), ('HY', self.tema['color_HY'])]:
            df_tipo = df_filtrado[df_filtrado['IG - HY'] == tipo]
            if not df_tipo.empty and len(df_tipo) >= 3:
                self._agregar_tendencia(fig, df_tipo, tipo, color)

        for tipo, color, nombre in [
            ('IG', self.tema['color_IG'], 'Investment Grade (IG)'),
            ('HY', self.tema['color_HY'], 'High Yield (HY)'),
        ]:
            df_puntos = df_filtrado[df_filtrado['IG - HY'] == tipo]
            if not df_puntos.empty:
                self._agregar_puntos(fig, df_puntos, nombre, color)

        self._aplicar_layout(fig)
        return fig

    def _agregar_tendencia(self, fig, df_tipo, tipo, color):
        if len(df_tipo) < 3:
            return

        grouped = df_tipo.groupby('Maturity').agg({'YTW %': 'mean'}).reset_index()
        grouped = grouped.sort_values('Maturity').reset_index(drop=True)

        if len(grouped) < 2:
            return

        try:
            x_numerico = grouped['Maturity'].apply(lambda x: x.toordinal()).values
            y_valores = grouped['YTW %'].values

            z = np.polyfit(x_numerico, y_valores, 2)
            p = np.poly1d(z)

            x_smooth_num = np.linspace(x_numerico.min(), x_numerico.max(), 150)
            x_smooth_dates = [datetime.date.fromordinal(int(x)) for x in x_smooth_num]

            fig.add_trace(go.Scatter(
                x=x_smooth_dates,
                y=p(x_smooth_num),
                mode='lines',
                name=f'Tendencia {tipo}',
                line=dict(color=color, width=3, dash='solid'),
                hoverinfo='skip',
                showlegend=True
            ))
        except Exception as e:
            st.warning(f"No se pudo calcular tendencia para {tipo}: {e}")

    def _agregar_puntos(self, fig, df_puntos, nombre_tipo, color):
        if df_puntos.empty:
            return

        try:
            textos_hover = []
            for _, row in df_puntos.iterrows():
                fecha_txt = row['Maturity'].strftime('%d/%m/%Y') if isinstance(row['Maturity'], pd.Timestamp) else str(row['Maturity'])
                rating_color = RATING_COLORS.get(str(row['Rating']), '#999')

                texto = (f"<b style='font-size: 14px; color: {rating_color};'>{row[self.col_emisor]}</b><br>"
                        f"<b>Rating:</b> {row['Rating']}<br>"
                        f"<b>YTW:</b> {row['YTW %']:.2f}%<br>"
                        f"<b>Cupón:</b> {row['Coupon %']:.2f}%<br>"
                        f"<b>Vencimiento:</b> {fecha_txt}")
                textos_hover.append(texto)

            fig.add_trace(go.Scatter(
                x=df_puntos['Maturity'],
                y=df_puntos['YTW %'],
                mode='markers',
                name=nombre_tipo,
                marker=dict(
                    size=11,
                    color=color,
                    opacity=0.85,
                    line=dict(width=2, color='white')
                ),
                text=textos_hover,
                hovertemplate='%{text}<extra></extra>',
                showlegend=True
            ))
        except Exception as e:
            st.warning(f"Error al agregar puntos: {e}")

    def _aplicar_layout(self, fig):
        fig.update_layout(
            title={
                'text': '<b>Análisis Dinámico de Curvas de Rendimiento (YTW)</b>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': self.tema['color_texto']}
            },
            xaxis_title='<b>Fecha de Vencimiento</b>',
            yaxis_title='<b>YTW - Yield to Worst (%)</b>',
            plot_bgcolor=self.tema['bg_principal'],
            paper_bgcolor='white',
            hovermode='closest',
            height=700,
            font=dict(
                color=self.tema['color_texto'],
                family=self.tema['font_principal'],
                size=12
            ),
            xaxis=dict(
                type='date',
                showline=True,
                linecolor=self.tema['color_texto'],
                linewidth=2,
                ticks='outside',
                tickcolor=self.tema['color_texto'],
                showgrid=True,
                gridcolor=self.tema['color_grid'],
                mirror=False
            ),
            yaxis=dict(
                showline=True,
                linecolor=self.tema['color_texto'],
                linewidth=2,
                ticks='outside',
                tickcolor=self.tema['color_texto'],
                ticksuffix='%',
                showgrid=True,
                gridcolor=self.tema['color_grid'],
                mirror=False
            ),
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor='rgba(255, 255, 255, 0.95)',
                bordercolor=self.tema['color_border'],
                borderwidth=2,
                font=dict(color=self.tema['color_texto'], size=12)
            ),
            margin=dict(l=70, r=50, t=100, b=80)
        )


# ============================================================================
# 🃏 TARJETAS DE DECISIÓN DE BONOS
# ============================================================================
class BondDecisionCardView:
    """Renderiza la tarjeta de decisión (Buy / Hold / Done) de un bono."""

    def __init__(self, col_emisor, col_decision):
        self.col_emisor = col_emisor
        self.col_decision = col_decision

    def _badge(self, texto, color):
        return (
            f"<div style='background-color: {color}; color: white; padding: 8px 12px; "
            f"border-radius: 6px; text-align: center; font-weight: bold;'>{texto}</div>"
        )

    def render(self, row):
        rating = str(row['Rating'])
        color_rating = RATING_COLORS.get(rating, '#999')
        tipo_bono = "Investment Grade (IG)" if row['IG - HY'] == 'IG' else "High Yield (HY)"
        fecha_txt = row['Maturity'].strftime('%d/%m/%Y') if isinstance(row['Maturity'], pd.Timestamp) else str(row['Maturity'])

        decision = str(row[self.col_decision]).strip() if self.col_decision else 'N/D'
        color_decision = DECISION_COLORS.get(decision, '#495057')
        icono_decision = DECISION_ICONS.get(decision, '⚪')

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### 🏢 {row[self.col_emisor]}")
                st.caption(tipo_bono)
            with col2:
                st.markdown(self._badge(rating, color_rating), unsafe_allow_html=True)

            st.divider()

            m1, m2, m3, m4, m5 = st.columns(5)

            with m1:
                st.metric("YTW", f"{row['YTW %']:.2f}%")

            with m2:
                st.metric("Cupón", f"{row['Coupon %']:.2f}%")

            with m3:
                st.metric("Vencimiento", fecha_txt)

            with m4:
                if 'Prev month YTW%' in row.index and pd.notna(row['Prev month YTW%']):
                    dif = row['YTW %'] - row['Prev month YTW%']
                    st.metric("Cambio YTW", f"{dif:+.2f}%")
                else:
                    st.metric("Cambio YTW", "N/D")

            with m5:
                st.markdown(f"<div style='margin-bottom: 4px; font-size: 12px; text-transform: uppercase; color: #aaa;'>Decisión</div>", unsafe_allow_html=True)
                st.markdown(self._badge(f"{icono_decision} {decision}", color_decision), unsafe_allow_html=True)


class BondDecisionTabView:
    """Orquesta la pestaña completa de 'Decisión de Bonos': filtro por decisión + listado de tarjetas."""

    def __init__(self, col_emisor, col_decision):
        self.col_emisor = col_emisor
        self.col_decision = col_decision
        self.card_view = BondDecisionCardView(col_emisor, col_decision)

    def render(self, df):
        st.subheader("⚖️ Decisión de Bonos")

        if not self.col_decision:
            st.warning(
                "⚠️ Para activar esta sección, agrega una columna de decisión en tu Excel "
                "(por ejemplo **'Decisión'**) con valores 'Buy', 'Hold' o 'Done'."
            )
            return

        decisiones_disponibles = sorted(df[self.col_decision].dropna().unique().tolist())
        decisiones_seleccionadas = st.multiselect(
            "Filtrar por decisión:",
            options=decisiones_disponibles,
            default=decisiones_disponibles,
        )

        df_decision = df[df[self.col_decision].isin(decisiones_seleccionadas)]

        if df_decision.empty:
            st.info("💡 No hay bonos con la decisión seleccionada en el filtro actual.")
            return

        conteo = df_decision[self.col_decision].value_counts()
        cols_resumen = st.columns(len(decisiones_disponibles) if decisiones_disponibles else 1)
        for i, decision in enumerate(decisiones_disponibles):
            with cols_resumen[i % len(cols_resumen)]:
                icono = DECISION_ICONS.get(decision, '⚪')
                st.metric(f"{icono} {decision}", int(conteo.get(decision, 0)))

        st.markdown("<br>", unsafe_allow_html=True)

        for _, row in df_decision.sort_values('Maturity').iterrows():
            self.card_view.render(row)


class ETFTableView:
    """Renderiza la tabla de ETFs de renta fija con descarga en CSV."""

    def render(self, df_etf):
        config_etf = {}
        for col in ['TER', 'YTW']:
            if col in df_etf.columns:
                config_etf[col] = st.column_config.NumberColumn(format="%.2f%%")

        if 'Link' in df_etf.columns:
            config_etf['Link'] = st.column_config.LinkColumn(display_text="Ver producto")

        altura = min(600, len(df_etf) * 35 + 50)
        st.dataframe(
            df_etf,
            use_container_width=True,
            column_config=config_etf,
            height=altura
        )

        csv_etf = df_etf.to_csv(index=False)
        st.download_button(
            label="📥 Descargar ETFs como CSV",
            data=csv_etf,
            file_name="etf_analisis.csv",
            mime="text/csv"
        )


# ============================================================================
# 🖥️ APLICACIÓN
# ============================================================================
class BondDashboardApp:
    """Orquesta la página completa: filtros, gráfico y pestañas."""

    def __init__(self):
        self.repo = BondRepository(NOMBRE_ARCHIVO_EXCEL)
        self.etf_repo = ETFRepository(NOMBRE_ARCHIVO_ETF)

    def run(self):
        self.repo.cargar()
        df = self.repo.df
        col_emisor = self.repo.col_emisor
        col_decision = self.repo.col_decision

        st.title("📊 Curva de Rendimiento de Bonos")
        st.caption("📅 FCA Asset Management • Dashboard Interactivo")
        st.markdown("")

        df_filtrado = self._render_filtros(df, col_emisor)

        st.markdown("")
        chart_builder = YieldCurveChartBuilder(TEMA, col_emisor)
        fig = chart_builder.construir(df_filtrado)

        tab1, tab2, tab3, tab4 = st.tabs(
            ["📊 Gráfico Interactivo", "📋 Tabla de Datos", "⚖️ Decisión de Bonos", "📊 ETF's"]
        )

        with tab1:
            self._render_tab_grafico(fig)
        with tab2:
            self._render_tab_tabla(df_filtrado, col_decision)
        with tab3:
            BondDecisionTabView(col_emisor, col_decision).render(df_filtrado)
        with tab4:
            st.subheader("📊 ETFs de Renta Fija")
            ETFTableView().render(self.etf_repo.cargar())

        self._render_footer(df)

    def _render_filtros(self, df, col_emisor):
        with st.expander("⚙️ **Filtros de Bonos y Resumen en Tiempo Real**", expanded=False):
            emisores_disponibles = sorted(df[col_emisor].unique())

            col_filter_1, col_filter_2 = st.columns([0.7, 0.3])

            with col_filter_1:
                emisores_seleccionados = st.multiselect(
                    "Selecciona los emisores a **INCLUIR**:",
                    options=emisores_disponibles,
                    default=emisores_disponibles,
                    help="Filtra los bonos por emisor"
                )

            with col_filter_2:
                tipos_disponibles = df['IG - HY'].unique()
                tipos_seleccionados = st.multiselect(
                    "Tipo de Bono",
                    options=tipos_disponibles,
                    default=tipos_disponibles,
                )

            df_filtrado = self.repo.filtrar(emisores_seleccionados, tipos_seleccionados)

            st.markdown("<hr style='margin: 15px 0; border: 0; border-top: 2px solid #E0E0E0;'>", unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)

            with m1:
                st.metric(
                    label="🏢 Bonos Analizados",
                    value=f"{len(df_filtrado)}",
                    delta=f"de {len(df)} total"
                )

            with m2:
                ytw_promedio = df_filtrado['YTW %'].mean() if not df_filtrado.empty else 0
                st.metric(label="📈 YTW Promedio", value=f"{ytw_promedio:.2f}%")

            with m3:
                coupon_promedio = df_filtrado['Coupon %'].mean() if not df_filtrado.empty else 0
                st.metric(label="💵 Cupón Promedio", value=f"{coupon_promedio:.2f}%")

            with m4:
                ig_count = len(df_filtrado[df_filtrado['IG - HY'] == 'IG'])
                hy_count = len(df_filtrado[df_filtrado['IG - HY'] == 'HY'])
                st.metric(label="📊 Distribución", value=f"IG: {ig_count} | HY: {hy_count}")

        return df_filtrado

    def _render_tab_grafico(self, fig):
        st.plotly_chart(fig, theme=None, use_container_width=True)
        st.markdown("""
        **💡 Cómo interpretar el gráfico:**
        - **Filtrado**: Con cada filtración las curvas se actualizan automaticamente
        - **Eje X**: Fecha de vencimiento | **Eje Y**: Rendimiento (YTW)
        - **Líneas**: Tendencias polinómicas | **Puntos**: Bonos individuales
        - **Celeste (IG)**: Investment Grade | **Naranja (HY)**: High Yield
        """)

    def _render_tab_tabla(self, df_filtrado, col_decision):
        config_visual = {}

        if 'Maturity' in df_filtrado.columns:
            config_visual['Maturity'] = st.column_config.DateColumn(format="DD/MM/YYYY")

        for col in ['YTW %', 'Coupon %', 'YTW% t-15']:
            if col in df_filtrado.columns:
                config_visual[col] = st.column_config.NumberColumn(format="%.2f%%")
        for col in ['Minimum Settlement', 'Outstanding US$']:
            if col in df_filtrado.columns:
                config_visual[col] = st.column_config.NumberColumn(format="$%.0f")
        for col in ['Price']:
            if col in df_filtrado.columns:
                config_visual[col] = st.column_config.NumberColumn(format="$%.2f")

        df_mostrar = df_filtrado

        st.dataframe(
            df_mostrar.sort_values('Maturity'),
            use_container_width=True,
            column_config=config_visual,
            height=600
        )

        csv = df_mostrar.to_csv(index=False)
        st.download_button(
            label="📥 Descargar como CSV",
            data=csv,
            file_name="bonos_analisis.csv",
            mime="text/csv"
        )

    def _render_footer(self, df):
        st.markdown("<hr style='margin: 40px 0; border: 0; border-top: 2px solid #E0E0E0;'>", unsafe_allow_html=True)

        col_footer_1, col_footer_2, col_footer_3 = st.columns([0.4, 0.3, 0.3])

        with col_footer_1:
            st.caption("📅 **Datos cargados correctamente**")

        with col_footer_2:
            st.caption(f"📊 **Total de registros:** {len(df)}")


BondDashboardApp().run()
