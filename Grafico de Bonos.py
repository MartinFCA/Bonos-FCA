import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import requests
import io
from urllib.error import URLError
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 🎨 CONFIGURACIÓN VISUAL Y TEMA
# ============================================================================
TEMA = {
    'bg_principal': '#F8F9FA',
    'color_IG': '#00A651',      # Verde profesional
    'color_HY': '#D32F2F',      # Rojo profesional
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

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Bonos",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# ============================================================================
# 🔒 OCULTAR ELEMENTOS DE STREAMLIT
# ============================================================================
ocultar_estilos = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Métricas centradas */
    div[data-testid="stMetric"] {text-align: center;}
    div[data-testid="stMetricValue"] {font-size: 28px; font-weight: bold;}
    div[data-testid="stMetricLabel"] {font-size: 12px; text-transform: uppercase; color: #666;}
    
    /* Tabs mejoradas */
    button[data-baseweb="tab"] {
        background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%);
        border-radius: 8px 8px 0 0;
    }
    
    /* Scrollbar personalizado */
    ::-webkit-scrollbar {width: 8px;}
    ::-webkit-scrollbar-track {background: #f1f1f1;}
    ::-webkit-scrollbar-thumb {background: #888; border-radius: 4px;}
    
    /* Expanders mejorados */
    div[data-testid="stExpander"] {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        background: linear-gradient(135deg, #FAFAFA 0%, #FFFFFF 100%);
    }
</style>
"""
st.markdown(ocultar_estilos, unsafe_allow_html=True)

## ============================================================================
# ⚙️ CONFIGURACIÓN: ENLACE DE ONEDRIVE (Tu enlace)
# ============================================================================
 
# ✅ TU ENLACE ACTUAL:
#TU_ENLACE_ONEDRIVE = "https://1drv.ms/x/c/74b4ddab53a69d15/IQBOAEOpBkSGR6-CgUzs9vH-ARIfQ_2GFrbRQRZ9mmWzIsI?e=VdNhhY"
 
# Convertimos a URL de descarga directa
#ONEDRIVE_URLS = [
 #   "https://1drv.ms/x/c/74b4ddab53a69d15!IQBOAEOpBkSGR6-CgUzs9vH-ARIfQ_2GFrbRQRZ9mmWzIsI?download=1",
  #  "https://1drv.ms/download?resid=74b4ddab53a69d15!IQBOAEOpBkSGR6-CgUzs9vH-ARIfQ_2GFrbRQRZ9mmWzIsI",
   # "https://onedrive.live.com/download?resid=74b4ddab53a69d15!IQBOAEOpBkSGR6-CgUzs9vH-ARIfQ_2GFrbRQRZ9mmWzIsI",
#]
 
# ============================================================================
 #Para pruebas locales, puedes usar un archivo local:
 #NOMBRE_ARCHIVO = "Bonos Ejemplo.xlsx"  # Descomenta para usar archivo local

# ============================================================================
# 🛠️ FUNCIONES AUXILIARES
# ============================================================================
 
@st.cache_resource
def get_session_state():
    """Mantiene estado entre reruns"""
    if 'datos_cargados' not in st.session_state:
        st.session_state.datos_cargados = False
        st.session_state.error_mensaje = None
    return st.session_state
 
@st.cache_data(ttl=300)
def cargar_datos_github():
    """Carga el archivo Excel desde el repositorio GitHub"""
    try:
        # URL raw del archivo en GitHub
        url = "https://raw.githubusercontent.com/tu-usuario/bonos-fca/main/Bonos%20-%20FCA%20Asset%20Management.xlsm"
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return pd.read_excel(io.BytesIO(response.content)), None
        else:
            return None, f"Error descargando desde GitHub: {response.status_code}"
    except Exception as e:
        return None, f"Error: {str(e)}"

 
def validar_y_preparar_datos(df):
    """
    Valida estructura del Excel y prepara datos para análisis.
    """
    # Columnas requeridas
    columnas_requeridas = ['Maturity', 'YTW %', 'Coupon %', 'IG - HY', 'Rating']
    faltantes = [col for col in columnas_requeridas if col not in df.columns]
    
    if faltantes:
        st.error(f"❌ **Columnas faltantes en Excel:**\n{', '.join(faltantes)}")
        st.info("Tu Excel debe contener estas columnas: " + ", ".join(columnas_requeridas))
        st.write("**Columnas disponibles en tu archivo:**")
        st.code(", ".join(df.columns.tolist()))
        return None
    
    try:
        # Convertir fechas
        df['Maturity'] = pd.to_datetime(df['Maturity'], errors='coerce')
        
        # Normalizar porcentajes
        columnas_porcentaje = ['YTW %', 'Coupon %', 'Prev monthYTW%']
        for col in columnas_porcentaje:
            if col in df.columns:
                if df[col].max() <= 1.0:
                    df[col] = df[col] * 100
        
        # Limpiar filas vacías
        df = df.dropna(subset=['Maturity', 'YTW %'])
        
        if df.empty:
            st.warning("⚠️ No hay datos válidos después de limpiar filas vacías.")
            return None
        
        return df
    
    except Exception as e:
        st.error(f"❌ Error preparando datos: {str(e)}")
        return None
 
def obtener_col_emisor(df):
    """Detecta dinámicamente la columna de emisores"""
    for col in ['Guarantor/Organization', 'Issuer', 'Emisor', 'issuer']:
        if col in df.columns:
            return col
    for col in df.columns:
        if df[col].dtype == 'object' and col not in ['IG - HY', 'Rating']:
            return col
    return None
 
def agregar_tendencia(fig, df_tipo, tipo, color):
    """Agrega línea de tendencia polinómica al gráfico"""
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
 
def agregar_puntos(fig, df_puntos, tipo, color, col_emisor, nombre_tipo):
    """Agrega puntos de bonos al gráfico"""
    if df_puntos.empty:
        return
    
    try:
        textos_hover = []
        for _, row in df_puntos.iterrows():
            fecha_txt = row['Maturity'].strftime('%d/%m/%Y') if isinstance(row['Maturity'], pd.Timestamp) else str(row['Maturity'])
            rating_color = RATING_COLORS.get(str(row['Rating']), '#999')
            
            texto = (f"<b style='font-size: 14px; color: {rating_color};'>{row[col_emisor]}</b><br>"
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
 
def crear_grafico_interactivo(df_filtrado, col_emisor):
    """Crea el gráfico principal de curvas de rendimiento"""
    fig = go.Figure()
    
    for tipo, color in [('IG', TEMA['color_IG']), ('HY', TEMA['color_HY'])]:
        df_tipo = df_filtrado[df_filtrado['IG - HY'] == tipo]
        if not df_tipo.empty and len(df_tipo) >= 3:
            agregar_tendencia(fig, df_tipo, tipo, color)
    
    for tipo, color, nombre in [('IG', TEMA['color_IG'], 'Investment Grade (IG)'),
                                 ('HY', TEMA['color_HY'], 'High Yield (HY)')]:
        df_puntos = df_filtrado[df_filtrado['IG - HY'] == tipo]
        if not df_puntos.empty:
            agregar_puntos(fig, df_puntos, tipo, color, col_emisor, nombre)
    
    fig.update_layout(
        title={
            'text': '<b>Análisis Dinámico de Curvas de Rendimiento (YTW)</b>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': TEMA['color_texto']}
        },
        xaxis_title='<b>Fecha de Vencimiento</b>',
        yaxis_title='<b>YTW - Yield to Worst (%)</b>',
        plot_bgcolor=TEMA['bg_principal'],
        paper_bgcolor='white',
        hovermode='closest',
        height=700,
        font=dict(
            color=TEMA['color_texto'],
            family=TEMA['font_principal'],
            size=12
        ),
        xaxis=dict(
            type='date',
            showline=True,
            linecolor=TEMA['color_texto'],
            linewidth=2,
            ticks='outside',
            tickcolor=TEMA['color_texto'],
            showgrid=True,
            gridcolor=TEMA['color_grid'],
            mirror=False
        ),
        yaxis=dict(
            showline=True,
            linecolor=TEMA['color_texto'],
            linewidth=2,
            ticks='outside',
            tickcolor=TEMA['color_texto'],
            ticksuffix='%',
            showgrid=True,
            gridcolor=TEMA['color_grid'],
            mirror=False
        ),
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255, 255, 255, 0.95)',
            bordercolor=TEMA['color_border'],
            borderwidth=2,
            font=dict(color=TEMA['color_texto'], size=12)
        ),
        margin=dict(l=70, r=50, t=100, b=80)
    )
    
    return fig
 
def mostrar_bono_recomendado(row, col_emisor):
    """Muestra una tarjeta mejorada de bono recomendado"""
    rating = str(row['Rating'])
    color_rating = RATING_COLORS.get(rating, '#999')
    tipo_bono = "Investment Grade (IG)" if row['IG - HY'] == 'IG' else "High Yield (HY)"
    fecha_txt = row['Maturity'].strftime('%d/%m/%Y') if isinstance(row['Maturity'], pd.Timestamp) else str(row['Maturity'])
    
    html_card = f"""
    <div style="
        border-left: 6px solid {color_rating};
        padding: 18px;
        border-radius: 10px;
        background: linear-gradient(135deg, #FAFAFA 0%, #FFFFFF 100%);
        margin: 12px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 1px solid #E8E8E8;
    ">
        <h3 style="margin: 0 0 12px 0; color: #222; display: flex; align-items: center;">
            🏢 {row[col_emisor]}
            <span style="
                display: inline-block;
                background-color: {color_rating};
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            ">{rating}</span>
        </h3>
        
        <p style="margin: 8px 0; color: #666; font-size: 13px;">
            <b>Categoría:</b> {tipo_bono}
        </p>
        
        <div style="
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #E0E0E0;
        ">
            <div style="text-align: center;">
                <div style="font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 0.5px;">Rendimiento</div>
                <div style="font-size: 18px; font-weight: bold; color: {color_rating};">{row['YTW %']:.2f}%</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 0.5px;">Cupón</div>
                <div style="font-size: 18px; font-weight: bold; color: #222;">{row['Coupon %']:.2f}%</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 0.5px;">Vencimiento</div>
                <div style="font-size: 16px; font-weight: bold; color: #222;">{fecha_txt}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html_card, unsafe_allow_html=True)
 
# ============================================================================
# 📊 TÍTULO Y HEADER
# ============================================================================
col_header_1, col_header_2 = st.columns([0.85, 0.15])
 
with col_header_1:
    st.title("📊 Curva de Rendimiento de Bonos")
    st.caption("📅 FCA Asset Management • Dashboard Interactivo")
 
with col_header_2:
    if st.button("🔄 Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
 
# ============================================================================
# 📥 CARGAR DATOS
# ============================================================================
st.markdown("")
 
with st.spinner("⏳ Conectando a OneDrive (esto puede tomar 10-15 segundos)..."):
    df, error = cargar_datos_github()
 
if error:
    st.error(error)
    
    with st.expander("🔧 Opciones Alternativas de Carga", expanded=True):
        st.markdown("""
        ### Si OneDrive no funciona, tienes estas opciones:
        
        **Opción 1: Descargar manualmente y usar archivo local**
        1. Descarga `Bonos - FCA Asset Management.xlsm` desde OneDrive
        2. Colócalo en la misma carpeta que el script
        3. Usa esta línea en el código:
        ```python
        df = pd.read_excel("Bonos - FCA Asset Management.xlsm")
        ```
        
        **Opción 2: Usar Google Drive (más confiable)**
        1. Sube el archivo a Google Drive
        2. Haz clic derecho → "Compartir" → Cualquiera puede ver
        3. Obtén el ID del archivo
        4. Usa:
        ```python
        DRIVE_URL = "https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"
        df = pd.read_excel(DRIVE_URL)
        ```
        
        **Opción 3: Convertir XLSM a XLSX**
        - Abre el archivo en Excel/Calc
        - Guardar como: .xlsx (no macro)
        - Intenta de nuevo
        """)
    st.stop()
 
# Validar datos
df = validar_y_preparar_datos(df)
if df is None or df.empty:
    st.stop()
 
# Detectar columna emisor
col_emisor = obtener_col_emisor(df)
if not col_emisor:
    st.error("❌ No se encontró columna de emisores en el Excel")
    st.info("Columnas detectadas: " + ", ".join(df.columns.tolist()))
    st.stop()
 
# ============================================================================
# 🔧 PANEL DE FILTROS
# ============================================================================
st.markdown("")
 
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
    
    df_filtrado = df[
        (df[col_emisor].isin(emisores_seleccionados)) &
        (df['IG - HY'].isin(tipos_seleccionados))
    ]
    
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
        st.metric(
            label="📈 YTW Promedio",
            value=f"{ytw_promedio:.2f}%"
        )
    
    with m3:
        coupon_promedio = df_filtrado['Coupon %'].mean() if not df_filtrado.empty else 0
        st.metric(
            label="💵 Cupón Promedio",
            value=f"{coupon_promedio:.2f}%"
        )
    
    with m4:
        ig_count = len(df_filtrado[df_filtrado['IG - HY'] == 'IG'])
        hy_count = len(df_filtrado[df_filtrado['IG - HY'] == 'HY'])
        st.metric(
            label="📊 Distribución",
            value=f"IG: {ig_count} | HY: {hy_count}"
        )
 
# ============================================================================
# 📊 GRÁFICO Y PESTAÑAS
# ============================================================================
st.markdown("")
 
fig = crear_grafico_interactivo(df_filtrado, col_emisor)
 
tab1, tab2, tab3 = st.tabs(["📊 Gráfico Interactivo", "📋 Tabla de Datos", "⭐ Bonos Recomendados"])
 
with tab1:
    st.plotly_chart(fig, theme=None, use_container_width=True)
    st.markdown("""
    **💡 Cómo interpretar el gráfico:**
    - **Eje X**: Fecha de vencimiento | **Eje Y**: Rendimiento (YTW)
    - **Líneas**: Tendencias polinómicas | **Puntos**: Bonos individuales
    - **Verde (IG)**: Investment Grade | **Rojo (HY)**: High Yield
    """)
 
with tab2:
    config_visual = {}
    
    if 'Maturity' in df_filtrado.columns:
        config_visual['Maturity'] = st.column_config.DateColumn(format="DD/MM/YYYY")
    
    for col in ['YTW %', 'Coupon %', 'Prev monthYTW%']:
        if col in df_filtrado.columns:
            config_visual[col] = st.column_config.NumberColumn(format="%.2f%%")
    
    st.dataframe(
        df_filtrado.sort_values('Maturity'),
        use_container_width=True,
        column_config=config_visual,
        height=600
    )
    
    csv = df_filtrado.to_csv(index=False)
    st.download_button(
        label="📥 Descargar como CSV",
        data=csv,
        file_name="bonos_analisis.csv",
        mime="text/csv"
    )
 
with tab3:
    st.subheader("⭐ Bonos Recomendados")
    
    col_recom = None
    for nombre_col in ['Recomendados', 'Recomendado', 'Recomendación', 'Recomend']:
        if nombre_col in df.columns:
            col_recom = nombre_col
            break
    
    if col_recom:
        df_recom = df_filtrado[df_filtrado[col_recom].astype(str).str.upper() == 'SI']
        
        if not df_recom.empty:
            for idx, row in df_recom.iterrows():
                mostrar_bono_recomendado(row, col_emisor)
        else:
            st.info("💡 No hay bonos recomendados en la selección actual.")
    else:
        st.warning("""
        ⚠️ Para activar esta sección, agrega una columna en tu Excel:
        - **'Recomendados'** con valores 'SI' o 'NO'
        """)
 
# ============================================================================
# 📌 FOOTER
# ============================================================================
st.markdown("<hr style='margin: 40px 0; border: 0; border-top: 2px solid #E0E0E0;'>", unsafe_allow_html=True)
 
col_footer_1, col_footer_2, col_footer_3 = st.columns([0.4, 0.3, 0.3])
 
with col_footer_1:
    st.caption(f"📅 **Datos cargados correctamente**")
 
with col_footer_2:
    st.caption(f"📊 **Total de registros:** {len(df)}")
 
with col_footer_3:
    st.caption("🔄 Se actualiza automáticamente cada 5 minutos")
