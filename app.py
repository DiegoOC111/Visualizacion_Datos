import streamlit as st
from dashboards import popularidad

st.set_page_config(page_title="Sistema de Reportes", layout="wide")

st.sidebar.title("Navegacion")
menu = st.sidebar.radio(
    "Selecciona un reporte:",
    ["Inicio", "Popularidad (Actores/Directores)"]
)

if menu == "Inicio":
    st.title("Bienvenido al Sistema de Reportes")
    st.write("Utiliza el menu de la izquierda para navegar entre los distintos dashboards disponibles.")
    
elif menu == "Popularidad (Actores/Directores)":
    popularidad.mostrar()