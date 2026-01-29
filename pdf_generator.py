"""
Módulo para generar PDFs de presupuestos y facturas
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from datetime import datetime
from typing import Dict, List, Optional
import os
import json


class PDFGenerator:
    def __init__(self, db=None):
        self.styles = getSampleStyleSheet()
        self.db = db
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados"""
        self.styles.add(ParagraphStyle(
            name='Titulo',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='NormalBold',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold'
        ))
    
    def _agregar_datos_empresa(self, story):
        """Agrega los datos de la empresa al inicio del documento"""
        # Esta función ahora solo prepara los datos, el layout se hace en generar_presupuesto/generar_factura
        pass
    
    def _obtener_datos_empresa(self):
        """Obtiene los datos de la empresa"""
        if self.db:
            return self.db.obtener_datos_empresa()
        return {}
    
    def _safe_float(self, value, default=0.0):
        """Convierte un valor a float de forma segura"""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def generar_presupuesto(self, presupuesto: Dict, output_path: str):
        """Genera un PDF de presupuesto"""
        try:
            # Configurar márgenes más pequeños
            doc = SimpleDocTemplate(output_path, pagesize=A4, 
                                   leftMargin=15*mm, rightMargin=15*mm,
                                   topMargin=15*mm, bottomMargin=15*mm)
            story = []
            
            # Obtener datos de la empresa
            empresa = self._obtener_datos_empresa()
            
            # Crear header con logo, datos empresa y datos cliente
            header_data = []
            
            # Logo (más pequeño - 30mm)
            logo_cell = ''
            logo_path = empresa.get('logo_path', '').strip()
            if logo_path and os.path.exists(logo_path):
                try:
                    from PIL import Image as PILImage
                    pil_img = PILImage.open(logo_path)
                    img_width, img_height = pil_img.size
                    aspect_ratio = img_height / img_width
                    logo_height = 30 * mm * aspect_ratio
                    logo_cell = Image(logo_path, width=30*mm, height=logo_height)
                except Exception as e:
                    print(f"Error al cargar logo: {str(e)}")
            
            # Datos de la empresa (debajo del logo)
            empresa_text = []
            if empresa.get('nombre'):
                empresa_text.append(Paragraph(f"<b>{empresa['nombre']}</b>", self.styles['Normal']))
            if empresa.get('nif'):
                empresa_text.append(Paragraph(f"NIF: {empresa['nif']}", self.styles['Normal']))
            
            direccion_parts = []
            if empresa.get('direccion'):
                direccion_parts.append(empresa['direccion'])
            if empresa.get('codigo_postal'):
                direccion_parts.append(empresa['codigo_postal'])
            if empresa.get('localidad'):
                direccion_parts.append(empresa['localidad'])
            if empresa.get('provincia'):
                direccion_parts.append(empresa['provincia'])
            if direccion_parts:
                empresa_text.append(Paragraph(', '.join(direccion_parts), self.styles['Normal']))
            
            if empresa.get('telefono'):
                empresa_text.append(Paragraph(f"Tel: {empresa['telefono']}", self.styles['Normal']))
            if empresa.get('email'):
                empresa_text.append(Paragraph(f"Email: {empresa['email']}", self.styles['Normal']))
            if empresa.get('web'):
                empresa_text.append(Paragraph(f"Web: {empresa['web']}", self.styles['Normal']))
            
            # Datos del cliente (a la derecha)
            cliente_text = []
            cliente_text.append(Paragraph("<b>CLIENTE:</b>", self.styles['Normal']))
            if presupuesto.get('cliente_nombre'):
                cliente_text.append(Paragraph(presupuesto['cliente_nombre'], self.styles['Normal']))
            if presupuesto.get('nif'):
                cliente_text.append(Paragraph(f"NIF: {presupuesto['nif']}", self.styles['Normal']))
            if presupuesto.get('direccion'):
                cliente_text.append(Paragraph(presupuesto['direccion'], self.styles['Normal']))
            if presupuesto.get('telefono'):
                cliente_text.append(Paragraph(f"Tel: {presupuesto['telefono']}", self.styles['Normal']))
            if presupuesto.get('email'):
                cliente_text.append(Paragraph(f"Email: {presupuesto['email']}", self.styles['Normal']))
            
            # Crear tabla de 3 columnas: logo | datos empresa | datos cliente
            num_filas = max(len(empresa_text), len(cliente_text), 1)
            
            for i in range(num_filas):
                row = []
                if i == 0:
                    row.append(logo_cell if logo_cell else '')
                else:
                    row.append('')
                
                if i < len(empresa_text):
                    row.append(empresa_text[i])
                else:
                    row.append('')
                
                if i < len(cliente_text):
                    row.append(cliente_text[i])
                else:
                    row.append('')
                
                header_data.append(row)
            
            # Aplicar SPAN para que el logo ocupe todas las filas
            header_table = Table(header_data, colWidths=[35*mm, 70*mm, 70*mm])
            header_style = TableStyle([
                ('VALIGN', (0, 0), (0, -1), 'TOP'),
                ('VALIGN', (1, 0), (1, -1), 'TOP'),
                ('VALIGN', (2, 0), (2, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 1),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ])
            if logo_cell:
                header_style.add('SPAN', (0, 0), (0, -1))
            header_table.setStyle(header_style)
            story.append(header_table)
            story.append(Spacer(1, 5*mm))
            
            # Título
            story.append(Paragraph("PRESUPUESTO", self.styles['Titulo']))
            story.append(Spacer(1, 3*mm))
            
            # Información del presupuesto (compacta)
            info_data = [
                ['Número:', presupuesto.get('numero', ''), 'Fecha:', presupuesto.get('fecha', ''), 'Estado:', (presupuesto.get('estado') or '').upper()]
            ]
            info_table = Table(info_data, colWidths=[25*mm, 30*mm, 20*mm, 30*mm, 20*mm, 30*mm])
            info_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
                ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                ('ALIGN', (4, 0), (4, 0), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
                ('FONTNAME', (4, 0), (4, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 3*mm))
            
            # Líneas del presupuesto
            story.append(Paragraph("CONCEPTOS", self.styles['NormalBold']))
            story.append(Spacer(1, 2*mm))
            
            lineas_data = [['Concepto', 'Cant.', 'Precio', 'Dto.%', 'IVA', 'Total']]
            
            total_base = 0.0
            total_iva = 0.0
            ivas_aplicados = {}
            
            for linea in presupuesto.get('lineas', []):
                cantidad = self._safe_float(linea.get('cantidad'), 0.0)
                precio = self._safe_float(linea.get('precio_unitario'), 0.0)
                descuento = self._safe_float(linea.get('descuento'), 0.0)
                iva_porcentaje = self._safe_float(linea.get('iva_porcentaje'), 0.0)
                
                base = cantidad * precio * (1 - descuento / 100)
                iva = base * (iva_porcentaje / 100)
                total_linea = base + iva
                
                total_base += base
                total_iva += iva
                
                if iva_porcentaje not in ivas_aplicados:
                    ivas_aplicados[iva_porcentaje] = 0.0
                ivas_aplicados[iva_porcentaje] += iva
                
                lineas_data.append([
                    linea.get('concepto', ''),
                    f"{cantidad:.2f}",
                    f"{precio:.2f} €",
                    f"{descuento:.1f}%" if descuento > 0 else "-",
                    f"{iva_porcentaje:.1f}%" if iva_porcentaje > 0 else "Sin IVA",
                    f"{total_linea:.2f} €"
                ])
            
            lineas_table = Table(lineas_data, colWidths=[70*mm, 20*mm, 25*mm, 20*mm, 20*mm, 25*mm])
            lineas_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ]))
            story.append(lineas_table)
            story.append(Spacer(1, 10*mm))
            
            # Totales
            total_presupuesto = self._safe_float(presupuesto.get('total'), 0.0)
            
            totales_data = [
                ['Base Imponible:', f"{total_base:.2f} €"],
                ['IVA:', f"{total_iva:.2f} €"],
                ['TOTAL:', f"{total_presupuesto:.2f} €"]
            ]
            totales_table = Table(totales_data, colWidths=[120*mm, 40*mm])
            totales_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -2), 9),
                ('FONTSIZE', (0, 2), (-1, 2), 12),
                ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#4472C4')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (2, 0), (2, -1), 5),
            ]))
            story.append(totales_table)
            
            # Observaciones
            if presupuesto.get('observaciones'):
                story.append(Spacer(1, 3*mm))
                story.append(Paragraph("OBSERVACIONES", self.styles['NormalBold']))
                story.append(Paragraph(presupuesto['observaciones'], self.styles['Normal']))
            
            doc.build(story)
        except Exception as e:
            import traceback
            error_msg = f"Error al generar PDF: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            raise Exception(error_msg)
    
    def generar_factura(self, factura: Dict, output_path: str):
        """Genera un PDF de factura"""
        try:
            # Configurar márgenes más pequeños
            doc = SimpleDocTemplate(output_path, pagesize=A4, 
                                   leftMargin=15*mm, rightMargin=15*mm,
                                   topMargin=15*mm, bottomMargin=15*mm)
            story = []
            
            # Obtener datos de la empresa
            empresa = self._obtener_datos_empresa()
            
            # Crear header con logo, datos empresa y datos cliente
            header_data = []
            
            # Logo (más pequeño - 30mm)
            logo_cell = ''
            logo_path = empresa.get('logo_path', '').strip()
            if logo_path and os.path.exists(logo_path):
                try:
                    from PIL import Image as PILImage
                    pil_img = PILImage.open(logo_path)
                    img_width, img_height = pil_img.size
                    aspect_ratio = img_height / img_width
                    logo_height = 30 * mm * aspect_ratio
                    logo_cell = Image(logo_path, width=30*mm, height=logo_height)
                except Exception as e:
                    print(f"Error al cargar logo: {str(e)}")
            
            # Datos de la empresa (debajo del logo)
            empresa_text = []
            if empresa.get('nombre'):
                empresa_text.append(Paragraph(f"<b>{empresa['nombre']}</b>", self.styles['Normal']))
            if empresa.get('nif'):
                empresa_text.append(Paragraph(f"NIF: {empresa['nif']}", self.styles['Normal']))
            
            direccion_parts = []
            if empresa.get('direccion'):
                direccion_parts.append(empresa['direccion'])
            if empresa.get('codigo_postal'):
                direccion_parts.append(empresa['codigo_postal'])
            if empresa.get('localidad'):
                direccion_parts.append(empresa['localidad'])
            if empresa.get('provincia'):
                direccion_parts.append(empresa['provincia'])
            if direccion_parts:
                empresa_text.append(Paragraph(', '.join(direccion_parts), self.styles['Normal']))
            
            if empresa.get('telefono'):
                empresa_text.append(Paragraph(f"Tel: {empresa['telefono']}", self.styles['Normal']))
            if empresa.get('email'):
                empresa_text.append(Paragraph(f"Email: {empresa['email']}", self.styles['Normal']))
            if empresa.get('web'):
                empresa_text.append(Paragraph(f"Web: {empresa['web']}", self.styles['Normal']))
            
            # Datos del cliente (a la derecha)
            cliente_text = []
            cliente_text.append(Paragraph("<b>CLIENTE:</b>", self.styles['Normal']))
            if factura.get('cliente_nombre'):
                cliente_text.append(Paragraph(factura['cliente_nombre'], self.styles['Normal']))
            if factura.get('nif'):
                cliente_text.append(Paragraph(f"NIF: {factura['nif']}", self.styles['Normal']))
            if factura.get('direccion'):
                cliente_text.append(Paragraph(factura['direccion'], self.styles['Normal']))
            if factura.get('telefono'):
                cliente_text.append(Paragraph(f"Tel: {factura['telefono']}", self.styles['Normal']))
            if factura.get('email'):
                cliente_text.append(Paragraph(f"Email: {factura['email']}", self.styles['Normal']))
            
            # Crear tabla de 3 columnas: logo | datos empresa | datos cliente
            num_filas = max(len(empresa_text), len(cliente_text), 1)
            
            for i in range(num_filas):
                row = []
                if i == 0:
                    row.append(logo_cell if logo_cell else '')
                else:
                    row.append('')
                
                if i < len(empresa_text):
                    row.append(empresa_text[i])
                else:
                    row.append('')
                
                if i < len(cliente_text):
                    row.append(cliente_text[i])
                else:
                    row.append('')
                
                header_data.append(row)
            
            # Aplicar SPAN para que el logo ocupe todas las filas
            header_table = Table(header_data, colWidths=[35*mm, 70*mm, 70*mm])
            header_style = TableStyle([
                ('VALIGN', (0, 0), (0, -1), 'TOP'),
                ('VALIGN', (1, 0), (1, -1), 'TOP'),
                ('VALIGN', (2, 0), (2, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 1),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ])
            if logo_cell:
                header_style.add('SPAN', (0, 0), (0, -1))
            header_table.setStyle(header_style)
            story.append(header_table)
            story.append(Spacer(1, 5*mm))
            
            # Título
            story.append(Paragraph("FACTURA", self.styles['Titulo']))
            story.append(Spacer(1, 3*mm))
            
            # Información de la factura (compacta)
            info_data = [
                ['Número:', factura.get('numero', ''), 'Fecha:', factura.get('fecha', ''), 'Estado:', (factura.get('estado') or '').upper()]
            ]
            info_table = Table(info_data, colWidths=[25*mm, 30*mm, 20*mm, 30*mm, 20*mm, 30*mm])
            info_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
                ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                ('ALIGN', (4, 0), (4, 0), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
                ('FONTNAME', (4, 0), (4, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 3*mm))
            
            # Líneas de la factura
            story.append(Paragraph("CONCEPTOS", self.styles['NormalBold']))
            story.append(Spacer(1, 2*mm))
            
            lineas_data = [['Concepto', 'Cant.', 'Precio', 'Dto.%', 'IVA', 'Total']]
            
            total_base = 0.0
            total_iva = 0.0
            ivas_aplicados = {}
            
            for linea in factura.get('lineas', []):
                cantidad = self._safe_float(linea.get('cantidad'), 0.0)
                precio = self._safe_float(linea.get('precio_unitario'), 0.0)
                descuento = self._safe_float(linea.get('descuento'), 0.0)
                iva_porcentaje = self._safe_float(linea.get('iva_porcentaje'), 0.0)
                
                base = cantidad * precio * (1 - descuento / 100)
                iva = base * (iva_porcentaje / 100)
                total_linea = base + iva
                
                total_base += base
                total_iva += iva
                
                if iva_porcentaje not in ivas_aplicados:
                    ivas_aplicados[iva_porcentaje] = 0.0
                ivas_aplicados[iva_porcentaje] += iva
                
                lineas_data.append([
                    linea.get('concepto', ''),
                    f"{cantidad:.2f}",
                    f"{precio:.2f} €",
                    f"{descuento:.1f}%" if descuento > 0 else "-",
                    f"{iva_porcentaje:.1f}%" if iva_porcentaje > 0 else "Sin IVA",
                    f"{total_linea:.2f} €"
                ])
            
            lineas_table = Table(lineas_data, colWidths=[65*mm, 15*mm, 20*mm, 15*mm, 15*mm, 20*mm])
            lineas_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                ('TOPPADDING', (0, 0), (-1, 0), 4),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
                ('TOPPADDING', (0, 1), (-1, -1), 2),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(lineas_table)
            story.append(Spacer(1, 3*mm))
            
            # Totales
            total_factura = self._safe_float(factura.get('total'), 0.0)
            
            totales_data = [
                ['Base Imponible:', f"{total_base:.2f} €"],
                ['IVA:', f"{total_iva:.2f} €"],
                ['TOTAL:', f"{total_factura:.2f} €"]
            ]
            totales_table = Table(totales_data, colWidths=[120*mm, 40*mm])
            totales_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -2), 9),
                ('FONTSIZE', (0, 2), (-1, 2), 12),
                ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#4472C4')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (2, 0), (2, -1), 5),
            ]))
            story.append(totales_table)
            
            # Observaciones
            if factura.get('observaciones'):
                story.append(Spacer(1, 3*mm))
                story.append(Paragraph("OBSERVACIONES", self.styles['NormalBold']))
                story.append(Paragraph(factura['observaciones'], self.styles['Normal']))
            
            doc.build(story)
        except Exception as e:
            import traceback
            error_msg = f"Error al generar PDF: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            raise Exception(error_msg)
    
    def generar_factura_con_plantilla(self, factura: Dict, output_path: str, plantilla_id: int):
        """Genera un PDF de factura usando una plantilla personalizada"""
        try:
            # Obtener plantilla
            plantilla = self.db.obtener_plantilla(plantilla_id)
            if not plantilla:
                # Si no hay plantilla, usar método por defecto
                self.generar_factura(factura, output_path)
                return
            
            # Cargar elementos de la plantilla
            datos = plantilla.get('datos', '[]')
            elementos = json.loads(datos) if datos else []
            
            # Si la plantilla está vacía o no tiene elementos, usar método original
            if not elementos or elementos == []:
                self.generar_factura(factura, output_path)
                return
            
            # Configurar documento
            doc = SimpleDocTemplate(output_path, pagesize=A4, 
                                   leftMargin=15*mm, rightMargin=15*mm,
                                   topMargin=15*mm, bottomMargin=15*mm)
            story = []
            
            # Obtener datos
            empresa = self._obtener_datos_empresa()
            cliente = self.db.obtener_cliente(factura['cliente_id']) if self.db else {}
            
            # Renderizar elementos según su posición y tipo
            elementos_ordenados = sorted(elementos, key=lambda e: (e.get('y', 0), e.get('x', 0)))
            
            for elemento in elementos_ordenados:
                tipo = elemento.get('tipo')
                
                if tipo == 'campo':
                    valor = self._obtener_valor_campo(elemento['campo_id'], factura, empresa, cliente)
                    if valor:
                        self._agregar_campo_pdf(story, elemento, valor)
                
                elif tipo == 'texto':
                    contenido = elemento.get('contenido', '')
                    if contenido:
                        self._agregar_texto_pdf(story, elemento, contenido)
                
                elif tipo == 'imagen':
                    ruta = elemento.get('ruta', '')
                    if ruta and os.path.exists(ruta):
                        self._agregar_imagen_pdf(story, elemento, ruta)
                
                elif tipo == 'tabla':
                    self._agregar_tabla_pdf(story, elemento, factura)
            
            # Verificar que hay contenido antes de construir el PDF
            if not story:
                # Si no hay contenido, usar método original
                self.generar_factura(factura, output_path)
                return
            
            doc.build(story)
        except Exception as e:
            # Si hay error, usar método por defecto
            print(f"Error al generar PDF con plantilla: {str(e)}")
            import traceback
            traceback.print_exc()
            # Asegurarse de que el archivo se genere correctamente
            try:
                self.generar_factura(factura, output_path)
            except Exception as e2:
                print(f"Error crítico al generar PDF: {str(e2)}")
                raise
    
    def generar_presupuesto_con_plantilla(self, presupuesto: Dict, output_path: str, plantilla_id: int):
        """Genera un PDF de presupuesto usando una plantilla personalizada"""
        try:
            # Obtener plantilla
            plantilla = self.db.obtener_plantilla(plantilla_id)
            if not plantilla:
                # Si no hay plantilla, usar método por defecto
                self.generar_presupuesto(presupuesto, output_path)
                return
            
            # Cargar elementos de la plantilla
            datos = plantilla.get('datos', '[]')
            elementos = json.loads(datos) if datos else []
            
            # Si la plantilla está vacía o no tiene elementos, usar método original
            if not elementos or elementos == []:
                self.generar_presupuesto(presupuesto, output_path)
                return
            
            # Configurar documento
            doc = SimpleDocTemplate(output_path, pagesize=A4, 
                                   leftMargin=15*mm, rightMargin=15*mm,
                                   topMargin=15*mm, bottomMargin=15*mm)
            story = []
            
            # Obtener datos
            empresa = self._obtener_datos_empresa()
            cliente = self.db.obtener_cliente(presupuesto['cliente_id']) if self.db else {}
            
            # Renderizar elementos según su posición y tipo
            elementos_ordenados = sorted(elementos, key=lambda e: (e.get('y', 0), e.get('x', 0)))
            
            for elemento in elementos_ordenados:
                tipo = elemento.get('tipo')
                
                if tipo == 'campo':
                    valor = self._obtener_valor_campo(elemento['campo_id'], presupuesto, empresa, cliente)
                    if valor:
                        self._agregar_campo_pdf(story, elemento, valor)
                
                elif tipo == 'texto':
                    contenido = elemento.get('contenido', '')
                    if contenido:
                        self._agregar_texto_pdf(story, elemento, contenido)
                
                elif tipo == 'imagen':
                    ruta = elemento.get('ruta', '')
                    if ruta and os.path.exists(ruta):
                        self._agregar_imagen_pdf(story, elemento, ruta)
                
                elif tipo == 'tabla':
                    self._agregar_tabla_pdf(story, elemento, presupuesto)
            
            # Verificar que hay contenido antes de construir el PDF
            if not story:
                # Si no hay contenido, usar método original
                self.generar_presupuesto(presupuesto, output_path)
                return
            
            doc.build(story)
        except Exception as e:
            # Si hay error, usar método por defecto
            print(f"Error al generar PDF con plantilla: {str(e)}")
            import traceback
            traceback.print_exc()
            # Asegurarse de que el archivo se genere correctamente
            try:
                self.generar_presupuesto(presupuesto, output_path)
            except Exception as e2:
                print(f"Error crítico al generar PDF: {str(e2)}")
                raise
    
    def _obtener_valor_campo(self, campo_id: str, documento: Dict, empresa: Dict, cliente: Dict) -> str:
        """Obtiene el valor de un campo según su ID"""
        valores = {
            'numero': documento.get('numero', ''),
            'fecha': documento.get('fecha', ''),
            'cliente_nombre': cliente.get('nombre', ''),
            'cliente_nif': cliente.get('nif', ''),
            'cliente_direccion': cliente.get('direccion', ''),
            'total': f"{documento.get('total', 0):.2f} €",
            'estado': documento.get('estado', ''),
            'empresa_nombre': empresa.get('nombre', ''),
            'empresa_nif': empresa.get('nif', ''),
            'empresa_direccion': empresa.get('direccion', ''),
        }
        return valores.get(campo_id, '')
    
    def _agregar_campo_pdf(self, story, elemento: Dict, valor: str):
        """Agrega un campo de datos al PDF"""
        # Crear estilo según propiedades del elemento
        estilo = ParagraphStyle(
            name=f"Campo_{elemento.get('campo_id', '')}",
            fontSize=elemento.get('tamano_fuente', 12),
            fontName='Helvetica-Bold' if elemento.get('negrita', False) else 'Helvetica',
            textColor=colors.HexColor(elemento.get('color', '#000000'))
        )
        
        story.append(Spacer(1, elemento.get('y', 0) * mm / 72))
        story.append(Paragraph(valor, estilo))
    
    def _agregar_texto_pdf(self, story, elemento: Dict, contenido: str):
        """Agrega un texto estático al PDF"""
        estilo = ParagraphStyle(
            name=f"Texto_{id(elemento)}",
            fontSize=elemento.get('tamano_fuente', 12),
            fontName='Helvetica-Bold' if elemento.get('negrita', False) else 'Helvetica',
            textColor=colors.HexColor(elemento.get('color', '#000000'))
        )
        
        story.append(Spacer(1, elemento.get('y', 0) * mm / 72))
        story.append(Paragraph(contenido, estilo))
    
    def _agregar_imagen_pdf(self, story, elemento: Dict, ruta: str):
        """Agrega una imagen al PDF"""
        try:
            ancho = elemento.get('ancho', 100) * mm / 72
            alto = elemento.get('alto', 100) * mm / 72
            
            img = Image(ruta, width=ancho, height=alto)
            story.append(Spacer(1, elemento.get('y', 0) * mm / 72))
            story.append(img)
        except Exception as e:
            print(f"Error al agregar imagen: {str(e)}")
    
    def _agregar_tabla_pdf(self, story, elemento: Dict, documento: Dict):
        """Agrega una tabla de líneas al PDF"""
        lineas = documento.get('lineas', [])
        if not lineas:
            return
        
        # Crear datos de la tabla
        datos_tabla = []
        
        # Encabezados
        columnas = elemento.get('columnas', ['Concepto', 'Cantidad', 'Precio', 'Total'])
        datos_tabla.append(columnas)
        
        # Líneas
        for linea in lineas:
            fila = []
            for col in columnas:
                if col == 'Concepto':
                    fila.append(linea.get('concepto', ''))
                elif col == 'Cantidad':
                    fila.append(f"{self._safe_float(linea.get('cantidad', 0)):.2f}")
                elif col == 'Precio':
                    fila.append(f"{self._safe_float(linea.get('precio_unitario', 0)):.2f} €")
                elif col == 'Total':
                    cantidad = self._safe_float(linea.get('cantidad', 0))
                    precio = self._safe_float(linea.get('precio_unitario', 0))
                    descuento = self._safe_float(linea.get('descuento', 0))
                    iva = self._safe_float(linea.get('iva_porcentaje', 0))
                    base = cantidad * precio * (1 - descuento / 100)
                    total = base * (1 + iva / 100)
                    fila.append(f"{total:.2f} €")
                else:
                    fila.append('')
            datos_tabla.append(fila)
        
        # Crear tabla
        ancho = elemento.get('ancho', 500) * mm / 72
        tabla = Table(datos_tabla, colWidths=[ancho / len(columnas)] * len(columnas))
        
        estilo_tabla = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
        ])
        
        tabla.setStyle(estilo_tabla)
        story.append(Spacer(1, elemento.get('y', 0) * mm / 72))
        story.append(tabla)
