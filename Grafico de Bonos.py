import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configuración de la página web
st.set_page_config(page_title="Dashboard de Bonos", layout="wide")

st.title("📊 Análisis y Curva de Rendimiento de Bonos")
st.write("Sube tu archivo Excel para recalcular las curvas de tendencia en tiempo real.")

# 1. Cargador de archivos interactivo estilo Web
uploaded_file = st.file_uploader("Elige tu archivo Excel de Bonos", type=["xlsx"])

if uploaded_file is not None:
    # Leer datos del archivo subido
    df = pd.read_excel(uploaded_file)
    
    # --- LIMPIEZA DE DATOS (Mismo código de tu notebook) ---
    df = df.dropna(subset=['Year', 'YTW %'])
    if df['YTW %'].max() <= 1.0:
        df['YTW %'] = df['YTW %'] * 100
    if 'Coupon %' in df.columns and df['Coupon %'].max() <= 1.0:
        df['Coupon %'] = df['Coupon %'] * 100

    # 2. FILTRO MULTI-SELECCIÓN ESTILO EXCEL
    # Buscamos la columna de emisores
    col_emisor = 'Guarantor/Organization' if 'Guarantor/Organization' in df.columns else 'Issuer'
    
    st.sidebar.header("Filtros del Portafolio")
    emisores_disponibles = sorted(df[col_emisor].unique())
    
    # El filtro inicia con TODOS los emisores seleccionados por defecto
    emisores_seleccionados = st.sidebar.multiselect(
        "Selecciona los emisores a INCLUIR:",
        options=emisores_disponibles,
        default=emisores_disponibles
    )
    
    # FILTRADO DINÁMICO DEL DATAFRAME
    df_filtrado = df[df[col_emisor].isin(emisores_seleccionados)]
    
    # 3. CREACIÓN DEL GRÁFICO (Se recalcula automáticamente al cambiar el filtro)
    fig = go.Figure()
    color_ig = '#FF9944'
    color_hy = '#1F77B4'
    
    # Recalcular curvas de tendencia basadas ÚNICAMENTE en los datos filtrados
    for tipo, color in [('IG', color_ig), ('HY', color_hy)]:
        df_tipo = df_filtrado[df_filtrado['IG - HY'] == tipo]
        if len(df_tipo) >= 3:  # Necesitamos al menos 3 puntos para una curva cuadrática
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

    # Pintar los puntos del gráfico
    for tipo, color in [('IG', color_ig), ('HY', color_hy)]:
        df_puntos = df_filtrado[df_filtrado['IG - HY'] == tipo]
        if not df_puntos.empty:
            fig.add_trace(go.Scatter(
                x=df_puntos['Year'], y=df_puntos['YTW %'],
                mode='markers', name=tipo,
                marker=dict(size=11, color=color, opacity=0.85, line=dict(width=1.5, color='white')),
                text=[f"<b>{row[col_emisor]}</b><br>Rating: {row['Rating']}<br>YTW: {row['YTW %']:.2f}%" for _, row in df_puntos.iterrows()],
                hovertemplate='%{text}<extra></extra>'
            ))
            
    fig.update_layout(
        xaxis_title='Año de Vencimiento', yaxis_title='YTW (%)',
        plot_bgcolor='#FAFAFA', paper_bgcolor='white', height=600
    )
    
    # PESTAÑAS NATIVAS DE STREAMLIT
    tab1, tab2 = st.tabs(["📊 Gráfico Interactivo", "📋 Tabla de Datos"])
    
    with tab1:
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        # Formatear la tabla visualmente
        df_tabla = df_filtrado.copy()
        st.dataframe(df_tabla, use_container_width=True)

else:
    st.info("💡 Por favor, sube un archivo Excel en el panel central para visualizar el Dashboard.")