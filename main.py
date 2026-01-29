"""
Software de Facturación - Aplicación Principal
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
from database import Database
from pdf_generator import PDFGenerator
from ventanas.clientes import VentanaClientes
from ventanas.ivas import VentanaIVAs
from ventanas.presupuestos import VentanaPresupuestos
from ventanas.facturas import VentanaFacturas
from ventanas.empresa import VentanaEmpresa
from ventanas.disenador_plantillas import VentanaDisenadorPlantillas


class AppFacturacion:
    def __init__(self, root):
        self.root = root
        self.root.title("Software de Facturación")
        self.root.geometry("1200x800")
        
        # Inicializar base de datos y generador de PDFs
        self.db = Database()
        self.pdf_gen = PDFGenerator(db=self.db)
        
        # Crear directorio para PDFs si no existe
        if not os.path.exists("pdfs"):
            os.makedirs("pdfs")
        
        # Pestañas activas (para evitar duplicados)
        self.pestanas_activas = {}  # {nombre: (frame, tab_id, ventana_instancia)}
        self.notebook = None
        self._notebook_click_binded = False
        
        self.crear_menu()
        self.crear_interfaz()
    
    def crear_menu(self):
        """Crea la barra de menú"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        menu_archivo = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=menu_archivo)
        menu_archivo.add_command(label="Salir", command=self.root.quit)
        
        # Menú Gestión
        menu_gestion = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Gestión", menu=menu_gestion)
        menu_gestion.add_command(label="Datos de la Empresa", command=self.abrir_empresa)
        menu_gestion.add_separator()
        menu_gestion.add_command(label="Clientes", command=self.abrir_clientes)
        menu_gestion.add_command(label="IVAs", command=self.abrir_ivas)
        
        # Menú Documentos
        menu_documentos = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Documentos", menu=menu_documentos)
        menu_documentos.add_command(label="Presupuestos", command=self.abrir_presupuestos)
        menu_documentos.add_command(label="Facturas", command=self.abrir_facturas)
    
    def crear_interfaz(self):
        """Crea la interfaz principal con sistema de paneles"""
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        # Barra de herramientas superior
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Botones de navegación con iconos
        ttk.Button(toolbar_frame, text="📋 Presupuestos", 
                   command=lambda: self.mostrar_panel("presupuestos"), width=18).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="🧾 Facturas", 
                   command=lambda: self.mostrar_panel("facturas"), width=18).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="👥 Clientes", 
                   command=lambda: self.mostrar_panel("clientes"), width=18).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="💰 IVAs", 
                   command=lambda: self.mostrar_panel("ivas"), width=18).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="🏢 Empresa", 
                   command=self.abrir_empresa, width=18).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="🎨 Diseñador", 
                   command=self.abrir_disenador, width=18).pack(side=tk.LEFT, padx=2)
        
        # Separador
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Notebook para pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Bind evento para cuando se cambia de pestaña
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    
    def crear_pestana_con_cerrar(self, frame, texto):
        """Crea un frame con botón de cerrar para usar como pestaña personalizada"""
        frame_pestana = ttk.Frame(self.notebook)
        
        label = ttk.Label(frame_pestana, text=texto, padding="5 2")
        label.pack(side=tk.LEFT)
        
        btn_cerrar = ttk.Button(frame_pestana, text="✕", width=2, 
                                command=lambda: self.cerrar_pestana_por_frame(frame))
        btn_cerrar.pack(side=tk.LEFT, padx=(5, 0))
        
        return frame_pestana
    
    def mostrar_panel(self, nombre_panel):
        """Muestra una pestaña específica, evitando duplicados"""
        # Mapeo de nombres a textos de pestaña
        nombres_pestanas = {
            "presupuestos": "📋 Presupuestos",
            "facturas": "🧾 Facturas",
            "clientes": "👥 Clientes",
            "ivas": "💰 IVAs"
        }
        
        texto_pestana = nombres_pestanas.get(nombre_panel, nombre_panel.capitalize())
        
        # Si la pestaña ya existe, cambiar el foco a ella
        if nombre_panel in self.pestanas_activas:
            frame, tab_id, ventana_instancia = self.pestanas_activas[nombre_panel]
            
            # Si tab_id es None, intentar encontrarlo por el frame
            if tab_id is None:
                try:
                    tabs = self.notebook.tabs()
                    for tab in tabs:
                        try:
                            tab_widget = self.notebook.nametowidget(tab)
                            if tab_widget == frame:
                                tab_id = tab
                                # Actualizar el tab_id en pestanas_activas
                                self.pestanas_activas[nombre_panel] = (frame, tab_id, ventana_instancia)
                                break
                        except:
                            pass
                except:
                    pass
            
            # Seleccionar la pestaña existente con múltiples métodos de respaldo
            seleccionado = False
            
            # Método 1: Intentar seleccionar por tab_id directamente (más directo)
            if tab_id is not None:
                try:
                    self.notebook.select(tab_id)
                    self.root.update_idletasks()
                    self.root.update()
                    seleccionado = True
                except Exception as e:
                    print(f"Error seleccionando por tab_id: {e}")
            
            # Método 2: Si falla, obtener el índice y seleccionar por índice
            if not seleccionado and tab_id is not None:
                try:
                    index = self.notebook.index(tab_id)
                    if index is not None and index >= 0:
                        self.notebook.select(index)
                        self.root.update_idletasks()
                        self.root.update()
                        seleccionado = True
                except Exception as e:
                    print(f"Error seleccionando por índice: {e}")
            
            # Método 3: Si todo falla, buscar recorriendo todas las pestañas comparando frames
            if not seleccionado:
                try:
                    tabs = self.notebook.tabs()
                    for i, tab in enumerate(tabs):
                        try:
                            tab_widget = self.notebook.nametowidget(tab)
                            if tab_widget == frame:
                                self.notebook.select(i)
                                self.root.update_idletasks()
                                self.root.update()
                                seleccionado = True
                                break
                        except:
                            pass
                except Exception as e:
                    print(f"Error buscando pestaña por frame: {e}")
            
            if seleccionado:
                # Si es la pestaña de presupuestos, refrescar el grid explícitamente
                if nombre_panel == "presupuestos" and ventana_instancia:
                    # Llamar directamente al método de la instancia
                    self.root.after(50, lambda v=ventana_instancia: v.cargar_presupuestos())
                    self.root.after(200, lambda v=ventana_instancia: v.cargar_presupuestos())
            else:
                print(f"ERROR: No se pudo seleccionar la pestaña {nombre_panel}")
            
            return
        
        # Crear contenedor principal para la pestaña
        contenedor_principal = ttk.Frame(self.notebook)
        
        # Crear frame para el contenido
        nuevo_frame = ttk.Frame(contenedor_principal)
        nuevo_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear el contenido según el tipo y guardar la instancia
        ventana_instancia = None
        if nombre_panel == "presupuestos":
            ventana_instancia = VentanaPresupuestos(nuevo_frame, self.db, self.pdf_gen)
        elif nombre_panel == "facturas":
            ventana_instancia = VentanaFacturas(nuevo_frame, self.db, self.pdf_gen)
        elif nombre_panel == "clientes":
            ventana_instancia = VentanaClientes(nuevo_frame, self.db)
        elif nombre_panel == "ivas":
            ventana_instancia = VentanaIVAs(nuevo_frame, self.db)
        
        # Agregar pestaña al notebook con X al inicio
        texto_con_x = f"✕ {texto_pestana}"
        self.notebook.add(contenedor_principal, text=texto_con_x)
        
        # Obtener el tab_id después de agregar (notebook.add puede devolver None, así que lo obtenemos de otra forma)
        tabs = self.notebook.tabs()
        tab_id = tabs[-1] if tabs else None  # El último tab agregado
        print(f"DEBUG: Pestaña {nombre_panel} creada con tab_id: {tab_id}")
        
        # Guardar referencia (usar contenedor_principal como frame y la instancia de la ventana)
        self.pestanas_activas[nombre_panel] = (contenedor_principal, tab_id, ventana_instancia)
        print(f"DEBUG: Pestaña guardada en pestanas_activas: {nombre_panel} -> tab_id: {tab_id}")
        
        # Bind eventos para detectar clic en el X de la pestaña (solo una vez)
        if not self._notebook_click_binded:
            self.notebook.bind("<Button-1>", self.on_notebook_click)
            self.notebook.bind("<ButtonRelease-1>", self.on_notebook_release)
            self._notebook_click_binded = True
        
        # Seleccionar la nueva pestaña (forzar selección)
        try:
            # Obtener el índice de la nueva pestaña
            index = self.notebook.index(tab_id)
            if index is not None and index >= 0:
                self.notebook.select(index)
            else:
                self.notebook.select(tab_id)
        except:
            # Si falla, intentar seleccionar directamente
            try:
                self.notebook.select(tab_id)
            except:
                pass
        
        # Forzar actualización para asegurar que se vea la selección
        self.root.update_idletasks()
        self.root.update()
    
    def refrescar_presupuestos(self, frame):
        """Refresca el grid de presupuestos en el frame dado"""
        # Esta función ya no se usa porque ahora tenemos referencia directa a la instancia
        # Se mantiene por compatibilidad pero debería usar ventana_instancia.cargar_presupuestos() directamente
        pass
    
    def on_tab_changed(self, event=None):
        """Se ejecuta cuando se cambia de pestaña"""
        try:
            # Obtener la pestaña seleccionada
            selected_tab = self.notebook.select()
            if not selected_tab:
                return
            
            # Obtener el widget de la pestaña seleccionada
            try:
                selected_widget = self.notebook.nametowidget(selected_tab)
            except:
                return
            
            # Buscar qué pestaña corresponde comparando los widgets directamente
            for nombre_panel, (frame, tab_id, ventana_instancia) in self.pestanas_activas.items():
                # Comparar el widget del frame (que es contenedor_principal) con el widget seleccionado
                # El frame puede estar dentro de contenedor_principal, así que buscamos recursivamente
                if self._widgets_iguales(selected_widget, frame) or self._widget_contiene(selected_widget, frame):
                    # Si es la pestaña de presupuestos, refrescar el grid directamente desde la instancia
                    if nombre_panel == "presupuestos" and ventana_instancia:
                        # Usar un pequeño delay para asegurar que la pestaña esté completamente visible
                        self.root.after(100, lambda v=ventana_instancia: v.cargar_presupuestos())
                    break
        except Exception as e:
            print(f"Error en on_tab_changed: {e}")
            import traceback
            traceback.print_exc()
    
    def _widgets_iguales(self, widget1, widget2):
        """Compara si dos widgets son el mismo"""
        try:
            return str(widget1) == str(widget2)
        except:
            return False
    
    def _widget_contiene(self, contenedor, widget_buscado):
        """Verifica si el contenedor contiene el widget buscado"""
        try:
            if str(contenedor) == str(widget_buscado):
                return True
            for child in contenedor.winfo_children():
                if self._widget_contiene(child, widget_buscado):
                    return True
            return False
        except:
            return False
    
    # Ya no necesitamos estos métodos porque usamos un botón real
    # def on_notebook_click(self, event):
    #     """Guarda la posición del clic para procesar en release"""
    #     self._notebook_click_x = event.x
    #     self._notebook_click_y = event.y
    
    def on_notebook_click(self, event):
        """Guarda la posición del clic para procesar en release"""
        self._notebook_click_x = event.x
        self._notebook_click_y = event.y
    
    def on_notebook_release(self, event):
        """Detecta clic en el área del X del encabezado de la pestaña (X al inicio)"""
        try:
            # Usar las coordenadas guardadas del click
            x = getattr(self, '_notebook_click_x', event.x)
            y = getattr(self, '_notebook_click_y', event.y)
            
            # Verificar que el clic fue en el área de tabs (no en el contenido)
            elemento = self.notebook.identify(x, y)
            if elemento != "label":
                return
            
            # Obtener el índice de la pestaña clickeada
            try:
                index = self.notebook.index(f"@{x},{y}")
            except:
                return
            
            if index is None or index < 0:
                return
            
            # Obtener el tab_id de la pestaña clickeada
            tabs = self.notebook.tabs()
            if index >= len(tabs):
                return
            
            tab_id_clickeado = tabs[index]
            
            # Calcular la posición x acumulada de las pestañas anteriores
            # Usar valores más conservadores y realistas
            tab_x_acumulado = 0
            for i in range(index):
                try:
                    texto_anterior = self.notebook.tab(tabs[i], "text")
                    # Estimar ancho más conservador: 6px por carácter normal, 11px por emoji, menos padding
                    caracteres_normales = len([c for c in texto_anterior if ord(c) < 0x1F000])
                    caracteres_especiales = len(texto_anterior) - caracteres_normales
                    ancho_anterior = caracteres_normales * 6 + caracteres_especiales * 11 + 18
                    tab_x_acumulado += ancho_anterior
                    print(f"DEBUG: Pestaña {i}: texto='{texto_anterior}', ancho={ancho_anterior}, tab_x_acumulado={tab_x_acumulado}")
                except Exception as e:
                    tab_x_acumulado += 120  # Fallback más conservador
                    print(f"DEBUG: Error calculando pestaña {i}: {e}")
            
            # El área del X está en los primeros 45 píxeles de la pestaña (donde está el ✕ al inicio)
            # Área más grande para facilitar el clic
            area_x_inicio = tab_x_acumulado
            area_x_fin = tab_x_acumulado + 45  # Primeros 45 píxeles
            
            print(f"DEBUG: Pestaña {index}, tab_x_acumulado={tab_x_acumulado}, área X: {area_x_inicio}-{area_x_fin}, clic en x={x}")
            
            # Verificar si el clic está en el área del X (al inicio de la pestaña)
            # Permitir un margen negativo más grande para facilitar el clic
            # Si el clic está cerca del área X (dentro de 20 píxeles antes), también cerrar
            if (area_x_inicio - 20) <= x <= area_x_fin:
                # Buscar la pestaña correspondiente y cerrarla
                for nombre_panel, (frame, tab_id, ventana_instancia) in self.pestanas_activas.items():
                    if str(tab_id) == str(tab_id_clickeado) or tab_id == tab_id_clickeado:
                        self.cerrar_pestana_por_nombre(nombre_panel)
                        return "break"
        except Exception as e:
            print(f"Error detectando clic en X: {e}")
            import traceback
            traceback.print_exc()
    
    def cerrar_pestana_actual(self):
        """Cierra la pestaña actualmente seleccionada"""
        seleccionado = self.notebook.select()
        if not seleccionado:
            return
        
        # Encontrar qué pestaña está seleccionada
        nombre_panel = None
        for nombre, (frame, tab_id, ventana_instancia) in self.pestanas_activas.items():
            if str(tab_id) == seleccionado:
                nombre_panel = nombre
                break
        
        if nombre_panel:
            self.cerrar_pestana_por_nombre(nombre_panel)
    
    def cerrar_pestana_por_nombre(self, nombre_panel):
        """Cierra una pestaña por su nombre"""
        print(f"DEBUG: cerrar_pestana_por_nombre llamado con: {nombre_panel}")
        print(f"DEBUG: Pestañas activas: {list(self.pestanas_activas.keys())}")
        
        if nombre_panel in self.pestanas_activas:
            frame, tab_id, ventana_instancia = self.pestanas_activas[nombre_panel]
            print(f"DEBUG: Pestaña encontrada - frame: {frame}, tab_id: {tab_id}")
            
            # Si tab_id es None, intentar encontrarlo por el frame
            if tab_id is None:
                print(f"DEBUG: tab_id es None, buscando por frame...")
                try:
                    # Buscar el tab_id comparando frames
                    tabs = self.notebook.tabs()
                    for tab in tabs:
                        try:
                            tab_widget = self.notebook.nametowidget(tab)
                            if tab_widget == frame:
                                tab_id = tab
                                print(f"DEBUG: tab_id encontrado por frame: {tab_id}")
                                # Actualizar el tab_id en pestanas_activas
                                self.pestanas_activas[nombre_panel] = (frame, tab_id, ventana_instancia)
                                break
                        except:
                            pass
                except Exception as e:
                    print(f"DEBUG: Error buscando tab_id por frame: {e}")
            
            if tab_id is None:
                print(f"ERROR: No se pudo encontrar tab_id para la pestaña {nombre_panel}")
                return
            
            try:
                # Obtener el índice antes de eliminar
                index = self.notebook.index(tab_id)
                print(f"DEBUG: Índice de la pestaña: {index}")
                
                # Eliminar la pestaña
                print(f"DEBUG: Intentando eliminar pestaña con tab_id: {tab_id}")
                self.notebook.forget(tab_id)
                print(f"DEBUG: Pestaña eliminada del notebook")
                del self.pestanas_activas[nombre_panel]
                print(f"DEBUG: Pestaña eliminada de pestanas_activas")
                
                # Si había otras pestañas, seleccionar una
                print(f"DEBUG: Pestañas restantes: {len(self.pestanas_activas)}")
                if len(self.pestanas_activas) > 0:
                    # Intentar seleccionar la pestaña que estaba antes (si existe)
                    try:
                        if index > 0:
                            # Seleccionar la pestaña anterior
                            nueva_index = index - 1
                            print(f"DEBUG: Seleccionando pestaña anterior con índice: {nueva_index}")
                            if nueva_index >= 0:
                                self.notebook.select(nueva_index)
                            else:
                                # Si no hay anterior, seleccionar la primera
                                print(f"DEBUG: Seleccionando primera pestaña (índice 0)")
                                self.notebook.select(0)
                        else:
                            # Si era la primera, seleccionar la nueva primera
                            print(f"DEBUG: Era la primera, seleccionando nueva primera (índice 0)")
                            self.notebook.select(0)
                    except Exception as e:
                        print(f"DEBUG: Error seleccionando por índice: {e}")
                        # Si falla, seleccionar la primera pestaña disponible
                        try:
                            primera_pestana = list(self.pestanas_activas.values())[0]
                            primera_frame, primera_tab_id, primera_ventana = primera_pestana
                            print(f"DEBUG: Seleccionando primera pestaña disponible con tab_id: {primera_tab_id}")
                            self.notebook.select(primera_tab_id)
                        except Exception as e2:
                            print(f"DEBUG: Error seleccionando primera pestaña: {e2}")
                            pass
                else:
                    print(f"DEBUG: No hay más pestañas, no se selecciona ninguna")
            except Exception as e:
                # Si falla, intentar eliminar directamente
                try:
                    self.notebook.forget(tab_id)
                    del self.pestanas_activas[nombre_panel]
                    # Seleccionar la primera pestaña disponible si hay alguna
                    if len(self.pestanas_activas) > 0:
                        try:
                            primera_pestana = list(self.pestanas_activas.values())[0]
                            primera_frame, primera_tab_id, primera_ventana = primera_pestana
                            self.notebook.select(primera_tab_id)
                        except:
                            pass
                except:
                    pass
    
    def cerrar_pestana_por_frame(self, frame):
        """Cierra una pestaña por su frame"""
        # Buscar el nombre de la pestaña por su frame
        for nombre, (frame_pestana, tab_id, ventana_instancia) in self.pestanas_activas.items():
            if frame_pestana == frame:
                self.cerrar_pestana_por_nombre(nombre)
                return
    
    def cerrar_pestana(self, texto_pestana):
        """Cierra una pestaña por su texto (usado por el botón X en la pestaña)"""
        # Encontrar la pestaña por su texto
        nombre_panel = None
        nombres_pestanas = {
            "presupuestos": "📋 Presupuestos",
            "facturas": "🧾 Facturas",
            "clientes": "👥 Clientes",
            "ivas": "💰 IVAs"
        }
        
        for nombre, texto in nombres_pestanas.items():
            if texto == texto_pestana:
                nombre_panel = nombre
                break
        
        if nombre_panel:
            self.cerrar_pestana_por_nombre(nombre_panel)
    
    def abrir_clientes(self):
        """Muestra el panel de gestión de clientes"""
        self.mostrar_panel("clientes")
    
    def abrir_empresa(self):
        """Abre la ventana de configuración de datos de la empresa (pop-up modal)"""
        ventana = tk.Toplevel(self.root)
        VentanaEmpresa(ventana, self.db, master=self.root)
    
    def abrir_disenador(self):
        """Abre la ventana del diseñador de plantillas"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Diseñador de Plantillas")
        ventana.geometry("1200x800")
        ventana.transient(self.root)
        
        VentanaDisenadorPlantillas(ventana, self.db)
    
    def abrir_ivas(self):
        """Muestra el panel de gestión de IVAs"""
        self.mostrar_panel("ivas")
    
    def abrir_presupuestos(self):
        """Muestra el panel de gestión de presupuestos"""
        self.mostrar_panel("presupuestos")
    
    def abrir_facturas(self):
        """Muestra el panel de gestión de facturas"""
        self.mostrar_panel("facturas")


if __name__ == "__main__":
    root = tk.Tk()
    app = AppFacturacion(root)
    # Almacenar referencia global a la app para acceso desde otras ventanas
    root._app_facturacion = app
    root.mainloop()
