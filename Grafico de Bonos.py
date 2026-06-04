import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime  # 📆 Necesario para la conversión matemática de fechas

# Configuración de la página web (Ancho completo)
st.set_page_config(
    page_title="Dashboard de Bonos", 
    layout="wide"
)

# 🔒 MEDIDA DE SEGURIDAD: Ocultamos menús de desarrollo pero DEJAMOS el header visible para evitar errores
ocultar_estilos_streamlit = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(ocultar_estilos_streamlit, unsafe_allow_html=True)

st.title("📊 Curva de Rendimiento de Bonos")
st.caption("📅 Análisis Visual de Activos • Actualizado al 15 de Mayo")

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
    
    # ============================================================================
    # 🛠️ SOLUCIÓN: PANEL ÚNICO DE FILTROS Y MÉTRICAS (PREMIUM Y SIEMPRE VISIBLE)
    # ============================================================================
    # Reemplazamos la barra lateral por un contenedor expandible en la pantalla principal
    with st.expander("⚙️ CONFIGURACIÓN: Filtros del Portafolio y Resumen en Tiempo Real", expanded=True):
        
        emisores_disponibles = sorted(df[col_emisor].unique())
        
        # Filtro de emisores en la pantalla principal
        emisores_seleccionados = st.multiselect(
            "Selecciona los emisores a INCLUIR en las curvas de rendimiento:",
            options=emisores_disponibles,
            default=emisores_disponibles
        )
        
        # Filtrado dinámico inmediato
        df_filtrado = df[df[col_emisor].isin(emisores_seleccionados)]
        
        st.markdown("<hr style='margin: 15px 0; border: 0; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
        
        # Las métricas ahora viven aquí dentro, justo abajo de lo que seleccionas
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(label="🏢 Activos bajo Análisis", value=f"{len(df_filtrado)} bonos")
        with m2:
            avg_ytw = df_filtrado['YTW %'].mean() if not df_filtrado.empty else 0
            st.metric(label="📈 Rendimiento Promedio (YTW)", value=f"{avg_ytw:.2f}%")
        with m3:
            avg_coupon = df_filtrado['Coupon %'].mean() if not df_filtrado.empty else 0
            st.metric(label="💵 Cupón Promedio Anual", value=f"{avg_coupon:.2f}%")

    st.markdown("<br>", unsafe_allow_html=True) 

    # --- CREACIÓN DEL GRÁFICO INTERACTIVO (Fondo limpio institucional) ---
    fig = go.Figure()
    
    color_ig = '#FF9944'  # Naranja claro
    color_hy = '#1F77B4'  # Azul oscuro
    
    # 1. Dibujar primero las Líneas de Tendencia
    for tipo, color in [('IG', color_ig), ('HY', color_hy)]:
        df_tipo = df_filtrado[df_filtrado['IG - HY'] == tipo]
        if len(df_tipo) >= 3:
            grouped = df_tipo.groupby('Maturity').agg({'YTW %': 'mean'}).reset_index().sort_values('Maturity')
            if len(grouped) >= 2:
                x_numerico = grouped['Maturity'].apply(lambda x: x.toordinal())
                
                z = np.polyfit(x_numerico, grouped['YTW %'], 2)
                p = np.poly1d(z)
                
                x_smooth_num = np.linspace(x_numerico.min(), x_numerico.max(), 150)
                x_smooth_dates = [datetime.date.fromordinal(int(x)) for x in x_smooth_num]
                
                fig.add_trace(go.Scatter(
                    x=x_smooth_dates, y=p(x_smooth_num),
                    mode='lines', 
                    name=f'Trend {tipo}',
                    line=dict(color=color, width=2.5),
                    hoverinfo='skip'
                ))

    # 2. Dibujar los Puntos de los Bonos
    for tipo, color in [('IG', color_ig), ('HY', color_hy)]:
        df_puntos = df_filtrado[df_filtrado['IG - HY'] == tipo]
        if not df_puntos.empty:
            fig.add_trace(go.Scatter(
                x=df_puntos['Maturity'], y=df_puntos['YTW %'],
                mode='markers', 
                name='Investment Grade (IG)' if tipo == 'IG' else 'High Yield (HY)',
                marker=dict(
                    size=9, 
                    color=color, 
                    opacity=0.82, 
                    line=dict(width=1.5, color='white') 
                ),
                text=[f"<b>{row[col_emisor]}</b><br>" +
                      f"Rating: {row['Rating']}<br>" +
                      f"YTW: {row['YTW %']:.2f}%<br>" +
                      f"Coupon: {row['Coupon %']:.2f}%<br>" +
                      f"Maturity: {row['Maturity'].strftime('%d/%m/%Y')}" 
                      for _, row in df_puntos.iterrows()],
                hovertemplate='%{text}<extra></extra>'
            ))

    # 3. Configuración del Layout (Ejes y leyenda clara flotante)
    fig.update_layout(
        title='<b>Análisis Dinámico de Curvas de Rendimiento (YTW)</b>',
        xaxis_title='<b>Fecha de Vencimiento</b>', 
        yaxis_title='<b>YTW - Yield to Worst (%)</b>', 
        plot_bgcolor='#FDFDFD',   
        paper_bgcolor='white',   
        hovermode='closest',
        height=660,              
        font=dict(color='#222222', family='Arial', size=12), 
        
        xaxis=dict(
            type='date',         
            showline=True,       
            linecolor='#444444',   
            linewidth=1.5,         
            ticks='outside',     
            tickcolor='#444444',   
            showgrid=True,
            gridcolor='#ECECEC', 
            mirror=False         
        ),
        yaxis=dict(
            showline=True,       
            linecolor='#444444',   
            linewidth=1.5,         
            ticks='outside',     
            tickcolor='#444444',   
            ticksuffix='%',      
            showgrid=True,
            gridcolor='#ECECEC', 
            mirror=False         
        ),
        legend=dict(
            x=0.015, 
            y=0.985, 
            bgcolor='rgba(255, 255, 255, 0.92)', 
            bordercolor='#CCCCCC',              
            borderwidth=1,
            font=dict(color='black', size=11) 
        )
    ) 
  
    # --- RENDERIZADO EN PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📊 Gráfico Interactivo", "📋 Tabla de Datos", "⬆️ Bonos Recomendados"])
    
    with tab1:
        st.plotly_chart(fig, theme=None, use_container_width=True)
        
    with tab2:
        config_visual = {}
        
        if 'Maturity' in df_filtrado.columns:
            config_visual['Maturity'] = st.column_config.DateColumn(
                format="DD/MM/YYYY"
            )
        
        columnas_a_formatear = ['YTW %', 'Coupon %', 'Prev monthYTW%']
        for col in columnas_a_formatear:
            if col in df_filtrado.columns:
                config_visual[col] = st.column_config.NumberColumn(
                    format="%.2f%%"  
                )
        
        columnas_a_formatear2 = ['Minimum Settlement', 'Outstanding US$']
        for col in columnas_a_formatear2:
            if col in df_filtrado.columns:
                config_visual[col] = st.column_config.NumberColumn(
                    format="$%.2f"  
                )
                    
        st.dataframe(
            df_filtrado, 
            use_container_width=True,
            column_config=config_visual
        )            
            
    with tab3:
        st.subheader("📌 Selección de Bonos Recomendados por el Equipo")
        st.markdown("Analizamos el mercado actual y destacamos los siguientes activos por su atractiva relación riesgo/retorno:")
        
        col_recom = 'Recomendados' if 'Recomendados' in df.columns else ('Recomendado' if 'Recomendado' in df.columns else None)
        
        if col_recom:
            df_recom = df[df[col_recom] == 'SI']
            
            if not df_recom.empty:
                for idx, row in df_recom.iterrows():
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                        
                        with c1:
                            st.markdown(f"### 🏢 {row[col_emisor]}")
                            tipo_bono = "Investment Grade (IG)" if row['IG - HY'] == 'IG' else "High Yield (HY)"
                            st.caption(f"**Categoría:** {tipo_bono} | **Rating:** {row['Rating']}")
                        
                        with c2:
                            ytw_actual = row['YTW %']
                            if 'Prev monthYTW%' in df.columns and pd.notnull(row['Prev monthYTW%']):
                                dif = ytw_actual - row['Prev monthYTW%']
                                st.metric(label="Rendimiento (YTW)", value=f"{ytw_actual:.2f}%", delta=f"{dif:+.2f}% vs mes ant.")
                            else:
                                st.metric(label="Rendimiento (YTW)", value=f"{ytw_actual:.2f}%")
                                
                        with c3:
                            st.metric(label="Cupón Anual", value=f"{row['Coupon %']:.2f}%")
                            
                        with c4:
                            fecha_txt = row['Maturity'].strftime('%d/%m/%Y') if isinstance(row['Maturity'], pd.Timestamp) else str(row['Maturity'])
                            st.metric(label="Vencimiento", value=fecha_txt)
            else:
                st.info("💡 Actualmente no hay ningún bono recomendado en la lista.")
        else:
            st.warning("⚠️ Para activar esta pestaña, necesitas agregar una columna llamada 'Recomendados' o 'Recomendado' en tu archivo Excel con la palabra 'SI' en tus favoritos.")

except FileNotFoundError:
    st.error(f"❌ No se pudo encontrar el archivo '{NOMBRE_ARCHIVO_EXCEL}' en tu repositorio de GitHub.")
    st.info("Por favor, asegúrate de subir el archivo Excel a la misma carpeta de GitHub y que el nombre coincida exactamente.")
