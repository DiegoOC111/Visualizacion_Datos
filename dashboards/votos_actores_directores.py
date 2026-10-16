import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def cargar_datos(tipo_bd):
    if tipo_bd == "Películas":
        return pd.read_csv("Datos/peliculas.csv")
    else:
        return pd.read_csv("Datos/series.csv")

def top_por_votos(df, columna_objetivo, columna_idioma=None, idiomas_permitidos=None, min_apariciones=5, top_n=5):
    total_votos_catalogo = df['vote_count'].sum() if 'vote_count' in df.columns else 1

    columnas = [columna_objetivo, 'vote_count', 'title']
    if columna_idioma:
        columnas.append(columna_idioma)
    
    df_temp = df[columnas].dropna(subset=[columna_objetivo, 'title', 'vote_count']).copy()
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
        total_votos=('vote_count', 'sum'),
        cantidad_apariciones=('title', 'count')
    )
    agrupado = agrupado[agrupado['cantidad_apariciones'] >= min_apariciones]
    
    agrupado['porcentaje_votos'] = (agrupado['total_votos'] / total_votos_catalogo) * 100
    agrupado['% del Total'] = agrupado['porcentaje_votos'].apply(lambda x: f"{x:.2f}%")
    
    return agrupado.sort_values(by='total_votos', ascending=False).head(top_n)

def crear_grafico_votos(df_top, columna_nombre, titulo_grafico, paleta_color="Blues"):
    df_plot = df_top.reset_index()
    
    fig = px.bar(
        df_plot,
        x=columna_nombre,
        y='total_votos',
        color='total_votos',
        color_continuous_scale=paleta_color,
        labels={
            columna_nombre: columna_nombre.capitalize(),
            'total_votos': 'Total de Votos',
            'cantidad_apariciones': 'Obras'
        },
        title=titulo_grafico,
        hover_data={'cantidad_apariciones': True, '% del Total': True}
    )
    
    fig.update_layout(
        xaxis={'categoryorder': 'total descending'},
        coloraxis_showscale=False,
        template='plotly_white',
        margin=dict(l=10, r=10, t=40, b=10),
        clickmode='event+select'
    )
    
    fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
    return fig

def crear_grafico_temporal_talento(df, columna_objetivo, talentos_top):
    if 'release_year' not in df.columns or 'vote_count' not in df.columns or columna_objetivo not in df.columns:
        return None, pd.DataFrame()
        
    df_temp = df.dropna(subset=[columna_objetivo, 'vote_count', 'release_year']).copy()
    df_temp[columna_objetivo] = df_temp[columna_objetivo].astype(str).str.split(',')
    df_temp = df_temp.explode(columna_objetivo)
    df_temp[columna_objetivo] = df_temp[columna_objetivo].str.strip()
    
    df_temp = df_temp[df_temp[columna_objetivo].isin(talentos_top)]
    
    df_agrupado = df_temp.groupby(['release_year', columna_objetivo])['vote_count'].mean().reset_index()
    df_agrupado.rename(columns={'vote_count': 'Promedio de Votos', 'release_year': 'Año'}, inplace=True)
    
    titulo = "Evolucion de Votos: Actores" if columna_objetivo == 'cast' else "Evolucion de Votos: Directores"
    
    fig = px.line(
        df_agrupado,
        x='Año',
        y='Promedio de Votos',
        color=columna_objetivo,
        title=titulo,
        labels={columna_objetivo: columna_objetivo.capitalize()},
        color_discrete_sequence=px.colors.qualitative.Pastel,
        markers=True
    )
    
    fig.update_layout(
        template='plotly_white',
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified"
    )
    
    return fig, df_agrupado

@st.dialog("Resumen de Interacciones", width="large")
def popup_detalles_votos(seleccion, df_actual):
    st.markdown(f"### {seleccion}")
    nombre_url = seleccion.replace(' ', '_')
    url_wiki = f"https://es.wikipedia.org/wiki/{nombre_url}"
    st.info(f"[Ver en Wikipedia]({url_wiki})")
    
    mask_cast = df_actual['cast'].fillna('').str.contains(seleccion, case=False, regex=False) if 'cast' in df_actual.columns else False
    mask_dir = df_actual['director'].fillna('').str.contains(seleccion, case=False, regex=False) if 'director' in df_actual.columns else False
    
    df_persona = df_actual[mask_cast | mask_dir].drop_duplicates(subset=['title']).copy()
    
    if not df_persona.empty:
        votos_totales = df_persona['vote_count'].sum()
        st.success(f"Interacciones Totales (Votos): {int(votos_totales):,}")
        
        with st.expander(f"Producciones encontradas ({len(df_persona)})", expanded=True):
            st.write(", ".join(df_persona['title'].astype(str).tolist()))
        
        st.write("") 
        
        mas_votada = df_persona.loc[df_persona['vote_count'].idxmax()]
        menos_votada = df_persona.loc[df_persona['vote_count'].idxmin()]
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Mas Votada**")
            st.markdown(f"##### {mas_votada['title']}")
            st.info(f"{mas_votada['vote_count']:,.0f} votos")
        with c2:
            st.markdown("**Menos Votada**")
            st.markdown(f"##### {menos_votada['title']}")
            st.warning(f"{menos_votada['vote_count']:,.0f} votos")

def mostrar():
    st.title("Dashboard de Interacciones: Actores y Directores")

    tipo_bd = st.selectbox("Selecciona la base de datos a analizar:", ["Películas", "Series"], key="bd_interacciones_ad")

    try:
        df_actual = cargar_datos(tipo_bd)
    except FileNotFoundError:
        st.error(f"No se encontro el archivo respectivo para {tipo_bd}.")
        st.stop()
        
    if 'filtro_anios' in st.session_state and 'release_year' in df_actual.columns:
        df_actual['release_year'] = pd.to_numeric(df_actual['release_year'], errors='coerce')
        min_y, max_y = st.session_state['filtro_anios']
        df_actual = df_actual[(df_actual['release_year'] >= min_y) & (df_actual['release_year'] <= max_y)]
        
    st.markdown("### Controles de Analisis")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        lista_idiomas = sorted(df_actual['language'].dropna().astype(str).str.strip().unique()) if 'language' in df_actual.columns else []
        idiomas_seleccionados = st.multiselect(
            "Filtro por Idioma(s):",
            options=lista_idiomas,
            default=["en"] if "en" in lista_idiomas else None,
            key="idiomas_interacciones_ad"
        )
        
    with col_c2:
        min_apariciones = st.slider("Apariciones minimas en producciones:", min_value=1, max_value=10, value=5, key="slider_int_ad")

    st.markdown("---")

    if "estado_actores_int" not in st.session_state:
        st.session_state.estado_actores_int = None
    if "estado_directores_int" not in st.session_state:
        st.session_state.estado_directores_int = None

    if not idiomas_seleccionados:
        st.warning("Por favor, selecciona al menos un idioma para ver los resultados.")
    else:
        with st.expander("1. Analisis de Interacciones: Actores", expanded=True):
            if 'cast' in df_actual.columns:
                top_actores = top_por_votos(df_actual, 'cast', 'language', idiomas_seleccionados, min_apariciones, 5)
                if not top_actores.empty:
                    fig_actores = crear_grafico_votos(top_actores, 'cast', 'Interacciones Totales: Actores', 'Blues')
                    event_actores = st.plotly_chart(
                        fig_actores, 
                        use_container_width=True, 
                        on_select="rerun", 
                        selection_mode="points",
                        key="grafico_actores_int"
                    )
                    
                    if st.button("Agregar Grafico (Barras) Actores al Informe", key="btn_add_graf_actores_votos"):
                        rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                        st.session_state['cuaderno_items'][f'graf_actores_votos-{rango_actual}'] = {
                            'tipo': 'grafico',
                            'titulo': f'Top 5 Actores por Interacciones ({tipo_bd})',
                            'figura': fig_actores,
                            'contenido': "Grafico exportado de Top Actores por Votos totales",
                            'rango_anios': rango_actual
                        }
                        st.toast("Grafico agregado al informe")
                        
                    st.markdown("##### Evolucion Temporal")
                    talentos_top_act = top_actores.index.tolist()
                    fig_line_act, df_temp_act = crear_grafico_temporal_talento(df_actual, 'cast', talentos_top_act)
                    
                    if fig_line_act is not None and not df_temp_act.empty:
                        st.plotly_chart(fig_line_act, use_container_width=True, key="line_votos_actores")
                        
                        if st.button("Agregar Grafico (Lineas) Actores al Informe", key="btn_add_line_actores_votos"):
                            rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                            st.session_state['cuaderno_items'][f'line_actores_votos-{rango_actual}'] = {
                                'tipo': 'grafico',
                                'titulo': f'Evolucion Votos: Actores ({tipo_bd})',
                                'figura': fig_line_act,
                                'contenido': "Evolucion promedio de votos por año para los top actores.",
                                'rango_anios': rango_actual
                            }
                            st.toast("Grafico agregado al informe")
                    
                    if st.toggle("Mostrar tablas de datos (Actores)", key="tgl_tablas_actores"):
                        st.write("**Totales de Interaccion**")
                        df_actores_limpio = top_actores.drop(columns=['porcentaje_votos'])
                        st.dataframe(df_actores_limpio, use_container_width=True)
                        if st.button("Agregar Tabla Totales al Informe", key="btn_add_tabla_actores_votos"):
                            rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                            st.session_state['cuaderno_items'][f'tabla_actores_votos-{rango_actual}'] = {
                                'tipo': 'tabla',
                                'titulo': f'Datos Top Actores por Interacciones ({tipo_bd})',
                                'contenido': df_actores_limpio,
                                'rango_anios': rango_actual
                            }
                            st.toast("Tabla agregada al reporte")
                            
                        if not df_temp_act.empty:
                            st.write("**Promedios Anuales**")
                            df_pivot_act = df_temp_act.pivot(index='Año', columns='cast', values='Promedio de Votos').reset_index().round(1).fillna(0)
                            st.dataframe(df_pivot_act, use_container_width=True)
                            if st.button("Agregar Tabla Temporal al Informe", key="btn_add_tabla_temp_act"):
                                rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                                st.session_state['cuaderno_items'][f'tabla_temp_act_votos-{rango_actual}'] = {
                                    'tipo': 'tabla',
                                    'titulo': f'Historico Promedio Votos Actores ({tipo_bd})',
                                    'contenido': df_pivot_act,
                                    'rango_anios': rango_actual
                                }
                                st.toast("Tabla agregada al reporte")
                else:
                    st.info("Sin resultados de Actores para los filtros seleccionados.")
            else:
                st.error("No existe la columna 'cast'.")

        with st.expander("2. Analisis de Interacciones: Directores", expanded=False):
            if 'director' in df_actual.columns:
                top_directores = top_por_votos(df_actual, 'director', 'language', idiomas_seleccionados, min_apariciones, 5)
                if not top_directores.empty:
                    fig_directores = crear_grafico_votos(top_directores, 'director', 'Interacciones Totales: Directores', 'Reds')
                    event_directores = st.plotly_chart(
                        fig_directores, 
                        use_container_width=True, 
                        on_select="rerun", 
                        selection_mode="points",
                        key="grafico_directores_int"
                    )
                    
                    if st.button("Agregar Grafico (Barras) Directores al Informe", key="btn_add_graf_directores_votos"):
                        rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                        st.session_state['cuaderno_items'][f'graf_directores_votos-{rango_actual}'] = {
                            'tipo': 'grafico',
                            'titulo': f'Top 5 Directores por Interacciones ({tipo_bd})',
                            'figura': fig_directores,
                            'contenido': "Grafico exportado de Top Directores por Votos totales",
                            'rango_anios': rango_actual
                        }
                        st.toast("Grafico agregado al informe")
                        
                    st.markdown("##### Evolucion Temporal")
                    talentos_top_dir = top_directores.index.tolist()
                    fig_line_dir, df_temp_dir = crear_grafico_temporal_talento(df_actual, 'director', talentos_top_dir)
                    
                    if fig_line_dir is not None and not df_temp_dir.empty:
                        st.plotly_chart(fig_line_dir, use_container_width=True, key="line_votos_directores")
                        
                        if st.button("Agregar Grafico (Lineas) Directores al Informe", key="btn_add_line_dir_votos"):
                            rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                            st.session_state['cuaderno_items'][f'line_dir_votos-{rango_actual}'] = {
                                'tipo': 'grafico',
                                'titulo': f'Evolucion Votos: Directores ({tipo_bd})',
                                'figura': fig_line_dir,
                                'contenido': "Evolucion promedio de votos por año para los top directores.",
                                'rango_anios': rango_actual
                            }
                            st.toast("Grafico agregado al informe")
                    
                    if st.toggle("Mostrar tablas de datos (Directores)", key="tgl_tablas_directores"):
                        st.write("**Totales de Interaccion**")
                        df_directores_limpio = top_directores.drop(columns=['porcentaje_votos'])
                        st.dataframe(df_directores_limpio, use_container_width=True)
                        if st.button("Agregar Tabla Totales al Informe", key="btn_add_tabla_directores_votos"):
                            rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                            st.session_state['cuaderno_items'][f'tabla_directores_votos-{rango_actual}'] = {
                                'tipo': 'tabla',
                                'titulo': f'Datos Top Directores por Interacciones ({tipo_bd})',
                                'contenido': df_directores_limpio,
                                'rango_anios': rango_actual
                            }
                            st.toast("Tabla agregada al reporte")
                            
                        if not df_temp_dir.empty:
                            st.write("**Promedios Anuales**")
                            df_pivot_dir = df_temp_dir.pivot(index='Año', columns='director', values='Promedio de Votos').reset_index().round(1).fillna(0)
                            st.dataframe(df_pivot_dir, use_container_width=True)
                            if st.button("Agregar Tabla Temporal al Informe", key="btn_add_tabla_temp_dir"):
                                rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                                st.session_state['cuaderno_items'][f'tabla_temp_dir_votos-{rango_actual}'] = {
                                    'tipo': 'tabla',
                                    'titulo': f'Historico Promedio Votos Directores ({tipo_bd})',
                                    'contenido': df_pivot_dir,
                                    'rango_anios': rango_actual
                                }
                                st.toast("Tabla agregada al reporte")
                else:
                    st.info("Sin resultados de Directores para los filtros seleccionados.")
            else:
                st.error("No existe la columna 'director'.")
        
        sel_actor = None
        sel_director = None
        
        if 'event_actores' in locals() and event_actores:
            sel_actor = event_actores.selection["points"][0]["x"] if event_actores.selection.get("points") else None
            
        if 'event_directores' in locals() and event_directores:
            sel_director = event_directores.selection["points"][0]["x"] if event_directores.selection.get("points") else None

        nuevo_actor = sel_actor if sel_actor != st.session_state.estado_actores_int else None
        nuevo_director = sel_director if sel_director != st.session_state.estado_directores_int else None

        st.session_state.estado_actores_int = sel_actor
        st.session_state.estado_directores_int = sel_director

        if nuevo_actor:
            popup_detalles_votos(nuevo_actor, df_actual)
        elif nuevo_director:
            popup_detalles_votos(nuevo_director, df_actual)