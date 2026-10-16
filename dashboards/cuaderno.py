import os
import re
import tempfile
import unicodedata

import pandas as pd
import streamlit as st
from fpdf import FPDF


def limpiar_texto(texto):
    """
    Convierte el contenido a texto compatible con las fuentes integradas
    de FPDF y divide cadenas largas sin espacios para facilitar el ajuste.
    """
    texto = str(texto)
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("latin-1", "replace").decode("latin-1")

    # Añade espacios en cadenas largas sin espacios (p. ej., URL o IDs).
    texto = re.sub(r"(\S{40})(?=\S)", r"\1 ", texto)
    return texto


def escribir_parrafo(pdf, texto, alto=6):
    """
    Escribe un párrafo usando el ancho útil de la página y restableciendo
    el cursor al margen izquierdo antes de llamar a multi_cell().
    """
    texto = limpiar_texto(texto)
    ancho = pdf.w - pdf.l_margin - pdf.r_margin

    # Garantiza un ancho positivo y evita heredar una posición horizontal
    # que deje demasiado poco espacio disponible.
    if ancho <= 0:
        raise ValueError("El ancho imprimible del PDF no es válido.")

    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(ancho, alto, texto)


def asegurar_espacio_vertical(pdf, alto_necesario=20):
    """Añade una página si queda poco espacio vertical."""
    if pdf.get_y() + alto_necesario > pdf.h - pdf.b_margin:
        pdf.add_page()


def generar_pdf(titulo, elementos_seleccionados, conclusion):
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(10, 10, 10)
    pdf.add_page()

    # Título principal
    pdf.set_font("Arial", "B", 16)
    escribir_parrafo(pdf, titulo, alto=10)
    pdf.ln(6)

    if not elementos_seleccionados:
        pdf.set_font("Arial", "", 11)
        escribir_parrafo(pdf, "No se seleccionaron datos.", alto=8)
    else:
        for item in elementos_seleccionados:
            asegurar_espacio_vertical(pdf, 25)

            # 1. Título del elemento
            pdf.set_font("Arial", "B", 12)
            escribir_parrafo(pdf, item.get("titulo", "Elemento sin título"), alto=8)

            # 2. Periodo analizado
            rango_str = item.get("rango_anios", "Histórico completo")
            pdf.set_font("Arial", "I", 10)
            escribir_parrafo(pdf, f"Periodo analizado: {rango_str}", alto=6)
            pdf.ln(2)

            # 3. Texto anterior
            texto_antes = item.get("texto_antes", "")
            if texto_antes:
                pdf.set_font("Arial", "B", 11)
                escribir_parrafo(pdf, texto_antes, alto=6)
                pdf.ln(2)

            # 4. Contenido: texto, KPI, tabla o gráfico
            tipo = item.get("tipo")
            contenido = item.get("contenido")

            pdf.set_font("Arial", "", 10)

            if tipo == "texto":
                if isinstance(contenido, (list, tuple)):
                    for linea in contenido:
                        escribir_parrafo(pdf, f"- {linea}", alto=6)
                elif contenido is not None:
                    escribir_parrafo(pdf, contenido, alto=6)

            elif tipo == "kpi":
                if isinstance(contenido, dict):
                    for metrica, valor in contenido.items():
                        escribir_parrafo(pdf, f"{metrica}: {valor}", alto=6)
                elif isinstance(contenido, (list, tuple)):
                    for linea in contenido:
                        escribir_parrafo(pdf, f"- {linea}", alto=6)
                elif contenido is not None:
                    escribir_parrafo(pdf, contenido, alto=6)

            elif tipo == "tabla":
                if isinstance(contenido, pd.DataFrame):
                    df = contenido
                    num_cols = len(df.columns)

                    if num_cols > 0:
                        ancho_util = pdf.w - pdf.l_margin - pdf.r_margin
                        col_width = ancho_util / num_cols

                        pdf.set_font("Arial", "B", 8)
                        for col in df.columns:
                            pdf.cell(
                                col_width,
                                8,
                                limpiar_texto(str(col))[:35],
                                border=1,
                            )
                        pdf.ln()

                        pdf.set_font("Arial", "", 8)
                        for _, row in df.iterrows():
                            asegurar_espacio_vertical(pdf, 10)
                            for col in df.columns:
                                texto_celda = limpiar_texto(str(row[col]))
                                # Conserva el límite para evitar celdas
                                # excesivamente largas.
                                pdf.cell(
                                    col_width,
                                    8,
                                    texto_celda[:35],
                                    border=1,
                                )
                            pdf.ln()
                else:
                    escribir_parrafo(
                        pdf,
                        "No se pudo generar la tabla porque el contenido no es un DataFrame.",
                        alto=6,
                    )

            elif tipo == "grafico":
                figura = item.get("figura")
                temp_filename = None

                try:
                    if figura is None:
                        raise ValueError("No se encontró la figura del gráfico.")

                    # Plotly necesita un motor compatible, normalmente Kaleido.
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".png"
                    ) as tmpfile:
                        temp_filename = tmpfile.name

                    figura.write_image(temp_filename, format="png")

                    asegurar_espacio_vertical(pdf, 45)
                    ancho_util = pdf.w - pdf.l_margin - pdf.r_margin
                    pdf.set_x(pdf.l_margin)
                    pdf.image(temp_filename, w=ancho_util)
                    pdf.ln(3)

                except Exception as e:
                    pdf.set_font("Arial", "I", 9)
                    escribir_parrafo(
                        pdf,
                        "El gráfico no se pudo renderizar. "
                        "Comprueba que Kaleido esté instalado "
                        "(python -m pip install -U kaleido). "
                        f"Error técnico: {e}",
                        alto=5,
                    )
                finally:
                    if temp_filename and os.path.exists(temp_filename):
                        try:
                            os.remove(temp_filename)
                        except OSError:
                            pass

                # Texto descriptivo del gráfico
                if isinstance(contenido, str) and contenido.strip():
                    pdf.set_font("Arial", "I", 10)
                    escribir_parrafo(pdf, f"Detalle: {contenido}", alto=6)

            elif contenido is not None:
                # Fallback para tipos de contenido no contemplados.
                escribir_parrafo(pdf, contenido, alto=6)

            pdf.ln(3)

            # 5. Texto posterior
            texto_despues = item.get("texto_despues", "")
            if texto_despues:
                pdf.set_font("Arial", "", 11)
                escribir_parrafo(pdf, texto_despues, alto=6)

            pdf.ln(8)

    # Conclusión final
    if conclusion and str(conclusion).strip():
        asegurar_espacio_vertical(pdf, 25)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        escribir_parrafo(pdf, "Interpretación / Conclusión final:", alto=8)
        pdf.set_font("Arial", "", 11)
        escribir_parrafo(pdf, conclusion, alto=8)

    # Compatible con versiones actuales de fpdf2.
    salida_pdf = pdf.output()
    if isinstance(salida_pdf, bytearray):
        return bytes(salida_pdf)
    if isinstance(salida_pdf, bytes):
        return salida_pdf
    # Compatibilidad con versiones que devuelven una cadena.
    return salida_pdf.encode("latin-1")


def mostrar():
    st.title("Constructor de Informe Final")

    if (
        "cuaderno_items" not in st.session_state
        or len(st.session_state["cuaderno_items"]) == 0
    ):
        st.info(
            "Tu cuaderno está vacío. Navega por los reportes en la barra "
            "lateral y agrega gráficos, KPIs o tablas."
        )
        return

    # Sincronizar el orden de los elementos guardados.
    if "orden_cuaderno" not in st.session_state:
        st.session_state["orden_cuaderno"] = list(
            st.session_state["cuaderno_items"].keys()
        )
    else:
        for key in st.session_state["cuaderno_items"].keys():
            if key not in st.session_state["orden_cuaderno"]:
                st.session_state["orden_cuaderno"].append(key)

        st.session_state["orden_cuaderno"] = [
            key
            for key in st.session_state["orden_cuaderno"]
            if key in st.session_state["cuaderno_items"]
        ]

    st.write(
        "Selecciona, ordena y personaliza los elementos guardados "
        "que deseas incluir en el PDF."
    )

    col_config, col_preview = st.columns([1.2, 1.5])

    with col_config:
        st.subheader("1. Configuración")
        titulo_reporte = st.text_input(
            "Título del informe", value="Reporte Ejecutivo"
        )

        st.markdown("**Orden y personalización:**")

        orden_actual = st.session_state["orden_cuaderno"]
        elementos_finales = []

        for i, key in enumerate(orden_actual):
            item = st.session_state["cuaderno_items"][key]

            with st.expander(item.get("titulo", "Elemento sin título"), expanded=False):
                c_check, c_up, c_down, c_del = st.columns([4, 1.5, 1.5, 1.5])

                with c_check:
                    incluido = item.get("incluido", True)
                    estado_actual = st.checkbox(
                        "Incluir", value=incluido, key=f"chk_{key}"
                    )
                    st.session_state["cuaderno_items"][key]["incluido"] = (
                        estado_actual
                    )

                    if estado_actual:
                        elementos_finales.append(
                            st.session_state["cuaderno_items"][key]
                        )

                with c_up:
                    if st.button(
                        "Subir",
                        key=f"up_{key}",
                        disabled=(i == 0),
                        use_container_width=True,
                    ):
                        orden_actual[i], orden_actual[i - 1] = (
                            orden_actual[i - 1],
                            orden_actual[i],
                        )
                        st.rerun()

                with c_down:
                    if st.button(
                        "Bajar",
                        key=f"down_{key}",
                        disabled=(i == len(orden_actual) - 1),
                        use_container_width=True,
                    ):
                        orden_actual[i], orden_actual[i + 1] = (
                            orden_actual[i + 1],
                            orden_actual[i],
                        )
                        st.rerun()

                with c_del:
                    if st.button(
                        "Quitar",
                        key=f"del_{key}",
                        type="primary",
                        use_container_width=True,
                    ):
                        del st.session_state["cuaderno_items"][key]
                        orden_actual.remove(key)
                        st.rerun()

                st.markdown("---")

                texto_antes = st.text_input(
                    "Texto antes (será un subtítulo en negrita):",
                    value=item.get("texto_antes", ""),
                    key=f"ant_{key}",
                )
                st.session_state["cuaderno_items"][key]["texto_antes"] = texto_antes

                texto_despues = st.text_area(
                    "Texto después (párrafo descriptivo/análisis):",
                    value=item.get("texto_despues", ""),
                    key=f"desp_{key}",
                )
                st.session_state["cuaderno_items"][key]["texto_despues"] = (
                    texto_despues
                )

        st.write("")

        if st.button("Limpiar cuaderno (borrar todo)"):
            st.session_state["cuaderno_items"] = {}
            st.session_state["orden_cuaderno"] = []
            st.rerun()

        st.markdown("### 2. Análisis final")
        conclusion = st.text_area(
            "Redacta tu conclusión general para el final del documento:",
            height=150,
        )

        st.markdown("---")
        st.markdown("### 3. Exportar")

        if elementos_finales:
            try:
                with st.spinner(
                    "Generando PDF (esto puede tomar unos segundos por las imágenes)..."
                ):
                    pdf_bytes = generar_pdf(
                        titulo_reporte, elementos_finales, conclusion
                    )

                st.download_button(
                    label="Descargar informe en PDF",
                    data=pdf_bytes,
                    file_name="informe_analisis.pdf",
                    mime="application/pdf",
                    type="primary",
                )
            except Exception as e:
                st.error(f"No se pudo generar el PDF: {e}")
        else:
            st.warning(
                "Selecciona al menos un elemento para habilitar la descarga."
            )

    with col_preview:
        st.subheader("Vista previa del informe")
        st.markdown(
            f"<h2 style='text-align: center;'>{titulo_reporte}</h2>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        for item in elementos_finales:
            st.markdown(f"#### {item.get('titulo', 'Elemento sin título')}")

            rango_str = item.get("rango_anios", "Histórico completo")
            st.caption(f"**Periodo analizado:** {rango_str}")

            if item.get("texto_antes"):
                st.markdown(f"**{item['texto_antes']}**")

            tipo = item.get("tipo")
            contenido = item.get("contenido")

            if tipo == "texto":
                if isinstance(contenido, (list, tuple)):
                    for linea in contenido:
                        st.write(f"- {linea}")
                elif contenido is not None:
                    st.write(contenido)

            elif tipo == "kpi":
                if isinstance(contenido, dict):
                    kpis = contenido
                    if kpis:
                        columnas_metricas = st.columns(len(kpis))
                        for idx, (nombre_metrica, valor_metrica) in enumerate(
                            kpis.items()
                        ):
                            columnas_metricas[idx].metric(
                                label=nombre_metrica, value=valor_metrica
                            )
                elif isinstance(contenido, (list, tuple)):
                    for linea in contenido:
                        st.write(f"- {linea}")
                elif contenido is not None:
                    st.write(contenido)

            elif tipo == "tabla":
                if isinstance(contenido, pd.DataFrame):
                    st.dataframe(contenido, use_container_width=True)
                else:
                    st.warning("El contenido de la tabla no es un DataFrame.")

            elif tipo == "grafico":
                figura = item.get("figura")
                if figura is not None:
                    st.plotly_chart(figura, use_container_width=True)
                if isinstance(contenido, str) and contenido.strip():
                    st.caption(contenido)

            if item.get("texto_despues"):
                st.write(item["texto_despues"])

            st.write("")
            st.markdown("---")

        if conclusion:
            st.markdown("#### Conclusión final")
            st.write(conclusion)
