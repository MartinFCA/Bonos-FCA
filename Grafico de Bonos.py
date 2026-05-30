import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configuración de la página web
st.set_page_config(page_title="Dashboard de Bonos", layout="wide")

st.title("📊 Análisis y Curva de Rendimiento de Bonos")

# ============================================================================
# ⚙️ CONFIGURACIÓN DEL ARCHIVO: Pon aquí el nombre exacto de tu Excel en GitHub
# ============================================================================
NOMBRE_ARCHIVO_EXCEL = "Bonos Ejemplo.xlsx" 

# Función para cargar datos (usamos caché para que la web vuele en velocidad)
@st.cache_data
def cargar_datos(ruta):
    return pd.read_excel(ruta)

try:
    # Leer datos automáticamente desde el repositorio de GitHub
    df = cargar_datos(NOMBRE_ARCHIVO_EXCEL)
    
    # --- LIMPIEZA DE DATOS AUTOMÁTICA ---
    df = df.dropna(subset=['Year', 'YTW %'])
    if df['YTW %'].max() <= 1.0:
        df['YTW %'] = df['YTW %'] * 100
    if 'Coupon %' in df.columns and df['Coupon %'].max() <= 1.0:
        df['Coupon %'] = df['Coupon %'] * 100

    # Determinar columna de emisores de forma dinámica
    col_emisor = 'Guarantor/Organization' if 'Guarantor/Organization' in df.columns else 'Issuer'
    
    # --- BARRA LATERAL DE FILTROS (ESTILO EXCEL) ---
    st.sidebar.header("Filtros del Portafolio")
    emisores_disponibles = sorted(df[col_emisor].unique())
    
    # El filtro inicia con TODOS los emisores seleccionados por defecto automáticamente
    emisores_seleccionados = st.sidebar.multiselect(
        "Selecciona los emisores a INCLUIR:",
        options=emisores_disponibles,
        default=emisores_disponibles
    )
    
    # Filtrado dinámico en tiempo real
    df_filtrado = df[df[col_emisor].isin(emisores_seleccionados)]
    
    # --- CREACIÓN DEL GRÁFICO INTERACTIVO ---
    fig = go.Figure()
    color_ig = '#FF9944'
    color_hy = '#1F77B4'
    
    # Recalcular curvas de tendencia en base a lo filtrado
    for tipo, color in [('IG', color_ig), ('HY', color_hy)]:
        df_tipo = df_filtrado[df_filtrado['IG - HY'] == tipo]
        if len(df_tipo) >= 3:
            grouped = df_tipo.groupby('Year').agg({'YTW %': 'mean'}).reset_index().sort_values('Year')
            if len(grouped) >= 2:
                z = np.polyfit(grouped['Year'], grouped['YTW %'], 2)
                p = np.poly1d(z)
                years_smooth = np.linspace(grouped['Year'].min(), grouped['Year'].max(), 150)
                
                fig.add_trace(go.Scatter(
                    x=years_smooth, y=p(years_smooth),
                    mode='lines', name=f'Tendencia {tipo}',
                    line=dict(color=color, width=3, dash='dash'),
                    hoverinfo='skip'
                ))

    # Dibujar los puntos de los bonos
    for tipo, color in [('IG', color_ig), ('HY', color_hy)]:
        df_puntos = df_filtrado[df_filtrado['IG - HY'] == tipo]
        if not df_puntos.empty:
            fig.add_trace(go.Scatter(
                x=df_puntos['Year'], y=df_puntos['YTW %'],
                mode='markers', name=tipo,
                marker=dict(size=11, color=color, opacity=0.85, line=dict(width=1.5, color='white')),
                text=[f"<b>{row[col_emisor]}</b><br>Rating: {row['Rating']}<br>YTW: {row['YTW %']:.2f}%<br>Maturity: {row['Maturity']}" for _, row in df_puntos.iterrows()],
                hovertemplate='%{text}<extra></extra>'
            ))
            
    fig.update_layout(
        xaxis_title='<b>Año de Vencimiento</b>', 
        yaxis_title='<b>YTW (%)</b>',
        plot_bgcolor='#FAFAFA', 
        paper_bgcolor='white', 
        height=650,
        margin=dict(l=40, r=40, t=20, b=40)
    )
    
    # --- RENDERIZADO DE PESTAÑAS ---
    tab1, tab2 = st.tabs(["📊 Gráfico Interactivo", "📋 Tabla de Datos"])
    
    with tab1:
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        # Copia para dar formato limpio en la tabla visual
        df_tabla = df_filtrado.copy()
        st.dataframe(df_tabla, use_container_width=True)

except FileNotFoundError:
    st.error(f"❌ No se pudo encontrar el archivo '{NOMBRE_ARCHIVO_EXCEL}' en tu repositorio de GitHub.")
    st.info("Por favor, asegúrate de subir el archivo Excel a la misma carpeta de GitHub y que el nombre coincida exactamente (respetando mayúsculas, minúsculas y extensión .xlsx).")
