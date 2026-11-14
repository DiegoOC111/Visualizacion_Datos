import streamlit as st
import pandas as pd

def generar_informe_html(titulo, elementos_seleccionados, conclusion):
    # Cabecera HTML y estilos CSS integrados para un diseño limpio y formal
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <title>{titulo}</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 900px; margin: auto; padding: 40px; color: #333; }}
            h1 {{ text-align: center; color: #2c3e50; font-size: 28px; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #2980b9; margin-top: 30px; font-size: 20px; }}
            h3 {{ color: #34495e; font-size: 16px; margin-bottom: 5px; }}
            p {{ line-height: 1.6; font-size: 15px; }}
            .rango {{ font-style: italic; color: #7f8c8d; font-size: 14px; margin-top: -15px; margin-bottom: 15px; display: block; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 14px; }}
            th, td {{ border: 1px solid #bdc3c7; padding: 10px; text-align: left; }}
            th {{ background-color: #ecf0f1; color: #2c3e50; }}
            .grafico-container {{ margin: 25px 0; border: 1px solid #ecf0f1; border-radius: 5px; padding: 10px; }}
            .conclusion-box {{ background-color: #f8f9fa; border-left: 4px solid #27ae60; padding: 15px; margin-top: 30px; }}
            hr {{ border: 0; border-top: 1px solid #ecf0f1; margin: 30px 0; }}
        </style>
    </head>
    <body>
        <h1>{titulo}</h1>
    """
    
    if not elementos_seleccionados:
        html += "<p>No se seleccionaron datos para este informe.</p>"
    else:
        for item in elementos_seleccionados:
            html += f"<h2>{item.get('titulo', 'Sin titulo')}</h2>"
            rango = item.get('rango_anios', 'Historico Completo')
            html += f"<span class='rango'>Periodo analizado: {rango}</span>"
            
            if item.get('texto_antes'):
                html += f"<p><strong>{item['texto_antes']}</strong></p>"
                
            # Procesar Listas de Texto
            if item['tipo'] == 'texto':
                html += "<ul>"
                for linea in item['contenido']:
                    html += f"<li>{linea}</li>"
                html += "</ul>"
                
            # Procesar KPIs
            elif item['tipo'] == 'kpi':
                html += "<ul>"
                if isinstance(item['contenido'], dict):
                    for m, v in item['contenido'].items():
                        html += f"<li><strong>{m}:</strong> {v}</li>"
                elif isinstance(item['contenido'], list):
                    for linea in item['contenido']:
                        html += f"<li>{linea}</li>"
                html += "</ul>"
                
            # Procesar Tablas de Pandas
            elif item['tipo'] == 'tabla':
                df = item['contenido']
                # Convierte el DataFrame a tabla HTML nativa
                html += df.to_html(index=False, classes="table", border=0, justify="left")
                
            # Procesar Gráficos de Plotly de forma nativa (CERO dependencias)
            elif item['tipo'] == 'grafico':
                if 'figura' in item and item['figura'] is not None:
                    # include_plotlyjs='cdn' inserta la librería web para que el gráfico sea interactivo offline
                    fig_html = item['figura'].to_html(full_html=False, include_plotlyjs='cdn')
                    html += f"<div class='grafico-container'>{fig_html}</div>"
                    
                contenido_desc = item.get('contenido')
                if isinstance(contenido_desc, str):
                    html += f"<p><i>Detalle: {contenido_desc}</i></p>"
                elif isinstance(contenido_desc, list):
                    html += "<ul>"
                    for linea in contenido_desc:
                        html += f"<li><i>Detalle: {linea}</i></li>"
                    html += "</ul>"
                    
            if item.get('texto_despues'):
                html += f"<p>{item['texto_despues']}</p>"
                
            html += "<hr>"
            
    if conclusion:
        html += "<div class='conclusion-box'>"
        html += "<h2>Interpretación / Conclusión Final</h2>"
        html += f"<p>{conclusion}</p>"
        html += "</div>"
        
    html += "</body></html>"
    
    return html.encode('utf-8')

def mostrar():
    st.title("Constructor de Informe Final")
    
    if 'cuaderno_items' not in st.session_state or len(st.session_state['cuaderno_items']) == 0:
        st.info("Tu cuaderno está vacío. Navega por los reportes en la barra lateral y agrega gráficos, KPIs o tablas.")
        return

    if 'orden_cuaderno' not in st.session_state:
        st.session_state['orden_cuaderno'] = list(st.session_state['cuaderno_items'].keys())
    else:
        for k in st.session_state['cuaderno_items'].keys():
            if k not in st.session_state['orden_cuaderno']:
                st.session_state['orden_cuaderno'].append(k)
        st.session_state['orden_cuaderno'] = [k for k in st.session_state['orden_cuaderno'] if k in st.session_state['cuaderno_items']]

    st.write("Selecciona, ordena y personaliza los elementos guardados que deseas incluir en tu informe interactivo.")
    
    col_config, col_preview = st.columns([1.2, 1.5])
    
    with col_config:
        st.subheader("Configuración")
        titulo_reporte = st.text_input("Título del Informe", value="Reporte Ejecutivo Analítico")
        
        st.markdown("**Orden y Personalización:**")
        
        orden_actual = st.session_state['orden_cuaderno']
        elementos_finales = []
        
        for i, key in enumerate(orden_actual):
            item = st.session_state['cuaderno_items'][key]
            rango_item = item.get('rango_anios', 'Histórico')
            
            with st.expander(f"{item.get('titulo', 'Sin Título')} ({rango_item})", expanded=False):
                c_check, c_up, c_down, c_del = st.columns([4, 1.5, 1.5, 1.5])
                with c_check:
                    incluido = item.get('incluido', True)
                    estado_actual = st.checkbox("Incluir", value=incluido, key=f"chk_{key}")
                    st.session_state['cuaderno_items'][key]['incluido'] = estado_actual
                    if estado_actual:
                        elementos_finales.append(item)
                        
                with c_up:
                    if st.button("Subir", key=f"up_{key}", disabled=(i == 0), use_container_width=True):
                        orden_actual[i], orden_actual[i-1] = orden_actual[i-1], orden_actual[i]
                        st.session_state.pop('html_bytes_listo', None)
                        st.rerun()
                        
                with c_down:
                    if st.button("Bajar", key=f"down_{key}", disabled=(i == len(orden_actual)-1), use_container_width=True):
                        orden_actual[i], orden_actual[i+1] = orden_actual[i+1], orden_actual[i]
                        st.session_state.pop('html_bytes_listo', None)
                        st.rerun()
                        
                with c_del:
                    if st.button("Quitar", key=f"del_{key}", type="primary", use_container_width=True):
                        del st.session_state['cuaderno_items'][key]
                        orden_actual.remove(key)
                        st.session_state.pop('html_bytes_listo', None)
                        st.rerun()
                
                st.markdown("---")
                texto_antes = st.text_input("Texto Antes (Subtítulo en negrita):", value=item.get('texto_antes', ''), key=f"ant_{key}")
                st.session_state['cuaderno_items'][key]['texto_antes'] = texto_antes
                
                texto_despues = st.text_area("Texto Después (Párrafo descriptivo):", value=item.get('texto_despues', ''), key=f"desp_{key}")
                st.session_state['cuaderno_items'][key]['texto_despues'] = texto_despues
        
        st.write("")
        if st.button("Limpiar Cuaderno (Borrar Todo)"):
            st.session_state['cuaderno_items'] = {}
            st.session_state['orden_cuaderno'] = []
            st.session_state.pop('html_bytes_listo', None)
            st.rerun()

        st.markdown("### 2. Análisis Final")
        conclusion = st.text_area("Redacta tu conclusión general para el final del documento:", height=150)
        
        st.markdown("---")
        st.markdown("### 3. Exportar Informe")
        
        if len(elementos_finales) > 0:
            if st.button("Generar Informe Web", use_container_width=True, type="secondary"):
                with st.spinner("Compilando código web y gráficos nativos..."):
                    html_bytes = generar_informe_html(titulo_reporte, elementos_finales, conclusion)
                    st.session_state['html_bytes_listo'] = html_bytes
                        
            if 'html_bytes_listo' in st.session_state and st.session_state['html_bytes_listo'] is not None:
                st.success("Documento preparado exitosamente.")
                
                st.download_button(
                    label="Descargar Informe Interactivo (HTML)",
                    data=st.session_state['html_bytes_listo'],
                    file_name="informe_analisis_interactivo.html",
                    mime="text/html",
                    type="primary",
                    use_container_width=True
                )
        else:
            st.warning("Selecciona al menos un elemento para habilitar la exportación.")
            st.session_state.pop('html_bytes_listo', None)

    with col_preview:
        st.subheader("Vista Previa del Informe")
        st.markdown(f"<h2 style='text-align: center;'>{titulo_reporte}</h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        for item in elementos_finales:
            st.markdown(f"#### {item.get('titulo', 'Sin Título')}")
            
            rango_str = item.get('rango_anios', 'Histórico Completo')
            st.caption(f"**Periodo analizado:** {rango_str}")
            
            if item.get('texto_antes'):
                st.markdown(f"**{item['texto_antes']}**")
                
            if item['tipo'] == 'texto':
                for linea in item['contenido']:
                    st.write(f"- {linea}")
                    
            elif item['tipo'] == 'kpi':
                if isinstance(item['contenido'], dict):
                    kpis = item['contenido']
                    columnas_metricas = st.columns(len(kpis))
                    for idx, (nombre_metrica, valor_metrica) in enumerate(kpis.items()):
                        columnas_metricas[idx].metric(label=nombre_metrica, value=valor_metrica)
                elif isinstance(item['contenido'], list):
                    for linea in item['contenido']:
                        st.write(f"- {linea}")
                    
            elif item['tipo'] == 'tabla':
                st.dataframe(item['contenido'], use_container_width=True)
                
            elif item['tipo'] == 'grafico':
                if 'figura' in item and item['figura'] is not None:
                    st.plotly_chart(item['figura'], use_container_width=True)
                else:
                    st.warning("El gráfico guardado está corrupto o no se encontró la figura.")
            
            if item.get('texto_despues'):
                st.write(item['texto_despues'])
                
            st.write("")
            st.markdown("---")
            
        if conclusion:
            st.markdown("#### Conclusión Final")
            st.write(conclusion)