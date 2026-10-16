import streamlit as st
import pandas as pd
from fpdf import FPDF

def limpiar_texto(texto):
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

def generar_pdf(titulo, elementos_seleccionados, conclusion):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, limpiar_texto(titulo), ln=True, align='C')
    pdf.ln(10)
    
    if not elementos_seleccionados:
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 8, limpiar_texto("No se seleccionaron datos."), ln=True)
    else:
        for item in elementos_seleccionados:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, limpiar_texto(item['titulo']), ln=True)
            pdf.set_font("Arial", '', 11)
            
            if item['tipo'] == 'texto':
                for linea in item['contenido']:
                    pdf.cell(0, 6, limpiar_texto(f"- {linea}"), ln=True)
                    
            elif item['tipo'] == 'kpi':
                if isinstance(item['contenido'], dict):
                    for metrica, valor in item['contenido'].items():
                        pdf.cell(0, 6, limpiar_texto(f"{metrica}: {valor}"), ln=True)
                elif isinstance(item['contenido'], list):
                    for linea in item['contenido']:
                        pdf.cell(0, 6, limpiar_texto(f"- {linea}"), ln=True)
                    
            elif item['tipo'] == 'tabla':
                df = item['contenido']
                num_cols = len(df.columns)
                col_width = 190 / num_cols if num_cols > 0 else 40
                
                pdf.set_font("Arial", 'B', 9)
                for col in df.columns:
                    pdf.cell(col_width, 8, limpiar_texto(col), border=1)
                pdf.ln()
                
                pdf.set_font("Arial", '', 9)
                for _, row in df.iterrows():
                    for col in df.columns:
                        texto_celda = str(row[col])[:30] 
                        pdf.cell(col_width, 8, limpiar_texto(texto_celda), border=1)
                    pdf.ln()
                    
            elif item['tipo'] == 'grafico':
                pdf.cell(0, 6, limpiar_texto("(Grafico interactivo adjunto en la version web)"), ln=True)
                if isinstance(item.get('contenido'), str):
                    pdf.cell(0, 6, limpiar_texto(f"Detalle: {item['contenido']}"), ln=True)
            pdf.ln(5)
            
    if conclusion:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, limpiar_texto("Interpretacion / Conclusion:"), ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 8, limpiar_texto(conclusion))
        
    salida_pdf = pdf.output(dest="S")
    if isinstance(salida_pdf, (bytes, bytearray)):
        return bytes(salida_pdf)
    return salida_pdf.encode("latin-1")


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

    st.write("Selecciona y ordena los elementos guardados que deseas incluir.")
    
    col_config, col_preview = st.columns([1.2, 1.5])
    
    with col_config:
        st.subheader("1. Configuracion")
        titulo_reporte = st.text_input("Titulo del Informe", value="Reporte Ejecutivo")
        
        st.markdown("**Orden y Seleccion:**")
        
        orden_actual = st.session_state['orden_cuaderno']
        elementos_finales = []
        
        for i, key in enumerate(orden_actual):
            item = st.session_state['cuaderno_items'][key]
            
            # Usamos un expander para agrupar los controles de forma limpia
            with st.expander(f"{item['titulo']}", expanded=False):
                c_check, c_up, c_down, c_del = st.columns([4, 1.5, 1.5, 1.5])
                
                with c_check:
                    incluido = item.get('incluido', True)
                    estado_actual = st.checkbox("Incluir en reporte", value=incluido, key=f"chk_{key}")
                    st.session_state['cuaderno_items'][key]['incluido'] = estado_actual
                    if estado_actual:
                        elementos_finales.append(item)
                        
                with c_up:
                    if st.button("Subir", key=f"up_{key}", disabled=(i == 0), use_container_width=True):
                        orden_actual[i], orden_actual[i-1] = orden_actual[i-1], orden_actual[i]
                        st.rerun()
                        
                with c_down:
                    if st.button("Bajar", key=f"down_{key}", disabled=(i == len(orden_actual)-1), use_container_width=True):
                        orden_actual[i], orden_actual[i+1] = orden_actual[i+1], orden_actual[i]
                        st.rerun()
                        
                with c_del:
                    if st.button("Quitar", key=f"del_{key}", type="primary", use_container_width=True):
                        del st.session_state['cuaderno_items'][key]
                        orden_actual.remove(key)
                        st.rerun()
        
        st.write("")
        if st.button("Limpiar Cuaderno (Borrar Todo)"):
            st.session_state['cuaderno_items'] = {}
            st.session_state['orden_cuaderno'] = []
            st.rerun()

        st.markdown("### 2. Analisis Final")
        conclusion = st.text_area("Redacta tu conclusion final:", height=150)
        
        st.markdown("---")
        st.markdown("### 3. Exportar")
        pdf_bytes = generar_pdf(titulo_reporte, elementos_finales, conclusion)
        
        st.download_button(
            label="Descargar Datos (PDF)",
            data=pdf_bytes,
            file_name="informe_datos.pdf",
            mime="application/pdf"
        )
        st.caption("Para exportar el reporte con graficos, usa Ctrl+P y Guardar como PDF.")

    with col_preview:
        st.subheader("Vista Previa del Informe")
        st.markdown(f"<h2 style='text-align: center;'>{titulo_reporte}</h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        for item in elementos_finales:
            st.markdown(f"#### {item['titulo']}")
            
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
                
            st.write("")
            
        if conclusion:
            st.markdown("---")
            st.markdown("#### Conclusion")
            st.write(conclusion)