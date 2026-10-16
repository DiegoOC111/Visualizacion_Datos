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
    
    if len(df_lang) > 3:
        top4 = df_lang.iloc[:3].copy()
        otros_count = df_lang.iloc[3:]['count'].sum()
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

def crear_grafico_temporal_popularidad_idiomas(df, idiomas_top):
    if 'release_year' not in df.columns or 'popularity' not in df.columns or 'language' not in df.columns:
        return None, pd.DataFrame()
        
    df_temp = df.dropna(subset=['language', 'popularity', 'release_year']).copy()
    df_temp['language'] = df_temp['language'].astype(str).str.strip()
    
    df_temp = df_temp[df_temp['language'].isin(idiomas_top)]
    
    df_agrupado = df_temp.groupby(['release_year', 'language'])['popularity'].median().reset_index()
    df_agrupado.rename(columns={'popularity': 'Promedio de Popularidad', 'release_year': 'Año'}, inplace=True)
    
    fig = px.line(
        df_agrupado,
        x='Año',
        y='Promedio de Popularidad',
        color='language',
        title="Evolucion Temporal: Popularidad Mediana por Idioma",
        labels={'language': 'Idioma'},
        color_discrete_sequence=px.colors.qualitative.Pastel,
        markers=True
    )
    
    fig.update_layout(
        template='plotly_white',
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified"
    )
    
    return fig, df_agrupado

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
        
    if 'filtro_anios' in st.session_state:
        min_y, max_y = st.session_state['filtro_anios']
        
        if 'release_year' in df_pelis.columns:
            df_pelis['release_year'] = pd.to_numeric(df_pelis['release_year'], errors='coerce')
            df_pelis = df_pelis[(df_pelis['release_year'] >= min_y) & (df_pelis['release_year'] <= max_y)]
            
        if 'release_year' in df_series.columns:
            df_series['release_year'] = pd.to_numeric(df_series['release_year'], errors='coerce')
            df_series = df_series[(df_series['release_year'] >= min_y) & (df_series['release_year'] <= max_y)]

    st.markdown("### Controles de Analisis")
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
        st.warning("Selecciona al menos un idioma para visualizar las graficas detalladas.")
        return

    st.markdown("---")

    with st.expander("1. Distribucion General de Producciones (Circulares)", expanded=False):
        col_pie1, col_pie2 = st.columns(2)
        
        with col_pie1:
            fig_pie_pelis = crear_pie_chart_idiomas(df_pelis, "Idiomas Principales en Peliculas")
            if fig_pie_pelis:
                st.plotly_chart(fig_pie_pelis, use_container_width=True, key="pie_pelis")
                if st.button("Agregar Grafico (Peliculas) al Informe", key="btn_add_pie_pelis"):
                    rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                    st.session_state['cuaderno_items'][f'pie_idiomas_pelis-{rango_actual}'] = {
                        'tipo': 'grafico',
                        'titulo': 'Distribucion de Idiomas - Peliculas',
                        'figura': fig_pie_pelis,
                        'contenido': f"Grafico circular de los 3 idiomas principales y agrupacion 'Otros' en Peliculas. Rango: {rango_actual}",
                        'rango_anios': rango_actual
                    }
                    st.toast("Grafico agregado al informe")

        with col_pie2:
            fig_pie_series = crear_pie_chart_idiomas(df_series, "Idiomas Principales en Series")
            if fig_pie_series:
                st.plotly_chart(fig_pie_series, use_container_width=True, key="pie_series")
                if st.button("Agregar Grafico (Series) al Informe", key="btn_add_pie_series"):
                    rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                    st.session_state['cuaderno_items'][f'pie_idiomas_series-{rango_actual}'] = {
                        'tipo': 'grafico',
                        'titulo': 'Distribucion de Idiomas - Series',
                        'figura': fig_pie_series,
                        'contenido': f"Grafico circular de los 3 idiomas principales y agrupacion 'Otros' en Series. Rango: {rango_actual}",
                        'rango_anios': rango_actual
                    }
                    st.toast("Grafico agregado al informe")

    with st.expander("2. Analisis Detallado de Popularidad (Barras)", expanded=True):
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

        event_idiomas = st.plotly_chart(
            fig,
            use_container_width=True,
            on_select="rerun",
            selection_mode="points",
            key="grafico_idiomas_interactivo"
        )
        
        if st.button("Agregar Grafico de Barras al Informe", key="btn_add_graf_idiomas_pop"):
            rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
            st.session_state['cuaderno_items'][f'graf_idiomas_pop-{rango_actual}'] = {
                'tipo': 'grafico',
                'titulo': f'Popularidad Mediana por Idiomas ({tipo_bd})',
                'figura': fig,
                'contenido': ["Grafico de barras exportado de Popularidad por Idiomas con ajuste Bayesiano."],
                'rango_anios': rango_actual
            }
            st.toast("Grafico agregado al informe")

        if st.toggle("Mostrar tabla de datos de barras", key="tgl_tabla_barras_idioma_pop"):
            df_idiomas_limpio = agrupado_idiomas.drop(columns=['porcentaje_total'])
            st.dataframe(df_idiomas_limpio, use_container_width=True)
            
            if st.button("Agregar Tabla de Idiomas al Informe", key="btn_add_tabla_idiomas"):
                rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                st.session_state['cuaderno_items'][f'tabla_idiomas_datos-{rango_actual}'] = {
                    'tipo': 'tabla',
                    'titulo': f'Datos Tabulares de Idiomas por Popularidad ({tipo_bd})',
                    'contenido': df_idiomas_limpio,
                    'rango_anios': rango_actual
                }
                st.toast("Tabla agregada al reporte")

    with st.expander("3. Evolucion de Popularidad Mediana (Lineas)", expanded=True):
        fig_line, df_temp_agrupado = crear_grafico_temporal_popularidad_idiomas(df, idiomas_seleccionados)
        
        if fig_line is not None and not df_temp_agrupado.empty:
            st.plotly_chart(fig_line, use_container_width=True, key="line_pop_temporal_idioma")
            
            if st.button("Agregar Grafico Temporal al Informe", key="btn_add_line_temporal_pop_idioma"):
                rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                st.session_state['cuaderno_items'][f'line_temporal_pop_idioma-{rango_actual}'] = {
                    'tipo': 'grafico',
                    'titulo': f'Evolucion de Popularidad por Idioma ({tipo_bd})',
                    'figura': fig_line,
                    'contenido': "Grafico de linea temporal mostrando la mediana de popularidad por año de los idiomas seleccionados.",
                    'rango_anios': rango_actual
                }
                st.toast("Grafico agregado al informe")
                
            if st.toggle("Mostrar datos temporales", key="tgl_tabla_temporal_idioma_pop"):
                df_pivot = df_temp_agrupado.pivot(index='Año', columns='language', values='Promedio de Popularidad').reset_index().round(1)
                df_pivot = df_pivot.fillna(0)
                st.dataframe(df_pivot, use_container_width=True)
                
                if st.button("Agregar Tabla Temporal al Informe", key="btn_add_tabla_temporal_pop_idioma"):
                    rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                    st.session_state['cuaderno_items'][f'tabla_temporal_pop_idioma-{rango_actual}'] = {
                        'tipo': 'tabla',
                        'titulo': f'Historico de Popularidad por Idioma ({tipo_bd})',
                        'contenido': df_pivot,
                        'rango_anios': rango_actual
                    }
                    st.toast("Tabla agregada al reporte")

    if "estado_idioma" not in st.session_state:
        st.session_state.estado_idioma = None

    sel_idioma = event_idiomas.selection["points"][0]["x"] if event_idiomas and event_idiomas.selection.get("points") else None
    nuevo_idioma = sel_idioma if sel_idioma != st.session_state.estado_idioma else None
    st.session_state.estado_idioma = sel_idioma

    if nuevo_idioma:
        popup_detalles_idioma(nuevo_idioma, df)