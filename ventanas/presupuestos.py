"""
Ventana de gestión de presupuestos
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import json
from database import Database
from pdf_generator import PDFGenerator


class VentanaPresupuestos:
    def __init__(self, parent, db: Database, pdf_gen: PDFGenerator):
        self.parent = parent
        self.db = db
        self.pdf_gen = pdf_gen
        
        # Solo establecer título y geometría si es una ventana Toplevel
        if isinstance(parent, tk.Toplevel):
            self.parent.title("Gestión de Presupuestos")
            self.parent.geometry("1000x600")
        
        self.presupuesto_id_seleccionado = None
        self.orden_columna = None  # Columna actual de ordenamiento
        self.orden_ascendente = True  # True = ascendente, False = descendente
        self.presupuestos_completos = []  # Almacenar todos los presupuestos para filtrar
        
        self.crear_interfaz()
        self.cargar_presupuestos()
    
    def crear_interfaz(self):
        """Crea la interfaz principal con lista de presupuestos"""
        # Frame principal
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo_frame = ttk.Frame(main_frame)
        titulo_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(titulo_frame, text="Presupuestos", font=("Arial", 18, "bold")).pack(side=tk.LEFT)
        
        # Botones en el título
        btn_titulo_frame = ttk.Frame(titulo_frame)
        btn_titulo_frame.pack(side=tk.RIGHT)
        
        # Botón de actualizar (pequeño)
        ttk.Button(btn_titulo_frame, text="🔄", command=self.cargar_presupuestos, width=3).pack(side=tk.LEFT, padx=2)
        
        # Botón nuevo presupuesto
        ttk.Button(btn_titulo_frame, text="➕ Nuevo Presupuesto", command=self.abrir_ventana_nuevo_presupuesto).pack(side=tk.LEFT, padx=2)
        
        # Frame de filtrado
        filtro_frame = ttk.Frame(main_frame)
        filtro_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filtro_frame, text="Filtrar por:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.filtro_campo_var = tk.StringVar(value="Cliente")
        filtro_campo_combo = ttk.Combobox(filtro_frame, textvariable=self.filtro_campo_var, 
                                          values=["Cliente", "Número", "Fecha", "Estado", "Facturado", "Total"],
                                          state="readonly", width=12)
        filtro_campo_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        self.filtro_texto_var = tk.StringVar()
        self.filtro_texto_var.trace('w', lambda *args: self.aplicar_filtro())
        filtro_entry = ttk.Entry(filtro_frame, textvariable=self.filtro_texto_var, width=30)
        filtro_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(filtro_frame, text="🔍", command=self.aplicar_filtro).pack(side=tk.LEFT, padx=2)
        ttk.Button(filtro_frame, text="❌", command=self.limpiar_filtro).pack(side=tk.LEFT, padx=2)
        
        # Lista de presupuestos
        list_frame = ttk.LabelFrame(main_frame, text="Lista de Presupuestos", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Número", "Cliente", "Fecha", "Estado", "Facturado", "Total")
        self.tree_presupuestos = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.tree_presupuestos.heading(col, text=col, command=lambda c=col: self.ordenar_por_columna(c))
            self.tree_presupuestos.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree_presupuestos.yview)
        self.tree_presupuestos.configure(yscrollcommand=scrollbar.set)
        
        self.tree_presupuestos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_presupuestos.bind("<Double-1>", self.on_double_click_presupuesto)
        
        # Botones de acción
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="✏️ Editar", command=self.abrir_ventana_editar_presupuesto).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✅ Aceptar", command=self.aceptar_presupuesto).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📄 PDF", command=self.generar_pdf).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🖨️ Imprimir", command=self.imprimir).pack(side=tk.LEFT, padx=2)
    
    def seleccionar_plantilla(self, tipo):
        """Muestra un diálogo para seleccionar una plantilla"""
        ventana = tk.Toplevel(self.parent.winfo_toplevel())
        ventana.title("Seleccionar Plantilla")
        ventana.geometry("400x350")
        ventana.transient(self.parent.winfo_toplevel())
        ventana.grab_set()
        
        resultado = {'plantilla_id': None}
        
        ttk.Label(ventana, text="Seleccione una plantilla:", font=("Arial", 10, "bold")).pack(pady=10)
        
        # Frame para lista y scrollbar
        list_frame = ttk.Frame(ventana)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        listbox = tk.Listbox(list_frame, height=12)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cargar plantillas
        plantillas = self.db.obtener_plantillas(tipo=tipo, solo_activas=True)
        
        # Agregar opción "Plantilla por defecto"
        listbox.insert(tk.END, "(Plantilla por defecto)")
        
        for plantilla in plantillas:
            listbox.insert(tk.END, f"{plantilla['nombre']} (ID: {plantilla['id']})")
        
        def seleccionar():
            seleccion = listbox.curselection()
            if not seleccion:
                messagebox.showwarning("Advertencia", "Seleccione una plantilla")
                return
            
            idx = seleccion[0]
            if idx == 0:
                # Plantilla por defecto
                resultado['plantilla_id'] = None
            else:
                plantilla = plantillas[idx - 1]
                resultado['plantilla_id'] = plantilla['id']
            
            ventana.destroy()
        
        def cancelar():
            resultado['plantilla_id'] = None
            ventana.destroy()
        
        btn_frame = ttk.Frame(ventana)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Seleccionar", command=seleccionar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=cancelar).pack(side=tk.LEFT, padx=5)
        
        # Esperar a que se cierre la ventana
        ventana.wait_window()
        
        return resultado['plantilla_id']
    
    def ordenar_por_columna(self, columna):
        """Ordena los presupuestos por la columna especificada"""
        # Si es la misma columna, invertir el orden
        if self.orden_columna == columna:
            self.orden_ascendente = not self.orden_ascendente
        else:
            self.orden_columna = columna
            self.orden_ascendente = True
        
        # Recargar presupuestos con el ordenamiento aplicado
        self.cargar_presupuestos()
    
    def aplicar_filtro(self):
        """Aplica el filtro a los presupuestos"""
        self.cargar_presupuestos()
    
    def limpiar_filtro(self):
        """Limpia el filtro"""
        self.filtro_texto_var.set("")
        self.cargar_presupuestos()
    
    def cargar_presupuestos(self):
        """Carga la lista de presupuestos"""
        for item in self.tree_presupuestos.get_children():
            self.tree_presupuestos.delete(item)
        
        presupuestos = self.db.obtener_presupuestos()
        self.presupuestos_completos = presupuestos.copy()
        
        # Aplicar filtro si hay texto
        texto_filtro = self.filtro_texto_var.get().strip().lower()
        if texto_filtro:
            campo_filtro = self.filtro_campo_var.get()
            presupuestos_filtrados = []
            
            for p in presupuestos:
                coincide = False
                
                if campo_filtro == "Cliente":
                    coincide = texto_filtro in str(p.get('cliente_nombre', '')).lower()
                elif campo_filtro == "Número":
                    coincide = texto_filtro in str(p.get('numero', '')).lower()
                elif campo_filtro == "Fecha":
                    coincide = texto_filtro in str(p.get('fecha', '')).lower()
                elif campo_filtro == "Estado":
                    coincide = texto_filtro in str(p.get('estado', '')).lower()
                elif campo_filtro == "Facturado":
                    facturado_texto = "sí" if p.get('facturado', 0) else "no"
                    coincide = texto_filtro in facturado_texto
                elif campo_filtro == "Total":
                    # Buscar en el total numérico
                    try:
                        total_str = f"{p.get('total', 0):.2f}"
                        coincide = texto_filtro in total_str.replace('.', ',').lower() or texto_filtro in total_str.lower()
                    except:
                        coincide = texto_filtro in str(p.get('total', '')).lower()
                
                if coincide:
                    presupuestos_filtrados.append(p)
            
            presupuestos = presupuestos_filtrados
        
        # Aplicar ordenamiento si hay una columna seleccionada
        if self.orden_columna:
            # Mapeo de nombres de columnas a claves de datos
            mapeo_columnas = {
                "Número": "numero",
                "Cliente": "cliente_nombre",
                "Fecha": "fecha",
                "Estado": "estado",
                "Facturado": "facturado",
                "Total": "total"
            }
            
            clave_orden = mapeo_columnas.get(self.orden_columna)
            if clave_orden:
                # Función de ordenamiento
                def obtener_valor(p):
                    valor = p.get(clave_orden, "")
                    # Convertir a número si es Total
                    if clave_orden == "total":
                        try:
                            return float(valor) if valor else 0.0
                        except:
                            return 0.0
                    # Convertir a número si es Número (extraer número de P000001)
                    elif clave_orden == "numero":
                        try:
                            return int(valor.replace("F", "").replace("P", "")) if valor else 0
                        except:
                            return 0
                    # Para Facturado, convertir booleano a número (Sí=1, No=0)
                    elif clave_orden == "facturado":
                        return 1 if p.get('facturado', 0) else 0
                    return str(valor).lower() if valor else ""
                
                presupuestos = sorted(presupuestos, key=obtener_valor, reverse=not self.orden_ascendente)
                
                # Actualizar indicador visual en la cabecera
                columns = ("Número", "Cliente", "Fecha", "Estado", "Facturado", "Total")
                for col in columns:
                    texto = col
                    if col == self.orden_columna:
                        texto += " ▲" if self.orden_ascendente else " ▼"
                    self.tree_presupuestos.heading(col, text=texto, command=lambda c=col: self.ordenar_por_columna(c))
        
        for p in presupuestos:
            facturado_texto = "Sí" if p.get('facturado', 0) else "No"
            if p.get('facturado', 0) and p.get('factura_numero'):
                facturado_texto = f"Sí ({p['factura_numero']})"
            
            self.tree_presupuestos.insert("", tk.END, values=(
                p['numero'],
                p['cliente_nombre'],
                p['fecha'],
                p['estado'],
                facturado_texto,
                f"{p['total']:.2f} €"
            ), tags=(p['id'],))
    
    def on_double_click_presupuesto(self, event):
        """Maneja el doble clic en el treeview de presupuestos"""
        # Verificar que el clic fue en una celda, no en una cabecera
        region = self.tree_presupuestos.identify_region(event.x, event.y)
        if region == "cell":
            # Solo abrir la ventana de edición si se hizo clic en una fila
            self.abrir_ventana_editar_presupuesto(event)
    
    def obtener_presupuesto_seleccionado(self):
        """Obtiene el ID del presupuesto seleccionado"""
        selection = self.tree_presupuestos.selection()
        if not selection:
            return None
        item = self.tree_presupuestos.item(selection[0])
        return item['tags'][0] if item['tags'] else None
    
    def abrir_ventana_nuevo_presupuesto(self):
        """Abre ventana para crear nuevo presupuesto"""
        # Obtener la ventana raíz (root) para los pop-ups modales
        root = self.parent.winfo_toplevel()
        ventana = tk.Toplevel(root)
        ventana.title("Nuevo Presupuesto")
        ventana.geometry("900x700")
        ventana.transient(root)
        ventana.grab_set()
        
        VentanaEditarPresupuesto(ventana, self.db, self.pdf_gen, None, self)
    
    def abrir_ventana_editar_presupuesto(self, event=None):
        """Abre ventana para editar presupuesto seleccionado"""
        presupuesto_id = self.obtener_presupuesto_seleccionado()
        if not presupuesto_id:
            messagebox.showwarning("Advertencia", "Seleccione un presupuesto")
            return
        
        # Obtener la ventana raíz (root) para los pop-ups modales
        root = self.parent.winfo_toplevel()
        ventana = tk.Toplevel(root)
        ventana.title("Editar Presupuesto")
        ventana.geometry("900x700")
        ventana.transient(root)
        ventana.grab_set()
        
        VentanaEditarPresupuesto(ventana, self.db, self.pdf_gen, presupuesto_id, self)
    
    def aceptar_presupuesto(self):
        """Marca el presupuesto como aceptado"""
        presupuesto_id = self.obtener_presupuesto_seleccionado()
        if not presupuesto_id:
            messagebox.showwarning("Advertencia", "Seleccione un presupuesto")
            return
        
        if messagebox.askyesno("Confirmar", "¿Marcar este presupuesto como aceptado?"):
            try:
                self.db.aceptar_presupuesto(presupuesto_id)
                messagebox.showinfo("Éxito", "Presupuesto marcado como aceptado")
                self.cargar_presupuestos()
            except Exception as e:
                messagebox.showerror("Error", f"Error al aceptar presupuesto: {str(e)}")
    
    def generar_pdf(self):
        """Genera un PDF del presupuesto"""
        presupuesto_id = self.obtener_presupuesto_seleccionado()
        if not presupuesto_id:
            messagebox.showwarning("Advertencia", "Seleccione un presupuesto")
            return
        
        try:
            presupuesto = self.db.obtener_presupuesto(presupuesto_id)
            if not presupuesto:
                messagebox.showerror("Error", "Presupuesto no encontrado")
                return
            
            # Asegurar que el directorio pdfs existe
            pdfs_dir = "pdfs"
            if not os.path.exists(pdfs_dir):
                os.makedirs(pdfs_dir)
            
            filename = os.path.join(pdfs_dir, f"presupuesto_{presupuesto['numero']}.pdf")
            filename_abs = os.path.abspath(filename)
            
            # Generar PDF directamente (sin plantillas)
            self.pdf_gen.generar_presupuesto(presupuesto, filename_abs)
            
            # Abrir el explorador de archivos
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                # Abrir el explorador y seleccionar el archivo (sin intentar abrir el PDF automáticamente)
                # Esto evita crashes de Chrome/Edge que son el visor predeterminado de PDFs
                try:
                    subprocess.run(['explorer', '/select,', filename_abs], check=False, timeout=5)
                    messagebox.showinfo("PDF Generado", 
                        f"PDF generado correctamente: {filename}\n\n"
                        f"El explorador de archivos se ha abierto con el archivo seleccionado.\n\n"
                        f"Para abrir el PDF, haga doble clic en el archivo desde el explorador.")
                except Exception as e1:
                    messagebox.showinfo("PDF Generado", 
                        f"PDF generado correctamente: {filename}\n\n"
                        f"Ubicación: {filename_abs}\n\n"
                        f"Error al abrir el explorador: {str(e1)}\n"
                        f"Puede navegar manualmente a la carpeta 'pdfs' para abrir el archivo.")
            elif platform.system() == 'Darwin':  # macOS
                try:
                    subprocess.run(['open', '-R', filename_abs])
                    subprocess.run(['open', filename_abs])
                    messagebox.showinfo("Éxito", f"PDF generado: {filename}\n\nEl explorador y el PDF se han abierto.")
                except Exception as e:
                    messagebox.showwarning("PDF Generado", f"PDF creado en: {filename_abs}\n\nError al abrir: {str(e)}")
            else:  # Linux
                try:
                    subprocess.run(['xdg-open', os.path.dirname(filename_abs)])
                    subprocess.run(['xdg-open', filename_abs])
                    messagebox.showinfo("Éxito", f"PDF generado: {filename}\n\nEl explorador y el PDF se han abierto.")
                except Exception as e:
                    messagebox.showwarning("PDF Generado", f"PDF creado en: {filename_abs}\n\nError al abrir: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF: {str(e)}")
    
    def imprimir(self):
        """Imprime el presupuesto directamente usando el diálogo de impresión de Windows"""
        presupuesto_id = self.obtener_presupuesto_seleccionado()
        if not presupuesto_id:
            messagebox.showwarning("Advertencia", "Seleccione un presupuesto")
            return
        
        try:
            presupuesto = self.db.obtener_presupuesto(presupuesto_id)
            if not presupuesto:
                messagebox.showerror("Error", "Presupuesto no encontrado")
                return
            
            # Asegurar que el directorio pdfs existe
            pdfs_dir = "pdfs"
            if not os.path.exists(pdfs_dir):
                os.makedirs(pdfs_dir)
            
            # Generar PDF temporal con ruta absoluta
            temp_pdf = os.path.join(pdfs_dir, f"temp_presupuesto_{presupuesto['numero']}.pdf")
            temp_pdf_abs = os.path.abspath(temp_pdf)
            
            self.pdf_gen.generar_presupuesto(presupuesto, temp_pdf_abs)
            
            # Verificar que el archivo se creó correctamente
            if not os.path.exists(temp_pdf_abs):
                messagebox.showerror("Error", f"No se pudo crear el archivo PDF: {temp_pdf_abs}")
                return
            
            # Generar PDF para impresión - el usuario debe usar "Generar PDF" para imprimir
            # Esto evita problemas con Chrome/Edge que crashean al intentar abrir PDFs
            messagebox.showinfo("PDF Generado", 
                f"El PDF se ha generado correctamente para impresión.\n\n"
                f"Para imprimir:\n"
                f"1. Haga clic en el botón 'Generar PDF'\n"
                f"2. Se abrirá el PDF automáticamente\n"
                f"3. Presione Ctrl+P para abrir el diálogo de impresión\n"
                f"4. Seleccione su impresora e imprima\n\n"
                f"El archivo se encuentra en:\n{temp_pdf_abs}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al imprimir: {str(e)}")


class VentanaEditarPresupuesto:
    def __init__(self, parent, db: Database, pdf_gen: PDFGenerator, presupuesto_id=None, ventana_lista=None):
        self.parent = parent
        self.db = db
        self.pdf_gen = pdf_gen
        self.ventana_lista = ventana_lista
        self.presupuesto_id_actual = presupuesto_id
        self.cliente_id_actual = None
        
        self.clientes_lista = []
        self.clientes_filtrados = []
        self.lineas_temporales = []  # Lista para almacenar líneas antes de guardar
        
        self.crear_interfaz()
        self.cargar_clientes()
        self.cargar_ivas()
        
        if presupuesto_id:
            self.cargar_presupuesto()
        else:
            # Inicializar lista vacía para nuevo presupuesto
            self.lineas_temporales = []
            # No llamar actualizar_lineas_temporales aquí, se creará línea vacía en crear_interfaz
    
    def crear_interfaz(self):
        """Crea la interfaz de edición/creación de presupuesto"""
        # Frame principal sin scroll (mejor uso del espacio)
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Barra superior con botones principales
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar_frame, text="💾 Guardar", command=self.guardar_presupuesto, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="❌ Cancelar", command=self.parent.destroy, width=15).pack(side=tk.LEFT, padx=2)
        
        # Sección de datos de presupuesto (arriba, más compacta)
        datos_frame = ttk.LabelFrame(main_frame, text="Datos del Presupuesto", padding="10")
        datos_frame.pack(fill=tk.X, pady=(0, 10))
        datos_frame.columnconfigure(1, weight=1)
        datos_frame.columnconfigure(3, weight=1)
        datos_frame.columnconfigure(5, weight=1)
        
        # Fila 1: Número y Cliente
        ttk.Label(datos_frame, text="Número:").grid(row=0, column=0, sticky=tk.W, pady=3, padx=5)
        self.numero_var = tk.StringVar()
        ttk.Label(datos_frame, textvariable=self.numero_var, foreground="gray", width=15).grid(row=0, column=1, sticky=tk.W, pady=3, padx=5)
        
        ttk.Label(datos_frame, text="Cliente ID:").grid(row=0, column=2, sticky=tk.W, pady=3, padx=(20, 5))
        self.cliente_id_var = tk.StringVar()
        self.cliente_id_var.trace('w', self.on_id_cliente_changed)
        ttk.Entry(datos_frame, textvariable=self.cliente_id_var, width=8).grid(row=0, column=3, sticky=tk.W, pady=3, padx=5)
        ttk.Button(datos_frame, text="🔍", command=self.abrir_ventana_seleccionar_cliente, width=3).grid(row=0, column=4, padx=2)
        ttk.Button(datos_frame, text="➕", command=self.crear_nuevo_cliente, width=3).grid(row=0, column=5, padx=2)
        
        # Fila 2: Cliente nombre y Fecha
        ttk.Label(datos_frame, text="Cliente:").grid(row=1, column=0, sticky=tk.W, pady=3, padx=5)
        self.cliente_busqueda_var = tk.StringVar()
        self.cliente_busqueda_var.trace('w', self.filtrar_clientes)
        self.cliente_entry = ttk.Entry(datos_frame, textvariable=self.cliente_busqueda_var)
        self.cliente_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=3, padx=5)
        
        self.cliente_combo = ttk.Combobox(datos_frame, state="readonly")
        self.cliente_combo.grid(row=1, column=3, columnspan=3, sticky=(tk.W, tk.E), pady=3, padx=5)
        self.cliente_combo.bind("<<ComboboxSelected>>", self.on_cliente_selected)
        
        # Fila 3: Fecha y Estado
        ttk.Label(datos_frame, text="Fecha:").grid(row=2, column=0, sticky=tk.W, pady=3, padx=5)
        self.fecha_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(datos_frame, textvariable=self.fecha_var, width=12).grid(row=2, column=1, sticky=tk.W, pady=3, padx=5)
        
        # Fila 4: Observaciones
        ttk.Label(datos_frame, text="Observaciones:").grid(row=3, column=0, sticky=tk.NW, pady=3, padx=5)
        self.observaciones_text = tk.Text(datos_frame, height=2, width=50)
        self.observaciones_text.grid(row=3, column=1, columnspan=5, sticky=(tk.W, tk.E), pady=3, padx=5)
        
        # Sección de líneas de detalle (abajo)
        lineas_frame = ttk.LabelFrame(main_frame, text="Líneas de Detalle", padding="10")
        lineas_frame.pack(fill=tk.BOTH, expand=True)
        lineas_frame.columnconfigure(0, weight=1)
        
        # Treeview de líneas editable inline
        tree_frame = ttk.Frame(lineas_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        columns_lineas = ("Concepto", "Cantidad", "Precio", "IVA", "Dto.%", "Total")
        self.tree_lineas = ttk.Treeview(tree_frame, columns=columns_lineas, show="headings", height=15)
        
        # Configurar columnas con anchos apropiados
        self.tree_lineas.heading("Concepto", text="Concepto")
        self.tree_lineas.column("Concepto", width=300)
        self.tree_lineas.heading("Cantidad", text="Cant.")
        self.tree_lineas.column("Cantidad", width=80)
        self.tree_lineas.heading("Precio", text="Precio")
        self.tree_lineas.column("Precio", width=100)
        self.tree_lineas.heading("IVA", text="IVA")
        self.tree_lineas.column("IVA", width=100)
        self.tree_lineas.heading("Dto.%", text="Dto.%")
        self.tree_lineas.column("Dto.%", width=80)
        self.tree_lineas.heading("Total", text="Total")
        self.tree_lineas.column("Total", width=100)
        
        scrollbar2 = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree_lineas.yview)
        self.tree_lineas.configure(yscrollcommand=scrollbar2.set)
        
        self.tree_lineas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Variables para edición inline
        self.edit_entry = None
        self.edit_item = None
        self.edit_column = None
        self.ivas_lista = []
        
        # Bind eventos para edición inline
        self.tree_lineas.bind("<Double-1>", self.on_double_click)
        self.tree_lineas.bind("<Button-1>", self.on_single_click)
        
        # Crear primera línea vacía si no hay presupuesto guardado
        if not self.presupuesto_id_actual:
            self.crear_linea_vacia()
        
        # Botones de acción y total
        action_frame = ttk.Frame(lineas_frame)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="🗑️ Eliminar Línea", command=self.eliminar_linea).pack(side=tk.LEFT, padx=2)
        
        # Total a la derecha
        total_frame = ttk.Frame(action_frame)
        total_frame.pack(side=tk.RIGHT)
        
        self.total_var = tk.StringVar(value="0.00 €")
        ttk.Label(total_frame, text="TOTAL:", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Label(total_frame, textvariable=self.total_var, font=("Arial", 11, "bold"), foreground="blue").pack(side=tk.LEFT, padx=5)
    
    def cargar_clientes(self):
        """Carga la lista de clientes"""
        self.clientes_lista = self.db.obtener_clientes()
        self.clientes_filtrados = self.clientes_lista.copy()
        self.actualizar_combo_clientes()
    
    def filtrar_clientes(self, *args):
        """Filtra clientes según el texto de búsqueda"""
        texto_busqueda = self.cliente_busqueda_var.get().lower().strip()
        
        if not texto_busqueda:
            self.clientes_filtrados = self.clientes_lista.copy()
        else:
            self.clientes_filtrados = [
                c for c in self.clientes_lista
                if texto_busqueda in c['nombre'].lower() or
                   texto_busqueda in (c.get('nif', '') or '').lower() or
                   texto_busqueda in (c.get('telefono', '') or '').lower()
            ]
        
        self.actualizar_combo_clientes()
    
    def actualizar_combo_clientes(self):
        """Actualiza el combo con los clientes filtrados"""
        nombres = [f"{c['id']} - {c['nombre']}" for c in self.clientes_filtrados]
        self.cliente_combo['values'] = nombres
        
        # Si hay un solo resultado y coincide con la búsqueda, seleccionarlo automáticamente
        if len(self.clientes_filtrados) == 1:
            texto_busqueda = self.cliente_busqueda_var.get().strip()
            cliente = self.clientes_filtrados[0]
            if texto_busqueda.lower() == cliente['nombre'].lower():
                self.cliente_combo.current(0)
                self.on_cliente_selected(None)
    
    def crear_nuevo_cliente(self):
        """Abre ventana para crear nuevo cliente"""
        # Obtener la ventana raíz (root) para los pop-ups modales
        root = self.parent.winfo_toplevel()
        ventana_cliente = tk.Toplevel(root)
        ventana_cliente.title("Nuevo Cliente")
        ventana_cliente.geometry("500x400")
        ventana_cliente.transient(root)
        ventana_cliente.grab_set()
        
        # Formulario rápido de cliente
        form_frame = ttk.Frame(ventana_cliente, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        nombre_var = tk.StringVar()
        nif_var = tk.StringVar()
        direccion_var = tk.StringVar()
        telefono_var = tk.StringVar()
        email_var = tk.StringVar()
        
        ttk.Label(form_frame, text="Nombre *:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=nombre_var, width=40).grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="NIF:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=nif_var, width=40).grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Dirección:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=direccion_var, width=40).grid(row=2, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Teléfono:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=telefono_var, width=40).grid(row=3, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Email:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=email_var, width=40).grid(row=4, column=1, pady=5, padx=5)
        
        def guardar_y_cerrar():
            if not nombre_var.get().strip():
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            
            try:
                cliente_id = self.db.crear_cliente(
                    nombre_var.get().strip(),
                    nif_var.get().strip(),
                    direccion_var.get().strip(),
                    telefono_var.get().strip(),
                    email_var.get().strip()
                )
                
                # Recargar clientes y seleccionar el nuevo
                self.cargar_clientes()
                nuevo_cliente = self.db.obtener_cliente(cliente_id)
                if nuevo_cliente:
                    self.cliente_id_actual = cliente_id
                    self.cliente_id_var.set(str(cliente_id))
                    self.cliente_busqueda_var.set(nuevo_cliente['nombre'])
                    self.filtrar_clientes()
                    # Buscar y seleccionar en el combo
                    for i, c in enumerate(self.clientes_filtrados):
                        if c['id'] == cliente_id:
                            self.cliente_combo.current(i)
                            self.on_cliente_selected(None)
                            break
                
                messagebox.showinfo("Éxito", "Cliente creado correctamente")
                ventana_cliente.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear cliente: {str(e)}")
        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Guardar", command=guardar_y_cerrar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=ventana_cliente.destroy).pack(side=tk.LEFT, padx=5)
    
    def cargar_ivas(self):
        """Carga la lista de IVAs en el combo"""
        self.ivas_lista = self.db.obtener_ivas(solo_activos=True)
        # Ya no hay iva_combo en el nuevo diseño, pero mantenemos la lista para edición inline
    
    def crear_linea_vacia(self):
        """Crea una línea vacía nueva en el treeview"""
        # Limpiar cualquier referencia a elemento anterior
        self.edit_item = None
        self.edit_column = None
        if self.edit_entry:
            try:
                self.edit_entry.destroy()
            except:
                pass
            self.edit_entry = None
        
        # Obtener IVA predeterminado (del cliente o 21% por defecto)
        iva_predeterminado = None
        iva_texto = ""
        
        if self.cliente_id_actual:
            cliente = self.db.obtener_cliente(self.cliente_id_actual)
            if cliente and cliente.get('iva_predeterminado_id'):
                iva = self.db.obtener_iva(cliente['iva_predeterminado_id'])
                if iva:
                    iva_predeterminado = iva
                    iva_texto = f"{iva['porcentaje']:.1f}%"
        
        # Si no hay IVA del cliente, usar el 21% por defecto
        if not iva_predeterminado:
            iva_predeterminado = self.db.obtener_iva_por_porcentaje(21.0)
            if iva_predeterminado:
                iva_texto = f"{iva_predeterminado['porcentaje']:.1f}%"
            else:
                # Si no existe el 21%, usar el predeterminado general como fallback
                iva_predeterminado = self.db.obtener_iva_predeterminado()
                if iva_predeterminado:
                    iva_texto = f"{iva_predeterminado['porcentaje']:.1f}%"
                else:
                    iva_texto = "Sin IVA"
        
        # Crear línea completamente vacía (excepto IVA predeterminado)
        item = self.tree_lineas.insert("", tk.END, values=("", "", "", iva_texto, "0%", ""), tags=("NUEVA",))
        self.tree_lineas.selection_set(item)
        self.tree_lineas.focus(item)
        
        # Pequeño delay para asegurar que el Entry anterior se haya destruido
        self.parent.after(10, lambda: self.iniciar_edicion(item, "Concepto"))
    
    def iniciar_edicion(self, item, column):
        """Inicia la edición de una celda"""
        # Cancelar edición anterior si existe
        if self.edit_entry:
            self.finalizar_edicion(guardar=False)
        
        # Obtener valor actual
        valores = list(self.tree_lineas.item(item, 'values'))
        col_index = self.tree_lineas['columns'].index(column)
        valor_actual = valores[col_index] if col_index < len(valores) else ""
        
        # Obtener posición de la celda
        bbox = self.tree_lineas.bbox(item, column)
        if not bbox:
            return
        
        x, y, width, height = bbox
        
        # Crear Entry o Combobox según la columna
        if column == "IVA":
            # Combobox para IVA
            self.edit_entry = ttk.Combobox(self.tree_lineas, state="readonly", width=width)
            valores_iva = [f"{iva['id']} - {iva['nombre']} ({iva['porcentaje']}%)" for iva in self.ivas_lista]
            self.edit_entry['values'] = valores_iva
            # Seleccionar IVA actual si existe
            if valor_actual and valor_actual != "Sin IVA":
                try:
                    porcentaje = float(valor_actual.replace("%", "").strip())
                    for idx, iva in enumerate(self.ivas_lista):
                        if abs(iva['porcentaje'] - porcentaje) < 0.01:
                            self.edit_entry.current(idx)
                            break
                except:
                    pass
        else:
            # Entry normal - solo insertar si hay valor, no insertar nada si está vacío
            self.edit_entry = ttk.Entry(self.tree_lineas, width=width)
            valor_limpio = valor_actual.replace(" €", "").replace("%", "").strip()
            # Solo insertar si hay un valor real (no vacío y no "0")
            if valor_limpio and valor_limpio != "0" and valor_limpio != "0.00":
                self.edit_entry.insert(0, valor_limpio)
        
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.focus()
        self.edit_entry.select_range(0, tk.END)
        
        self.edit_item = item
        self.edit_column = column
        
        # Bind eventos
        self.edit_entry.bind("<Return>", lambda e: self.finalizar_edicion_y_avanzar())
        self.edit_entry.bind("<Tab>", lambda e: self.finalizar_edicion_y_avanzar())
        self.edit_entry.bind("<Escape>", lambda e: self.finalizar_edicion(guardar=False))
        self.edit_entry.bind("<FocusOut>", lambda e: self.finalizar_edicion())
        if column == "IVA":
            self.edit_entry.bind("<<ComboboxSelected>>", lambda e: self.finalizar_edicion_y_avanzar())
    
    def finalizar_edicion_y_avanzar(self):
        """Finaliza la edición y avanza al siguiente campo"""
        # Guardar item y columna antes de finalizar (porque finalizar_edicion los limpia)
        item_actual = self.edit_item
        columna_actual = self.edit_column
        
        # Guardar cambios en BD si es necesario (solo para líneas existentes)
        if item_actual and self.presupuesto_id_actual:
            tags = self.tree_lineas.item(item_actual, 'tags')
            tag = tags[0] if tags else ""
            # Si es una línea existente en BD, guardarla ahora
            if tag and not tag.startswith("T") and tag != "NUEVA":
                try:
                    valores = list(self.tree_lineas.item(item_actual, 'values'))
                    concepto = valores[0].strip() if len(valores) > 0 else ""
                    if concepto:  # Solo guardar si tiene concepto
                        self.guardar_linea_desde_treeview(item_actual)
                except:
                    pass
        
        self.finalizar_edicion(guardar=True)
        
        if not item_actual or not columna_actual:
            return
        
        # Columnas editables en orden
        columnas = ["Concepto", "Cantidad", "Precio", "IVA", "Dto.%"]
        try:
            col_index = columnas.index(columna_actual)
            siguiente_col = columnas[col_index + 1] if col_index + 1 < len(columnas) else None
            
            if siguiente_col:
                # Avanzar al siguiente campo
                # Pequeño delay para asegurar que el Entry anterior se haya destruido
                self.parent.after(10, lambda: self.iniciar_edicion(item_actual, siguiente_col))
            else:
                # Estamos en el último campo (Dto.%), crear nueva línea automáticamente
                self.parent.after(10, lambda: self.crear_linea_vacia_desde_actual())
        except ValueError:
            pass
    
    def crear_linea_vacia_desde_actual(self):
        """Crea una nueva línea vacía después de completar la actual"""
        # Primero asegurarse de que la línea actual esté guardada
        if self.edit_item:
            valores = list(self.tree_lineas.item(self.edit_item, 'values'))
            concepto = valores[0].strip() if len(valores) > 0 else ""
            cantidad = valores[1].strip() if len(valores) > 1 else ""
            precio = valores[2].replace(" €", "").strip() if len(valores) > 2 else ""
            
            # Si tiene datos mínimos, guardar la línea
            if concepto and cantidad and precio:
                self.guardar_linea_desde_treeview(self.edit_item)
        
        # Crear nueva línea vacía
        self.crear_linea_vacia()
    
    def completar_linea_y_crear_nueva(self):
        """Completa la línea actual y crea una nueva línea vacía"""
        item = self.edit_item
        if not item:
            return
        
        valores = list(self.tree_lineas.item(item, 'values'))
        
        # Verificar que tenga datos mínimos
        concepto = valores[0].strip() if len(valores) > 0 else ""
        cantidad = valores[1].strip() if len(valores) > 1 else ""
        precio = valores[2].replace(" €", "").strip() if len(valores) > 2 else ""
        
        if concepto and cantidad and precio:
            # La línea está completa, guardarla y crear nueva
            self.guardar_linea_desde_treeview(item)
            self.crear_linea_vacia()
        else:
            # No hay datos suficientes, solo crear nueva línea vacía
            self.crear_linea_vacia()
    
    def guardar_linea_desde_treeview(self, item):
        """Guarda una línea desde el treeview a la lista temporal o BD"""
        valores = list(self.tree_lineas.item(item, 'values'))
        tags = self.tree_lineas.item(item, 'tags')
        
        concepto = valores[0].strip() if len(valores) > 0 else ""
        cantidad_str = valores[1].strip() if len(valores) > 1 else "0"
        precio_str = valores[2].replace(" €", "").strip() if len(valores) > 2 else "0"
        iva_str = valores[3] if len(valores) > 3 else "Sin IVA"
        descuento_str = valores[4].replace("%", "").strip() if len(valores) > 4 else "0"
        
        if not concepto:
            return
        
        try:
            cantidad = float(cantidad_str) if cantidad_str else 0
            precio = float(precio_str) if precio_str else 0
            descuento = float(descuento_str) if descuento_str else 0
        except ValueError:
            messagebox.showerror("Error", "Cantidad, precio y descuento deben ser números válidos")
            return
        
        # Obtener IVA
        iva_id = None
        iva_porcentaje = 0
        if iva_str and iva_str != "Sin IVA":
            try:
                porcentaje = float(iva_str.replace("%", "").strip())
                for iva in self.ivas_lista:
                    if abs(iva['porcentaje'] - porcentaje) < 0.01:
                        iva_id = iva['id']
                        iva_porcentaje = iva['porcentaje']
                        break
            except:
                pass
        
        # Calcular total
        base = cantidad * precio * (1 - descuento / 100)
        total_linea = base * (1 + iva_porcentaje / 100)
        
        # Actualizar valores en treeview
        self.tree_lineas.item(item, values=(
            concepto,
            f"{cantidad:.2f}",
            f"{precio:.2f} €",
            f"{iva_porcentaje:.1f}%" if iva_porcentaje > 0 else "Sin IVA",
            f"{descuento:.1f}%" if descuento > 0 else "0%",
            f"{total_linea:.2f} €"
        ))
        
        # Guardar en memoria o BD
        linea = {
            'concepto': concepto,
            'cantidad': cantidad,
            'precio_unitario': precio,
            'iva_id': iva_id,
            'iva_porcentaje': iva_porcentaje,
            'descuento': descuento
        }
        
        if self.presupuesto_id_actual:
            # Guardar en BD
            try:
                tag = tags[0] if tags else ""
                # Si la línea ya existe en BD (tag es un número), actualizarla
                if tag and not tag.startswith("T") and tag != "NUEVA":
                    try:
                        linea_id = int(tag)
                        self.db.actualizar_linea_presupuesto(
                            linea_id, concepto, cantidad, precio, iva_id, descuento
                        )
                        # Actualizar tag para mantener el ID
                        self.tree_lineas.item(item, tags=(str(linea_id),))
                    except ValueError:
                        # Si no es un número válido, agregar como nueva línea
                        self.db.agregar_linea_presupuesto(
                            self.presupuesto_id_actual, concepto, cantidad, precio, iva_id, descuento
                        )
                        self.cargar_lineas()
                else:
                    # Es una línea nueva, agregarla
                    self.db.agregar_linea_presupuesto(
                        self.presupuesto_id_actual, concepto, cantidad, precio, iva_id, descuento
                    )
                    self.cargar_lineas()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar línea: {str(e)}")
        else:
            # Guardar en lista temporal
            tag = tags[0] if tags else ""
            if tag.startswith("T"):
                idx = int(tag[1:])
                if 0 <= idx < len(self.lineas_temporales):
                    self.lineas_temporales[idx] = linea
                else:
                    self.lineas_temporales.append(linea)
            elif tag == "NUEVA":
                self.lineas_temporales.append(linea)
                self.tree_lineas.item(item, tags=(f"T{len(self.lineas_temporales)-1}",))
        
        self.actualizar_total()
    
    def actualizar_total(self):
        """Actualiza el total del presupuesto"""
        total = 0
        for item in self.tree_lineas.get_children():
            valores = self.tree_lineas.item(item, 'values')
            if len(valores) > 5:
                total_str = valores[5].replace(" €", "").strip()
                try:
                    total += float(total_str)
                except:
                    pass
        self.total_var.set(f"{total:.2f} €")
    
    def finalizar_edicion(self, guardar=True):
        """Finaliza la edición de una celda"""
        if not self.edit_entry or not self.edit_item or not self.edit_column:
            return
        
        if guardar:
            nuevo_valor = self.edit_entry.get()
            valores = list(self.tree_lineas.item(self.edit_item, 'values'))
            col_index = self.tree_lineas['columns'].index(self.edit_column)
            
            # Actualizar valor según el tipo de columna
            if self.edit_column == "IVA":
                # Extraer el porcentaje del texto del combobox (formato: "1 - IVA General (21.0%)")
                porcentaje_iva = 0
                if nuevo_valor and nuevo_valor != "Sin IVA":
                    try:
                        # Buscar el porcentaje entre paréntesis
                        import re
                        match = re.search(r'\(([\d.]+)%\)', nuevo_valor)
                        if match:
                            porcentaje_iva = float(match.group(1))
                            valores[col_index] = f"{porcentaje_iva:.1f}%"
                        else:
                            # Si no hay formato esperado, intentar parsear directamente
                            porcentaje_iva = float(nuevo_valor.replace("%", "").strip())
                            valores[col_index] = f"{porcentaje_iva:.1f}%"
                    except:
                        valores[col_index] = "Sin IVA"
                else:
                    valores[col_index] = "Sin IVA"
            elif self.edit_column == "Cantidad":
                try:
                    cantidad = float(nuevo_valor) if nuevo_valor else 0
                    valores[col_index] = f"{cantidad:.2f}"
                except:
                    valores[col_index] = "0.00"
            elif self.edit_column == "Precio":
                try:
                    precio = float(nuevo_valor) if nuevo_valor else 0
                    valores[col_index] = f"{precio:.2f} €"
                except:
                    valores[col_index] = "0.00 €"
            elif self.edit_column == "Dto.%":
                try:
                    descuento = float(nuevo_valor) if nuevo_valor else 0
                    valores[col_index] = f"{descuento:.1f}%"
                except:
                    valores[col_index] = "0%"
            else:
                valores[col_index] = nuevo_valor
            
            self.tree_lineas.item(self.edit_item, values=valores)
            
            # Recalcular total de la línea si cambió cantidad, precio, IVA o descuento
            # Pero NO guardar en BD inmediatamente si estamos editando una línea existente
            # Solo actualizar el total visual
            if self.edit_column in ["Cantidad", "Precio", "IVA", "Dto.%"]:
                # Solo actualizar el total visual, no guardar en BD todavía
                # El guardado se hará cuando se complete la edición o se avance al siguiente campo
                self.actualizar_total()
        
        self.edit_entry.destroy()
        self.edit_entry = None
        self.edit_item = None
        self.edit_column = None
    
    def on_double_click(self, event):
        """Maneja doble clic para iniciar edición"""
        region = self.tree_lineas.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree_lineas.identify_row(event.y)
            column = self.tree_lineas.identify_column(event.x)
            if item and column:
                # Convertir número de columna a nombre
                col_num = int(column.replace("#", "")) - 1
                columns = self.tree_lineas['columns']
                if 0 <= col_num < len(columns):
                    col_name = columns[col_num]
                    # No editar Total (es calculado)
                    if col_name != "Total":
                        self.iniciar_edicion(item, col_name)
    
    def on_single_click(self, event):
        """Maneja clic simple para cancelar edición si se hace clic fuera"""
        if self.edit_entry:
            self.finalizar_edicion(guardar=True)
    
    def on_id_cliente_changed(self, *args):
        """Maneja el cambio en el campo ID de cliente"""
        id_text = self.cliente_id_var.get().strip()
        if id_text:
            try:
                cliente_id = int(id_text)
                cliente = self.db.obtener_cliente(cliente_id)
                if cliente:
                    self.cliente_id_actual = cliente_id
                    self.cliente_busqueda_var.set(cliente['nombre'])
                    # Buscar en la lista filtrada y seleccionar
                    for i, c in enumerate(self.clientes_filtrados):
                        if c['id'] == cliente_id:
                            self.cliente_combo.current(i)
                            break
                else:
                    self.cliente_id_actual = None
                    self.cliente_busqueda_var.set("")
            except ValueError:
                # Si no es un número válido, no hacer nada
                pass
    
    def abrir_ventana_seleccionar_cliente(self):
        """Abre ventana para seleccionar cliente con búsqueda"""
        # Obtener la ventana raíz (root) para los pop-ups modales
        root = self.parent.winfo_toplevel()
        ventana = tk.Toplevel(root)
        ventana.title("Seleccionar Cliente")
        ventana.geometry("700x500")
        ventana.transient(root)
        ventana.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(ventana, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Búsqueda
        busqueda_frame = ttk.LabelFrame(main_frame, text="Buscar Cliente", padding="10")
        busqueda_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(busqueda_frame, text="Buscar por nombre:").grid(row=0, column=0, sticky=tk.W, padx=5)
        busqueda_var = tk.StringVar()
        busqueda_entry = ttk.Entry(busqueda_frame, textvariable=busqueda_var, width=40)
        busqueda_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        busqueda_entry.focus()
        
        busqueda_frame.columnconfigure(1, weight=1)
        
        # Lista de clientes
        list_frame = ttk.LabelFrame(main_frame, text="Clientes", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Nombre", "NIF", "Teléfono", "Email")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def filtrar_y_cargar():
            texto = busqueda_var.get().lower().strip()
            # Limpiar treeview
            for item in tree.get_children():
                tree.delete(item)
            
            # Filtrar y cargar clientes
            clientes = self.db.obtener_clientes()
            if texto:
                clientes = [c for c in clientes if texto in c['nombre'].lower()]
            
            for cliente in clientes:
                tree.insert("", tk.END, values=(
                    cliente['id'],
                    cliente['nombre'],
                    cliente.get('nif', '') or '',
                    cliente.get('telefono', '') or '',
                    cliente.get('email', '') or ''
                ), tags=(cliente['id'],))
        
        busqueda_var.trace('w', lambda *args: filtrar_y_cargar())
        filtrar_y_cargar()  # Cargar inicialmente
        
        def seleccionar_cliente():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Advertencia", "Seleccione un cliente")
                return
            
            item = tree.item(selection[0])
            cliente_id = item['tags'][0]
            
            cliente = self.db.obtener_cliente(cliente_id)
            if cliente:
                self.cliente_id_actual = cliente_id
                self.cliente_id_var.set(str(cliente_id))
                self.cliente_busqueda_var.set(cliente['nombre'])
                self.filtrar_clientes()
                # Seleccionar en el combo
                for i, c in enumerate(self.clientes_filtrados):
                    if c['id'] == cliente_id:
                        self.cliente_combo.current(i)
                        break
                ventana.destroy()
        
        tree.bind("<Double-1>", lambda e: seleccionar_cliente())
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Seleccionar", command=seleccionar_cliente).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=ventana.destroy).pack(side=tk.LEFT, padx=5)
    
    def on_cliente_selected(self, event):
        """Maneja la selección de cliente"""
        selection = self.cliente_combo.current()
        if selection >= 0 and selection < len(self.clientes_filtrados):
            self.cliente_id_actual = self.clientes_filtrados[selection]['id']
            # Actualizar el campo de ID y búsqueda con el nombre completo
            cliente = self.clientes_filtrados[selection]
            self.cliente_id_var.set(str(cliente['id']))
            self.cliente_busqueda_var.set(cliente['nombre'])
    
    def cargar_presupuesto(self):
        """Carga un presupuesto existente"""
        if not self.presupuesto_id_actual:
            return
        
        presupuesto = self.db.obtener_presupuesto(self.presupuesto_id_actual)
        if presupuesto:
            self.numero_var.set(presupuesto['numero'])
            self.fecha_var.set(presupuesto['fecha'])
            self.observaciones_text.delete(1.0, tk.END)
            self.observaciones_text.insert(1.0, presupuesto.get('observaciones', ''))
            
            # Seleccionar cliente
            cliente = self.db.obtener_cliente(presupuesto['cliente_id'])
            if cliente:
                self.cliente_id_actual = presupuesto['cliente_id']
                self.cliente_id_var.set(str(presupuesto['cliente_id']))
                self.cliente_busqueda_var.set(cliente['nombre'])
                self.filtrar_clientes()
                cliente_idx = next((i for i, c in enumerate(self.clientes_filtrados) if c['id'] == presupuesto['cliente_id']), -1)
                if cliente_idx >= 0:
                    self.cliente_combo.current(cliente_idx)
            
            self.cargar_lineas()
    
    def guardar_presupuesto(self):
        """Guarda o actualiza un presupuesto"""
        if not self.cliente_id_actual:
            messagebox.showerror("Error", "Seleccione un cliente")
            return
        
        fecha = self.fecha_var.get().strip()
        observaciones = self.observaciones_text.get(1.0, tk.END).strip()
        
        try:
            if not self.presupuesto_id_actual:
                # Crear nuevo presupuesto
                self.presupuesto_id_actual = self.db.crear_presupuesto(
                    self.cliente_id_actual, fecha, observaciones
                )
                self.numero_var.set(self.db.obtener_presupuesto(self.presupuesto_id_actual)['numero'])
                
                # Guardar todas las líneas desde el treeview
                for item in self.tree_lineas.get_children():
                    valores = self.tree_lineas.item(item, 'values')
                    tags = self.tree_lineas.item(item, 'tags')
                    
                    concepto = valores[0].strip() if len(valores) > 0 else ""
                    if not concepto:
                        continue
                    
                    try:
                        cantidad = float(valores[1]) if len(valores) > 1 and valores[1] else 0
                        precio = float(valores[2].replace(" €", "")) if len(valores) > 2 and valores[2] else 0
                        iva_str = valores[3] if len(valores) > 3 else "Sin IVA"
                        descuento = float(valores[4].replace("%", "")) if len(valores) > 4 and valores[4] else 0
                    except:
                        continue
                    
                    # Obtener IVA
                    iva_id = None
                    if iva_str and iva_str != "Sin IVA":
                        try:
                            porcentaje = float(iva_str.replace("%", "").strip())
                            for iva in self.ivas_lista:
                                if abs(iva['porcentaje'] - porcentaje) < 0.01:
                                    iva_id = iva['id']
                                    break
                        except:
                            pass
                    
                    self.db.agregar_linea_presupuesto(
                        self.presupuesto_id_actual,
                        concepto,
                        cantidad,
                        precio,
                        iva_id,
                        descuento
                    )
                
                # Limpiar líneas temporales y recargar desde BD
                self.lineas_temporales = []
                self.cargar_lineas()
                
                messagebox.showinfo("Éxito", "Presupuesto creado correctamente")
            else:
                # Actualizar observaciones y fecha
                # Las líneas ya están guardadas, solo recargar
                self.cargar_lineas()
                messagebox.showinfo("Éxito", "Presupuesto actualizado")
            
            if self.ventana_lista:
                self.ventana_lista.cargar_presupuestos()
            
            # Cerrar la ventana después de guardar exitosamente
            self.parent.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar presupuesto: {str(e)}")
    
    def agregar_linea(self):
        """Agrega una línea al presupuesto (en memoria o en BD según corresponda)"""
        concepto = self.concepto_var.get().strip()
        if not concepto:
            messagebox.showerror("Error", "El concepto es obligatorio")
            return
        
        try:
            cantidad = float(self.cantidad_var.get())
            precio = float(self.precio_var.get())
            descuento = float(self.descuento_var.get() or "0")
        except ValueError:
            messagebox.showerror("Error", "Cantidad, precio y descuento deben ser números válidos")
            return
        
        # Obtener IVA seleccionado
        iva_id = None
        iva_porcentaje = 0
        if self.iva_combo.current() >= 0:
            ivas = self.db.obtener_ivas(solo_activos=True)
            iva_seleccionado = ivas[self.iva_combo.current()]
            iva_id = iva_seleccionado['id']
            iva_porcentaje = iva_seleccionado['porcentaje']
        
        # Crear línea temporal
        linea = {
            'concepto': concepto,
            'cantidad': cantidad,
            'precio_unitario': precio,
            'iva_id': iva_id,
            'iva_porcentaje': iva_porcentaje,
            'descuento': descuento
        }
        
        if self.presupuesto_id_actual:
            # Si el presupuesto ya está guardado, agregar directamente a BD
            try:
                self.db.agregar_linea_presupuesto(
                    self.presupuesto_id_actual, concepto, cantidad, precio, iva_id, descuento
                )
                self.cargar_lineas()
            except Exception as e:
                messagebox.showerror("Error", f"Error al agregar línea: {str(e)}")
        else:
            # Si es nuevo presupuesto, agregar a lista temporal
            self.lineas_temporales.append(linea)
            self.actualizar_lineas_temporales()
        
        # Limpiar campos
        self.concepto_var.set("")
        self.cantidad_var.set("")
        self.precio_var.set("")
        self.descuento_var.set("0")
    
    def actualizar_lineas_temporales(self):
        """Actualiza la visualización de líneas temporales y calcula el total"""
        # No borrar todas las líneas, solo actualizar las existentes
        # Esto permite mantener la edición inline activa
        self.actualizar_total()
    
    def cargar_lineas(self):
        """Carga las líneas del presupuesto actual desde BD"""
        for item in self.tree_lineas.get_children():
            self.tree_lineas.delete(item)
        
        if not self.presupuesto_id_actual:
            # Si no hay presupuesto guardado, mostrar líneas temporales
            self.actualizar_lineas_temporales()
            return
        
        presupuesto = self.db.obtener_presupuesto(self.presupuesto_id_actual)
        if presupuesto and presupuesto.get('lineas'):
            total = 0
            for linea in presupuesto['lineas']:
                cantidad = linea['cantidad']
                precio = linea['precio_unitario']
                descuento = linea.get('descuento', 0)
                iva_porcentaje = linea.get('iva_porcentaje', 0) or 0
                
                base = cantidad * precio * (1 - descuento / 100)
                total_linea = base * (1 + iva_porcentaje / 100)
                total += total_linea
                
                self.tree_lineas.insert("", tk.END, values=(
                    linea['concepto'],
                    f"{cantidad:.2f}",
                    f"{precio:.2f} €",
                    f"{iva_porcentaje:.1f}%" if iva_porcentaje > 0 else "Sin IVA",
                    f"{descuento:.1f}%" if descuento > 0 else "0%",
                    f"{total_linea:.2f} €"
                ), tags=(str(linea['id']),))
            
            self.total_var.set(f"{total:.2f} €")
    
    def eliminar_linea(self):
        """Elimina la línea seleccionada"""
        selection = self.tree_lineas.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una línea para eliminar")
            return
        
        item = self.tree_lineas.item(selection[0])
        tags = item['tags']
        
        if self.presupuesto_id_actual:
            # Si el presupuesto está guardado, eliminar de BD
            try:
                tag = tags[0] if tags else None
                if tag and not str(tag).startswith('T'):
                    self.db.eliminar_linea_presupuesto(int(tag))
                    self.cargar_lineas()
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar línea: {str(e)}")
        else:
            # Si es temporal, eliminar de la lista
            try:
                tag = tags[0] if tags else None
                if tag and tag.startswith('T'):
                    idx = int(tag[1:])  # Extraer el índice del tag "T0", "T1", etc.
                    if 0 <= idx < len(self.lineas_temporales):
                        self.lineas_temporales.pop(idx)
                        self.actualizar_lineas_temporales()
            except (ValueError, IndexError) as e:
                messagebox.showerror("Error", f"Error al eliminar línea: {str(e)}")
