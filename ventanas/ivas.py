"""
Ventana de gestión de IVAs
"""
import tkinter as tk
from tkinter import ttk, messagebox
from database import Database


class VentanaIVAs:
    def __init__(self, parent, db: Database):
        self.parent = parent
        self.db = db
        
        # Solo establecer título y geometría si es una ventana Toplevel
        if isinstance(parent, tk.Toplevel):
            self.parent.title("Gestión de IVAs")
            self.parent.geometry("600x500")
        
        self.crear_interfaz()
        self.cargar_ivas()
    
    def crear_interfaz(self):
        """Crea la interfaz de la ventana"""
        # Frame principal
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame de formulario
        form_frame = ttk.LabelFrame(main_frame, text="Datos del IVA", padding="10")
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Campos del formulario
        ttk.Label(form_frame, text="Nombre:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.nombre_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.nombre_var, width=30).grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Porcentaje:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.porcentaje_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.porcentaje_var, width=30).grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Predeterminado:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.predeterminado_var = tk.BooleanVar()
        ttk.Checkbutton(form_frame, text="Marcar como IVA predeterminado", variable=self.predeterminado_var).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Botones del formulario
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Guardar", command=self.guardar_iva).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Nuevo", command=self.nuevo_iva).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self.eliminar_iva).pack(side=tk.LEFT, padx=5)
        
        self.iva_id_actual = None
        
        # Lista de IVAs
        list_frame = ttk.LabelFrame(main_frame, text="Lista de IVAs", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ("ID", "Nombre", "Porcentaje", "Activo", "Predeterminado")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.seleccionar_iva)
    
    def cargar_ivas(self):
        """Carga la lista de IVAs"""
        # Limpiar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Cargar IVAs
        ivas = self.db.obtener_ivas()
        for iva in ivas:
            self.tree.insert("", tk.END, values=(
                iva['id'],
                iva['nombre'],
                f"{iva['porcentaje']:.2f}%",
                "Sí" if iva['activo'] else "No",
                "Sí" if iva.get('predeterminado', 0) else "No"
            ))
    
    def nuevo_iva(self):
        """Limpia el formulario para crear un nuevo IVA"""
        self.iva_id_actual = None
        self.nombre_var.set("")
        self.porcentaje_var.set("")
        self.predeterminado_var.set(False)
    
    def guardar_iva(self):
        """Guarda o actualiza un IVA"""
        nombre = self.nombre_var.get().strip()
        porcentaje_str = self.porcentaje_var.get().strip()
        
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio")
            return
        
        try:
            porcentaje = float(porcentaje_str)
        except ValueError:
            messagebox.showerror("Error", "El porcentaje debe ser un número válido")
            return
        
        try:
            predeterminado = self.predeterminado_var.get()
            if self.iva_id_actual:
                # Actualizar
                self.db.actualizar_iva(self.iva_id_actual, nombre, porcentaje, predeterminado=predeterminado)
                messagebox.showinfo("Éxito", "IVA actualizado correctamente")
            else:
                # Crear nuevo
                self.db.crear_iva(nombre, porcentaje, predeterminado=predeterminado)
                messagebox.showinfo("Éxito", "IVA creado correctamente")
            
            self.cargar_ivas()
            self.nuevo_iva()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar IVA: {str(e)}")
    
    def eliminar_iva(self):
        """Elimina (desactiva) el IVA seleccionado"""
        if not self.iva_id_actual:
            messagebox.showwarning("Advertencia", "Seleccione un IVA para eliminar")
            return
        
        if messagebox.askyesno("Confirmar", "¿Está seguro de desactivar este IVA?"):
            try:
                self.db.eliminar_iva(self.iva_id_actual)
                messagebox.showinfo("Éxito", "IVA desactivado correctamente")
                self.cargar_ivas()
                self.nuevo_iva()
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar IVA: {str(e)}")
    
    def seleccionar_iva(self, event):
        """Carga los datos del IVA seleccionado en el formulario"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        iva_id = item['values'][0]
        
        iva = self.db.obtener_iva(iva_id)
        if iva:
            self.iva_id_actual = iva['id']
            self.nombre_var.set(iva['nombre'] or "")
            self.porcentaje_var.set(str(iva['porcentaje']))
            self.predeterminado_var.set(bool(iva.get('predeterminado', 0)))
