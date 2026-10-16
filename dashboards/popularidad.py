import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def cargar_datos(tipo_bd):
    if tipo_bd == "Peliculas":
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
    
    total_apariciones = agrupado['cantidad_apariciones'].sum()
    agrupado['porcentaje_total'] = (agrupado['cantidad_apariciones'] / total_apariciones) * 100
    
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
            'mediana_popularidad': 'Pop. Mediana',
            'cantidad_apariciones': 'Obras'
        },
        title=titulo_grafico,
        hover_data={'cantidad_apariciones': True}
    )
    
    fig.update_layout(
        xaxis={'categoryorder': 'total descending'},
        coloraxis_showscale=False,
        template='plotly_white',
        margin=dict(l=10, r=10, t=40, b=10),
        clickmode='event+select'
    )
    
    fig.update_traces(texttemplate='%{y:.1f}', textposition='outside')
    
    return fig

def crear_grafico_temporal_popularidad(df, columna_objetivo, talentos_top):
    if 'release_year' not in df.columns or 'popularity' not in df.columns or columna_objetivo not in df.columns:
        return None, pd.DataFrame()
        
    df_temp = df.dropna(subset=[columna_objetivo, 'popularity', 'release_year']).copy()
    df_temp[columna_objetivo] = df_temp[columna_objetivo].astype(str).str.split(',')
    df_temp = df_temp.explode(columna_objetivo)
    df_temp[columna_objetivo] = df_temp[columna_objetivo].str.strip()
    
    df_temp = df_temp[df_temp[columna_objetivo].isin(talentos_top)]
    
    df_agrupado = df_temp.groupby(['release_year', columna_objetivo])['popularity'].mean().reset_index()
    df_agrupado.rename(columns={'popularity': 'Promedio de Popularidad', 'release_year': 'Año'}, inplace=True)
    
    titulo = "Evolucion de Popularidad: Actores" if columna_objetivo == 'cast' else "Evolucion de Popularidad: Directores"
    
    fig = px.line(
        df_agrupado,
        x='Año',
        y='Promedio de Popularidad',
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

@st.dialog("Mini-Resumen", width="large")
def popup_detalles(seleccion, df_actual):
    st.markdown(f"### {seleccion}")
    nombre_url = seleccion.replace(' ', '_')
    url_wiki = f"https://es.wikipedia.org/wiki/{nombre_url}"
    st.info(f"[Haz clic aqui para abrir la Wikipedia de {seleccion}]({url_wiki})")
    
    mask_cast = df_actual['cast'].fillna('').str.contains(seleccion, case=False, regex=False) if 'cast' in df_actual.columns else False
    mask_dir = df_actual['director'].fillna('').str.contains(seleccion, case=False, regex=False) if 'director' in df_actual.columns else False
    
    df_persona = df_actual[mask_cast | mask_dir].drop_duplicates(subset=['title']).copy()
    
    if not df_persona.empty:
        titulos_lista = ", ".join(df_persona['title'].astype(str).tolist())
        
        with st.expander(f"Producciones encontradas ({len(df_persona)})", expanded=True):
            st.write(titulos_lista)
        
        st.write("") 
        
        mas_popular = df_persona.loc[df_persona['popularity'].idxmax()]
        menos_popular = df_persona.loc[df_persona['popularity'].idxmin()]
        
        columnas_fecha_posibles = ['release_date', 'first_air_date', 'year', 'date_added']
        col_fecha_usada = next((col for col in columnas_fecha_posibles if col in df_persona.columns), None)
        
        fecha_str = "N/A"
        mas_reciente_titulo = "Desconocido"
        if col_fecha_usada:
            df_persona[col_fecha_usada] = pd.to_datetime(df_persona[col_fecha_usada], errors='coerce')
            mas_reciente = df_persona.sort_values(by=col_fecha_usada, ascending=False).iloc[0]
            fecha_str = mas_reciente[col_fecha_usada].strftime('%Y') if pd.notnull(mas_reciente[col_fecha_usada]) else "N/A"
            mas_reciente_titulo = mas_reciente['title']

        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown("**Mas Popular**")
            st.markdown(f"##### {mas_popular['title']}")
            st.success(f" {mas_popular['popularity']:.1f} pop")
            
        with c2:
            st.markdown("**Menos Popular**")
            st.markdown(f"##### {menos_popular['title']}")
            st.error(f" {menos_popular['popularity']:.1f} pop")
            
        with c3:
            st.markdown("**Mas Reciente**")
            st.markdown(f"##### {mas_reciente_titulo}")
            st.info(f"Año: {fecha_str}")

def mostrar():
    st.title("Dashboard de Popularidad: Actores y Directores")

    tipo_bd = st.selectbox("Selecciona la base de datos a analizar:", ["Peliculas", "Series"])

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
            default=["en"] if "en" in lista_idiomas else None
        )
        
    with col_c2:
        min_apariciones = st.slider("Apariciones minimas en producciones:", min_value=1, max_value=10, value=8)

    st.markdown("---")

    if "estado_actores" not in st.session_state:
        st.session_state.estado_actores = None
    if "estado_directores" not in st.session_state:
        st.session_state.estado_directores = None

    if not idiomas_seleccionados:
        st.warning("Por favor, selecciona al menos un idioma para ver los resultados.")
    else:
        with st.expander("1. Analisis de Popularidad: Actores", expanded=True):
            if 'cast' in df_actual.columns:
                top_actores = top_por_popularidad_por_idioma(
                    df_actual, 'cast', 'language', idiomas_seleccionados, min_apariciones, 5
                )
                if not top_actores.empty:
                    fig_actores = crear_grafico_degrade(
                        top_actores, 'cast', 'Popularidad de Actores', paleta_color='Tealgrn'
                    )
                    event_actores = st.plotly_chart(
                        fig_actores, 
                        use_container_width=True, 
                        on_select="rerun", 
                        selection_mode="points",
                        key="grafico_actores"
                    )
                    
                    if st.button("Agregar Grafico (Barras) Actores al Informe", key="btn_add_graf_actores"):
                        rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                        st.session_state['cuaderno_items'][f'graf_actores_pop-{rango_actual}'] = {
                            'tipo': 'grafico',
                            'titulo': f'Top 5 Actores por Popularidad ({tipo_bd})',
                            'figura': fig_actores,
                            'contenido': "Grafico exportado de Top Actores",
                            'rango_anios': rango_actual
                        }
                        st.toast("Grafico agregado al reporte")
                        
                    st.markdown("##### Evolucion Temporal")
                    talentos_top_act = top_actores.index.tolist()
                    fig_line_act, df_temp_act = crear_grafico_temporal_popularidad(df_actual, 'cast', talentos_top_act)
                    
                    if fig_line_act is not None and not df_temp_act.empty:
                        st.plotly_chart(fig_line_act, use_container_width=True, key="line_pop_actores")
                        
                        if st.button("Agregar Grafico (Lineas) Actores al Informe", key="btn_add_line_actores_pop"):
                            rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                            st.session_state['cuaderno_items'][f'line_actores_pop-{rango_actual}'] = {
                                'tipo': 'grafico',
                                'titulo': f'Evolucion Popularidad: Actores ({tipo_bd})',
                                'figura': fig_line_act,
                                'contenido': "Evolucion promedio de popularidad por año para los top actores.",
                                'rango_anios': rango_actual
                            }
                            st.toast("Grafico agregado al informe")
                    
                    if st.toggle("Mostrar tablas de datos (Actores)", key="tgl_tablas_actores_pop"):
                        st.write("**Top Popularidad**")
                        df_actores_limpio = top_actores.drop(columns=['porcentaje_total'])
                        st.dataframe(df_actores_limpio, use_container_width=True)
                        if st.button("Agregar Tabla Totales al Informe", key="btn_add_tabla_actores"):
                             rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                             st.session_state['cuaderno_items'][f'tabla_actores_pop-{rango_actual}'] = {
                                'tipo': 'tabla',
                                'titulo': f'Datos Top 5 Actores por Popularidad ({tipo_bd})',
                                'contenido': df_actores_limpio,
                                'rango_anios': rango_actual
                            }
                             st.toast("Tabla agregada al reporte")
                             
                        if not df_temp_act.empty:
                            st.write("**Promedios Anuales**")
                            df_pivot_act = df_temp_act.pivot(index='Año', columns='cast', values='Promedio de Popularidad').reset_index().round(1).fillna(0)
                            st.dataframe(df_pivot_act, use_container_width=True)
                            if st.button("Agregar Tabla Temporal al Informe", key="btn_add_tabla_temp_act_pop"):
                                rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                                st.session_state['cuaderno_items'][f'tabla_temp_act_pop-{rango_actual}'] = {
                                    'tipo': 'tabla',
                                    'titulo': f'Historico Promedio Popularidad Actores ({tipo_bd})',
                                    'contenido': df_pivot_act,
                                    'rango_anios': rango_actual
                                }
                                st.toast("Tabla agregada al reporte")
                else:
                    st.info("Sin resultados de Actores para los filtros seleccionados.")
            else:
                st.error("No existe la columna 'cast'.")

        with st.expander("2. Analisis de Popularidad: Directores", expanded=False):
            if 'director' in df_actual.columns:
                top_directores = top_por_popularidad_por_idioma(
                    df_actual, 'director', 'language', idiomas_seleccionados, min_apariciones, 5
                )
                if not top_directores.empty:
                    fig_directores = crear_grafico_degrade(
                        top_directores, 'director', 'Popularidad de Directores', paleta_color='Sunset'
                    )
                    event_directores = st.plotly_chart(
                        fig_directores, 
                        use_container_width=True, 
                        on_select="rerun", 
                        selection_mode="points",
                        key="grafico_directores"
                    )
                    
                    if st.button("Agregar Grafico (Barras) Directores al Informe", key="btn_add_graf_directores"):
                        rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                        st.session_state['cuaderno_items'][f'graf_directores_pop-{rango_actual}'] = {
                            'tipo': 'grafico',
                            'titulo': f'Top 5 Directores por Popularidad ({tipo_bd})',
                            'figura': fig_directores,
                            'contenido': "Grafico exportado de Top Directores",
                            'rango_anios': rango_actual
                        }
                        st.toast("Grafico agregado al reporte")
                        
                    st.markdown("##### Evolucion Temporal")
                    talentos_top_dir = top_directores.index.tolist()
                    fig_line_dir, df_temp_dir = crear_grafico_temporal_popularidad(df_actual, 'director', talentos_top_dir)
                    
                    if fig_line_dir is not None and not df_temp_dir.empty:
                        st.plotly_chart(fig_line_dir, use_container_width=True, key="line_pop_directores")
                        
                        if st.button("Agregar Grafico (Lineas) Directores al Informe", key="btn_add_line_dir_pop"):
                            rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                            st.session_state['cuaderno_items'][f'line_dir_pop-{rango_actual}'] = {
                                'tipo': 'grafico',
                                'titulo': f'Evolucion Popularidad: Directores ({tipo_bd})',
                                'figura': fig_line_dir,
                                'contenido': "Evolucion promedio de popularidad por año para los top directores.",
                                'rango_anios': rango_actual
                            }
                            st.toast("Grafico agregado al informe")
                    
                    if st.toggle("Mostrar tablas de datos (Directores)", key="tgl_tablas_directores_pop"):
                        st.write("**Top Popularidad**")
                        df_directores_limpio = top_directores.drop(columns=['porcentaje_total'])
                        st.dataframe(df_directores_limpio, use_container_width=True)
                        if st.button("Agregar Tabla Totales al Informe", key="btn_add_tabla_directores"):
                             rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                             st.session_state['cuaderno_items'][f'tabla_directores_pop-{rango_actual}'] = {
                                'tipo': 'tabla',
                                'titulo': f'Datos Top 5 Directores por Popularidad ({tipo_bd})',
                                'contenido': df_directores_limpio,
                                'rango_anios': rango_actual
                            }
                             st.toast("Tabla agregada al reporte")
                             
                        if not df_temp_dir.empty:
                            st.write("**Promedios Anuales**")
                            df_pivot_dir = df_temp_dir.pivot(index='Año', columns='director', values='Promedio de Popularidad').reset_index().round(1).fillna(0)
                            st.dataframe(df_pivot_dir, use_container_width=True)
                            if st.button("Agregar Tabla Temporal al Informe", key="btn_add_tabla_temp_dir_pop"):
                                rango_actual = f"{st.session_state['filtro_anios'][0]} - {st.session_state['filtro_anios'][1]}" if 'filtro_anios' in st.session_state else "Historico Completo"
                                st.session_state['cuaderno_items'][f'tabla_temp_dir_pop-{rango_actual}'] = {
                                    'tipo': 'tabla',
                                    'titulo': f'Historico Promedio Popularidad Directores ({tipo_bd})',
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

        nuevo_actor = sel_actor if sel_actor != st.session_state.estado_actores else None
        nuevo_director = sel_director if sel_director != st.session_state.estado_directores else None

        st.session_state.estado_actores = sel_actor
        st.session_state.estado_directores = sel_director

        if nuevo_actor:
            popup_detalles(nuevo_actor, df_actual)
        elif nuevo_director:
            popup_detalles(nuevo_director, df_actual)