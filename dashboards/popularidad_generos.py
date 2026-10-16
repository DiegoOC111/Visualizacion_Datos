import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def cargar_datos(tipo_bd):
    if tipo_bd == "Películas":
        return pd.read_csv("Datos/peliculas.csv")
    else:
        return pd.read_csv("Datos/series.csv")

def crear_pie_chart_generos(df, titulo):
    if 'genres' not in df.columns:
        return None
        
    df_gen = df.dropna(subset=['genres']).copy()
    df_gen['genres'] = df_gen['genres'].astype(str).str.split(',')
    df_gen = df_gen.explode('genres')
    df_gen['genres'] = df_gen['genres'].str.strip()
    df_gen = df_gen[df_gen['genres'].str.lower() != 'unknown']
    
    df_counts = df_gen['genres'].value_counts().reset_index()
    df_counts.columns = ['genres', 'count']
    
    if len(df_counts) > 4:
        top4 = df_counts.iloc[:4].copy()
        otros_count = df_counts.iloc[4:]['count'].sum()
        otros_df = pd.DataFrame({'genres': ['Otros'], 'count': [otros_count]})
        df_final = pd.concat([top4, otros_df], ignore_index=True)
    else:
        df_final = df_counts
        
    fig = px.pie(
        df_final, 
        values='count', 
        names='genres', 
        title=titulo,
        hole=0.3,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    return fig

def obtener_mas_famoso_mediana(df, columna, min_apariciones=5):
    df_temp = df.dropna(subset=[columna, 'popularity', 'title']).copy()
    df_temp[columna] = df_temp[columna].astype(str).str.split(',')
    df_temp = df_temp.explode(columna)
    df_temp[columna] = df_temp[columna].str.strip()
    df_temp = df_temp[df_temp[columna].str.lower() != 'unknown']
    df_temp = df_temp.drop_duplicates(subset=[columna, 'title'])
    
    if df_temp.empty:
        return "No hay datos registrados"
        
    agrupado = df_temp.groupby(columna).agg(
        mediana_popularidad=('popularity', 'median'),
        conteo=('title', 'count')
    ).reset_index()
    
    agrupado = agrupado[agrupado['conteo'] >= min_apariciones]
    
    if agrupado.empty:
        return "No hay datos con suficientes apariciones"
        
    top_1 = agrupado.sort_values(by='mediana_popularidad', ascending=False).head(1)[columna].values[0]
    
    return top_1

@st.dialog("Resumen de Genero", width="large")
def popup_detalles_genero(genero_seleccionado, df_actual):
    st.markdown(f"### Genero: {genero_seleccionado.upper()}")
    
    # Filtramos las producciones que contengan el género seleccionado en su lista separada por comas
    mask = df_actual['genres'].fillna('').str.contains(genero_seleccionado, case=False, regex=False)
    df_genero = df_actual[mask].copy()
    
    if df_genero.empty:
        st.warning("No hay datos para este genero.")
        return

    cantidad_producciones = df_genero['title'].nunique()
    total_bd = df_actual['title'].nunique()
    porcentaje_total = (cantidad_producciones / total_bd) * 100
    
    st.info(f"Cantidad de producciones: {cantidad_producciones:,} ({porcentaje_total:.2f}% del catalogo total)")
        
    st.write("")
    
    if not df_genero.dropna(subset=['title', 'popularity']).empty:
        agrupado_titulos = df_genero.groupby('title')['popularity'].median().reset_index()
        titulo_top = agrupado_titulos.sort_values(by='popularity', ascending=False).head(1)['title'].values[0]
    else:
        titulo_top = "No hay datos"

    actor_top = obtener_mas_famoso_mediana(df_genero, 'cast') if 'cast' in df_genero.columns else "No disponible"
    director_top = obtener_mas_famoso_mediana(df_genero, 'director') if 'director' in df_genero.columns else "No disponible"

    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("**Produccion mas famosa**")
        st.markdown(f"##### {titulo_top}")
        
    with c2:
        st.markdown("**Actor mas famoso**")
        st.markdown(f"##### {actor_top}")
        
    with c3:
        st.markdown("**Director mas famoso**")
        st.markdown(f"##### {director_top}")

def mostrar():
    st.title("Popularidad Mediana por Genero")

    try:
        df_pelis = cargar_datos("Películas")
        df_series = cargar_datos("Series")
    except FileNotFoundError:
        st.error("No se encontraron los archivos de datos.")
        st.stop()

    st.subheader("Distribucion General de Generos en el Catalogo")
    col_pie1, col_pie2 = st.columns(2)
    
    with col_pie1:
        fig_pie_pelis = crear_pie_chart_generos(df_pelis, "Generos Principales en Peliculas")
        if fig_pie_pelis:
            st.plotly_chart(fig_pie_pelis, use_container_width=True, key="pie_generos_pelis")
            if st.button("Agregar Grafico de Peliculas al Informe", key="btn_add_pie_generos_pelis"):
                st.session_state['cuaderno_items']['pie_generos_pelis'] = {
                    'tipo': 'grafico',
                    'titulo': 'Distribucion de Generos - Peliculas',
                    'figura': fig_pie_pelis,
                    'contenido': "Grafico circular de los 4 generos principales y agrupacion 'Otros' en Peliculas."
                }
                st.toast("Grafico agregado al informe")

    with col_pie2:
        fig_pie_series = crear_pie_chart_generos(df_series, "Generos Principales en Series")
        if fig_pie_series:
            st.plotly_chart(fig_pie_series, use_container_width=True, key="pie_generos_series")
            if st.button("Agregar Grafico de Series al Informe", key="btn_add_pie_generos_series"):
                st.session_state['cuaderno_items']['pie_generos_series'] = {
                    'tipo': 'grafico',
                    'titulo': 'Distribucion de Generos - Series',
                    'figura': fig_pie_series,
                    'contenido': "Grafico circular de los 4 generos principales y agrupacion 'Otros' en Series."
                }
                st.toast("Grafico agregado al informe")

    st.markdown("---")
    
    st.subheader("Analisis Detallado de Popularidad")
    tipo_bd = st.selectbox("Selecciona la base de datos:", ["Películas", "Series"], key="bd_generos")

    df = df_pelis if tipo_bd == "Películas" else df_series

    if 'genres' not in df.columns:
        st.error("La base de datos seleccionada no contiene una columna de generos.")
        st.stop()

    # Pre-procesamiento de la columna de géneros (ya que vienen separados por comas)
    df_exp = df.dropna(subset=['genres', 'popularity']).copy()
    df_exp['genres'] = df_exp['genres'].astype(str).str.split(',')
    df_exp = df_exp.explode('genres')
    df_exp['genres'] = df_exp['genres'].str.strip()
    df_exp = df_exp[df_exp['genres'].str.lower() != 'unknown']

    total_producciones_catalogo = len(df)

    lista_generos = sorted(df_exp['genres'].unique())
    # Valores por defecto: los 3 generos más comunes
    top_3_generos = df_exp['genres'].value_counts().head(3).index.tolist()
    
    generos_seleccionados = st.multiselect(
        "Agrega los generos que deseas comparar:",
        options=lista_generos,
        default=top_3_generos
    )
    if not generos_seleccionados:
        st.warning("Selecciona al menos un genero para visualizar la grafica.")
        return

    df_filtrado = df_exp[df_exp['genres'].isin(generos_seleccionados)]
    agrupado_generos = df_filtrado.groupby('genres').agg(
        mediana_popularidad=('popularity', 'median'),
        conteo_producciones=('title', 'nunique')
    ).reset_index()

    agrupado_generos['porcentaje_total'] = (agrupado_generos['conteo_producciones'] / total_producciones_catalogo) * 100
    agrupado_generos['% del Total'] = agrupado_generos['porcentaje_total'].apply(lambda x: f"{x:.2f}%")

    C = df_filtrado['popularity'].median()
    m = agrupado_generos['conteo_producciones'].quantile(0.25)

    agrupado_generos['popularidad_ajustada'] = (
        (agrupado_generos['conteo_producciones'] / (agrupado_generos['conteo_producciones'] + m)) * agrupado_generos['mediana_popularidad'] +
        (m / (agrupado_generos['conteo_producciones'] + m)) * C
    )

    agrupado_generos = agrupado_generos.sort_values(by='popularidad_ajustada', ascending=False)

    fig = px.bar(
        agrupado_generos,
        x='genres',
        y='popularidad_ajustada',
        color='conteo_producciones',
        color_continuous_scale='Purp',
        labels={
            'genres': 'Genero', 
            'popularidad_ajustada': 'Popularidad (Ajustada)',
            'conteo_producciones': 'Volumen de Datos'
        },
        title="Popularidad por Genero (Ajuste Bayesiano)",
        hover_data={'mediana_popularidad': True, '% del Total': True} 
    )
    
    fig.update_layout(
        xaxis={'categoryorder': 'total descending'},
        template='plotly_white',
        margin=dict(l=10, r=10, t=40, b=10),
        clickmode='event+select'
    )
    
    fig.update_traces(texttemplate='%{y:.1f}', textposition='outside')

    if "estado_genero" not in st.session_state:
        st.session_state.estado_genero = None

    event_generos = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key="grafico_generos_interactivo"
    )
    
    if st.button("Agregar Grafico de Barras al Informe", key="btn_add_graf_generos_pop"):
        st.session_state['cuaderno_items']['graf_generos_pop'] = {
            'tipo': 'grafico',
            'titulo': f'Popularidad Mediana por Generos ({tipo_bd})',
            'figura': fig,
            'contenido': ["Grafico de barras exportado de Popularidad por Generos"]
        }
        st.toast("Grafico agregado al informe")

    with st.expander("Ver tabla de datos", expanded=False):
        df_generos_limpio = agrupado_generos.drop(columns=['porcentaje_total'])
        st.dataframe(df_generos_limpio, use_container_width=True)
        
        if st.button("Agregar Tabla de Generos al Informe", key="btn_add_tabla_generos"):
            contenido_texto = []
            for _, row in df_generos_limpio.iterrows():
                contenido_texto.append(f"Genero {row['genres']}: Popularidad Ajustada = {row['popularidad_ajustada']:.2f}, Obras = {row['conteo_producciones']}, Representa = {row['% del Total']}")
                
            st.session_state['cuaderno_items']['tabla_generos_datos'] = {
                'tipo': 'tabla',
                'titulo': f'Datos Tabulares de Generos por Popularidad ({tipo_bd})',
                'contenido': df_generos_limpio
            }
            st.toast("Tabla agregada al reporte")

    st.markdown("---")

    sel_genero = event_generos.selection["points"][0]["x"] if event_generos and event_generos.selection.get("points") else None
    nuevo_genero = sel_genero if sel_genero != st.session_state.estado_genero else None
    st.session_state.estado_genero = sel_genero

    if nuevo_genero:
        popup_detalles_genero(nuevo_genero, df)