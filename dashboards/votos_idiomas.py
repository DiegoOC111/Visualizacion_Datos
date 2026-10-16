import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def cargar_datos(tipo_bd):
    if tipo_bd == "Películas":
        return pd.read_csv("Datos/peliculas.csv")
    else:
        return pd.read_csv("Datos/series.csv")

def crear_pie_chart_idiomas_votos(df, titulo):
    if 'language' not in df.columns or 'vote_count' not in df.columns:
        return None
        
    df_lang = df.dropna(subset=['language', 'vote_count']).copy()
    df_lang['language'] = df_lang['language'].astype(str).str.strip()
    
    df_counts = df_lang.groupby('language')['vote_count'].sum().reset_index()
    df_counts.columns = ['language', 'total_votos']
    df_counts = df_counts.sort_values(by='total_votos', ascending=False)
    
    if len(df_counts) > 3:
        top4 = df_counts.iloc[:3].copy()
        otros_count = df_counts.iloc[3:]['total_votos'].sum()
        otros_df = pd.DataFrame({'language': ['Otros'], 'total_votos': [otros_count]})
        df_final = pd.concat([top4, otros_df], ignore_index=True)
    else:
        df_final = df_counts
        
    fig = px.pie(
        df_final, 
        values='total_votos', 
        names='language', 
        title=titulo,
        hole=0.3,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    return fig

def crear_grafico_temporal_votos_idiomas(df, idiomas_top):
    if 'release_year' not in df.columns or 'vote_count' not in df.columns or 'language' not in df.columns:
        return None, pd.DataFrame()
        
    df_temp = df.dropna(subset=['language', 'vote_count', 'release_year']).copy()
    df_temp['language'] = df_temp['language'].astype(str).str.strip()
    
    df_temp = df_temp[df_temp['language'].isin(idiomas_top)]
    
    df_agrupado = df_temp.groupby(['release_year', 'language'])['vote_count'].mean().reset_index()
    df_agrupado.rename(columns={'vote_count': 'Promedio de Votos', 'release_year': 'Año'}, inplace=True)
    
    fig = px.line(
        df_agrupado,
        x='Año',
        y='Promedio de Votos',
        color='language',
        title="Evolucion Temporal: Promedio de Votos por Idioma",
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

def obtener_mas_votado(df, columna, min_apariciones=2):
    df_temp = df.dropna(subset=[columna, 'vote_count', 'title']).copy()
    df_temp[columna] = df_temp[columna].astype(str).str.split(',')
    df_temp = df_temp.explode(columna)
    df_temp[columna] = df_temp[columna].str.strip()
    df_temp = df_temp[df_temp[columna].str.lower() != 'unknown']
    df_temp = df_temp.drop_duplicates(subset=[columna, 'title'])
    
    if df_temp.empty:
        return "No hay datos"
        
    agrupado = df_temp.groupby(columna).agg(
        total_votos=('vote_count', 'sum'),
        conteo=('title', 'count')
    ).reset_index()
    
    agrupado = agrupado[agrupado['conteo'] >= min_apariciones]
    if agrupado.empty:
        return "Datos insuficientes"
        
    top_1 = agrupado.sort_values(by='total_votos', ascending=False).head(1)[columna].values[0]
    return top_1

@st.dialog("Resumen de Interacciones por Idioma", width="large")
def popup_detalles_idioma_votos(idioma, df_actual):
    st.markdown(f"### Idioma: {idioma.upper()}")
    
    df_idioma = df_actual[df_actual['language'] == idioma].copy()
    if df_idioma.empty:
        st.warning("No hay datos para este idioma.")
        return

    votos_idioma = df_idioma['vote_count'].sum()
    votos_totales_bd = df_actual['vote_count'].sum()
    porcentaje_votos = (votos_idioma / votos_totales_bd) * 100 if votos_totales_bd > 0 else 0
    
    st.info(f"Total de Interacciones: {int(votos_idioma):,} votos ({porcentaje_votos:.2f}% de los votos totales)")
    st.write("")
    
    if not df_idioma.dropna(subset=['title', 'vote_count']).empty:
        mas_votada = df_idioma.loc[df_idioma['vote_count'].idxmax()]
        titulo_top = mas_votada['title']
        votos_top = mas_votada['vote_count']
    else:
        titulo_top = "No hay datos"
        votos_top = 0

    actor_top = obtener_mas_votado(df_idioma, 'cast') if 'cast' in df_idioma.columns else "No disponible"
    director_top = obtener_mas_votado(df_idioma, 'director') if 'director' in df_idioma.columns else "No disponible"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Produccion mas votada**")
        st.markdown(f"##### {titulo_top}")
        st.success(f"{votos_top:,.0f} votos")
    with c2:
        st.markdown("**Actor mas votado**")
        st.markdown(f"##### {actor_top}")
    with c3:
        st.markdown("**Director mas votado**")
        st.markdown(f"##### {director_top}")

def mostrar():
    st.title("Interacciones Totales por Idioma")

    try:
        df_pelis = cargar_datos("Películas")
        df_series = cargar_datos("Series")
    except FileNotFoundError:
        st.error("No se encontraron los archivos de datos.")
        st.stop()
        
    # --- FILTRO GLOBAL ---
    if 'filtro_anios' in st.session_state:
        min_y, max_y = st.session_state['filtro_anios']
        
        if 'release_year' in df_pelis.columns:
            df_pelis['release_year'] = pd.to_numeric(df_pelis['release_year'], errors='coerce')
            df_pelis = df_pelis[(df_pelis['release_year'] >= min_y) & (df_pelis['release_year'] <= max_y)]
            
        if 'release_year' in df_series.columns:
            df_series['release_year'] = pd.to_numeric(df_series['release_year'], errors='coerce')
            df_series = df_series[(df_series['release_year'] >= min_y) & (df_series['release_year'] <= max_y)]

    # --- CONTROLES DE ANALISIS DETALLADO ---
    st.markdown("### Controles de Analisis")
    tipo_bd = st.selectbox("Selecciona la base de datos:", ["Películas", "Series"], key="bd_idiomas_int")

    df = df_pelis if tipo_bd == "Películas" else df_series

    if 'language' not in df.columns or 'vote_count' not in df.columns:
        st.error("Faltan columnas necesarias (language o vote_count).")
        st.stop()

    total_votos_catalogo = df['vote_count'].sum() if 'vote_count' in df.columns else 1

    lista_idiomas = sorted(df['language'].dropna().astype(str).str.strip().unique())
    idiomas_seleccionados = st.multiselect(
        "Agrega los idiomas que deseas comparar:",
        options=lista_idiomas,
        default=["en", "es", "ja"] if all(i in lista_idiomas for i in ["en", "es", "ja"]) else lista_idiomas[:3],
        key="idiomas_int"
    )
    
    if not idiomas_seleccionados:
        st.warning("Selecciona al menos un idioma para visualizar las graficas detalladas.")
        return

    st.markdown("---")

    # --- SEGMENTO 1: GRAFICOS CIRCULARES ---
    with st.expander("1. Distribucion General de Votos (Circulares)", expanded=False):
        col_pie1, col_pie2 = st.columns(2)
        
        with col_pie1:
            fig_pie_pelis = crear_pie_chart_idiomas_votos(df_pelis, "Votos por Idioma en Peliculas")
            if fig_pie_pelis:
                st.plotly_chart(fig_pie_pelis, use_container_width=True, key="pie_votos_idioma_pelis")
                if st.button("Agregar Grafico (Peliculas) al Informe", key="btn_add_pie_votos_idioma_pelis"):
                    rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                    st.session_state['cuaderno_items'][f'pie_votos_idioma_pelis-{rango_actual}'] = {
                        'tipo': 'grafico',
                        'titulo': 'Distribucion de Votos por Idioma - Peliculas',
                        'figura': fig_pie_pelis,
                        'contenido': "Grafico circular de interacciones de los 3 idiomas principales en Peliculas.",
                        'rango_anios': rango_actual
                    }
                    st.toast("Grafico agregado al informe")

        with col_pie2:
            fig_pie_series = crear_pie_chart_idiomas_votos(df_series, "Votos por Idioma en Series")
            if fig_pie_series:
                st.plotly_chart(fig_pie_series, use_container_width=True, key="pie_votos_idioma_series")
                if st.button("Agregar Grafico (Series) al Informe", key="btn_add_pie_votos_idioma_series"):
                    rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                    st.session_state['cuaderno_items'][f'pie_votos_idioma_series-{rango_actual}'] = {
                        'tipo': 'grafico',
                        'titulo': 'Distribucion de Votos por Idioma - Series',
                        'figura': fig_pie_series,
                        'contenido': "Grafico circular de interacciones de los 3 idiomas principales en Series.",
                        'rango_anios': rango_actual
                    }
                    st.toast("Grafico agregado al informe")

    # --- SEGMENTO 2: GRAFICO DE BARRAS ---
    with st.expander("2. Analisis Detallado de Interacciones (Barras)", expanded=True):
        df_filtrado = df[df['language'].isin(idiomas_seleccionados)]
        agrupado_idiomas = df_filtrado.groupby('language').agg(
            total_votos=('vote_count', 'sum'),
            conteo_producciones=('title', 'count')
        ).reset_index()

        agrupado_idiomas['porcentaje_total'] = (agrupado_idiomas['total_votos'] / total_votos_catalogo) * 100
        agrupado_idiomas['% del Total'] = agrupado_idiomas['porcentaje_total'].apply(lambda x: f"{x:.2f}%")
        agrupado_idiomas = agrupado_idiomas.sort_values(by='total_votos', ascending=False)

        fig = px.bar(
            agrupado_idiomas,
            x='language',
            y='total_votos',
            color='total_votos',
            color_continuous_scale='Purp',
            labels={'language': 'Idioma', 'total_votos': 'Total de Votos', 'conteo_producciones': 'Volumen de Datos'},
            title="Interacciones por Idioma",
            hover_data={'conteo_producciones': True, '% del Total': True} 
        )
        
        fig.update_layout(
            xaxis={'categoryorder': 'total descending'},
            template='plotly_white',
            margin=dict(l=10, r=10, t=40, b=10),
            clickmode='event+select',
            coloraxis_showscale=False
        )
        fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')

        event_idiomas = st.plotly_chart(
            fig,
            use_container_width=True,
            on_select="rerun",
            selection_mode="points",
            key="grafico_idiomas_int_interactivo"
        )
        
        if st.button("Agregar Grafico de Barras al Informe", key="btn_add_graf_idiomas_votos"):
            rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
            st.session_state['cuaderno_items'][f'graf_idiomas_votos-{rango_actual}'] = {
                'tipo': 'grafico',
                'titulo': f'Interacciones Totales por Idioma ({tipo_bd})',
                'figura': fig,
                'contenido': "Grafico de barras exportado de Interacciones por Idioma",
                'rango_anios': rango_actual
            }
            st.toast("Grafico agregado al informe")
        
        if st.toggle("Mostrar tabla de datos de barras", key="tgl_tabla_barras_idioma"):
            df_idiomas_limpio = agrupado_idiomas.drop(columns=['porcentaje_total'])
            st.dataframe(df_idiomas_limpio, use_container_width=True)
            
            if st.button("Agregar Tabla de Idiomas al Informe", key="btn_add_tabla_idiomas_votos"):
                rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                st.session_state['cuaderno_items'][f'tabla_idiomas_votos-{rango_actual}'] = {
                    'tipo': 'tabla',
                    'titulo': f'Datos Interacciones por Idioma ({tipo_bd})',
                    'contenido': df_idiomas_limpio,
                    'rango_anios': rango_actual
                }
                st.toast("Tabla agregada al reporte")

    # --- SEGMENTO 3: GRAFICO TEMPORAL ---
    with st.expander("3. Evolucion de Votos Promedio (Lineas)", expanded=True):
        fig_line, df_temp_agrupado = crear_grafico_temporal_votos_idiomas(df, idiomas_seleccionados)
        
        if fig_line is not None and not df_temp_agrupado.empty:
            st.plotly_chart(fig_line, use_container_width=True, key="line_votos_temporal_idioma")
            
            if st.button("Agregar Grafico Temporal al Informe", key="btn_add_line_temporal_votos_idioma"):
                rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                st.session_state['cuaderno_items'][f'line_temporal_votos_idioma-{rango_actual}'] = {
                    'tipo': 'grafico',
                    'titulo': f'Evolucion de Promedio de Votos por Idioma ({tipo_bd})',
                    'figura': fig_line,
                    'contenido': "Grafico de linea temporal mostrando el promedio de votos por año de los idiomas seleccionados.",
                    'rango_anios': rango_actual
                }
                st.toast("Grafico agregado al informe")
                
            if st.toggle("Mostrar datos temporales", key="tgl_tabla_temporal_idioma"):
                df_pivot = df_temp_agrupado.pivot(index='Año', columns='language', values='Promedio de Votos').reset_index().round(1)
                df_pivot = df_pivot.fillna(0)
                st.dataframe(df_pivot, use_container_width=True)
                
                if st.button("Agregar Tabla Temporal al Informe", key="btn_add_tabla_temporal_votos_idioma"):
                    rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                    st.session_state['cuaderno_items'][f'tabla_temporal_votos_idioma-{rango_actual}'] = {
                        'tipo': 'tabla',
                        'titulo': f'Historico de Promedio de Votos por Idioma ({tipo_bd})',
                        'contenido': df_pivot,
                        'rango_anios': rango_actual
                    }
                    st.toast("Tabla agregada al reporte")

    # Dialogo de seleccion
    if "estado_idioma_int" not in st.session_state:
        st.session_state.estado_idioma_int = None

    sel_idioma = event_idiomas.selection["points"][0]["x"] if event_idiomas and event_idiomas.selection.get("points") else None
    nuevo_idioma = sel_idioma if sel_idioma != st.session_state.estado_idioma_int else None
    st.session_state.estado_idioma_int = sel_idioma

    if nuevo_idioma:
        popup_detalles_idioma_votos(nuevo_idioma, df)