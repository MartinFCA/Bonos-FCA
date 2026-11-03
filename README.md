# FCA Asset Management · Plataforma de inversiones

Aplicación Streamlit con el análisis de bonos corporativos, ETFs de renta fija y los reportes Market Views del comité.

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run Inicio.py
```

## Estructura

```
Inicio.py              Punto de entrada: configuración y menú de navegación
app_pages/             Una página por archivo (Inicio, Bonos, Estrategia, Recursos)
fca/
  config.py            Rutas de datos, colores y constantes de marca
  ui.py                Encabezado, tarjetas, KPIs, pie de página (HTML escapado)
  charts.py            Gráficos Altair con estilo unificado
  data/                Carga y limpieza de datos (sin dependencias de UI)
    cleaning.py        Conversión tolerante de números, porcentajes y fechas
    bonds.py           Universo de bonos y curva de tendencia
    etfs.py            ETFs de renta fija
    reports.py         Catálogo de reportes Market Views
data/
  bonos.xlsx           Universo de bonos
  etfs.xlsx            ETFs
  market_views/        Reportes HTML: FCA_Market_Views_<Mes><Año>[_<versión>].html
.streamlit/config.toml Tema visual y opciones de seguridad
```

## Actualizar datos

- **Bonos / ETFs**: reemplazar `data/bonos.xlsx` o `data/etfs.xlsx` manteniendo los encabezados.
  Columnas obligatorias de bonos: `Guarantor/Organization` (o `Issuer`), `IG - HY`, `Maturity`, `YTW %`.
  Los porcentajes pueden venir como decimales (0.05) o en puntos (5). Las celdas con texto inválido
  se dejan vacías y se informan en "Avisos de calidad de datos", sin romper la página.
  Los bonos con decisión `Done` no se muestran.
- **Market Views**: copiar el HTML nuevo en `data/market_views/` con el formato de nombre indicado.
  El más reciente aparece primero automáticamente.

La caché se invalida sola cuando cambia un archivo.

## Agregar una sección

1. Crear `app_pages/mi_seccion.py` empezando con `ui.page_setup("Título", "Subtítulo")`.
2. Agregarla a `PAGES` en `Inicio.py`.

## Publicar con dominio propio

Streamlit Community Cloud no admite dominios propios. Para usar uno:

```bash
docker build -t fca-app .
docker run -p 8501:8501 fca-app
```

La imagen se puede desplegar en cualquier servicio de contenedores (Google Cloud Run, Azure Container Apps,
AWS App Runner, Railway, Render) y apuntar el dominio a ese servicio. Si los datos dejan de ser públicos,
conviene agregar autenticación (`st.login` con un proveedor OIDC) antes de publicar.
