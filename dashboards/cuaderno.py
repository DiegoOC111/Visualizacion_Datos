import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import os
import gc
import subprocess

# --- INSTALACIÓN AUTOMÁTICA DE CHROME EN EL SERVIDOR ---
@st.cache_resource
def preparar_motor_grafico():
    """Ejecuta el comando de terminal que exige Kaleido para descargar Chrome en la nube"""
    try:
        subprocess.run(["plotly_get_chrome"], capture_output=True)
    except:
        pass

preparar_motor_grafico()
# -------------------------------------------------------

def limpiar_texto(texto):
    if texto is None:
        return ""
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

def generar_pdf(titulo, elementos_seleccionados, conclusion):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, limpiar_texto(titulo), ln=True, align='C')
    pdf.ln(10)
    
    if not elementos_seleccionados:
        pdf.set_font("Arial", '', 11)
        pdf.cell(190, 8, limpiar_texto("No se seleccionaron datos."), ln=True)
    else:
        for item in elementos_seleccionados:
            pdf.set_font("Arial", 'B', 12)
            pdf.multi_cell(190, 8, limpiar_texto(item.get('titulo', 'Sin titulo')))
            
            rango_str = item.get('rango_anios', 'Historico Completo')
            pdf.set_font("Arial", 'I', 10)
            pdf.cell(190, 6, limpiar_texto(f"Periodo analizado: {rango_str}"), ln=True)
            pdf.ln(2)
            
            if item.get('texto_antes'):
                pdf.set_font("Arial", 'B', 11)
                pdf.multi_cell(190, 6, limpiar_texto(item['texto_antes']))
                pdf.ln(2)
            
            pdf.set_font("Arial", '', 10)
            if item['tipo'] == 'texto':
                for linea in item['contenido']:
                    pdf.multi_cell(190, 6, limpiar_texto(f"- {linea}"))
                    
            elif item['tipo'] == 'kpi':
                if isinstance(item['contenido'], dict):
                    for metrica, valor in item['contenido'].items():
                        pdf.multi_cell(190, 6, limpiar_texto(f"{metrica}: {valor}"))
                elif isinstance(item['contenido'], list):
                    for linea in item['contenido']:
                        pdf.multi_cell(190, 6, limpiar_texto(f"- {linea}"))
                    
            elif item['tipo'] == 'tabla':
                df = item['contenido']
                num_cols = len(df.columns)
                col_width = 190 / num_cols if num_cols > 0 else 40
                
                pdf.set_font("Arial", 'B', 8)
                for col in df.columns:
                    pdf.cell(col_width, 8, limpiar_texto(str(col)[:20]), border=1)
                pdf.ln()
                
                pdf.set_font("Arial", '', 8)
                for _, row in df.iterrows():
                    for col in df.columns:
                        texto_celda = str(row[col])[:22] 
                        pdf.cell(col_width, 8, limpiar_texto(texto_celda), border=1)
                    pdf.ln()
                    
            elif item['tipo'] == 'grafico':
                temp_filename = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                        temp_filename = tmpfile.name
                    
                    item['figura'].write_image(temp_filename, format='png', width=800, height=450)
                    
                    if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
                        pdf.image(temp_filename, w=180)
                        pdf.ln(2)
                    else:
                        pdf.set_font("Arial", 'I', 9)
                        pdf.multi_cell(190, 6, limpiar_texto("(No se pudo generar la imagen del grafico en el servidor)."))
                        
                except Exception as e:
                    pdf.set_font("Arial", 'I', 9)
                    pdf.multi_cell(190, 6, limpiar_texto(f"(Error al renderizar grafico en el servidor: {str(e)[:100]})"))
                finally:
                    if temp_filename and os.path.exists(temp_filename):
                        try:
                            os.remove(temp_filename)
                        except:
                            pass
                
                contenido_desc = item.get('contenido')
                if isinstance(contenido_desc, str):
                    pdf.set_font("Arial", 'I', 9)
                    pdf.multi_cell(190, 6, limpiar_texto(f"Detalle: {contenido_desc}"))
                elif isinstance(contenido_desc, list):
                    pdf.set_font("Arial", 'I', 9)
                    for linea in contenido_desc:
                        pdf.multi_cell(190, 6, limpiar_texto(f"Detalle: {linea}"))
                    
            pdf.ln(3)
            
            if item.get('texto_despues'):
                pdf.set_font("Arial", '', 11)
                pdf.multi_cell(190, 6, limpiar_texto(item['texto_despues']))
                
            pdf.ln(8)
            
    if conclusion:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, limpiar_texto("Interpretacion / Conclusion Final:"), ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(190, 8, limpiar_texto(conclusion))
        
    temp_pdf_path = os.path.join(tempfile.gettempdir(), "informe_temporal_app.pdf")
    
    try:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            
        pdf.output(temp_pdf_path)
        return temp_pdf_path
        
    except Exception as e:
        raise Exception(f"Fallo al escribir el PDF temporal: {str(e)}")

def mostrar():
    st.title("Constructor de Informe Final")
    
    if 'cuaderno_items' not in st.session_state or len(st.session_state['cuaderno_items']) == 0:
        st.info("Tu cuaderno esta vacio. Navega por los reportes en la barra lateral y agrega graficos, KPIs o tablas.")
        return

    if 'orden_cuaderno' not in st.session_state:
        st.session_state['orden_cuaderno'] = list(st.session_state['cuaderno_items'].keys())
    else:
        for k in st.session_state['cuaderno_items'].keys():
            if k not in st.session_state['orden_cuaderno']:
                st.session_state['orden_cuaderno'].append(k)
        st.session_state['orden_cuaderno'] = [k for k in st.session_state['orden_cuaderno'] if k in st.session_state['cuaderno_items']]

    st.write("Selecciona, ordena y personaliza los elementos guardados que deseas incluir en el PDF.")
    
    col_config, col_preview = st.columns([1.2, 1.5])
    
    with col_config:
        st.subheader("Configuracion")
        titulo_reporte = st.text_input("Titulo del Informe", value="Reporte Ejecutivo")
        
        st.markdown("**Orden y Personalizacion:**")
        
        orden_actual = st.session_state['orden_cuaderno']
        elementos_finales = []
        
        for i, key in enumerate(orden_actual):
            item = st.session_state['cuaderno_items'][key]
            rango_item = item.get('rango_anios', 'Historico')
            
            with st.expander(f"{item.get('titulo', 'Sin Titulo')} ({rango_item})", expanded=False):
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
                        st.session_state.pop('ruta_pdf_listo', None)
                        st.rerun()
                        
                with c_down:
                    if st.button("Bajar", key=f"down_{key}", disabled=(i == len(orden_actual)-1), use_container_width=True):
                        orden_actual[i], orden_actual[i+1] = orden_actual[i+1], orden_actual[i]
                        st.session_state.pop('ruta_pdf_listo', None)
                        st.rerun()
                        
                with c_del:
                    if st.button("Quitar", key=f"del_{key}", type="primary", use_container_width=True):
                        del st.session_state['cuaderno_items'][key]
                        orden_actual.remove(key)
                        st.session_state.pop('ruta_pdf_listo', None)
                        st.rerun()
                
                st.markdown("---")
                texto_antes = st.text_input("Texto Antes (Subtitulo en negrita):", value=item.get('texto_antes', ''), key=f"ant_{key}")
                st.session_state['cuaderno_items'][key]['texto_antes'] = texto_antes
                
                texto_despues = st.text_area("Texto Despues (Parrafo descriptivo/analisis):", value=item.get('texto_despues', ''), key=f"desp_{key}")
                st.session_state['cuaderno_items'][key]['texto_despues'] = texto_despues
        
        st.write("")
        if st.button("Limpiar Cuaderno (Borrar Todo)"):
            st.session_state['cuaderno_items'] = {}
            st.session_state['orden_cuaderno'] = []
            st.session_state.pop('ruta_pdf_listo', None)
            st.rerun()

        st.markdown("### 2. Analisis Final")
        conclusion = st.text_area("Redacta tu conclusion general para el final del documento:", height=150)
        
        st.markdown("---")
        st.markdown("### 3. Exportar")
        
        if len(elementos_finales) > 0:
            if st.button("Preparar Documento PDF", use_container_width=True, type="secondary"):
                with st.spinner("Compilando graficos y construyendo el PDF... esto toma unos segundos."):
                    try:
                        ruta_pdf = generar_pdf(titulo_reporte, elementos_finales, conclusion)
                        st.session_state['ruta_pdf_listo'] = ruta_pdf
                    except Exception as e:
                        st.error(f"Ocurrio un error al generar el documento: {str(e)}")
                        
            if 'ruta_pdf_listo' in st.session_state and st.session_state['ruta_pdf_listo'] is not None:
                st.success("Documento preparado exitosamente.")
                
                try:
                    with open(st.session_state['ruta_pdf_listo'], "rb") as pdf_file:
                        PDFbyte = pdf_file.read()

                    st.download_button(
                        label="Descargar Informe en PDF",
                        data=PDFbyte,
                        file_name="informe_analisis.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
                except FileNotFoundError:
                    st.error("El archivo temporal expiro. Por favor, vuelve a presionar 'Preparar Documento PDF'.")
                    st.session_state.pop('ruta_pdf_listo', None)
        else:
            st.warning("Selecciona al menos un elemento para habilitar la exportacion.")
            st.session_state.pop('ruta_pdf_listo', None)

    with col_preview:
        st.subheader("Vista Previa del Informe")
        st.markdown(f"<h2 style='text-align: center;'>{titulo_reporte}</h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        for item in elementos_finales:
            st.markdown(f"#### {item.get('titulo', 'Sin Titulo')}")
            
            rango_str = item.get('rango_anios', 'Historico Completo')
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
                    st.warning("El grafico guardado esta corrupto o no se encontro la figura.")
            
            if item.get('texto_despues'):
                st.write(item['texto_despues'])
                
            st.write("")
            st.markdown("---")
            
        if conclusion:
            st.markdown("#### Conclusion Final")
            st.write(conclusion)
            
        gc.collect()