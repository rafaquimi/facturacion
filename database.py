"""
Módulo de gestión de base de datos SQLite
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class Database:
    def __init__(self, db_path: str = "facturacion.db"):
        """Inicializa la conexión a la base de datos"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Obtiene una conexión a la base de datos"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Crea las tablas necesarias si no existen"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                nif TEXT,
                direccion TEXT,
                telefono TEXT,
                email TEXT,
                iva_predeterminado_id INTEGER,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (iva_predeterminado_id) REFERENCES ivas(id)
            )
        """)
        
        # Tabla de IVAs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ivas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                porcentaje REAL NOT NULL,
                activo INTEGER DEFAULT 1,
                predeterminado INTEGER DEFAULT 0
            )
        """)
        
        # Agregar columnas si no existen (para bases de datos existentes)
        try:
            cursor.execute("ALTER TABLE clientes ADD COLUMN iva_predeterminado_id INTEGER")
        except sqlite3.OperationalError:
            pass  # La columna ya existe
        
        try:
            cursor.execute("ALTER TABLE ivas ADD COLUMN predeterminado INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # La columna ya existe
        
        # Tabla de presupuestos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS presupuestos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT UNIQUE NOT NULL,
                cliente_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                estado TEXT DEFAULT 'pendiente',
                observaciones TEXT,
                total REAL DEFAULT 0,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        """)
        
        # Tabla de líneas de presupuesto
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS presupuesto_lineas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                presupuesto_id INTEGER NOT NULL,
                concepto TEXT NOT NULL,
                cantidad REAL NOT NULL,
                precio_unitario REAL NOT NULL,
                iva_id INTEGER,
                descuento REAL DEFAULT 0,
                FOREIGN KEY (presupuesto_id) REFERENCES presupuestos(id),
                FOREIGN KEY (iva_id) REFERENCES ivas(id)
            )
        """)
        
        # Tabla de facturas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT UNIQUE NOT NULL,
                cliente_id INTEGER NOT NULL,
                presupuesto_id INTEGER,
                fecha TEXT NOT NULL,
                estado TEXT DEFAULT 'pendiente',
                observaciones TEXT,
                total REAL DEFAULT 0,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                FOREIGN KEY (presupuesto_id) REFERENCES presupuestos(id)
            )
        """)
        
        # Tabla de líneas de factura
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS factura_lineas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factura_id INTEGER NOT NULL,
                concepto TEXT NOT NULL,
                cantidad REAL NOT NULL,
                precio_unitario REAL NOT NULL,
                iva_id INTEGER,
                descuento REAL DEFAULT 0,
                FOREIGN KEY (factura_id) REFERENCES facturas(id),
                FOREIGN KEY (iva_id) REFERENCES ivas(id)
            )
        """)
        
        # Tabla de datos de la empresa (solo un registro)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresa (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                nombre TEXT,
                nif TEXT,
                direccion TEXT,
                codigo_postal TEXT,
                localidad TEXT,
                provincia TEXT,
                telefono TEXT,
                email TEXT,
                web TEXT,
                logo_path TEXT
            )
        """)
        
        # Tabla de plantillas de documentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plantillas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL,
                activa INTEGER DEFAULT 1,
                predeterminado INTEGER DEFAULT 0,
                datos TEXT,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Agregar columna predeterminado si no existe
        try:
            cursor.execute("ALTER TABLE plantillas ADD COLUMN predeterminado INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # La columna ya existe
        
        conn.commit()
        conn.close()
        
        # Insertar IVAs por defecto si no existen
        self._init_default_ivas()
        
        # Crear plantillas predeterminadas si no existen
        self._init_default_plantillas()
    
    def _init_default_ivas(self):
        """Inserta IVAs por defecto si no existen"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM ivas")
        if cursor.fetchone()[0] == 0:
            ivas_default = [
                ("IVA General", 21.0, 1),  # El primero es predeterminado
                ("IVA Reducido", 10.0, 0),
                ("IVA Superreducido", 4.0, 0),
                ("Sin IVA", 0.0, 0)
            ]
            cursor.executemany(
                "INSERT INTO ivas (nombre, porcentaje, predeterminado) VALUES (?, ?, ?)",
                ivas_default
            )
            conn.commit()
        
        conn.close()
    
    def _init_default_plantillas(self):
        """Crea plantillas predeterminadas si no existen"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Verificar si ya existen plantillas predeterminadas
        cursor.execute("SELECT COUNT(*) FROM plantillas WHERE predeterminado = 1 AND tipo = 'factura'")
        if cursor.fetchone()[0] == 0:
            # Crear plantilla predeterminada "General" para facturas
            # Si está vacía (datos = "[]"), el sistema usará el método original
            cursor.execute("""
                INSERT INTO plantillas (nombre, tipo, activa, predeterminado, datos)
                VALUES (?, ?, ?, ?, ?)
            """, ("General", "factura", 1, 1, "[]"))
        
        cursor.execute("SELECT COUNT(*) FROM plantillas WHERE predeterminado = 1 AND tipo = 'presupuesto'")
        if cursor.fetchone()[0] == 0:
            # Crear plantilla predeterminada "General" para presupuestos
            # Si está vacía (datos = "[]"), el sistema usará el método original
            cursor.execute("""
                INSERT INTO plantillas (nombre, tipo, activa, predeterminado, datos)
                VALUES (?, ?, ?, ?, ?)
            """, ("General", "presupuesto", 1, 1, "[]"))
        
        conn.commit()
        conn.close()
    
    # ========== CLIENTES ==========
    def crear_cliente(self, nombre: str, nif: str = "", direccion: str = "", 
                     telefono: str = "", email: str = "", iva_predeterminado_id: int = None) -> int:
        """Crea un nuevo cliente y devuelve su ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clientes (nombre, nif, direccion, telefono, email, iva_predeterminado_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, nif, direccion, telefono, email, iva_predeterminado_id))
        conn.commit()
        cliente_id = cursor.lastrowid
        conn.close()
        return cliente_id
    
    def obtener_clientes(self) -> List[Dict]:
        """Obtiene todos los clientes"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes ORDER BY nombre")
        clientes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return clientes
    
    def obtener_cliente(self, cliente_id: int) -> Optional[Dict]:
        """Obtiene un cliente por ID"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def actualizar_cliente(self, cliente_id: int, nombre: str, nif: str = "",
                          direccion: str = "", telefono: str = "", email: str = "", 
                          iva_predeterminado_id: int = None):
        """Actualiza un cliente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clientes 
            SET nombre = ?, nif = ?, direccion = ?, telefono = ?, email = ?, iva_predeterminado_id = ?
            WHERE id = ?
        """, (nombre, nif, direccion, telefono, email, iva_predeterminado_id, cliente_id))
        conn.commit()
        conn.close()
    
    def eliminar_cliente(self, cliente_id: int):
        """Elimina un cliente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        conn.commit()
        conn.close()
    
    # ========== IVAs ==========
    def crear_iva(self, nombre: str, porcentaje: float, predeterminado: bool = False) -> int:
        """Crea un nuevo IVA y devuelve su ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Si se marca como predeterminado, quitar predeterminado de los demás
        if predeterminado:
            cursor.execute("UPDATE ivas SET predeterminado = 0")
        cursor.execute("""
            INSERT INTO ivas (nombre, porcentaje, predeterminado)
            VALUES (?, ?, ?)
        """, (nombre, porcentaje, 1 if predeterminado else 0))
        conn.commit()
        iva_id = cursor.lastrowid
        conn.close()
        return iva_id
    
    def obtener_ivas(self, solo_activos: bool = False) -> List[Dict]:
        """Obtiene todos los IVAs"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if solo_activos:
            cursor.execute("SELECT * FROM ivas WHERE activo = 1 ORDER BY porcentaje DESC")
        else:
            cursor.execute("SELECT * FROM ivas ORDER BY porcentaje DESC")
        ivas = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return ivas
    
    def obtener_iva(self, iva_id: int) -> Optional[Dict]:
        """Obtiene un IVA por ID"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ivas WHERE id = ?", (iva_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def actualizar_iva(self, iva_id: int, nombre: str, porcentaje: float, activo: bool = True, predeterminado: bool = False):
        """Actualiza un IVA"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Si se marca como predeterminado, quitar predeterminado de los demás
        if predeterminado:
            cursor.execute("UPDATE ivas SET predeterminado = 0 WHERE id != ?", (iva_id,))
        cursor.execute("""
            UPDATE ivas 
            SET nombre = ?, porcentaje = ?, activo = ?, predeterminado = ?
            WHERE id = ?
        """, (nombre, porcentaje, 1 if activo else 0, 1 if predeterminado else 0, iva_id))
        conn.commit()
        conn.close()
    
    def eliminar_iva(self, iva_id: int):
        """Elimina un IVA (marca como inactivo)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE ivas SET activo = 0, predeterminado = 0 WHERE id = ?", (iva_id,))
        conn.commit()
        conn.close()
    
    def obtener_iva_predeterminado(self) -> Optional[Dict]:
        """Obtiene el IVA predeterminado (el marcado como predeterminado)"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ivas WHERE predeterminado = 1 AND activo = 1 LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    # ========== PRESUPUESTOS ==========
    def obtener_siguiente_numero_presupuesto(self) -> str:
        """Obtiene el siguiente número de presupuesto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(CAST(SUBSTR(numero, 2) AS INTEGER)) FROM presupuestos WHERE numero LIKE 'P%'")
        result = cursor.fetchone()[0]
        conn.close()
        siguiente = (result or 0) + 1
        return f"P{siguiente:06d}"
    
    def crear_presupuesto(self, cliente_id: int, fecha: str, observaciones: str = "") -> int:
        """Crea un nuevo presupuesto y devuelve su ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        numero = self.obtener_siguiente_numero_presupuesto()
        cursor.execute("""
            INSERT INTO presupuestos (numero, cliente_id, fecha, observaciones)
            VALUES (?, ?, ?, ?)
        """, (numero, cliente_id, fecha, observaciones))
        conn.commit()
        presupuesto_id = cursor.lastrowid
        conn.close()
        return presupuesto_id
    
    def agregar_linea_presupuesto(self, presupuesto_id: int, concepto: str,
                                  cantidad: float, precio_unitario: float,
                                  iva_id: int = None, descuento: float = 0):
        """Agrega una línea a un presupuesto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO presupuesto_lineas 
            (presupuesto_id, concepto, cantidad, precio_unitario, iva_id, descuento)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (presupuesto_id, concepto, cantidad, precio_unitario, iva_id, descuento))
        conn.commit()
        self._actualizar_total_presupuesto(presupuesto_id)
        conn.close()
    
    def actualizar_linea_presupuesto(self, linea_id: int, concepto: str,
                                     cantidad: float, precio_unitario: float,
                                     iva_id: int = None, descuento: float = 0):
        """Actualiza una línea de presupuesto existente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT presupuesto_id FROM presupuesto_lineas WHERE id = ?", (linea_id,))
        resultado = cursor.fetchone()
        if not resultado:
            conn.close()
            return
        
        presupuesto_id = resultado[0]
        cursor.execute("""
            UPDATE presupuesto_lineas 
            SET concepto = ?, cantidad = ?, precio_unitario = ?, iva_id = ?, descuento = ?
            WHERE id = ?
        """, (concepto, cantidad, precio_unitario, iva_id, descuento, linea_id))
        conn.commit()
        self._actualizar_total_presupuesto(presupuesto_id)
        conn.close()
    
    def _actualizar_total_presupuesto(self, presupuesto_id: int):
        """Actualiza el total de un presupuesto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM((cantidad * precio_unitario * (1 - descuento/100)) * 
                      (1 + COALESCE((SELECT porcentaje FROM ivas WHERE id = iva_id), 0)/100))
            FROM presupuesto_lineas
            WHERE presupuesto_id = ?
        """, (presupuesto_id,))
        total = cursor.fetchone()[0] or 0
        cursor.execute("UPDATE presupuestos SET total = ? WHERE id = ?", (total, presupuesto_id))
        conn.commit()
        conn.close()
    
    def obtener_presupuestos(self) -> List[Dict]:
        """Obtiene todos los presupuestos con información de facturación"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, c.nombre as cliente_nombre,
                   CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END as facturado,
                   f.numero as factura_numero
            FROM presupuestos p
            JOIN clientes c ON p.cliente_id = c.id
            LEFT JOIN facturas f ON f.presupuesto_id = p.id
            ORDER BY p.fecha DESC, p.numero DESC
        """)
        presupuestos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return presupuestos
    
    def obtener_presupuestos_aceptados_no_facturados(self) -> List[Dict]:
        """Obtiene presupuestos aceptados que aún no han sido facturados"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, c.nombre as cliente_nombre
            FROM presupuestos p
            JOIN clientes c ON p.cliente_id = c.id
            LEFT JOIN facturas f ON f.presupuesto_id = p.id
            WHERE p.estado = 'aceptado' AND f.id IS NULL
            ORDER BY p.fecha DESC, p.numero DESC
        """)
        presupuestos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return presupuestos
    
    def presupuesto_esta_facturado(self, presupuesto_id: int) -> bool:
        """Verifica si un presupuesto ya ha sido facturado"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM facturas WHERE presupuesto_id = ?", (presupuesto_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def obtener_presupuesto(self, presupuesto_id: int) -> Optional[Dict]:
        """Obtiene un presupuesto con sus líneas"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, c.nombre as cliente_nombre, c.nif, c.direccion, c.telefono, c.email
            FROM presupuestos p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = ?
        """, (presupuesto_id,))
        presupuesto = cursor.fetchone()
        if presupuesto:
            presupuesto = dict(presupuesto)
            cursor.execute("""
                SELECT pl.*, i.nombre as iva_nombre, i.porcentaje as iva_porcentaje
                FROM presupuesto_lineas pl
                LEFT JOIN ivas i ON pl.iva_id = i.id
                WHERE pl.presupuesto_id = ?
            """, (presupuesto_id,))
            presupuesto['lineas'] = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return presupuesto
    
    def eliminar_linea_presupuesto(self, linea_id: int):
        """Elimina una línea de presupuesto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT presupuesto_id FROM presupuesto_lineas WHERE id = ?", (linea_id,))
        presupuesto_id = cursor.fetchone()[0]
        cursor.execute("DELETE FROM presupuesto_lineas WHERE id = ?", (linea_id,))
        conn.commit()
        self._actualizar_total_presupuesto(presupuesto_id)
        conn.close()
    
    def aceptar_presupuesto(self, presupuesto_id: int):
        """Marca un presupuesto como aceptado"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE presupuestos SET estado = 'aceptado' WHERE id = ?", (presupuesto_id,))
        conn.commit()
        conn.close()
    
    # ========== FACTURAS ==========
    def obtener_siguiente_numero_factura(self) -> str:
        """Obtiene el siguiente número de factura"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(CAST(SUBSTR(numero, 2) AS INTEGER)) FROM facturas WHERE numero LIKE 'F%'")
        result = cursor.fetchone()[0]
        conn.close()
        siguiente = (result or 0) + 1
        return f"F{siguiente:06d}"
    
    def crear_factura_desde_presupuesto(self, presupuesto_id: int, fecha: str, observaciones: str = "") -> int:
        """Crea una factura desde un presupuesto aceptado"""
        presupuesto = self.obtener_presupuesto(presupuesto_id)
        if not presupuesto:
            raise ValueError("Presupuesto no encontrado")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        numero = self.obtener_siguiente_numero_factura()
        cursor.execute("""
            INSERT INTO facturas (numero, cliente_id, presupuesto_id, fecha, observaciones)
            VALUES (?, ?, ?, ?, ?)
        """, (numero, presupuesto['cliente_id'], presupuesto_id, fecha, observaciones))
        factura_id = cursor.lastrowid
        
        # Copiar líneas del presupuesto a la factura
        print(f"DEBUG: Copiando {len(presupuesto.get('lineas', []))} líneas del presupuesto {presupuesto_id} a la factura {factura_id}")
        for linea in presupuesto.get('lineas', []):
            print(f"DEBUG: Insertando línea - concepto: {linea.get('concepto')}, cantidad: {linea.get('cantidad')}, precio: {linea.get('precio_unitario')}, iva_id: {linea.get('iva_id')}, descuento: {linea.get('descuento')}")
            cursor.execute("""
                INSERT INTO factura_lineas 
                (factura_id, concepto, cantidad, precio_unitario, iva_id, descuento)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (factura_id, 
                  linea.get('concepto', ''),
                  linea.get('cantidad', 0) or 0,
                  linea.get('precio_unitario', 0) or 0,
                  linea.get('iva_id'),
                  linea.get('descuento', 0) or 0))
        
        conn.commit()
        self._actualizar_total_factura(factura_id)
        conn.close()
        return factura_id
    
    def crear_factura(self, cliente_id: int, fecha: str, observaciones: str = "") -> int:
        """Crea una nueva factura vacía"""
        conn = self.get_connection()
        cursor = conn.cursor()
        numero = self.obtener_siguiente_numero_factura()
        cursor.execute("""
            INSERT INTO facturas (numero, cliente_id, fecha, observaciones)
            VALUES (?, ?, ?, ?)
        """, (numero, cliente_id, fecha, observaciones))
        conn.commit()
        factura_id = cursor.lastrowid
        conn.close()
        return factura_id
    
    def agregar_linea_factura(self, factura_id: int, concepto: str,
                             cantidad: float, precio_unitario: float,
                             iva_id: int = None, descuento: float = 0):
        """Agrega una línea a una factura"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO factura_lineas 
            (factura_id, concepto, cantidad, precio_unitario, iva_id, descuento)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (factura_id, concepto, cantidad, precio_unitario, iva_id, descuento))
        conn.commit()
        self._actualizar_total_factura(factura_id)
        conn.close()
    
    def actualizar_linea_factura(self, linea_id: int, concepto: str,
                                 cantidad: float, precio_unitario: float,
                                 iva_id: int = None, descuento: float = 0):
        """Actualiza una línea de factura existente"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT factura_id FROM factura_lineas WHERE id = ?", (linea_id,))
        resultado = cursor.fetchone()
        if not resultado:
            conn.close()
            return
        
        factura_id = resultado[0]
        cursor.execute("""
            UPDATE factura_lineas 
            SET concepto = ?, cantidad = ?, precio_unitario = ?, iva_id = ?, descuento = ?
            WHERE id = ?
        """, (concepto, cantidad, precio_unitario, iva_id, descuento, linea_id))
        conn.commit()
        self._actualizar_total_factura(factura_id)
        conn.close()
    
    def _actualizar_total_factura(self, factura_id: int):
        """Actualiza el total de una factura"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM((cantidad * precio_unitario * (1 - descuento/100)) * 
                      (1 + COALESCE((SELECT porcentaje FROM ivas WHERE id = iva_id), 0)/100))
            FROM factura_lineas
            WHERE factura_id = ?
        """, (factura_id,))
        total = cursor.fetchone()[0] or 0
        cursor.execute("UPDATE facturas SET total = ? WHERE id = ?", (total, factura_id))
        conn.commit()
        conn.close()
    
    def obtener_facturas(self) -> List[Dict]:
        """Obtiene todas las facturas"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, c.nombre as cliente_nombre
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            ORDER BY f.fecha DESC, f.numero DESC
        """)
        facturas = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return facturas
    
    def obtener_factura(self, factura_id: int) -> Optional[Dict]:
        """Obtiene una factura con sus líneas"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, c.nombre as cliente_nombre, c.nif, c.direccion, c.telefono, c.email
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.id = ?
        """, (factura_id,))
        factura = cursor.fetchone()
        if factura:
            factura = dict(factura)
            cursor.execute("""
                SELECT fl.*, i.nombre as iva_nombre, i.porcentaje as iva_porcentaje
                FROM factura_lineas fl
                LEFT JOIN ivas i ON fl.iva_id = i.id
                WHERE fl.factura_id = ?
            """, (factura_id,))
            factura['lineas'] = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return factura
    
    def eliminar_linea_factura(self, linea_id: int):
        """Elimina una línea de factura"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT factura_id FROM factura_lineas WHERE id = ?", (linea_id,))
        factura_id = cursor.fetchone()[0]
        cursor.execute("DELETE FROM factura_lineas WHERE id = ?", (linea_id,))
        conn.commit()
        self._actualizar_total_factura(factura_id)
        conn.close()
    
    # ========== EMPRESA ==========
    def obtener_datos_empresa(self) -> Dict:
        """Obtiene los datos de la empresa"""
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM empresa WHERE id = 1")
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            else:
                # Retornar estructura vacía si no hay datos
                return {
                    'id': None,
                    'nombre': '',
                    'nif': '',
                    'direccion': '',
                    'codigo_postal': '',
                    'localidad': '',
                    'provincia': '',
                    'telefono': '',
                    'email': '',
                    'web': '',
                    'logo_path': ''
                }
        except sqlite3.OperationalError as e:
            # Si la tabla no existe, crearla y retornar estructura vacía
            if "no such table" in str(e).lower():
                self._crear_tabla_empresa()
                return {
                    'id': None,
                    'nombre': '',
                    'nif': '',
                    'direccion': '',
                    'codigo_postal': '',
                    'localidad': '',
                    'provincia': '',
                    'telefono': '',
                    'email': '',
                    'web': '',
                    'logo_path': ''
                }
            else:
                raise
        except Exception as e:
            # En caso de cualquier otro error, retornar estructura vacía
            print(f"Error al obtener datos de empresa: {str(e)}")
            return {
                'id': None,
                'nombre': '',
                'nif': '',
                'direccion': '',
                'codigo_postal': '',
                'localidad': '',
                'provincia': '',
                'telefono': '',
                'email': '',
                'web': '',
                'logo_path': ''
            }
    
    def _crear_tabla_empresa(self):
        """Crea la tabla empresa si no existe"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresa (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                nombre TEXT,
                nif TEXT,
                direccion TEXT,
                codigo_postal TEXT,
                localidad TEXT,
                provincia TEXT,
                telefono TEXT,
                email TEXT,
                web TEXT,
                logo_path TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def guardar_datos_empresa(self, nombre: str = "", nif: str = "", direccion: str = "",
                              codigo_postal: str = "", localidad: str = "", provincia: str = "",
                              telefono: str = "", email: str = "", web: str = "", logo_path: str = ""):
        """Guarda o actualiza los datos de la empresa"""
        try:
            # Asegurar que la tabla existe
            self._crear_tabla_empresa()
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Verificar si existe un registro
            cursor.execute("SELECT COUNT(*) FROM empresa WHERE id = 1")
            existe = cursor.fetchone()[0] > 0
            
            if existe:
                cursor.execute("""
                    UPDATE empresa SET
                        nombre = ?, nif = ?, direccion = ?, codigo_postal = ?,
                        localidad = ?, provincia = ?, telefono = ?, email = ?,
                        web = ?, logo_path = ?
                    WHERE id = 1
                """, (nombre, nif, direccion, codigo_postal, localidad, provincia, telefono, email, web, logo_path))
            else:
                cursor.execute("""
                    INSERT INTO empresa (id, nombre, nif, direccion, codigo_postal,
                                       localidad, provincia, telefono, email, web, logo_path)
                    VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (nombre, nif, direccion, codigo_postal, localidad, provincia, telefono, email, web, logo_path))
            
            conn.commit()
            conn.close()
        except Exception as e:
            conn.close()
            raise Exception(f"Error al guardar datos de empresa: {str(e)}")
    
    # ========== PLANTILLAS ==========
    def crear_plantilla(self, nombre: str, tipo: str, datos: str, predeterminado: bool = False) -> int:
        """Crea una nueva plantilla y devuelve su ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Si se marca como predeterminado, quitar predeterminado de los demás del mismo tipo
        if predeterminado:
            cursor.execute("UPDATE plantillas SET predeterminado = 0 WHERE tipo = ?", (tipo,))
        cursor.execute("""
            INSERT INTO plantillas (nombre, tipo, datos, predeterminado)
            VALUES (?, ?, ?, ?)
        """, (nombre, tipo, datos, 1 if predeterminado else 0))
        conn.commit()
        plantilla_id = cursor.lastrowid
        conn.close()
        return plantilla_id
    
    def obtener_plantillas(self, tipo: str = None, solo_activas: bool = False) -> List[Dict]:
        """Obtiene todas las plantillas, opcionalmente filtradas por tipo"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if tipo:
            if solo_activas:
                cursor.execute("SELECT * FROM plantillas WHERE tipo = ? AND activa = 1 ORDER BY nombre", (tipo,))
            else:
                cursor.execute("SELECT * FROM plantillas WHERE tipo = ? ORDER BY nombre", (tipo,))
        else:
            if solo_activas:
                cursor.execute("SELECT * FROM plantillas WHERE activa = 1 ORDER BY nombre")
            else:
                cursor.execute("SELECT * FROM plantillas ORDER BY nombre")
        
        plantillas = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return plantillas
    
    def obtener_plantilla(self, plantilla_id: int) -> Optional[Dict]:
        """Obtiene una plantilla por ID"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM plantillas WHERE id = ?", (plantilla_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def obtener_plantilla_predeterminada(self, tipo: str) -> Optional[Dict]:
        """Obtiene la plantilla predeterminada para un tipo"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM plantillas WHERE tipo = ? AND predeterminado = 1 LIMIT 1", (tipo,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def actualizar_plantilla(self, plantilla_id: int, nombre: str, datos: str, activa: bool = True, predeterminado: bool = False):
        """Actualiza una plantilla"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Si se marca como predeterminado, quitar predeterminado de los demás del mismo tipo
        if predeterminado:
            cursor.execute("SELECT tipo FROM plantillas WHERE id = ?", (plantilla_id,))
            tipo = cursor.fetchone()[0]
            cursor.execute("UPDATE plantillas SET predeterminado = 0 WHERE tipo = ? AND id != ?", (tipo, plantilla_id))
        cursor.execute("""
            UPDATE plantillas 
            SET nombre = ?, datos = ?, activa = ?, predeterminado = ?
            WHERE id = ?
        """, (nombre, datos, 1 if activa else 0, 1 if predeterminado else 0, plantilla_id))
        conn.commit()
        conn.close()
    
    def eliminar_plantilla(self, plantilla_id: int):
        """Elimina una plantilla"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM plantillas WHERE id = ?", (plantilla_id,))
        conn.commit()
        conn.close()
