import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def cargar_datos(tipo_bd):
    if tipo_bd == "Películas":
        return pd.read_csv("Datos/peliculas.csv")
    else:
        return pd.read_csv("Datos/series.csv")

def top_por_popularidad_por_idioma(df, columna_objetivo, columna_idioma=None, idiomas_permitidos=None, min_apariciones=10, top_n=10):
    columnas = [columna_objetivo, 'popularity', 'title']
    if columna_idioma:
        columnas.append(columna_idioma)
    df_temp = df[columnas].dropna(subset=[columna_objetivo, 'title']).copy()
    df_temp['title'] = df_temp['title'].str.strip()
    if columna_idioma and idiomas_permitidos:
        idiomas_limpios = [idioma.lower().strip() for idioma in idiomas_permitidos]
        patron_regex = '|'.join([rf"\b{idioma}\b" for idioma in idiomas_limpios])
        df_temp = df_temp[df_temp[columna_idioma].str.strip().str.lower().str.contains(patron_regex, regex=True, na=False)]
    df_temp = df_temp[df_temp[columna_objetivo].str.strip().str.lower() != 'unknown']
    df_temp[columna_objetivo] = df_temp[columna_objetivo].str.split(',')
    df_exploded = df_temp.explode(columna_objetivo)
    df_exploded[columna_objetivo] = df_exploded[columna_objetivo].str.strip()
    df_exploded = df_exploded[df_exploded[columna_objetivo].str.lower() != 'unknown']
    df_exploded = df_exploded.drop_duplicates(subset=[columna_objetivo, 'title'])
    agrupado = df_exploded.groupby(columna_objetivo).agg(
        mediana_popularidad=('popularity', 'median'),
        cantidad_apariciones=('title', 'count')
    )
    agrupado = agrupado[agrupado['cantidad_apariciones'] >= min_apariciones]
    return agrupado.sort_values(by='mediana_popularidad', ascending=False).head(top_n)

def crear_grafico_degrade(df_top, columna_nombre, titulo_grafico, paleta_color="Tealgrn"):
    df_plot = df_top.reset_index()
    
    fig = px.bar(
        df_plot,
        x=columna_nombre,
        y='mediana_popularidad',
        color='mediana_popularidad',
        color_continuous_scale=paleta_color,
        labels={
            columna_nombre: columna_nombre.capitalize(),
            'mediana_popularidad': 'Popularidad Mediana'
        },
        title=titulo_grafico
    )
    
    fig.update_layout(
        xaxis={'categoryorder': 'total descending'},
        coloraxis_showscale=False,
        template='plotly_white',
        margin=dict(l=10, r=10, t=40, b=10),
        clickmode='event+select'
    )
    
    return fig

# Definimos la función del pop-up modal
@st.dialog("Mini-Resumen", width="large")
def popup_detalles(seleccion, df_actual):
    st.markdown(f"### 👤 {seleccion}")
    nombre_url = seleccion.replace(' ', '_')
    url_wiki = f"https://es.wikipedia.org/wiki/{nombre_url}"
    st.info(f"[Haz clic aquí para abrir la Wikipedia de {seleccion}]({url_wiki})")
    
    mask_cast = df_actual['cast'].fillna('').str.contains(seleccion, case=False, regex=False) if 'cast' in df_actual.columns else False
    mask_dir = df_actual['director'].fillna('').str.contains(seleccion, case=False, regex=False) if 'director' in df_actual.columns else False
    
    df_persona = df_actual[mask_cast | mask_dir].drop_duplicates(subset=['title']).copy()
    
    if not df_persona.empty:
        titulos_lista = ", ".join(df_persona['title'].astype(str).tolist())
        
        # Agrupamos la lista en un "expander" para que se vea más ordenado
        with st.expander(f"🎬 Producciones encontradas ({len(df_persona)})", expanded=True):
            st.write(titulos_lista)
        
        st.write("") 
        
        mas_popular = df_persona.loc[df_persona['popularity'].idxmax()]
        menos_popular = df_persona.loc[df_persona['popularity'].idxmin()]
        
        # Lógica de fecha más reciente
        columnas_fecha_posibles = ['release_date', 'first_air_date', 'year', 'date_added']
        col_fecha_usada = next((col for col in columnas_fecha_posibles if col in df_persona.columns), None)
        
        fecha_str = "N/A"
        mas_reciente_titulo = "Desconocido"
        if col_fecha_usada:
            df_persona[col_fecha_usada] = pd.to_datetime(df_persona[col_fecha_usada], errors='coerce')
            mas_reciente = df_persona.sort_values(by=col_fecha_usada, ascending=False).iloc[0]
            fecha_str = mas_reciente[col_fecha_usada].strftime('%Y') if pd.notnull(mas_reciente[col_fecha_usada]) else "N/A"
            mas_reciente_titulo = mas_reciente['title']

        # Usamos columnas y markdown en lugar de st.metric para evitar recortes
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown(" **Más Popular**")
            st.markdown(f"##### {mas_popular['title']}")
            st.success(f"↑ {mas_popular['popularity']:.1f} pop")
            
        with c2:
            st.markdown("**Menos Popular**")
            st.markdown(f"##### {menos_popular['title']}")
            st.error(f"↓ {menos_popular['popularity']:.1f} pop")
            
        with c3:
            st.markdown("**Más Reciente**")
            st.markdown(f"##### {mas_reciente_titulo}")
            st.info(f" Año: {fecha_str}")

def mostrar():
    st.title("🎬 Dashboard de Popularidad: Actores y Directores")

    tipo_bd = st.selectbox("Selecciona la base de datos a analizar:", ["Películas", "Series"])

    try:
        df_actual = cargar_datos(tipo_bd)
    except FileNotFoundError:
        st.error(f"No se encontró el archivo respectivo para {tipo_bd}.")
        st.stop()

    st.sidebar.header(" Filtros de Búsqueda")
    
    if 'language' in df_actual.columns:
        lista_idiomas = sorted(df_actual['language'].dropna().astype(str).str.strip().unique())
    else:
        lista_idiomas = []

    idiomas_seleccionados = st.sidebar.multiselect(
        "Selecciona el/los idioma(s):",
        options=lista_idiomas,
        default=["en"] if "en" in lista_idiomas else None
    )

    min_apariciones = st.sidebar.slider("Apariciones mínimas (Rango: 1 - 10):", min_value=1, max_value=10, value=8)

    st.markdown("---")

    # Inicializamos variables de estado para evitar el "choque" de pop-ups
    if "estado_actores" not in st.session_state:
        st.session_state.estado_actores = None
    if "estado_directores" not in st.session_state:
        st.session_state.estado_directores = None

    if not idiomas_seleccionados:
        st.warning("👈 Por favor, selecciona al menos un idioma en la barra lateral para ver los resultados.")
    else:
        col1, col2 = st.columns(2)
        
        event_actores = None
        event_directores = None

        with col1:
            st.subheader(" Top 5 Actores")
            if 'cast' in df_actual.columns:
                top_actores = top_por_popularidad_por_idioma(
                    df_actual, 'cast', 'language', idiomas_seleccionados, min_apariciones, 5
                )
                if not top_actores.empty:
                    st.dataframe(top_actores, use_container_width=True)
                    
                    fig_actores = crear_grafico_degrade(
                        top_actores, 'cast', 'Popularidad de Actores', paleta_color='Tealgrn'
                    )
                    
                    # IMPORTANTE: Se añade key="grafico_actores" y selection_mode
                    event_actores = st.plotly_chart(
                        fig_actores, 
                        use_container_width=True, 
                        on_select="rerun", 
                        selection_mode="points",
                        key="grafico_actores"
                    )
                else:
                    st.info("Sin resultados.")
            else:
                st.error("No existe la columna 'cast'.")

        with col2:
            st.subheader(" Top 5 Directores")
            if 'director' in df_actual.columns:
                top_directores = top_por_popularidad_por_idioma(
                    df_actual, 'director', 'language', idiomas_seleccionados, min_apariciones, 5
                )
                if not top_directores.empty:
                    st.dataframe(top_directores, use_container_width=True)
                    
                    fig_directores = crear_grafico_degrade(
                        top_directores, 'director', 'Popularidad de Directores', paleta_color='Sunset'
                    )
                    
                    # IMPORTANTE: Se añade key="grafico_directores" y selection_mode
                    event_directores = st.plotly_chart(
                        fig_directores, 
                        use_container_width=True, 
                        on_select="rerun", 
                        selection_mode="points",
                        key="grafico_directores"
                    )
                else:
                    st.info("Sin resultados.")
            else:
                st.error("No existe la columna 'director'.")

        # ==========================================
        # LÓGICA DE CONTROL DE POP-UPS (EVITA ERRORES)
        # ==========================================
        
        # 1. Extraemos la selección actual (si existe) de cada gráfico
        sel_actor = event_actores.selection["points"][0]["x"] if event_actores and event_actores.selection.get("points") else None
        sel_director = event_directores.selection["points"][0]["x"] if event_directores and event_directores.selection.get("points") else None

        # 2. Comparamos con el estado anterior para detectar si hubo un clic NUEVO
        nuevo_actor = sel_actor if sel_actor != st.session_state.estado_actores else None
        nuevo_director = sel_director if sel_director != st.session_state.estado_directores else None

        # 3. Guardamos el estado actual para la próxima recarga
        st.session_state.estado_actores = sel_actor
        st.session_state.estado_directores = sel_director

        # 4. Solo abrimos el pop-up para el elemento que acaba de ser clicado
        if nuevo_actor:
            popup_detalles(nuevo_actor, df_actual)
        elif nuevo_director:
            popup_detalles(nuevo_director, df_actual)