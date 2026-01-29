"""
Ventana de configuración de datos de la empresa
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import Database


class VentanaEmpresa:
    def __init__(self, parent, db: Database, master=None):
        self.parent = parent
        self.db = db
        
        self.parent.title("Datos de la Empresa")
        self.parent.geometry("600x550")
        
        # Establecer transient usando el master proporcionado
        # Solo establecer transient si se proporciona un master válido y diferente de parent
        if master and master != parent:
            try:
                self.parent.transient(master)
            except Exception:
                # Si falla, simplemente continuar sin transient
                pass
        
        self.parent.grab_set()
        
        # Crear interfaz primero (sin manejo de excepciones para ver errores)
        self.crear_interfaz()
        
        # Cargar datos después (con manejo de errores silencioso)
        try:
            self.cargar_datos()
        except Exception as e:
            # Si hay error al cargar, simplemente dejar los campos vacíos
            print(f"Error al cargar datos de empresa: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def crear_interfaz(self):
        """Crea la interfaz de la ventana"""
        # Inicializar variables primero
        self.nombre_var = tk.StringVar()
        self.nif_var = tk.StringVar()
        self.direccion_var = tk.StringVar()
        self.codigo_postal_var = tk.StringVar()
        self.localidad_var = tk.StringVar()
        self.provincia_var = tk.StringVar()
        self.telefono_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.web_var = tk.StringVar()
        self.logo_path_var = tk.StringVar()
        
        # Frame principal
        main_frame = ttk.Frame(self.parent, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = ttk.Label(main_frame, text="Datos de la Empresa", 
                          font=("Arial", 16, "bold"))
        titulo.pack(pady=(0, 20))
        
        # Formulario
        form_frame = ttk.LabelFrame(main_frame, text="Información de la Empresa", padding="15")
        form_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Campos del formulario
        row = 0
        
        ttk.Label(form_frame, text="Nombre/Razón Social *:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(form_frame, textvariable=self.nombre_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(form_frame, text="NIF/CIF:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(form_frame, textvariable=self.nif_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(form_frame, text="Dirección:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(form_frame, textvariable=self.direccion_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(form_frame, text="Código Postal:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(form_frame, textvariable=self.codigo_postal_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(form_frame, text="Localidad:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(form_frame, textvariable=self.localidad_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(form_frame, text="Provincia:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(form_frame, textvariable=self.provincia_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(form_frame, text="Teléfono:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(form_frame, textvariable=self.telefono_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(form_frame, text="Email:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(form_frame, textvariable=self.email_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(form_frame, text="Web:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(form_frame, textvariable=self.web_var, width=40).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        ttk.Label(form_frame, text="Logo (ruta):").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        logo_frame = ttk.Frame(form_frame)
        logo_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Entry(logo_frame, textvariable=self.logo_path_var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(logo_frame, text="Buscar...", command=self.seleccionar_logo).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        form_frame.columnconfigure(1, weight=1)
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(btn_frame, text="Guardar", command=self.guardar_datos).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.parent.destroy).pack(side=tk.LEFT, padx=5)
        
        # Forzar actualización de la ventana
        self.parent.update_idletasks()
    
    def seleccionar_logo(self):
        """Abre diálogo para seleccionar archivo de logo"""
        try:
            filename = filedialog.askopenfilename(
                title="Seleccionar Logo",
                filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Todos los archivos", "*.*")]
            )
            if filename:
                self.logo_path_var.set(filename)
        except Exception as e:
            messagebox.showerror("Error", f"Error al seleccionar archivo: {str(e)}")
    
    def cargar_datos(self):
        """Carga los datos de la empresa desde la base de datos"""
        try:
            datos = self.db.obtener_datos_empresa()
            
            self.nombre_var.set(datos.get('nombre', '') or '')
            self.nif_var.set(datos.get('nif', '') or '')
            self.direccion_var.set(datos.get('direccion', '') or '')
            self.codigo_postal_var.set(datos.get('codigo_postal', '') or '')
            self.localidad_var.set(datos.get('localidad', '') or '')
            self.provincia_var.set(datos.get('provincia', '') or '')
            self.telefono_var.set(datos.get('telefono', '') or '')
            self.email_var.set(datos.get('email', '') or '')
            self.web_var.set(datos.get('web', '') or '')
            self.logo_path_var.set(datos.get('logo_path', '') or '')
        except Exception as e:
            # Si hay error al cargar, simplemente dejar los campos vacíos
            print(f"Error al cargar datos de empresa: {str(e)}")
    
    def guardar_datos(self):
        """Guarda los datos de la empresa"""
        try:
            self.db.guardar_datos_empresa(
                nombre=self.nombre_var.get().strip(),
                nif=self.nif_var.get().strip(),
                direccion=self.direccion_var.get().strip(),
                codigo_postal=self.codigo_postal_var.get().strip(),
                localidad=self.localidad_var.get().strip(),
                provincia=self.provincia_var.get().strip(),
                telefono=self.telefono_var.get().strip(),
                email=self.email_var.get().strip(),
                web=self.web_var.get().strip(),
                logo_path=self.logo_path_var.get().strip()
            )
            messagebox.showinfo("Éxito", "Datos de la empresa guardados correctamente")
            self.parent.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar los datos: {str(e)}")
