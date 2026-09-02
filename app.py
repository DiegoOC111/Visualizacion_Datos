import streamlit as st

# Importamos los reportes
from dashboards import popularidad
from dashboards import popularidad_idiomas

st.set_page_config(page_title="Sistema de Reportes", layout="wide")

st.sidebar.title("Navegación")
menu = st.sidebar.radio(
    "Selecciona un reporte:",
    ["Inicio", "Popularidad (Actores/Directores)", "Popularidad por Idiomas"]
)

if menu == "Inicio":
    st.title("Bienvenido al Sistema de Reportes")
    st.write("Utiliza el menú de la izquierda para navegar entre los distintos dashboards disponibles.")
    
elif menu == "Popularidad (Actores/Directores)":
    popularidad.mostrar()
    
elif menu == "Popularidad por Idiomas":
    popularidad_idiomas.mostrar()