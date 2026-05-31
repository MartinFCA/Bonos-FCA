import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configuración de la página web (Ancho completo estilo ejecutivo)
st.set_page_config(page_title="Dashboard de Bonos", layout="wide")

# 🔒 MEDIDA DE SEGURIDAD: Ocultar menús de desarrollo y marcas de Streamlit
ocultar_estilos_streamlit = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
# CORRECCIÓN: Cambiado 'unsafe_with_html' por 'unsafe_allow_html'
st.markdown(ocultar_estilos_streamlit, unsafe_allow_html=True)

st.title("📊 Curva de Rendimiento de Bonos")
st.caption("📅 Actualizado al 15 de Mayo")

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

    # 📆 SOLUCIÓN: Formatear la columna de fecha para quitar las horas
    if 'Maturity' in df.columns:
        # Convierte a fecha y la formatea como Día/Mes/Año (ej: 15/05/2028)
        df['Maturity'] = pd.to_datetime(df['Maturity'], errors='coerce').dt.strftime('%d/%m/%Y')
        
# 📊 Normalizar todas las columnas de porcentaje a escala 0-100
    columnas_porcentaje = ['YTW %', 'Coupon %', 'Prev monthYTW%']
    for col in columnas_porcentaje:
        if col in df.columns and df[col].max() <= 1.0:
            df[col] = df[col] * 100

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
    # 3. Configuración del Layout (Ejes, fondo y leyenda)
    fig.update_layout(
        title='<b>Curva de Rendimiento de Bonos - Análisis YTW</b>',
        xaxis_title='<b>Año de Vencimiento</b>', 
        yaxis_title='<b>YTW - Yield to Worst (%)</b>', 
        plot_bgcolor='#FAFAFA',   
        paper_bgcolor='white',   
        hovermode='closest',
        height=720,              
        font=dict(color='black', family='Arial', size=12), # <--- Letra negra para todo el gráfico
        # 🛠️ CONFIGURACIÓN DEL EJE X EN NEGRO
        xaxis=dict(
            showline=True,       # Activa la línea base del eje X
            linecolor='black',   # Color negro para la línea
            linewidth=2,         # Grosor de la línea del eje
            ticks='outside',     # Saca las pequeñas marcas de los años hacia afuera
            tickcolor='black',   # Color negro para las marcas de los años
            mirror=False         # Evita que se duplique la línea arriba del gráfico
        ),
        
        # 🛠️ CONFIGURACIÓN DEL EJE Y EN NEGRO
        yaxis=dict(
            showline=True,       # Activa la línea base del eje Y
            linecolor='black',   # Color negro para la línea
            linewidth=2,         # Grosor de la línea del eje
            ticks='outside',     # Saca las pequeñas marcas de los porcentajes hacia afuera
            tickcolor='black',   # Color negro para las marcas de los porcentajes
            ticksuffix='%',      # 🌟 LA CLAVE: Agrega el símbolo de porcentaje a cada número del eje
            mirror=False         # Evita que se duplique la línea a la derecha del gráfico
        ),
        
        # Leyenda en negro con letra blanca (para que contraste internamente)
        legend=dict(
            x=0.015, 
            y=0.985, 
            bgcolor='rgba(0, 0, 0, 0.85)',    
            bordercolor='black',              
            borderwidth=1,
            font=dict(color='white', size=11) 
        )
    ) # <--- ASEGÚRATE DE QUE ESTE PARÉNTESIS ESTÉ CERRADO
  
    
    # --- RENDERIZADO EN PESTAÑAS ---
    tab1, tab2 = st.tabs(["📊 Gráfico Interactivo", "📋 Tabla de Datos"])
    
    with tab1:
        # MODIFICA ESTA LÍNEA AGREGANDO theme=None:
        st.plotly_chart(fig, theme=None, use_container_width=True)
        
    with tab2:
        # Crear la configuración de formato para las columnas de la tabla
        config_visual = {}
        
        # Columnas a las que queremos ponerle % al final y 2 decimales
        columnas_a_formatear = ['YTW %', 'Coupon %', 'Prev monthYTW%']
        
        for col in columnas_a_formatear:
            if col in df_filtrado.columns:
                # 🛠️ CORRECCIÓN: Quitamos 'suffix' y usamos '%%' dentro del format
                config_visual[col] = st.column_config.NumberColumn(
                    format="%.2f%%"  # El '%%' le dice a Python que pinte un '%' real al final del número
                )
        
            columnas_a_formatear2 = ['Minimum Settlement', 'Outstanding US$']
             for col in columnas_a_formatear2:
                        if col in df_filtrado.columns:
                            # 🛠️ CORRECCIÓN: Quitamos 'suffix' y usamos '%%' dentro del format
                            config_visual[col] = st.column_config.NumberColumn(
                                format="$%.2f"  # El '%%' le dice a Python que pinte un '%' real al final del número
                            )
                    
        # Renderizar la tabla con la configuración visual aplicada
        st.dataframe(
            df_filtrado, 
            use_container_width=True,
            column_config=config_visual
        )
                

except FileNotFoundError:
    st.error(f"❌ No se pudo encontrar el archivo '{NOMBRE_ARCHIVO_EXCEL}' en tu repositorio de GitHub.")
    st.info("Por favor, asegúrate de subir el archivo Excel a la misma carpeta de GitHub y que el nombre coincida exactamente.")
