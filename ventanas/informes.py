"""
Ventana de Informes - Generación de informes con filtros
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from database import Database
from pdf_generator import PDFGenerator
import os
import subprocess
import platform

try:
    from tkcalendar import DateEntry
    CALENDAR_AVAILABLE = True
except ImportError as e:
    CALENDAR_AVAILABLE = False
    print(f"tkcalendar no está disponible: {e}. Usando campos de texto para fechas.")
except Exception as e:
    CALENDAR_AVAILABLE = False
    print(f"Error al importar tkcalendar: {e}. Usando campos de texto para fechas.")


class VentanaInformes:
    def __init__(self, parent, db: Database, pdf_gen: PDFGenerator):
        self.parent = parent
        self.db = db
        self.pdf_gen = pdf_gen
        
        self.crear_interfaz()
        self.cargar_clientes()
    
    def crear_interfaz(self):
        """Crea la interfaz de informes"""
        # Frame principal
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo_frame = ttk.Frame(main_frame)
        titulo_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(titulo_frame, text="📊 Informes", font=("Arial", 18, "bold")).pack(side=tk.LEFT)
        
        # Frame de filtros
        filtros_frame = ttk.LabelFrame(main_frame, text="Filtros", padding="10")
        filtros_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Fila 1: Cliente
        ttk.Label(filtros_frame, text="Cliente:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.cliente_var = tk.StringVar()
        self.cliente_combo = ttk.Combobox(filtros_frame, textvariable=self.cliente_var, 
                                         state="readonly", width=40)
        self.cliente_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Button(filtros_frame, text="Todos", command=self.seleccionar_todos_clientes).grid(row=0, column=2, padx=5)
        
        # Fila 2: Fecha desde
        ttk.Label(filtros_frame, text="Fecha desde:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.fecha_desde_var = tk.StringVar()
        self.fecha_desde_cal = None
        
        # Intentar crear calendario
        try:
            from tkcalendar import DateEntry
            self.fecha_desde_cal = DateEntry(filtros_frame, 
                                             width=12, 
                                             background='darkblue',
                                             foreground='white', 
                                             borderwidth=2,
                                             date_pattern='yyyy-mm-dd')
            self.fecha_desde_cal.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
            # Sincronizar con StringVar cuando se selecciona una fecha
            self.fecha_desde_cal.bind("<<DateEntrySelected>>", 
                                     lambda e: self.fecha_desde_var.set(self.fecha_desde_cal.get_date().strftime("%Y-%m-%d")))
            # Establecer fecha inicial
            self.fecha_desde_var.set(self.fecha_desde_cal.get_date().strftime("%Y-%m-%d"))
        except Exception as e:
            print(f"Error creando calendario fecha desde: {e}")
            import traceback
            traceback.print_exc()
            self.fecha_desde_cal = None
            fecha_desde_entry = ttk.Entry(filtros_frame, textvariable=self.fecha_desde_var, width=15)
            fecha_desde_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
            ttk.Label(filtros_frame, text="(YYYY-MM-DD)", font=("Arial", 8)).grid(row=1, column=4, padx=5)
        
        fecha_desde_btns = ttk.Frame(filtros_frame)
        fecha_desde_btns.grid(row=1, column=2, columnspan=2, sticky=tk.W, padx=5)
        ttk.Button(fecha_desde_btns, text="Hoy", command=self.set_fecha_desde_hoy).pack(side=tk.LEFT, padx=2)
        ttk.Button(fecha_desde_btns, text="Mes", command=self.set_fecha_desde_mes).pack(side=tk.LEFT, padx=2)
        
        # Fila 3: Fecha hasta
        ttk.Label(filtros_frame, text="Fecha hasta:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        self.fecha_hasta_var = tk.StringVar()
        self.fecha_hasta_cal = None
        
        # Intentar crear calendario
        try:
            from tkcalendar import DateEntry
            self.fecha_hasta_cal = DateEntry(filtros_frame, 
                                             width=12, 
                                             background='darkblue',
                                             foreground='white', 
                                             borderwidth=2,
                                             date_pattern='yyyy-mm-dd')
            self.fecha_hasta_cal.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
            # Sincronizar con StringVar cuando se selecciona una fecha
            self.fecha_hasta_cal.bind("<<DateEntrySelected>>", 
                                     lambda e: self.fecha_hasta_var.set(self.fecha_hasta_cal.get_date().strftime("%Y-%m-%d")))
            # Establecer fecha inicial
            self.fecha_hasta_var.set(self.fecha_hasta_cal.get_date().strftime("%Y-%m-%d"))
        except Exception as e:
            print(f"Error creando calendario fecha hasta: {e}")
            import traceback
            traceback.print_exc()
            self.fecha_hasta_cal = None
            fecha_hasta_entry = ttk.Entry(filtros_frame, textvariable=self.fecha_hasta_var, width=15)
            fecha_hasta_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
            ttk.Label(filtros_frame, text="(YYYY-MM-DD)", font=("Arial", 8)).grid(row=2, column=4, padx=5)
        
        fecha_hasta_btns = ttk.Frame(filtros_frame)
        fecha_hasta_btns.grid(row=2, column=2, columnspan=2, sticky=tk.W, padx=5)
        ttk.Button(fecha_hasta_btns, text="Hoy", command=self.set_fecha_hasta_hoy).pack(side=tk.LEFT, padx=2)
        ttk.Button(fecha_hasta_btns, text="Limpiar", command=self.limpiar_filtros).pack(side=tk.LEFT, padx=2)
        
        # Fila 4: Tipo de documento
        ttk.Label(filtros_frame, text="Tipo:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
        self.tipo_var = tk.StringVar(value="Facturas")
        tipo_combo = ttk.Combobox(filtros_frame, textvariable=self.tipo_var,
                                  values=["Facturas", "Presupuestos"], 
                                  state="readonly", width=15)
        tipo_combo.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Fila 5: Estado
        ttk.Label(filtros_frame, text="Estado:").grid(row=4, column=0, sticky=tk.W, pady=5, padx=5)
        self.estado_var = tk.StringVar(value="Todos")
        estado_combo = ttk.Combobox(filtros_frame, textvariable=self.estado_var,
                                    values=["Todos", "Pendiente", "Aceptado", "Rechazado", "Pagado", "Vencido"], 
                                    state="readonly", width=15)
        estado_combo.grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Botones de acción
        acciones_frame = ttk.Frame(filtros_frame)
        acciones_frame.grid(row=5, column=0, columnspan=5, pady=10)
        
        ttk.Button(acciones_frame, text="🔍 Generar Informe", 
                  command=self.generar_informe, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(acciones_frame, text="📄 Exportar PDF", 
                  command=self.exportar_pdf, width=20).pack(side=tk.LEFT, padx=5)
        
        # Frame de resultados
        resultados_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
        resultados_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview para mostrar resultados
        columns = ("Tipo", "Número", "Cliente", "Fecha", "Bruto", "IVA", "Neto", "Estado")
        self.tree_resultados = ttk.Treeview(resultados_frame, columns=columns, show="headings", height=15)
        
        # Configurar columnas
        self.tree_resultados.heading("Tipo", text="Tipo")
        self.tree_resultados.heading("Número", text="Número")
        self.tree_resultados.heading("Cliente", text="Cliente")
        self.tree_resultados.heading("Fecha", text="Fecha")
        self.tree_resultados.heading("Bruto", text="Bruto")
        self.tree_resultados.heading("IVA", text="IVA")
        self.tree_resultados.heading("Neto", text="Neto")
        self.tree_resultados.heading("Estado", text="Estado")
        
        self.tree_resultados.column("Tipo", width=80)
        self.tree_resultados.column("Número", width=80)
        self.tree_resultados.column("Cliente", width=150)
        self.tree_resultados.column("Fecha", width=100)
        self.tree_resultados.column("Bruto", width=90)
        self.tree_resultados.column("IVA", width=90)
        self.tree_resultados.column("Neto", width=90)
        self.tree_resultados.column("Estado", width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(resultados_frame, orient=tk.VERTICAL, command=self.tree_resultados.yview)
        self.tree_resultados.configure(yscrollcommand=scrollbar.set)
        
        self.tree_resultados.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame de resumen (guardar referencia para poder limpiarlo)
        self.resumen_frame = ttk.LabelFrame(resultados_frame, text="Resumen", padding="10")
        self.resumen_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.resumen_label = ttk.Label(self.resumen_frame, 
                                       text="Total registros: 0 | Bruto: 0.00 € | IVA: 0.00 € | Neto: 0.00 €", 
                                       font=("Arial", 10, "bold"))
        self.resumen_label.pack()
    
    def cargar_clientes(self):
        """Carga la lista de clientes en el combobox"""
        clientes = self.db.obtener_clientes()
        clientes_list = ["Todos"] + [f"{c['id']} - {c['nombre']}" for c in clientes]
        self.cliente_combo['values'] = clientes_list
        self.cliente_combo.current(0)  # Seleccionar "Todos" por defecto
    
    def seleccionar_todos_clientes(self):
        """Selecciona todos los clientes"""
        self.cliente_combo.current(0)
    
    def set_fecha_desde_hoy(self):
        """Establece la fecha desde a hoy"""
        fecha_hoy = datetime.now().date()
        if self.fecha_desde_cal:
            self.fecha_desde_cal.set_date(fecha_hoy)
        self.fecha_desde_var.set(fecha_hoy.strftime("%Y-%m-%d"))
    
    def set_fecha_desde_mes(self):
        """Establece la fecha desde a hace un mes"""
        fecha_mes = (datetime.now() - timedelta(days=30)).date()
        if self.fecha_desde_cal:
            self.fecha_desde_cal.set_date(fecha_mes)
        self.fecha_desde_var.set(fecha_mes.strftime("%Y-%m-%d"))
    
    def set_fecha_hasta_hoy(self):
        """Establece la fecha hasta a hoy"""
        fecha_hoy = datetime.now().date()
        if self.fecha_hasta_cal:
            self.fecha_hasta_cal.set_date(fecha_hoy)
        self.fecha_hasta_var.set(fecha_hoy.strftime("%Y-%m-%d"))
    
    def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self.cliente_combo.current(0)
        self.fecha_desde_var.set("")
        self.fecha_hasta_var.set("")
        if self.fecha_desde_cal:
            self.fecha_desde_cal.set_date(datetime.now().date())
        if self.fecha_hasta_cal:
            self.fecha_hasta_cal.set_date(datetime.now().date())
        self.tipo_var.set("Facturas")
        self.estado_var.set("Todos")
        # Limpiar resultados
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        # Limpiar resumen
        for widget in self.resumen_frame.winfo_children():
            widget.destroy()
        self.resumen_label = ttk.Label(self.resumen_frame, 
                                       text="Total registros: 0 | Bruto: 0.00 € | IVA: 0.00 € | Neto: 0.00 €", 
                                       font=("Arial", 10, "bold"))
        self.resumen_label.pack()
    
    def generar_informe(self):
        """Genera el informe con los filtros aplicados"""
        # Obtener filtros
        cliente_id = None
        cliente_seleccionado = self.cliente_var.get()
        if cliente_seleccionado and cliente_seleccionado != "Todos":
            try:
                cliente_id = int(cliente_seleccionado.split(" - ")[0])
            except:
                pass
        
        # Obtener fechas del calendario o del StringVar
        if self.fecha_desde_cal:
            try:
                fecha_desde = self.fecha_desde_cal.get_date().strftime("%Y-%m-%d")
            except:
                fecha_desde = self.fecha_desde_var.get().strip()
        else:
            fecha_desde = self.fecha_desde_var.get().strip()
        
        if self.fecha_hasta_cal:
            try:
                fecha_hasta = self.fecha_hasta_cal.get_date().strftime("%Y-%m-%d")
            except:
                fecha_hasta = self.fecha_hasta_var.get().strip()
        else:
            fecha_hasta = self.fecha_hasta_var.get().strip()
        
        tipo = self.tipo_var.get()
        estado = self.estado_var.get()
        
        # Validar fechas
        if fecha_desde:
            try:
                datetime.strptime(fecha_desde, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha desde incorrecto. Use YYYY-MM-DD")
                return
        
        if fecha_hasta:
            try:
                datetime.strptime(fecha_hasta, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha hasta incorrecto. Use YYYY-MM-DD")
                return
        
        # Obtener datos filtrados
        resultados = []
        total_bruto = 0.0
        total_iva = 0.0
        total_neto = 0.0
        
        # Determinar si mostrar columna cliente (solo si no hay cliente específico seleccionado)
        mostrar_cliente = (cliente_seleccionado == "Todos" or not cliente_seleccionado)
        
        if tipo == "Facturas":
            facturas = self.db.obtener_facturas_filtradas(cliente_id, fecha_desde, fecha_hasta, estado)
            for f in facturas:
                bruto = float(f.get("bruto", 0) or 0)
                iva = float(f.get("iva", 0) or 0)
                neto = float(f.get("neto", 0) or 0)
                
                resultados.append({
                    "tipo": "Factura",
                    "numero": f.get("numero", ""),
                    "cliente": f.get("cliente_nombre", ""),
                    "fecha": f.get("fecha", ""),
                    "bruto": bruto,
                    "iva": iva,
                    "neto": neto,
                    "total": neto,  # Mantener para compatibilidad
                    "estado": f.get("estado", "")
                })
                total_bruto += bruto
                total_iva += iva
                total_neto += neto
        
        elif tipo == "Presupuestos":
            presupuestos = self.db.obtener_presupuestos_filtrados(cliente_id, fecha_desde, fecha_hasta, estado)
            for p in presupuestos:
                bruto = float(p.get("bruto", 0) or 0)
                iva = float(p.get("iva", 0) or 0)
                neto = float(p.get("neto", 0) or 0)
                
                resultados.append({
                    "tipo": "Presupuesto",
                    "numero": p.get("numero", ""),
                    "cliente": p.get("cliente_nombre", ""),
                    "fecha": p.get("fecha", ""),
                    "bruto": bruto,
                    "iva": iva,
                    "neto": neto,
                    "total": neto,  # Mantener para compatibilidad
                    "estado": p.get("estado", "")
                })
                total_bruto += bruto
                total_iva += iva
                total_neto += neto
        
        # Ordenar por fecha descendente
        resultados.sort(key=lambda x: x["fecha"], reverse=True)
        
        # Limpiar treeview
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        
        # Configurar columnas según si hay cliente seleccionado
        if mostrar_cliente:
            # Mostrar todas las columnas incluyendo cliente
            columns_visibles = ("Tipo", "Número", "Cliente", "Fecha", "Bruto", "IVA", "Neto", "Estado")
            for col in columns_visibles:
                self.tree_resultados.column(col, width=120 if col != "Cliente" else 150, stretch=False)
        else:
            # Ocultar columna cliente
            self.tree_resultados.column("Cliente", width=0, stretch=False, minwidth=0)
            self.tree_resultados.heading("Cliente", text="")
        
        # Mostrar resultados
        for r in resultados:
            if mostrar_cliente:
                valores = (
                    r["tipo"],
                    r["numero"],
                    r["cliente"],
                    r["fecha"],
                    f"{r['bruto']:.2f} €",
                    f"{r['iva']:.2f} €",
                    f"{r['neto']:.2f} €",
                    r["estado"]
                )
            else:
                valores = (
                    r["tipo"],
                    r["numero"],
                    "",  # Cliente vacío pero columna existe
                    r["fecha"],
                    f"{r['bruto']:.2f} €",
                    f"{r['iva']:.2f} €",
                    f"{r['neto']:.2f} €",
                    r["estado"]
                )
            self.tree_resultados.insert("", tk.END, values=valores)
        
        # Actualizar resumen con recuadro más vistoso
        for widget in self.resumen_frame.winfo_children():
            widget.destroy()
        
        # Crear recuadro de resumen más vistoso
        resumen_inner = ttk.Frame(self.resumen_frame)
        resumen_inner.pack(fill=tk.X, padx=5, pady=5)
        
        # Título del resumen
        ttk.Label(resumen_inner, text="RESUMEN DEL INFORME", 
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Totales en grid
        totales_frame = ttk.Frame(resumen_inner)
        totales_frame.pack()
        
        # Fila 1: Total registros
        ttk.Label(totales_frame, text="Total de registros:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Label(totales_frame, text=f"{len(resultados)}", font=("Arial", 10)).grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Fila 2: Bruto
        ttk.Label(totales_frame, text="Total Bruto:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Label(totales_frame, text=f"{total_bruto:.2f} €", font=("Arial", 10)).grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Fila 3: IVA
        ttk.Label(totales_frame, text="Total IVA:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Label(totales_frame, text=f"{total_iva:.2f} €", font=("Arial", 10)).grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Fila 4: Neto (destacado)
        ttk.Label(totales_frame, text="Total Neto:", font=("Arial", 11, "bold")).grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Label(totales_frame, text=f"{total_neto:.2f} €", 
                 font=("Arial", 11, "bold"), foreground="blue").grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Guardar referencia al label para poder actualizarlo
        self.resumen_label = resumen_inner
        
        # Guardar resultados para exportar PDF
        self.resultados_actuales = resultados
        self.mostrar_cliente = mostrar_cliente
        self.filtros_aplicados = {
            "cliente_id": cliente_id,
            "cliente_nombre": cliente_seleccionado if cliente_seleccionado != "Todos" else "Todos",
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "tipo": tipo,
            "estado": estado,
            "bruto": total_bruto,
            "iva": total_iva,
            "neto": total_neto,
            "total": total_neto  # Mantener para compatibilidad
        }
    
    def exportar_pdf(self):
        """Exporta el informe a PDF"""
        if not hasattr(self, 'resultados_actuales') or not self.resultados_actuales:
            messagebox.showwarning("Advertencia", "Primero debe generar un informe")
            return
        
        try:
            # Asegurar que el directorio pdfs existe
            pdfs_dir = "pdfs"
            if not os.path.exists(pdfs_dir):
                os.makedirs(pdfs_dir)
            
            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(pdfs_dir, f"informe_{timestamp}.pdf")
            filename_abs = os.path.abspath(filename)
            
            # Generar PDF
            self.pdf_gen.generar_informe(
                self.resultados_actuales,
                self.filtros_aplicados,
                filename_abs
            )
            
            # Abrir el explorador de archivos
            if platform.system() == 'Windows':
                try:
                    subprocess.run(['explorer', '/select,', filename_abs], check=False, timeout=5)
                    messagebox.showinfo("PDF Generado", 
                        f"Informe PDF generado correctamente: {filename}\n\n"
                        f"El explorador de archivos se ha abierto con el archivo seleccionado.")
                except Exception as e1:
                    messagebox.showinfo("PDF Generado", 
                        f"Informe PDF generado correctamente: {filename}\n\n"
                        f"Ubicación: {filename_abs}")
            else:
                messagebox.showinfo("PDF Generado", 
                    f"Informe PDF generado correctamente: {filename}\n\n"
                    f"Ubicación: {filename_abs}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF: {str(e)}")
            import traceback
            traceback.print_exc()
