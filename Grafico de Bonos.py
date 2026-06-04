import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime  # 📆 Necesario para la conversión matemática de fechas

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

    # 📆 SOLUCIÓN: Convertir a Fecha Real (Datetime) para mantener orden cronológico exacto
    if 'Maturity' in df.columns:
        df['Maturity'] = pd.to_datetime(df['Maturity'], errors='coerce')
        
    # Limpieza de filas vacías basada en la fecha y el rendimiento
    df = df.dropna(subset=['Maturity', 'YTW %'])
        
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
    
    # 1. Dibujar primero las Líneas de Tendencia (Matemática basada en días ordinales)
    for tipo, color in [('IG', color_ig), ('HY', color_hy)]:
        df_tipo = df_filtrado[df_filtrado['IG - HY'] == tipo]
        if len(df_tipo) >= 3:
            grouped = df_tipo.groupby('Maturity').agg({'YTW %': 'mean'}).reset_index().sort_values('Maturity')
            if len(grouped) >= 2:
                # Convertimos las fechas a números (días ordinales) para que np.polyfit funcione
                x_numerico = grouped['Maturity'].apply(lambda x: x.toordinal())
                
                z = np.polyfit(x_numerico, grouped['YTW %'], 2)
                p = np.poly1d(z)
                
                # Generamos un rango continuo de días entre la fecha mínima y máxima
                x_smooth_num = np.linspace(x_numerico.min(), x_numerico.max(), 150)
                # Convertimos esos números de vuelta a fechas reales para Plotly
                x_smooth_dates = [datetime.date.fromordinal(int(x)) for x in x_smooth_num]
                
                fig.add_trace(go.Scatter(
                    x=x_smooth_dates, y=p(x_smooth_num),
                    mode='lines', 
                    name=f'Trend {tipo}',
                    line=dict(color=color, width=2),
                    hoverinfo='skip'
                ))

    # 2. Dibujar los Puntos de los Bonos (Distribuidos por su fecha exacta)
    for tipo, color in [('IG', color_ig), ('HY', color_hy)]:
        df_puntos = df_filtrado[df_filtrado['IG - HY'] == tipo]
        if not df_puntos.empty:
            fig.add_trace(go.Scatter(
                x=df_puntos['Maturity'], y=df_puntos['YTW %'],
                mode='markers', 
                name='Investment Grade (IG)' if tipo == 'IG' else 'High Yield (HY)',
                marker=dict(
                    size=8, 
                    color=color, 
                    opacity=0.75, 
                    line=dict(width=2, color='white') 
                ),
                # Tooltip flotante: Formateamos la fecha directamente aquí (.strftime) para el cuadro visual
                text=[f"<b>{row[col_emisor]}</b><br>" +
                      f"Rating: {row['Rating']}<br>" +
                      f"YTW: {row['YTW %']:.2f}%<br>" +
                      f"Coupon: {row['Coupon %']:.2f}%<br>" +
                      f"Maturity: {row['Maturity'].strftime('%d/%m/%Y')}" 
                      for _, row in df_puntos.iterrows()],
                hovertemplate='%{text}<extra></extra>'
            ))

    # 3. Configuración del Layout (Ejes, fondo y leyenda)
    fig.update_layout(
        title='<b>Curva de Rendimiento de Bonos - Análisis YTW</b>',
        xaxis_title='<b>Fecha de Vencimiento</b>', 
        yaxis_title='<b>YTW - Yield to Worst (%)</b>', 
        plot_bgcolor='#FAFAFA',   
        paper_bgcolor='white',   
        hovermode='closest',
        height=720,              
        font=dict(color='black', family='Arial', size=12), 
        
        # 🛠️ CONFIGURACIÓN DEL EJE X (Eje de tiempo continuo)
        xaxis=dict(
            type='date',         # Declara explícitamente que el eje X maneja fechas
            showline=True,       
            linecolor='black',   
            linewidth=2,         
            ticks='outside',     
            tickcolor='black',   
            mirror=False         
        ),
        
        # 🛠️ CONFIGURACIÓN DEL EJE Y EN NEGRO
        yaxis=dict(
            showline=True,       
            linecolor='black',   
            linewidth=2,         
            ticks='outside',     
            tickcolor='black',   
            ticksuffix='%',      
            mirror=False         
        ),
        
        # Leyenda en negro con letra blanca
        legend=dict(
            x=0.015, 
            y=0.985, 
            bgcolor='rgba(0, 0, 0, 0.85)',    
            bordercolor='black',              
            borderwidth=1,
            font=dict(color='white', size=11) 
        )
    ) 
  
# --- RENDERIZADO EN PESTAÑAS ---
    # 🛠️ CAMBIO: Añadimos la tercera pestaña aquí
    tab1, tab2, tab3 = st.tabs(["📊 Gráfico Interactivo", "📋 Tabla de Datos", "⬆️ Bonos Recomendados"])
    
    with tab1:
        st.plotly_chart(fig, theme=None, use_container_width=True)
        
    with tab2:
        config_visual = {}
        
        # 📅 Formato visual para la columna de Fecha en la tabla sin corromper sus propiedades
        if 'Maturity' in df_filtrado.columns:
            config_visual['Maturity'] = st.column_config.DateColumn(
                format="DD/MM/YYYY"
            )
        
        # 1️⃣ Formato para columnas de Porcentaje
        columnas_a_formatear = ['YTW %', 'Coupon %', 'Prev monthYTW%']
        for col in columnas_a_formatear:
            if col in df_filtrado.columns:
                config_visual[col] = st.column_config.NumberColumn(
                    format="%.2f%%"  
                )
        
        # 2️⃣ Formato para columnas de Dinero / Dólares
        columnas_a_formatear2 = ['Minimum Settlement', 'Outstanding US$']
        for col in columnas_a_formatear2:
            if col in df_filtrado.columns:
                config_visual[col] = st.column_config.NumberColumn(
                    format="$%.2f"  
                )
                    
        # Renderizar la tabla con la configuración visual aplicada
        st.dataframe(
            df_filtrado, 
            use_container_width=True,
            column_config=config_visual
        )
            with tab3:
                    st.subheader("📌 Selección de Bonos Recomendados por el Equipo")
                    st.markdown("Analizamos el mercado actual y destacamos los siguientes activos por su relación riesgo/retorno:")
                    
                    # Verificar si existe la columna en el Excel para evitar que se caiga
                    if 'Recomendado' in df.columns:
                        # Filtramos únicamente los bonos marcados con 'SI'
                        df_recom = df[df['Recomendado'] == 'SI']
                        
                        if not df_recom.empty:
                            # Iteramos sobre cada bono recomendado para armar su "tarjeta"
                            for idx, row in df_recom.iterrows():
                                
                                # Creamos una caja contenedora con borde para cada bono (Estilo Tarjeta)
                                with st.container(border=True):
                                    # Dividimos la tarjeta en 4 columnas visuales
                                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                                    
                                    with c1:
                                        # Nombre del emisor y su clasificación
                                        st.markdown(f"### 🏢 {row[col_emisor]}")
                                        tipo_bono = "Investment Grade (IG)" if row['IG - HY'] == 'IG' else "High Yield (HY)"
                                        st.caption(f"**Categoría:** {tipo_bono} | **Rating:** {row['Rating']}")
                                    
                                    with c2:
                                        # Rendimiento Actual vs Mes Anterior
                                        ytw_actual = row['YTW %']
                                        # Si existe el mes anterior calcula el diferencial, si no, solo muestra el número
                                        if 'Prev monthYTW%' in df.columns and pd.notnull(row['Prev monthYTW%']):
                                            dif = ytw_actual - row['Prev monthYTW%']
                                            st.metric(label="Rendimiento (YTW)", value=f"{ytw_actual:.2f}%", delta=f"{dif:+.2f}% vs mes ant.")
                                        else:
                                            st.metric(label="Rendimiento (YTW)", value=f"{ytw_actual:.2f}%")
                                            
                                    with c3:
                                        # Tasa de cupón
                                        st.metric(label="Cupón Anual", value=f"{row['Coupon %']:.2f}%")
                                        
                                    with c4:
                                        # Fecha de Vencimiento formateada de forma segura
                                        fecha_txt = row['Maturity'].strftime('%d/%m/%Y') if isinstance(row['Maturity'], pd.Timestamp) else str(row['Maturity'])
                                        st.metric(label="Vencimiento", value=fecha_txt)
                        else:
                            st.info("💡 Actualmente no hay ningún bono recomendado")
                    else:
                        st.warning("⚠️ Para activar esta pestaña, necesitas agregar una columna llamada 'Recomendado' en tu archivo Excel con la palabra 'SI' en tus favoritos.")

except FileNotFoundError:
    st.error(f"❌ No se pudo encontrar el archivo '{NOMBRE_ARCHIVO_EXCEL}' en tu repositorio de GitHub.")
    st.info("Por favor, asegúrate de subir el archivo Excel a la misma carpeta de GitHub y que el nombre coincida exactamente.")
