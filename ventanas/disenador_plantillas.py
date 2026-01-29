"""
Ventana diseñador de plantillas para facturas y presupuestos
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from database import Database


class VentanaDisenadorPlantillas:
    def __init__(self, parent, db: Database):
        self.parent = parent
        self.db = db
        
        if isinstance(parent, tk.Toplevel):
            self.parent.title("Diseñador de Plantillas")
            self.parent.geometry("1200x800")
        
        self.tipo_plantilla = "factura"  # "factura" o "presupuesto"
        self.elementos = []  # Lista de elementos en el canvas
        self.elemento_seleccionado = None
        self.plantilla_actual_id = None  # ID de la plantilla actualmente cargada
        self.es_predeterminada = False  # Si la plantilla actual es predeterminada
        
        self.crear_interfaz()
        self.cargar_plantilla_predeterminada()
    
    def crear_interfaz(self):
        """Crea la interfaz del diseñador"""
        # Frame principal
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Barra superior
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(toolbar_frame, text="Tipo:").pack(side=tk.LEFT, padx=5)
        self.tipo_var = tk.StringVar(value="factura")
        tipo_combo = ttk.Combobox(toolbar_frame, textvariable=self.tipo_var, 
                                   values=["factura", "presupuesto"], state="readonly", width=15)
        tipo_combo.pack(side=tk.LEFT, padx=5)
        tipo_combo.bind("<<ComboboxSelected>>", lambda e: self.cambiar_tipo())
        
        ttk.Button(toolbar_frame, text="💾 Guardar", command=self.guardar_plantilla).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="📂 Copiar desde Predeterminado", command=self.copiar_desde_predeterminado).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="🗑️ Eliminar Plantilla", command=self.eliminar_plantilla_actual).pack(side=tk.LEFT, padx=2)
        
        # Label para mostrar estado
        self.estado_label = ttk.Label(toolbar_frame, text="", foreground="blue", font=("Arial", 9, "bold"))
        self.estado_label.pack(side=tk.RIGHT, padx=10)
        
        # Panel izquierdo: Paleta de elementos
        left_panel = ttk.LabelFrame(main_frame, text="Elementos", padding="10", width=200)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Campos de datos disponibles
        ttk.Label(left_panel, text="Campos de Datos:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        campos_factura = [
            ("Número", "numero"),
            ("Fecha", "fecha"),
            ("Cliente Nombre", "cliente_nombre"),
            ("Cliente NIF", "cliente_nif"),
            ("Cliente Dirección", "cliente_direccion"),
            ("Total", "total"),
        ]
        
        campos_presupuesto = campos_factura + [
            ("Estado", "estado"),
        ]
        
        self.campos_disponibles = campos_factura if self.tipo_plantilla == "factura" else campos_presupuesto
        
        for nombre, campo_id in self.campos_disponibles:
            btn = ttk.Button(left_panel, text=f"📄 {nombre}", 
                           command=lambda c=campo_id: self.agregar_campo(c))
            btn.pack(fill=tk.X, pady=2)
        
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Label(left_panel, text="Elementos:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Button(left_panel, text="📝 Texto", command=self.agregar_texto).pack(fill=tk.X, pady=2)
        ttk.Button(left_panel, text="🖼️ Imagen", command=self.agregar_imagen).pack(fill=tk.X, pady=2)
        ttk.Button(left_panel, text="📊 Tabla Líneas", command=self.agregar_tabla).pack(fill=tk.X, pady=2)
        
        # Panel central: Canvas de diseño (simulando página A4)
        center_panel = ttk.LabelFrame(main_frame, text="Diseño", padding="10")
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas con fondo blanco (simulando papel)
        self.canvas = tk.Canvas(center_panel, bg="white", width=595, height=842)  # A4 en puntos (72 DPI)
        scrollbar_y = ttk.Scrollbar(center_panel, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar_x = ttk.Scrollbar(center_panel, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Panel derecho: Propiedades del elemento seleccionado
        right_panel = ttk.LabelFrame(main_frame, text="Propiedades", padding="10", width=250)
        right_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))
        right_panel.pack_propagate(False)
        
        self.propiedades_frame = ttk.Frame(right_panel)
        self.propiedades_frame.pack(fill=tk.BOTH, expand=True)
        
        self.actualizar_propiedades()
    
    def cambiar_tipo(self):
        """Cambia el tipo de plantilla"""
        self.tipo_plantilla = self.tipo_var.get()
        # Cargar plantilla predeterminada del nuevo tipo
        self.cargar_plantilla_predeterminada()
    
    def verificar_permiso_edicion(self):
        """Verifica si se puede editar la plantilla actual"""
        if not self.es_predeterminada:
            messagebox.showwarning("Restricción", 
                                "Solo se puede modificar la plantilla predeterminada.\n"
                                "Para crear una nueva plantilla, use 'Copiar desde Predeterminado'.")
            return False
        return True
    
    def agregar_campo(self, campo_id):
        """Agrega un campo de datos al canvas"""
        if not self.verificar_permiso_edicion():
            return
        elemento = {
            'tipo': 'campo',
            'campo_id': campo_id,
            'x': 50,
            'y': 50,
            'ancho': 200,
            'alto': 20,
            'fuente': 'Arial',
            'tamano_fuente': 12,
            'negrita': False,
            'color': '#000000'
        }
        self.elementos.append(elemento)
        self.dibujar_elemento(elemento)
    
    def agregar_texto(self):
        """Agrega un texto estático al canvas"""
        if not self.verificar_permiso_edicion():
            return
        elemento = {
            'tipo': 'texto',
            'contenido': 'Texto',
            'x': 50,
            'y': 50,
            'ancho': 200,
            'alto': 20,
            'fuente': 'Arial',
            'tamano_fuente': 12,
            'negrita': False,
            'color': '#000000'
        }
        self.elementos.append(elemento)
        self.dibujar_elemento(elemento)
    
    def agregar_imagen(self):
        """Agrega una imagen al canvas"""
        if not self.verificar_permiso_edicion():
            return
        elemento = {
            'tipo': 'imagen',
            'ruta': '',
            'x': 50,
            'y': 50,
            'ancho': 100,
            'alto': 100
        }
        self.elementos.append(elemento)
        self.dibujar_elemento(elemento)
    
    def agregar_tabla(self):
        """Agrega una tabla de líneas al canvas"""
        if not self.verificar_permiso_edicion():
            return
        elemento = {
            'tipo': 'tabla',
            'x': 50,
            'y': 200,
            'ancho': 500,
            'alto': 300,
            'columnas': ['Concepto', 'Cantidad', 'Precio', 'Total']
        }
        self.elementos.append(elemento)
        self.dibujar_elemento(elemento)
    
    def dibujar_elemento(self, elemento):
        """Dibuja un elemento en el canvas"""
        x = elemento['x']
        y = elemento['y']
        ancho = elemento['ancho']
        alto = elemento.get('alto', 20)
        
        # Dibujar rectángulo del elemento
        rect_id = self.canvas.create_rectangle(x, y, x + ancho, y + alto, 
                                               outline='blue', width=2, tags='elemento')
        
        # Dibujar texto según el tipo
        if elemento['tipo'] == 'campo':
            texto = f"[{elemento['campo_id']}]"
        elif elemento['tipo'] == 'texto':
            texto = elemento.get('contenido', 'Texto')
        elif elemento['tipo'] == 'imagen':
            texto = '[Imagen]'
        elif elemento['tipo'] == 'tabla':
            texto = '[Tabla Líneas]'
        else:
            texto = '[Elemento]'
        
        text_id = self.canvas.create_text(x + 5, y + alto/2, anchor=tk.W, 
                                         text=texto, tags='elemento')
        
        # Guardar IDs en el elemento
        elemento['rect_id'] = rect_id
        elemento['text_id'] = text_id
        elemento['canvas_ids'] = [rect_id, text_id]
    
    def on_canvas_click(self, event):
        """Maneja clic en el canvas"""
        # Buscar elemento clickeado
        item = self.canvas.find_closest(event.x, event.y)
        if item:
            # Buscar elemento que contiene este item
            for elem in self.elementos:
                if item[0] in elem.get('canvas_ids', []):
                    self.seleccionar_elemento(elem)
                    return
        
        # Si no se clickeó ningún elemento, deseleccionar
        self.deseleccionar_elemento()
    
    def seleccionar_elemento(self, elemento):
        """Selecciona un elemento"""
        self.deseleccionar_elemento()
        self.elemento_seleccionado = elemento
        
        # Resaltar elemento seleccionado
        if 'rect_id' in elemento:
            self.canvas.itemconfig(elemento['rect_id'], outline='red', width=3)
        
        self.actualizar_propiedades()
    
    def deseleccionar_elemento(self):
        """Deselecciona el elemento actual"""
        if self.elemento_seleccionado and 'rect_id' in self.elemento_seleccionado:
            self.canvas.itemconfig(self.elemento_seleccionado['rect_id'], outline='blue', width=2)
        self.elemento_seleccionado = None
        self.actualizar_propiedades()
    
    def on_canvas_drag(self, event):
        """Maneja arrastre en el canvas"""
        if not self.es_predeterminada:
            return
        if self.elemento_seleccionado:
            # Mover elemento
            dx = event.x - self.elemento_seleccionado['x']
            dy = event.y - self.elemento_seleccionado['y']
            
            self.elemento_seleccionado['x'] = event.x
            self.elemento_seleccionado['y'] = event.y
            
            # Mover elementos visuales
            for canvas_id in self.elemento_seleccionado.get('canvas_ids', []):
                self.canvas.move(canvas_id, dx, dy)
    
    def on_canvas_release(self, event):
        """Maneja liberación del mouse"""
        pass
    
    def actualizar_propiedades(self):
        """Actualiza el panel de propiedades"""
        # Limpiar frame de propiedades
        for widget in self.propiedades_frame.winfo_children():
            widget.destroy()
        
        if not self.elemento_seleccionado:
            ttk.Label(self.propiedades_frame, text="Seleccione un elemento").pack(pady=20)
            return
        
        elem = self.elemento_seleccionado
        
        # Propiedades comunes
        ttk.Label(self.propiedades_frame, text="Posición X:").grid(row=0, column=0, sticky=tk.W, pady=5)
        x_var = tk.StringVar(value=str(elem['x']))
        ttk.Entry(self.propiedades_frame, textvariable=x_var, width=15).grid(row=0, column=1, pady=5)
        x_var.trace('w', lambda *args: self.actualizar_propiedad('x', x_var))
        
        ttk.Label(self.propiedades_frame, text="Posición Y:").grid(row=1, column=0, sticky=tk.W, pady=5)
        y_var = tk.StringVar(value=str(elem['y']))
        ttk.Entry(self.propiedades_frame, textvariable=y_var, width=15).grid(row=1, column=1, pady=5)
        y_var.trace('w', lambda *args: self.actualizar_propiedad('y', y_var))
        
        ttk.Label(self.propiedades_frame, text="Ancho:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ancho_var = tk.StringVar(value=str(elem['ancho']))
        ttk.Entry(self.propiedades_frame, textvariable=ancho_var, width=15).grid(row=2, column=1, pady=5)
        ancho_var.trace('w', lambda *args: self.actualizar_propiedad('ancho', ancho_var))
        
        # Propiedades específicas según tipo
        if elem['tipo'] == 'texto':
            ttk.Label(self.propiedades_frame, text="Texto:").grid(row=3, column=0, sticky=tk.W, pady=5)
            texto_var = tk.StringVar(value=elem.get('contenido', ''))
            ttk.Entry(self.propiedades_frame, textvariable=texto_var, width=15).grid(row=3, column=1, pady=5)
            texto_var.trace('w', lambda *args: self.actualizar_propiedad('contenido', texto_var))
        
        ttk.Button(self.propiedades_frame, text="🗑️ Eliminar", 
                  command=self.eliminar_elemento).grid(row=10, column=0, columnspan=2, pady=10)
    
    def actualizar_propiedad(self, propiedad, var):
        """Actualiza una propiedad del elemento seleccionado"""
        if not self.es_predeterminada:
            messagebox.showwarning("Restricción", "Solo se puede modificar la plantilla predeterminada.")
            return
        if not self.elemento_seleccionado:
            return
        
        try:
            valor = var.get()
            if propiedad in ['x', 'y', 'ancho', 'alto']:
                valor = int(valor)
            
            self.elemento_seleccionado[propiedad] = valor
            
            # Redibujar si cambió posición o tamaño
            if propiedad in ['x', 'y', 'ancho', 'alto']:
                self.redibujar_elemento(self.elemento_seleccionado)
        except:
            pass
    
    def redibujar_elemento(self, elemento):
        """Redibuja un elemento en el canvas"""
        # Eliminar elementos visuales antiguos
        for canvas_id in elemento.get('canvas_ids', []):
            self.canvas.delete(canvas_id)
        
        # Volver a dibujar
        self.dibujar_elemento(elemento)
    
    def eliminar_elemento(self):
        """Elimina el elemento seleccionado"""
        if not self.verificar_permiso_edicion():
            return
        if not self.elemento_seleccionado:
            return
        
        # Eliminar del canvas
        for canvas_id in self.elemento_seleccionado.get('canvas_ids', []):
            self.canvas.delete(canvas_id)
        
        # Eliminar de la lista
        self.elementos.remove(self.elemento_seleccionado)
        self.elemento_seleccionado = None
        self.actualizar_propiedades()
    
    def copiar_desde_predeterminado(self):
        """Crea una nueva plantilla copiando desde el predeterminado"""
        # Obtener plantilla predeterminada
        plantilla_pred = self.db.obtener_plantilla_predeterminada(self.tipo_plantilla)
        if not plantilla_pred:
            messagebox.showerror("Error", "No existe plantilla predeterminada para este tipo")
            return
        
        # Pedir nombre para la nueva plantilla
        nombre = tk.simpledialog.askstring("Nueva Plantilla", 
                                           "Nombre de la nueva plantilla (copiada desde predeterminada):")
        if not nombre:
            return
        
        # Cargar datos del predeterminado
        datos_pred = plantilla_pred.get('datos', '[]')
        
        # Crear nueva plantilla (NO predeterminada)
        try:
            nueva_id = self.db.crear_plantilla(nombre, self.tipo_plantilla, datos_pred, predeterminado=False)
            messagebox.showinfo("Éxito", f"Plantilla '{nombre}' creada correctamente")
            
            # Cargar la nueva plantilla
            nueva_plantilla = self.db.obtener_plantilla(nueva_id)
            if nueva_plantilla:
                self.cargar_plantilla_en_canvas(nueva_plantilla)
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear plantilla: {str(e)}")
    
    def cargar_plantilla_predeterminada(self):
        """Carga la plantilla predeterminada del tipo actual"""
        plantilla_pred = self.db.obtener_plantilla_predeterminada(self.tipo_plantilla)
        if plantilla_pred:
            self.cargar_plantilla_en_canvas(plantilla_pred)
        else:
            # Si no existe, crear una vacía
            self.elementos = []
            self.plantilla_actual_id = None
            self.es_predeterminada = False
            self.canvas.delete("all")
            self.actualizar_propiedades()
            self.actualizar_estado()
    
    def cargar_plantilla_en_canvas(self, plantilla: dict):
        """Carga una plantilla en el canvas"""
        self.plantilla_actual_id = plantilla['id']
        self.es_predeterminada = bool(plantilla.get('predeterminado', 0))
        
        # Limpiar canvas
        self.canvas.delete("all")
        self.elemento_seleccionado = None
        
        # Cargar elementos
        datos = plantilla.get('datos', '[]')
        try:
            self.elementos = json.loads(datos) if datos else []
        except:
            self.elementos = []
        
        # Dibujar elementos
        for elemento in self.elementos:
            self.dibujar_elemento(elemento)
        
        self.actualizar_propiedades()
        self.actualizar_estado()
    
    def actualizar_estado(self):
        """Actualiza el label de estado"""
        if self.es_predeterminada:
            self.estado_label.config(text="📌 PLANTILLA PREDETERMINADA (Editable)", foreground="green")
        elif self.plantilla_actual_id:
            self.estado_label.config(text="⚠️ Plantilla personalizada (Solo lectura)", foreground="orange")
        else:
            self.estado_label.config(text="", foreground="blue")
    
    def guardar_plantilla(self):
        """Guarda la plantilla actual (solo predeterminada)"""
        if not self.es_predeterminada:
            messagebox.showwarning("Restricción", 
                                "Solo se puede guardar la plantilla predeterminada.\n"
                                "Las plantillas personalizadas se guardan automáticamente al crearlas.")
            return
        
        if not self.plantilla_actual_id:
            messagebox.showerror("Error", "No hay plantilla predeterminada cargada")
            return
        
        # Convertir elementos a JSON
        datos_json = json.dumps(self.elementos)
        
        try:
            # Actualizar la plantilla predeterminada
            plantilla = self.db.obtener_plantilla(self.plantilla_actual_id)
            if plantilla:
                self.db.actualizar_plantilla(self.plantilla_actual_id, 
                                           plantilla['nombre'], 
                                           datos_json, 
                                           activa=True, 
                                           predeterminado=True)
                messagebox.showinfo("Éxito", "Plantilla predeterminada guardada correctamente")
            else:
                messagebox.showerror("Error", "No se encontró la plantilla predeterminada")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar plantilla: {str(e)}")
    
    def eliminar_plantilla_actual(self):
        """Elimina la plantilla actual (si no es predeterminada)"""
        if self.es_predeterminada:
            messagebox.showwarning("Restricción", "No se puede eliminar la plantilla predeterminada")
            return
        
        if not self.plantilla_actual_id:
            messagebox.showwarning("Advertencia", "No hay plantilla cargada para eliminar")
            return
        
        respuesta = messagebox.askyesno("Confirmar", 
                                       f"¿Está seguro de eliminar esta plantilla?\n"
                                       f"Esta acción no se puede deshacer.")
        if respuesta:
            try:
                self.db.eliminar_plantilla(self.plantilla_actual_id)
                messagebox.showinfo("Éxito", "Plantilla eliminada correctamente")
                # Volver a cargar la predeterminada
                self.cargar_plantilla_predeterminada()
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar plantilla: {str(e)}")
    
    def cargar_plantillas(self):
        """Carga la lista de plantillas (para referencia)"""
        pass  # Ya no se usa, se carga automáticamente la predeterminada
