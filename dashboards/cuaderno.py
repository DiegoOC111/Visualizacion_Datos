import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import os

def limpiar_texto(texto):
    if texto is None:
        return ""
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

def generar_pdf(titulo, elementos_seleccionados, conclusion):
    pdf = FPDF()
    pdf.add_page()
    
    # Titulo principal
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, limpiar_texto(titulo), ln=True, align='C')
    pdf.ln(10)
    
    if not elementos_seleccionados:
        pdf.set_font("Arial", '', 11)
        pdf.cell(190, 8, limpiar_texto("No se seleccionaron datos."), ln=True)
    else:
        for item in elementos_seleccionados:
            # 1. Titulo original del elemento guardado
            pdf.set_font("Arial", 'B', 12)
            pdf.multi_cell(190, 8, limpiar_texto(item['titulo']))
            
            # 2. Periodo de tiempo analizado
            rango_str = item.get('rango_anios', 'Historico Completo')
            pdf.set_font("Arial", 'I', 10)
            pdf.cell(190, 6, limpiar_texto(f"Periodo analizado: {rango_str}"), ln=True)
            pdf.ln(2)
            
            # 3. Texto Antes (Tipo Titulo secundario)
            if item.get('texto_antes'):
                pdf.set_font("Arial", 'B', 11)
                pdf.multi_cell(190, 6, limpiar_texto(item['texto_antes']))
                pdf.ln(2)
            
            # 4. Renderizado del contenido real (Tabla, KPI, Grafico)
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
                    # Crear archivo temporal
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                        temp_filename = tmpfile.name
                    
                    # Exportar imagen con dimensiones fijas para evitar errores de memoria en la nube
                    item['figura'].write_image(temp_filename, format='png', width=800, height=450)
                    
                    # Verificar que el archivo realmente tenga peso antes de incrustarlo
                    if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
                        pdf.image(temp_filename, w=180)
                        pdf.ln(2)
                    else:
                        pdf.set_font("Arial", 'I', 9)
                        pdf.multi_cell(190, 6, limpiar_texto("(No se pudo generar la imagen del grafico en el servidor)."))
                        
                except Exception as e:
                    pdf.set_font("Arial", 'I', 9)
                    pdf.multi_cell(190, 6, limpiar_texto(f"(Error al renderizar grafico en el servidor: {str(e)})"))
                finally:
                    if temp_filename and os.path.exists(temp_filename):
                        os.remove(temp_filename)
                
                # Agregar el texto descriptivo si existe
                contenido_desc = item.get('contenido')
                if isinstance(contenido_desc, str):
                    pdf.set_font("Arial", 'I', 9)
                    pdf.multi_cell(190, 6, limpiar_texto(f"Detalle: {contenido_desc}"))
                elif isinstance(contenido_desc, list):
                    pdf.set_font("Arial", 'I', 9)
                    for linea in contenido_desc:
                        pdf.multi_cell(190, 6, limpiar_texto(f"Detalle: {linea}"))
                    
            pdf.ln(3)
            
            # 5. Texto Despues (Tipo Normal explicativo)
            if item.get('texto_despues'):
                pdf.set_font("Arial", '', 11)
                pdf.multi_cell(190, 6, limpiar_texto(item['texto_despues']))
                
            pdf.ln(8)
            
    # Conclusion Final
    if conclusion:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, limpiar_texto("Interpretacion / Conclusion Final:"), ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(190, 8, limpiar_texto(conclusion))
        
    # Manejo compatible tanto para fpdf antiguo como para fpdf2
    try:
        salida = pdf.output()
        if isinstance(salida, str):
            return salida.encode('latin-1')
        return bytes(salida)
    except TypeError:
        salida = pdf.output(dest='S')
        if isinstance(salida, str):
            return salida.encode('latin-1')
        return bytes(salida)


def mostrar():
    st.title("Constructor de Informe Final")
    
    if 'cuaderno_items' not in st.session_state or len(st.session_state['cuaderno_items']) == 0:
        st.info("Tu cuaderno esta vacio. Navega por los reportes en la barra lateral y agrega graficos, KPIs o tablas.")
        return

    # Sincronizacion del orden
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
        st.subheader("1. Configuracion")
        titulo_reporte = st.text_input("Titulo del Informe", value="Reporte Ejecutivo")
        
        st.markdown("**Orden y Personalizacion:**")
        
        orden_actual = st.session_state['orden_cuaderno']
        elementos_finales = []
        
        for i, key in enumerate(orden_actual):
            item = st.session_state['cuaderno_items'][key]
            rango_item = item.get('rango_anios', 'Historico')
            
            with st.expander(f"{item['titulo']} ({rango_item})", expanded=False):
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
                        st.session_state.pop('pdf_generado', None)
                        st.rerun()
                        
                with c_down:
                    if st.button("Bajar", key=f"down_{key}", disabled=(i == len(orden_actual)-1), use_container_width=True):
                        orden_actual[i], orden_actual[i+1] = orden_actual[i+1], orden_actual[i]
                        st.session_state.pop('pdf_generado', None)
                        st.rerun()
                        
                with c_del:
                    if st.button("Quitar", key=f"del_{key}", type="primary", use_container_width=True):
                        del st.session_state['cuaderno_items'][key]
                        orden_actual.remove(key)
                        st.session_state.pop('pdf_generado', None)
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
            st.session_state.pop('pdf_generado', None)
            st.rerun()

        st.markdown("### 2. Analisis Final")
        conclusion = st.text_area("Redacta tu conclusion general para el final del documento:", height=150)
        
        st.markdown("---")
        st.markdown("### 3. Exportar")
        
        if len(elementos_finales) > 0:
            # Boton 1: Construye el PDF bajo demanda y lo guarda en memoria
            if st.button("1. Preparar Documento PDF", use_container_width=True):
                with st.spinner("Renderizando graficos y compilando PDF..."):
                    st.session_state['pdf_generado'] = generar_pdf(titulo_reporte, elementos_finales, conclusion)
                st.success("Documento listo para descargar.")
            
            # Boton 2: Aparece solo cuando los bytes del PDF ya existen y son validos
            if 'pdf_generado' in st.session_state and st.session_state['pdf_generado']:
                st.download_button(
                    label="2. Descargar Informe en PDF",
                    data=st.session_state['pdf_generado'],
                    file_name="informe_analisis.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
        else:
            st.warning("Selecciona al menos un elemento para habilitar la exportacion.")

    with col_preview:
        st.subheader("Vista Previa del Informe")
        st.markdown(f"<h2 style='text-align: center;'>{titulo_reporte}</h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        for item in elementos_finales:
            st.markdown(f"#### {item['titulo']}")
            
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
                st.plotly_chart(item['figura'], use_container_width=True)
            
            if item.get('texto_despues'):
                st.write(item['texto_despues'])
                
            st.write("")
            st.markdown("---")
            
        if conclusion:
            st.markdown("#### Conclusion Final")
            st.write(conclusion)