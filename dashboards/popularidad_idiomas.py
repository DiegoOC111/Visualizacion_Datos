import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def cargar_datos(tipo_bd):
    if tipo_bd == "Películas":
        return pd.read_csv("Datos/peliculas.csv")
    else:
        return pd.read_csv("Datos/series.csv")

def crear_pie_chart_idiomas(df, titulo):
    if 'language' not in df.columns:
        return None
        
    df_lang = df['language'].dropna().str.strip().value_counts().reset_index()
    df_lang.columns = ['language', 'count']
    
    if len(df_lang) > 4:
        top4 = df_lang.iloc[:4].copy()
        otros_count = df_lang.iloc[4:]['count'].sum()
        otros_df = pd.DataFrame({'language': ['Otros'], 'count': [otros_count]})
        df_final = pd.concat([top4, otros_df], ignore_index=True)
    else:
        df_final = df_lang
        
    fig = px.pie(
        df_final, 
        values='count', 
        names='language', 
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

@st.dialog("Resumen de Idioma", width="large")
def popup_detalles_idioma(idioma, df_actual):
    st.markdown(f"### Idioma: {idioma.upper()}")
    
    df_idioma = df_actual[df_actual['language'] == idioma].copy()
    
    if df_idioma.empty:
        st.warning("No hay datos para este idioma.")
        return

    cantidad_producciones = df_idioma['title'].nunique()
    total_bd = df_actual['title'].nunique()
    porcentaje_total = (cantidad_producciones / total_bd) * 100
    
    st.info(f"Cantidad de producciones: {cantidad_producciones:,} ({porcentaje_total:.2f}% del catalogo total)")
        
    st.write("")
    
    if not df_idioma.dropna(subset=['title', 'popularity']).empty:
        agrupado_titulos = df_idioma.groupby('title')['popularity'].median().reset_index()
        titulo_top = agrupado_titulos.sort_values(by='popularity', ascending=False).head(1)['title'].values[0]
    else:
        titulo_top = "No hay datos"

    actor_top = obtener_mas_famoso_mediana(df_idioma, 'cast') if 'cast' in df_idioma.columns else "No disponible"
    director_top = obtener_mas_famoso_mediana(df_idioma, 'director') if 'director' in df_idioma.columns else "No disponible"

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
    st.title("Popularidad Mediana por Idioma")

    try:
        df_pelis = cargar_datos("Películas")
        df_series = cargar_datos("Series")
    except FileNotFoundError:
        st.error("No se encontraron los archivos de datos.")
        st.stop()

    # --- SECCION NUEVA: GRAFICOS PIE ---
    st.subheader("Distribucion General de Idiomas en el Catalogo")
    col_pie1, col_pie2 = st.columns(2)
    
    with col_pie1:
        fig_pie_pelis = crear_pie_chart_idiomas(df_pelis, "Idiomas Principales en Peliculas")
        if fig_pie_pelis:
            st.plotly_chart(fig_pie_pelis, use_container_width=True, key="pie_pelis")
            if st.button("Agregar Grafico de Peliculas al Informe", key="btn_add_pie_pelis"):
                st.session_state['cuaderno_items']['pie_idiomas_pelis'] = {
                    'tipo': 'grafico',
                    'titulo': 'Distribucion de Idiomas - Peliculas',
                    'figura': fig_pie_pelis,
                    'contenido': "Grafico circular de los 4 idiomas principales y agrupacion 'Otros' en Peliculas."
                }
                st.toast("Grafico agregado al informe")

    with col_pie2:
        fig_pie_series = crear_pie_chart_idiomas(df_series, "Idiomas Principales en Series")
        if fig_pie_series:
            st.plotly_chart(fig_pie_series, use_container_width=True, key="pie_series")
            if st.button("Agregar Grafico de Series al Informe", key="btn_add_pie_series"):
                st.session_state['cuaderno_items']['pie_idiomas_series'] = {
                    'tipo': 'grafico',
                    'titulo': 'Distribucion de Idiomas - Series',
                    'figura': fig_pie_series,
                    'contenido': "Grafico circular de los 4 idiomas principales y agrupacion 'Otros' en Series."
                }
                st.toast("Grafico agregado al informe")

    st.markdown("---")
    
    # --- SECCION ORIGINAL: ANALISIS DETALLADO ---
    st.subheader("Analisis Detallado de Popularidad")
    tipo_bd = st.selectbox("Selecciona la base de datos:", ["Películas", "Series"], key="bd_idiomas")

    df = df_pelis if tipo_bd == "Películas" else df_series

    if 'language' not in df.columns:
        st.error("La base de datos seleccionada no contiene una columna de idiomas.")
        st.stop()

    total_producciones_catalogo = len(df)

    lista_idiomas = sorted(df['language'].dropna().astype(str).str.strip().unique())
    idiomas_seleccionados = st.multiselect(
        "Agrega los idiomas que deseas comparar:",
        options=lista_idiomas,
        default=["en", "es", "ja"] if all(i in lista_idiomas for i in ["en", "es", "ja"]) else lista_idiomas[:3]
    )
    if not idiomas_seleccionados:
        st.warning("Selecciona al menos un idioma para visualizar la grafica.")
        return

    df_filtrado = df[df['language'].isin(idiomas_seleccionados)]
    agrupado_idiomas = df_filtrado.groupby('language').agg(
        mediana_popularidad=('popularity', 'median'),
        conteo_producciones=('title', 'count')
    ).reset_index()

    agrupado_idiomas['porcentaje_total'] = (agrupado_idiomas['conteo_producciones'] / total_producciones_catalogo) * 100
    agrupado_idiomas['% del Total'] = agrupado_idiomas['porcentaje_total'].apply(lambda x: f"{x:.2f}%")

    C = df_filtrado['popularity'].median()
    m = agrupado_idiomas['conteo_producciones'].quantile(0.25)

    agrupado_idiomas['popularidad_ajustada'] = (
        (agrupado_idiomas['conteo_producciones'] / (agrupado_idiomas['conteo_producciones'] + m)) * agrupado_idiomas['mediana_popularidad'] +
        (m / (agrupado_idiomas['conteo_producciones'] + m)) * C
    )

    agrupado_idiomas = agrupado_idiomas.sort_values(by='popularidad_ajustada', ascending=False)

    fig = px.bar(
        agrupado_idiomas,
        x='language',
        y='popularidad_ajustada',
        color='conteo_producciones',
        color_continuous_scale='Purp',
        labels={
            'language': 'Idioma', 
            'popularidad_ajustada': 'Popularidad (Ajustada)',
            'conteo_producciones': 'Volumen de Datos'
        },
        title="Popularidad por Idioma (Ajuste Bayesiano)",
        hover_data={'mediana_popularidad': True, '% del Total': True} 
    )
    
    fig.update_layout(
        xaxis={'categoryorder': 'total descending'},
        template='plotly_white',
        margin=dict(l=10, r=10, t=40, b=10),
        clickmode='event+select'
    )
    
    fig.update_traces(texttemplate='%{y:.1f}', textposition='outside')

    if "estado_idioma" not in st.session_state:
        st.session_state.estado_idioma = None

    event_idiomas = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key="grafico_idiomas_interactivo"
    )
    
    if st.button("Agregar Grafico de Barras al Informe", key="btn_add_graf_idiomas_pop"):
        st.session_state['cuaderno_items']['graf_idiomas_pop'] = {
            'tipo': 'grafico',
            'titulo': 'Popularidad Mediana por Idiomas (Ajuste Bayesiano)',
            'figura': fig,
            'contenido': ["Grafico de barras exportado de Popularidad por Idiomas"]
        }
        st.toast("Grafico agregado al informe")

    with st.expander("Ver tabla de datos", expanded=False):
        df_idiomas_limpio = agrupado_idiomas.drop(columns=['porcentaje_total'])
        st.dataframe(df_idiomas_limpio, use_container_width=True)
        
        if st.button("Agregar Tabla de Idiomas al Informe", key="btn_add_tabla_idiomas"):
            contenido_texto = []
            for _, row in df_idiomas_limpio.iterrows():
                contenido_texto.append(f"Idioma {row['language']}: Popularidad Ajustada = {row['popularidad_ajustada']:.2f}, Obras = {row['conteo_producciones']}, Representa = {row['% del Total']}")
                
            st.session_state['cuaderno_items']['tabla_idiomas_datos'] = {
                'tipo': 'tabla',
                'titulo': f'Datos Tabulares de Idiomas por Popularidad ({tipo_bd})',
                'contenido': df_idiomas_limpio
            }
            st.toast("Tabla agregada al reporte")

    st.markdown("---")

    sel_idioma = event_idiomas.selection["points"][0]["x"] if event_idiomas and event_idiomas.selection.get("points") else None
    nuevo_idioma = sel_idioma if sel_idioma != st.session_state.estado_idioma else None
    st.session_state.estado_idioma = sel_idioma

    if nuevo_idioma:
        popup_detalles_idioma(nuevo_idioma, df)