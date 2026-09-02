import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def cargar_datos(tipo_bd):
    if tipo_bd == "Películas":
        return pd.read_csv("Datos/peliculas.csv")
    else:
        return pd.read_csv("Datos/series.csv")
def obtener_mas_famoso_mediana(df, columna, min_apariciones=5):
    df_temp = df.dropna(subset=[columna, 'popularity', 'title']).copy()
    df_temp[columna] = df_temp[columna].astype(str).str.split(',')
    df_temp = df_temp.explode(columna)
    df_temp[columna] = df_temp[columna].str.strip()
    df_temp = df_temp[df_temp[columna].str.lower() != 'unknown']
    df_temp = df_temp.drop_duplicates(subset=[columna, 'title'])
    
    if df_temp.empty:
        return "No hay datos registrados"
        
    # Agrupamos calculando tanto la mediana como la cantidad de producciones
    agrupado = df_temp.groupby(columna).agg(
        mediana_popularidad=('popularity', 'median'),
        conteo=('title', 'count')
    ).reset_index()
    
    # Filtramos a los que tengan muy pocas apariciones (One-Hit Wonders)
    agrupado = agrupado[agrupado['conteo'] >= min_apariciones]
    
    if agrupado.empty:
        return "No hay datos con suficientes apariciones"
        
    # Ordenamos y sacamos el top 1
    top_1 = agrupado.sort_values(by='mediana_popularidad', ascending=False).head(1)[columna].values[0]
    
    return top_1

@st.dialog("Resumen de Idioma", width="large")
def popup_detalles_idioma(idioma, df_actual):
    st.markdown(f"### Idioma: {idioma.upper()}")
    
    df_idioma = df_actual[df_actual['language'] == idioma].copy()
    
    if df_idioma.empty:
        st.warning("No hay datos para este idioma.")
        return

    # Se reemplaza la lista completa por un contador de producciones únicas
    cantidad_producciones = df_idioma['title'].nunique()
    st.info(f"**Cantidad de producciones encontradas:** {cantidad_producciones}")
        
    st.write("")
    
    # Cálculos de popularidad basados en la mediana
    if not df_idioma.dropna(subset=['title', 'popularity']).empty:
        agrupado_titulos = df_idioma.groupby('title')['popularity'].median().reset_index()
        titulo_top = agrupado_titulos.sort_values(by='popularity', ascending=False).head(1)['title'].values[0]
    else:
        titulo_top = "No hay datos"

    actor_top = obtener_mas_famoso_mediana(df_idioma, 'cast') if 'cast' in df_idioma.columns else "No disponible"
    director_top = obtener_mas_famoso_mediana(df_idioma, 'director') if 'director' in df_idioma.columns else "No disponible"

    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("**Producción más famosa**")
        st.markdown(f"##### {titulo_top}")
        
    with c2:
        st.markdown("**Actor más famoso**")
        st.markdown(f"##### {actor_top}")
        
    with c3:
        st.markdown("**Director más famoso**")
        st.markdown(f"##### {director_top}")

def mostrar():
    st.title("Popularidad Mediana por Idioma")

    tipo_bd = st.selectbox("Selecciona la base de datos:", ["Películas", "Series"], key="bd_idiomas")

    try:
        df = cargar_datos(tipo_bd)
    except FileNotFoundError:
        st.error(f"No se encontró el archivo de {tipo_bd}.")
        st.stop()

    if 'language' not in df.columns:
        st.error("La base de datos seleccionada no contiene una columna de idiomas.")
        st.stop()

    lista_idiomas = sorted(df['language'].dropna().astype(str).str.strip().unique())
    idiomas_seleccionados = st.multiselect(
        "Agrega los idiomas que deseas comparar:",
        options=lista_idiomas,
        default=["en", "es", "ja"] if all(i in lista_idiomas for i in ["en", "es", "ja"]) else lista_idiomas[:3]
    )
    if not idiomas_seleccionados:
        st.warning("Selecciona al menos un idioma para visualizar la gráfica.")
        return

    # 1. Filtrar y calcular la mediana y el conteo (volumen de datos)
    df_filtrado = df[df['language'].isin(idiomas_seleccionados)]
    agrupado_idiomas = df_filtrado.groupby('language').agg(
        mediana_popularidad=('popularity', 'median'),
        conteo_producciones=('title', 'count')
    ).reset_index()

    # 2. Aplicar la fórmula del Promedio Bayesiano
    # C = Mediana global de toda la muestra actual
    C = df_filtrado['popularity'].median()
    # m = Umbral mínimo de confianza (usaremos el percentil 25 del volumen de datos)
    m = agrupado_idiomas['conteo_producciones'].quantile(0.25)

    # Fórmula: (v / (v+m)) * R + (m / (v+m)) * C
    agrupado_idiomas['popularidad_ajustada'] = (
        (agrupado_idiomas['conteo_producciones'] / (agrupado_idiomas['conteo_producciones'] + m)) * agrupado_idiomas['mediana_popularidad'] +
        (m / (agrupado_idiomas['conteo_producciones'] + m)) * C
    )

    agrupado_idiomas = agrupado_idiomas.sort_values(by='popularidad_ajustada', ascending=False)

    # 3. Configuración del gráfico reflejando el ajuste
    fig = px.bar(
        agrupado_idiomas,
        x='language',
        y='popularidad_ajustada',
        color='conteo_producciones', # El color ahora te mostrará visualmente el peso de la población
        color_continuous_scale='Purp',
        labels={
            'language': 'Idioma', 
            'popularidad_ajustada': 'Popularidad (Ajustada)',
            'conteo_producciones': 'Volumen de Datos'
        },
        title="Popularidad por Idioma (Ajuste Bayesiano)",
        hover_data={'mediana_popularidad': True} # Muestra la mediana original al pasar el mouse
    )
    
    fig.update_layout(
        xaxis={'categoryorder': 'total descending'},
        template='plotly_white',
        margin=dict(l=10, r=10, t=40, b=10),
        clickmode='event+select'
    )

    st.markdown("---")
    # Control de estado de sesión para el clic en la gráfica
    if "estado_idioma" not in st.session_state:
        st.session_state.estado_idioma = None

    # Gráfico interactivo con st.plotly_chart
    event_idiomas = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key="grafico_idiomas_interactivo"
    )

    # Lógica de detección de nuevo clic
    sel_idioma = event_idiomas.selection["points"][0]["x"] if event_idiomas and event_idiomas.selection.get("points") else None
    nuevo_idioma = sel_idioma if sel_idioma != st.session_state.estado_idioma else None
    st.session_state.estado_idioma = sel_idioma

    if nuevo_idioma:
        popup_detalles_idioma(nuevo_idioma, df)