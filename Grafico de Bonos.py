import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configuración de la página web (Ancho completo estilo ejecutivo)
st.set_page_config(page_title="Dashboard de Bonos", layout="wide")

st.title("📊 Análisis y Curva de Rendimiento de Bonos")

# ============================================================================
# ⚙️ CONFIGURACIÓN DEL ARCHIVO: Pon aquí el nombre exacto de tu Excel en GitHub
# ============================================================================
NOMBRE_ARCHIVO_EXCEL = "Bonos Ejemplo.xlsx" 

# Función para cargar datos (usamos caché para máxima velocidad de carga)
@st.cache_data
def cargar_datos(ruta):
    return pd.read_excel(ruta)

try:
    # Leer datos automáticamente desde el repositorio de GitHub
    df = cargar_datos(NOMBRE_ARCHIVO_EXCEL)
    
    # --- LIMPIEZA DE DATOS AUTOMÁTICA (IGUAL A COLAB) ---
    df = df.dropna(subset=['Year', 'YTW %'])
    if df['YTW %'].max() <= 1.0:
        df['YTW %'] = df['YTW %'] * 100
    if 'Coupon %' in df.columns and df['Coupon %'].max() <= 1.0:
        df['Coupon %'] = df['Coupon %'] * 100

    # Determinar la columna de emisores de forma dinámica
    col_emisor = 'Guarantor/Organization' if 'Guarantor/Organization' in df.columns else 'Issuer'
    
    # --- BARRA LATERAL DE FILTROS ---
    st.sidebar.header("Filtros del Portafolio")
    emisores_disponibles = sorted(df[col_emisor].unique())
    
    # El filtro inicia con TODOS los emisores seleccionados por defecto automáticamente
    emisores_seleccionados = st.sidebar.multiselect(
        "Selecciona los emisores a INCLUIR:",
        options=emisores_disponibles,
        default=emisores_disponibles
    )
    
    # Filtrado dinámico en tiempo real según la barra lateral
    df_filtrado = df[df[col_emisor].isin(emisores_seleccionados)]
    
    # --- CREACIÓN DEL GRÁFICO INTERACTIVO (ESTILO COLAB) ---
    fig = go.Figure()
    
    # Colores originales de tu Colab
    color_ig = '#FF9944'  # Naranja claro
    color_hy = '#1F77B4'  # Azul oscuro
    
    # 1. Dibujar primero las Líneas de Tendencia (continuas y gruesas)
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
                    mode='lines', 
                    name=f'Trend {tipo}',
                    line=dict(color=color, width=2),  # Grosor 2 continuo original de Colab
                    hoverinfo='skip'
                ))

    # 2. Dibujar los Puntos de los Bonos (Marcadores con borde y opacidad de Colab)
    for tipo, color in [('IG', color_ig), ('HY', color_hy)]:
        df_puntos = df_filtrado[df_filtrado['IG - HY'] == tipo]
        if not df_puntos.empty:
            fig.add_trace(go.Scatter(
                x=df_puntos['Year'], y=df_puntos['YTW %'],
                mode='markers', 
                name='Investment Grade (IG)' if tipo == 'IG' else 'High Yield (HY)',
                marker=dict(
                    size=8, 
                    color=color, 
                    opacity=0.75,  # Opacidad exacta de Colab
                    line=dict(width=2, color='white')  # Borde blanco marcado
                ),
                # Tooltip flotante con la estructura exacta que tenías (con Cupón incluido)
                text=[f"<b>{row[col_emisor]}</b><br>" +
                      f"Rating: {row['Rating']}<br>" +
                      f"YTW: {row['YTW %']:.2f}%<br>" +
                      f"Coupon: {row['Coupon %']:.2f}%<br>" +
                      f"Maturity: {row['Maturity']}" 
                      for _, row in df_puntos.iterrows()],
                hovertemplate='%{text}<extra></extra>'
            ))
            
    # 3. Configuración del Layout idéntico al de Colab (Ejes, fondo y leyenda)
    fig.update_layout(
        title='<b>Curva de Rendimiento de Bonos - Análisis YTW</b>',
        xaxis_title='<b>Año de Vencimiento</b>', 
        yaxis_title='<b>YTW - Yield to Worst (%)</b>', 
        plot_bgcolor='#FAFAFA',   # Fondo gris muy claro de la cuadrícula (puedes cambiarlo a 'white' si lo quieres blanco puro)
        paper_bgcolor='white',   # Fondo exterior del gráfico blanco
        hovermode='closest',
        height=720,              
        
        # TEXTO GENERAL EN NEGRO
        font=dict(
            family='Arial', 
            size=12, 
            color='black'  # <--- Esto fuerza a que todo el texto del gráfico sea negro puro
        )
    )
        
        # LEYENDA EN NEGRO INTERACTIVA
        legend=dict(
            x=0.015, 
            y=0.985, 
            bgcolor='rgba(0, 0, 0, 0.85)',    # Fondo negro elegante (85% de opacidad para que no tape 100% los puntos de atrás)
            bordercolor='black',              # Borde negro para cerrar el cuadro
            borderwidth=1,
            font=dict(color='white', size=11) # ¡Clave! Letra blanca para que contraste perfectamente sobre el fondo negro
        )
    )
    
    # --- RENDERIZADO EN PESTAÑAS ---
    tab1, tab2 = st.tabs(["📊 Gráfico Interactivo", "📋 Tabla de Datos"])
    
    with tab1:
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        # Mostrar tabla de datos formateada
        st.dataframe(df_filtrado, use_container_width=True)

except FileNotFoundError:
    st.error(f"❌ No se pudo encontrar el archivo '{NOMBRE_ARCHIVO_EXCEL}' en tu repositorio de GitHub.")
    st.info("Por favor, asegúrate de subir el archivo Excel a la misma carpeta de GitHub y que el nombre coincida exactamente.")
