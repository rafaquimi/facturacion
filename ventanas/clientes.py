"""
Ventana de gestión de clientes
"""
import tkinter as tk
from tkinter import ttk, messagebox
from database import Database


class VentanaClientes:
    def __init__(self, parent, db: Database):
        self.parent = parent
        self.db = db
        
        # Solo establecer título y geometría si es una ventana Toplevel
        if isinstance(parent, tk.Toplevel):
            self.parent.title("Gestión de Clientes")
            self.parent.geometry("800x600")
        
        self.crear_interfaz()
        self.cargar_clientes()
    
    def cargar_ivas(self):
        """Carga la lista de IVAs activos en el combobox"""
        ivas = self.db.obtener_ivas(solo_activos=True)
        valores = ["(Ninguno)"] + [f"{iva['id']} - {iva['nombre']} ({iva['porcentaje']}%)" for iva in ivas]
        self.iva_combo['values'] = valores
    
    def crear_interfaz(self):
        """Crea la interfaz de la ventana"""
        # Frame principal
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame de formulario
        form_frame = ttk.LabelFrame(main_frame, text="Datos del Cliente", padding="10")
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Campos del formulario
        ttk.Label(form_frame, text="Nombre:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.nombre_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.nombre_var, width=40).grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="NIF:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.nif_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.nif_var, width=40).grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Dirección:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.direccion_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.direccion_var, width=40).grid(row=2, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Teléfono:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.telefono_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.telefono_var, width=40).grid(row=3, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Email:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_var, width=40).grid(row=4, column=1, pady=5, padx=5)
        
        # Botones del formulario
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Guardar", command=self.guardar_cliente).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Nuevo", command=self.nuevo_cliente).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self.eliminar_cliente).pack(side=tk.LEFT, padx=5)
        
        self.cliente_id_actual = None
        
        # Lista de clientes
        list_frame = ttk.LabelFrame(main_frame, text="Lista de Clientes", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ("ID", "Nombre", "NIF", "Dirección", "Teléfono", "Email")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.seleccionar_cliente)
    
    def cargar_clientes(self):
        """Carga la lista de clientes"""
        # Limpiar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Cargar clientes
        clientes = self.db.obtener_clientes()
        for cliente in clientes:
            self.tree.insert("", tk.END, values=(
                cliente['id'],
                cliente['nombre'],
                cliente['nif'] or '',
                cliente['direccion'] or '',
                cliente['telefono'] or '',
                cliente['email'] or ''
            ))
    
    def nuevo_cliente(self):
        """Limpia el formulario para crear un nuevo cliente"""
        self.cliente_id_actual = None
        self.nombre_var.set("")
        self.nif_var.set("")
        self.direccion_var.set("")
        self.telefono_var.set("")
        self.email_var.set("")
        self.iva_predeterminado_var.set("(Ninguno)")
    
    def guardar_cliente(self):
        """Guarda o actualiza un cliente"""
        nombre = self.nombre_var.get().strip()
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio")
            return
        
        try:
            # Obtener IVA predeterminado seleccionado
            iva_seleccionado = self.iva_predeterminado_var.get()
            iva_id = None
            if iva_seleccionado and iva_seleccionado != "(Ninguno)":
                try:
                    iva_id = int(iva_seleccionado.split(" - ")[0])
                except:
                    pass
            
            if self.cliente_id_actual:
                # Actualizar
                self.db.actualizar_cliente(
                    self.cliente_id_actual,
                    nombre,
                    self.nif_var.get().strip(),
                    self.direccion_var.get().strip(),
                    self.telefono_var.get().strip(),
                    self.email_var.get().strip(),
                    iva_predeterminado_id=iva_id
                )
                messagebox.showinfo("Éxito", "Cliente actualizado correctamente")
            else:
                # Crear nuevo
                self.db.crear_cliente(
                    nombre,
                    self.nif_var.get().strip(),
                    self.direccion_var.get().strip(),
                    self.telefono_var.get().strip(),
                    self.email_var.get().strip(),
                    iva_predeterminado_id=iva_id
                )
                messagebox.showinfo("Éxito", "Cliente creado correctamente")
            
            self.cargar_clientes()
            self.nuevo_cliente()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar cliente: {str(e)}")
    
    def eliminar_cliente(self):
        """Elimina el cliente seleccionado"""
        if not self.cliente_id_actual:
            messagebox.showwarning("Advertencia", "Seleccione un cliente para eliminar")
            return
        
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este cliente?"):
            try:
                self.db.eliminar_cliente(self.cliente_id_actual)
                messagebox.showinfo("Éxito", "Cliente eliminado correctamente")
                self.cargar_clientes()
                self.nuevo_cliente()
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar cliente: {str(e)}")
    
    def seleccionar_cliente(self, event):
        """Carga los datos del cliente seleccionado en el formulario"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        cliente_id = item['values'][0]
        
        cliente = self.db.obtener_cliente(cliente_id)
        if cliente:
            self.cliente_id_actual = cliente['id']
            self.nombre_var.set(cliente['nombre'] or "")
            self.nif_var.set(cliente['nif'] or "")
            self.direccion_var.set(cliente['direccion'] or "")
            self.telefono_var.set(cliente['telefono'] or "")
            self.email_var.set(cliente['email'] or "")
            
            # Cargar IVA predeterminado
            iva_id = cliente.get('iva_predeterminado_id')
            if iva_id:
                iva = self.db.obtener_iva(iva_id)
                if iva:
                    self.iva_predeterminado_var.set(f"{iva['id']} - {iva['nombre']} ({iva['porcentaje']}%)")
                else:
                    self.iva_predeterminado_var.set("(Ninguno)")
            else:
                self.iva_predeterminado_var.set("(Ninguno)")
