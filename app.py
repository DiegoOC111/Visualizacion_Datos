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

df_peliculas, df_series = cargar_datos()

# --- NAVEGACIÓN ---
st.sidebar.title("Navegación")
menu = st.sidebar.radio(
    "Selecciona un reporte:",
    ["Inicio", "Popularidad (Actores/Directores)", "Popularidad por Idiomas","Popularidad por Generos", "Votos por Actores/Directores", "Votos por Idiomas","Votos por Generos", "Crear Informe"]
)

# --- PÁGINAS ---
if menu == "Inicio":
    st.title("Bienvenido al Sistema de Reportes")
    st.write("Explora las métricas generales utilizando los menús desplegables a continuación.")
    
    col_idioma = "language" 
    col_genero = "genres" 
    
    # ==========================================
    # SECCIÓN: PELÍCULAS
    # ==========================================
    st.markdown("---")
    st.header("Resumen de Películas")
    
    with st.expander("KPIs Generales (Conteo Global)", expanded=True):
        total_pelis = len(df_peliculas)
        idiomas_totales_peli = df_peliculas[col_idioma].nunique()
        generos_unicos_peli = df_peliculas[col_genero].dropna().str.split(',').explode().str.strip().nunique()
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total de Películas", f"{total_pelis:,}")
        kpi2.metric("Idiomas Registrados", idiomas_totales_peli)
        kpi3.metric("Géneros Únicos", generos_unicos_peli)
        
        if st.button("Agregar a Informe", key="btn_kpi_gral_peli"):
            st.session_state['cuaderno_items']['kpi_gral_peli'] = {
                'tipo': 'kpi', 
                'titulo': 'KPIs Generales - Películas',
                'contenido': {
                    "Total de Películas": f"{total_pelis:,}",
                    "Idiomas Registrados": str(idiomas_totales_peli),
                    "Géneros Únicos": str(generos_unicos_peli)
                }
            }
            st.toast("Agregado al informe")

    with st.expander("KPIs de Popularidad (Por Producción)", expanded=False):
        idiomas_peli = df_peliculas[col_idioma].dropna()
        idioma_pop_peli, idioma_porc_peli = obtener_top_y_porcentaje(idiomas_peli)
        generos_peli = df_peliculas[col_genero].dropna().str.split(',').explode().str.strip()
        genero_pop_peli, genero_porc_peli = obtener_top_y_porcentaje(generos_peli)
        
        kpi4, kpi5 = st.columns(2)
        kpi4.metric("Idioma más producido", idioma_pop_peli, f"{idioma_porc_peli:.1f}% del catálogo", delta_color="off")
        kpi5.metric("Género más producido", genero_pop_peli, f"{genero_porc_peli:.1f}% del catálogo", delta_color="off")
        
        if st.button("Agregar a Informe", key="btn_kpi_pop_peli"):
            st.session_state['cuaderno_items']['kpi_pop_peli'] = {
                'tipo': 'kpi', 
                'titulo': 'Popularidad por Producción - Películas',
                'contenido': {
                    "Idioma más producido": f"{idioma_pop_peli} ({idioma_porc_peli:.1f}%)",
                    "Género más producido": f"{genero_pop_peli} ({genero_porc_peli:.1f}%)"
                }
            }
            st.toast("Agregado al informe")

    with st.expander("KPIs de Interacción (Votos de Usuarios)", expanded=False):
        interacciones_totales_peli = df_peliculas['vote_count'].sum() if 'vote_count' in df_peliculas.columns else 0
        idioma_int_peli, idioma_int_porc_peli = obtener_top_interacciones_pct(df_peliculas, col_idioma)
        genero_int_peli, genero_int_porc_peli = obtener_top_interacciones_pct(df_peliculas, col_genero)
        
        kpi6, kpi7, kpi8 = st.columns(3)
        kpi6.metric("Interacciones Totales", f"{int(interacciones_totales_peli):,}")
        kpi7.metric("Idioma con + Interacciones", idioma_int_peli, f"{idioma_int_porc_peli:.1f}% de los votos", delta_color="normal")
        kpi8.metric("Género con + Interacciones", genero_int_peli, f"{genero_int_porc_peli:.1f}% de los votos", delta_color="normal")

        if st.button("Agregar a Informe", key="btn_kpi_int_peli"):
            st.session_state['cuaderno_items']['kpi_int_peli'] = {
                'tipo': 'kpi', 
                'titulo': 'Interacciones - Películas',
                'contenido': {
                    "Interacciones Totales": f"{int(interacciones_totales_peli):,}",
                    "Idioma con + Interacciones": f"{idioma_int_peli} ({idioma_int_porc_peli:.1f}%)",
                    "Género con + Interacciones": f"{genero_int_peli} ({genero_int_porc_peli:.1f}%)"
                }
            }
            st.toast("Agregado al informe")

    # ==========================================
    # SECCIÓN: SERIES
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
        kpi11.metric("Géneros Únicos", generos_unicos_serie)
        
        if st.button("Agregar a Informe", key="btn_kpi_gral_serie"):
            st.session_state['cuaderno_items']['kpi_gral_serie'] = {
                'tipo': 'kpi', 
                'titulo': 'KPIs Generales - Series',
                'contenido': {
                    "Total de Series": f"{total_series:,}",
                    "Idiomas Registrados": str(idiomas_totales_serie),
                    "Géneros Únicos": str(generos_unicos_serie)
                }
            }
            st.toast("Agregado al informe")

    with st.expander("KPIs de Popularidad (Por Producción)", expanded=False):
        idiomas_serie = df_series[col_idioma].dropna()
        idioma_pop_serie, idioma_porc_serie = obtener_top_y_porcentaje(idiomas_serie)
        generos_serie = df_series[col_genero].dropna().str.split(',').explode().str.strip()
        genero_pop_serie, genero_porc_serie = obtener_top_y_porcentaje(generos_serie)
        
        kpi12, kpi13 = st.columns(2)
        kpi12.metric("Idioma más producido", idioma_pop_serie, f"{idioma_porc_serie:.1f}% del catálogo", delta_color="off")
        kpi13.metric("Género más producido", genero_pop_serie, f"{genero_porc_serie:.1f}% del catálogo", delta_color="off")

        if st.button("Agregar a Informe", key="btn_kpi_pop_serie"):
            st.session_state['cuaderno_items']['kpi_pop_serie'] = {
                'tipo': 'kpi', 
                'titulo': 'Popularidad por Producción - Series',
                'contenido': {
                    "Idioma más producido": f"{idioma_pop_serie} ({idioma_porc_serie:.1f}%)",
                    "Género más producido": f"{genero_pop_serie} ({genero_porc_serie:.1f}%)"
                }
            }
            st.toast("Agregado al informe")

    with st.expander("KPIs de Interacción (Votos de Usuarios)", expanded=False):
        interacciones_totales_serie = df_series['vote_count'].sum() if 'vote_count' in df_series.columns else 0
        idioma_int_serie, idioma_int_porc_serie = obtener_top_interacciones_pct(df_series, col_idioma)
        genero_int_serie, genero_int_porc_serie = obtener_top_interacciones_pct(df_series, col_genero)
        
        kpi14, kpi15, kpi16 = st.columns(3)
        kpi14.metric("Interacciones Totales", f"{int(interacciones_totales_serie):,}")
        kpi15.metric("Idioma con + Interacciones", idioma_int_serie, f"{idioma_int_porc_serie:.1f}% de los votos", delta_color="normal")
        kpi16.metric("Género con + Interacciones", genero_int_serie, f"{genero_int_porc_serie:.1f}% de los votos", delta_color="normal")

        if st.button("Agregar a Informe", key="btn_kpi_int_serie"):
            st.session_state['cuaderno_items']['kpi_int_serie'] = {
                'tipo': 'kpi', 
                'titulo': 'Interacciones - Series',
                'contenido': {
                    "Interacciones Totales": f"{int(interacciones_totales_serie):,}",
                    "Idioma con + Interacciones": f"{idioma_int_serie} ({idioma_int_porc_serie:.1f}%)",
                    "Género con + Interacciones": f"{genero_int_serie} ({genero_int_porc_serie:.1f}%)"
                }
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