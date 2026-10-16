import streamlit as st
import pandas as pd

# Importamos los reportes
from dashboards import popularidad, popularidad_generos, votos_generos
from dashboards import popularidad_idiomas
from dashboards import votos_actores_directores
from dashboards import votos_idiomas
from dashboards import cuaderno

st.set_page_config(page_title="Sistema de Reportes", layout="wide")

# --- INICIALIZAR MEMORIA DEL CUADERNO ---
if 'cuaderno_items' not in st.session_state:
    st.session_state['cuaderno_items'] = {}

# --- FUNCIONES PARA CARGAR Y CALCULAR DATOS ---
@st.cache_data
def cargar_datos():
    df_peliculas = pd.read_csv("Datos/peliculas.csv")
    df_series = pd.read_csv("Datos/series.csv")
    
    # Aseguramos que release_year sea numerico
    if 'release_year' in df_peliculas.columns:
        df_peliculas['release_year'] = pd.to_numeric(df_peliculas['release_year'], errors='coerce')
    if 'release_year' in df_series.columns:
        df_series['release_year'] = pd.to_numeric(df_series['release_year'], errors='coerce')
        
    return df_peliculas, df_series

def obtener_top_y_porcentaje(serie_datos):
    if serie_datos.empty:
        return "N/A", 0.0
    conteo = serie_datos.value_counts(normalize=True) * 100
    return conteo.index[0], conteo.iloc[0]

def obtener_top_interacciones_pct(df, columna_categoria, columna_votos='vote_count'):
    if df.empty or columna_categoria not in df.columns or columna_votos not in df.columns:
        return "N/A", 0.0
    
    df_temp = df.dropna(subset=[columna_categoria, columna_votos]).copy()
    df_temp[columna_categoria] = df_temp[columna_categoria].astype(str).str.split(',')
    df_temp = df_temp.explode(columna_categoria)
    df_temp[columna_categoria] = df_temp[columna_categoria].str.strip()
    
    agrupado = df_temp.groupby(columna_categoria)[columna_votos].sum().reset_index()
    if agrupado.empty:
        return "N/A", 0.0
        
    total_votos_global = agrupado[columna_votos].sum()
    top_row = agrupado.sort_values(by=columna_votos, ascending=False).iloc[0]
    porcentaje = (top_row[columna_votos] / total_votos_global) * 100 if total_votos_global > 0 else 0
    return top_row[columna_categoria], porcentaje

# Cargamos los datos crudos
df_peliculas_crudo, df_series_crudo = cargar_datos()

# --- FILTRO GLOBAL (SIDEBAR) ---
st.sidebar.title("Filtro Global")

# Obtener rango de años
min_year = 1900
max_year = 2026
if 'release_year' in df_peliculas_crudo.columns and 'release_year' in df_series_crudo.columns:
    min_year = int(min(df_peliculas_crudo['release_year'].min(), df_series_crudo['release_year'].min()))
    max_year = int(max(df_peliculas_crudo['release_year'].max(), df_series_crudo['release_year'].max()))

rango_anios = st.sidebar.slider(
    "Periodo de estreno:",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# Guardamos el filtro en la memoria global y preparamos el texto del rango
st.session_state['filtro_anios'] = rango_anios
rango_actual = f"{rango_anios[0]} - {rango_anios[1]}"

# Aplicamos el filtro a los dataframes locales para la vista "Inicio"
if 'release_year' in df_peliculas_crudo.columns:
    df_peliculas = df_peliculas_crudo[
        (df_peliculas_crudo['release_year'] >= rango_anios[0]) & 
        (df_peliculas_crudo['release_year'] <= rango_anios[1])
    ]
else:
    df_peliculas = df_peliculas_crudo

if 'release_year' in df_series_crudo.columns:
    df_series = df_series_crudo[
        (df_series_crudo['release_year'] >= rango_anios[0]) & 
        (df_series_crudo['release_year'] <= rango_anios[1])
    ]
else:
    df_series = df_series_crudo

# --- NAVEGACION ---
st.sidebar.markdown("---")
st.sidebar.title("Navegacion")
menu = st.sidebar.radio(
    "Selecciona un reporte:",
    ["Inicio", "Popularidad (Actores/Directores)", "Popularidad por Idiomas","Popularidad por Generos", "Votos por Actores/Directores", "Votos por Idiomas","Votos por Generos", "Crear Informe"]
)

# --- PAGINAS ---
if menu == "Inicio":
    st.title("Bienvenido al Sistema de Reportes")
    st.write("Explora las metricas generales utilizando los menus desplegables a continuacion.")
    
    col_idioma = "language" 
    col_genero = "genres" 
    
    # ==========================================
    # SECCION: PELICULAS
    # ==========================================
    st.markdown("---")
    st.header("Resumen de Peliculas")
    
    with st.expander("KPIs Generales (Conteo Global)", expanded=True):
        total_pelis = len(df_peliculas)
        idiomas_totales_peli = df_peliculas[col_idioma].nunique()
        generos_unicos_peli = df_peliculas[col_genero].dropna().str.split(',').explode().str.strip().nunique()
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total de Peliculas", f"{total_pelis:,}")
        kpi2.metric("Idiomas Registrados", idiomas_totales_peli)
        kpi3.metric("Generos Unicos", generos_unicos_peli)
        
        if st.button("Agregar a Informe", key="btn_kpi_gral_peli"):
            st.session_state['cuaderno_items'][f'kpi_gral_peli_{rango_actual}'] = {
                'tipo': 'kpi', 
                'titulo': 'KPIs Generales - Peliculas',
                'contenido': {
                    "Total de Peliculas": f"{total_pelis:,}",
                    "Idiomas Registrados": str(idiomas_totales_peli),
                    "Generos Unicos": str(generos_unicos_peli)
                },
                'rango_anios': rango_actual
            }
            st.toast("Agregado al informe")

    with st.expander("KPIs de Popularidad (Por Produccion)", expanded=False):
        idiomas_peli = df_peliculas[col_idioma].dropna()
        idioma_pop_peli, idioma_porc_peli = obtener_top_y_porcentaje(idiomas_peli)
        generos_peli = df_peliculas[col_genero].dropna().str.split(',').explode().str.strip()
        genero_pop_peli, genero_porc_peli = obtener_top_y_porcentaje(generos_peli)
        
        kpi4, kpi5 = st.columns(2)
        kpi4.metric("Idioma mas producido", idioma_pop_peli, f"{idioma_porc_peli:.1f}% del catalogo", delta_color="off")
        kpi5.metric("Genero mas producido", genero_pop_peli, f"{genero_porc_peli:.1f}% del catalogo", delta_color="off")
        
        if st.button("Agregar a Informe", key="btn_kpi_pop_peli"):
            st.session_state['cuaderno_items'][f'kpi_pop_peli_{rango_actual}'] = {
                'tipo': 'kpi', 
                'titulo': 'Popularidad por Produccion - Peliculas',
                'contenido': {
                    "Idioma mas producido": f"{idioma_pop_peli} ({idioma_porc_peli:.1f}%)",
                    "Genero mas producido": f"{genero_pop_peli} ({genero_porc_peli:.1f}%)"
                },
                'rango_anios': rango_actual
            }
            st.toast("Agregado al informe")

    with st.expander("KPIs de Interaccion (Votos de Usuarios)", expanded=False):
        interacciones_totales_peli = df_peliculas['vote_count'].sum() if 'vote_count' in df_peliculas.columns else 0
        idioma_int_peli, idioma_int_porc_peli = obtener_top_interacciones_pct(df_peliculas, col_idioma)
        genero_int_peli, genero_int_porc_peli = obtener_top_interacciones_pct(df_peliculas, col_genero)
        
        kpi6, kpi7, kpi8 = st.columns(3)
        kpi6.metric("Interacciones Totales", f"{int(interacciones_totales_peli):,}")
        kpi7.metric("Idioma con + Interacciones", idioma_int_peli, f"{idioma_int_porc_peli:.1f}% de los votos", delta_color="normal")
        kpi8.metric("Genero con + Interacciones", genero_int_peli, f"{genero_int_porc_peli:.1f}% de los votos", delta_color="normal")

        if st.button("Agregar a Informe", key="btn_kpi_int_peli"):
            st.session_state['cuaderno_items'][f'kpi_int_peli_{rango_actual}'] = {
                'tipo': 'kpi', 
                'titulo': 'Interacciones - Peliculas',
                'contenido': {
                    "Interacciones Totales": f"{int(interacciones_totales_peli):,}",
                    "Idioma con + Interacciones": f"{idioma_int_peli} ({idioma_int_porc_peli:.1f}%)",
                    "Genero con + Interacciones": f"{genero_int_peli} ({genero_int_porc_peli:.1f}%)"
                },
                'rango_anios': rango_actual
            }
            st.toast("Agregado al informe")

    # ==========================================
    # SECCION: SERIES
    # ==========================================
    st.markdown("---")
    st.header("Resumen de Series")
    
    with st.expander("KPIs Generales (Conteo Global)", expanded=True):
        total_series = len(df_series)
        idiomas_totales_serie = df_series[col_idioma].nunique()
        generos_unicos_serie = df_series[col_genero].dropna().str.split(',').explode().str.strip().nunique()
        
        kpi9, kpi10, kpi11 = st.columns(3)
        kpi9.metric("Total de Series", f"{total_series:,}")
        kpi10.metric("Idiomas Registrados", idiomas_totales_serie)
        kpi11.metric("Generos Unicos", generos_unicos_serie)
        
        if st.button("Agregar a Informe", key="btn_kpi_gral_serie"):
            st.session_state['cuaderno_items'][f'kpi_gral_serie_{rango_actual}'] = {
                'tipo': 'kpi', 
                'titulo': 'KPIs Generales - Series',
                'contenido': {
                    "Total de Series": f"{total_series:,}",
                    "Idiomas Registrados": str(idiomas_totales_serie),
                    "Generos Unicos": str(generos_unicos_serie)
                },
                'rango_anios': rango_actual
            }
            st.toast("Agregado al informe")

    with st.expander("KPIs de Popularidad (Por Produccion)", expanded=False):
        idiomas_serie = df_series[col_idioma].dropna()
        idioma_pop_serie, idioma_porc_serie = obtener_top_y_porcentaje(idiomas_serie)
        generos_serie = df_series[col_genero].dropna().str.split(',').explode().str.strip()
        genero_pop_serie, genero_porc_serie = obtener_top_y_porcentaje(generos_serie)
        
        kpi12, kpi13 = st.columns(2)
        kpi12.metric("Idioma mas producido", idioma_pop_serie, f"{idioma_porc_serie:.1f}% del catalogo", delta_color="off")
        kpi13.metric("Genero mas producido", genero_pop_serie, f"{genero_porc_serie:.1f}% del catalogo", delta_color="off")

        if st.button("Agregar a Informe", key="btn_kpi_pop_serie"):
            st.session_state['cuaderno_items'][f'kpi_pop_serie_{rango_actual}'] = {
                'tipo': 'kpi', 
                'titulo': 'Popularidad por Produccion - Series',
                'contenido': {
                    "Idioma mas producido": f"{idioma_pop_serie} ({idioma_porc_serie:.1f}%)",
                    "Genero mas producido": f"{genero_pop_serie} ({genero_porc_serie:.1f}%)"
                },
                'rango_anios': rango_actual
            }
            st.toast("Agregado al informe")

    with st.expander("KPIs de Interaccion (Votos de Usuarios)", expanded=False):
        interacciones_totales_serie = df_series['vote_count'].sum() if 'vote_count' in df_series.columns else 0
        idioma_int_serie, idioma_int_porc_serie = obtener_top_interacciones_pct(df_series, col_idioma)
        genero_int_serie, genero_int_porc_serie = obtener_top_interacciones_pct(df_series, col_genero)
        
        kpi14, kpi15, kpi16 = st.columns(3)
        kpi14.metric("Interacciones Totales", f"{int(interacciones_totales_serie):,}")
        kpi15.metric("Idioma con + Interacciones", idioma_int_serie, f"{idioma_int_porc_serie:.1f}% de los votos", delta_color="normal")
        kpi16.metric("Genero con + Interacciones", genero_int_serie, f"{genero_int_porc_serie:.1f}% de los votos", delta_color="normal")

        if st.button("Agregar a Informe", key="btn_kpi_int_serie"):
            st.session_state['cuaderno_items'][f'kpi_int_serie_{rango_actual}'] = {
                'tipo': 'kpi', 
                'titulo': 'Interacciones - Series',
                'contenido': {
                    "Interacciones Totales": f"{int(interacciones_totales_serie):,}",
                    "Idioma mas votado": f"{idioma_int_serie} ({idioma_int_porc_serie:.1f}%)",
                    "Genero mas votado": f"{genero_int_serie} ({genero_int_porc_serie:.1f}%)"
                },
                'rango_anios': rango_actual
            }
            st.toast("Agregado al informe")

elif menu == "Popularidad (Actores/Directores)":
    popularidad.mostrar()
elif menu == "Popularidad por Idiomas":
    popularidad_idiomas.mostrar()
elif menu == "Votos por Actores/Directores":
    votos_actores_directores.mostrar()
elif menu == "Votos por Idiomas":
    votos_idiomas.mostrar()
elif menu == "Popularidad por Generos":
    popularidad_generos.mostrar()
elif menu == "Votos por Generos":
    votos_generos.mostrar()
elif menu == "Crear Informe":
    cuaderno.mostrar()