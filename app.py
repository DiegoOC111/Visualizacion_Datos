import streamlit as st
import pandas as pd

# Importamos los reportes (Asegúrate de que existan)
from dashboards import popularidad
from dashboards import popularidad_idiomas

st.set_page_config(page_title="Sistema de Reportes", layout="wide")

# --- FUNCIONES PARA CARGAR Y CALCULAR DATOS ---
@st.cache_data
def cargar_datos():
    # Asegúrate de que la ruta coincida con la ubicación de tus archivos
    df_peliculas = pd.read_csv("Datos/peliculas.csv")
    df_series = pd.read_csv("Datos/series.csv")
    return df_peliculas, df_series

# Función auxiliar para calcular el más popular y su porcentaje
def obtener_top_y_porcentaje(serie_datos):
    if serie_datos.empty:
        return "N/A", 0.0
    # value_counts(normalize=True) devuelve la frecuencia en formato decimal (ej: 0.45)
    conteo = serie_datos.value_counts(normalize=True) * 100
    top_nombre = conteo.index[0]
    top_porcentaje = conteo.iloc[0]
    return top_nombre, top_porcentaje

# Cargamos los DataFrames
df_peliculas, df_series = cargar_datos()

# --- NAVEGACIÓN ---
st.sidebar.title("Navegación")
menu = st.sidebar.radio(
    "Selecciona un reporte:",
    ["Inicio", "Popularidad (Actores/Directores)", "Popularidad por Idiomas"]
)

# --- PÁGINAS ---
if menu == "Inicio":
    st.title("Bienvenido al Sistema de Reportes")
    st.write("Utiliza el menú de la izquierda para navegar entre los distintos dashboards disponibles.")
    
    st.markdown("---") # Línea divisoria
    
    # === KPI DE PELÍCULAS ===
    st.header("Kpis  Películas")

    col_idioma_peli = "language" 
    col_genero_peli = "genres" 
    
    # Cálculos Idioma
    idiomas_peli = df_peliculas[col_idioma_peli].dropna()
    idioma_pop_peli, idioma_porc_peli = obtener_top_y_porcentaje(idiomas_peli)
    
    # Cálculos Género (separando los géneros combinados por comas)
    generos_peli = df_peliculas[col_genero_peli].dropna().str.split(',').explode().str.strip()
    genero_pop_peli, genero_porc_peli = obtener_top_y_porcentaje(generos_peli)
    
    total_pelis = len(df_peliculas)
    idiomas_totales_peli = idiomas_peli.nunique()
    generos_unicos_peli = generos_peli.nunique()

    # st.columns divide la pantalla en 5 columnas del mismo tamaño
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    # delta_color="off" hace que el porcentaje se vea gris (neutro) en lugar de verde/rojo
    kpi1.metric("Idioma más popular", idioma_pop_peli, f"{idioma_porc_peli:.1f}% del total", delta_color="off")
    kpi2.metric("Idiomas totales", idiomas_totales_peli)
    kpi3.metric("Género más popular", genero_pop_peli, f"{genero_porc_peli:.1f}% del total", delta_color="off")
    kpi4.metric("Total de Películas", f"{total_pelis:,}")
    kpi5.metric("Géneros (Únicos)", generos_unicos_peli)

    st.markdown("---") # Línea divisoria
    
    # === KPI DE SERIES ===
    st.header("Kpis Series")
    
    col_idioma_serie = "language" 
    col_genero_serie = "genres" 
    
    # Cálculos Idioma
    idiomas_serie = df_series[col_idioma_serie].dropna()
    idioma_pop_serie, idioma_porc_serie = obtener_top_y_porcentaje(idiomas_serie)
    
    # Cálculos Género (separando los géneros combinados por comas)
    generos_serie = df_series[col_genero_serie].dropna().str.split(',').explode().str.strip()
    genero_pop_serie, genero_porc_serie = obtener_top_y_porcentaje(generos_serie)
    
    total_series = len(df_series)
    idiomas_totales_serie = idiomas_serie.nunique()
    generos_unicos_serie = generos_serie.nunique()

    kpi6, kpi7, kpi8, kpi9, kpi10 = st.columns(5)
    kpi6.metric("Idioma más popular", idioma_pop_serie, f"{idioma_porc_serie:.1f}% del total", delta_color="off")
    kpi7.metric("Idiomas totales", idiomas_totales_serie)
    kpi8.metric("Género más popular", genero_pop_serie, f"{genero_porc_serie:.1f}% del total", delta_color="off")
    kpi9.metric("Total de Series", f"{total_series:,}")
    kpi10.metric("Géneros (Únicos)", generos_unicos_serie)

elif menu == "Popularidad (Actores/Directores)":
    popularidad.mostrar()
    
elif menu == "Popularidad por Idiomas":
    popularidad_idiomas.mostrar()