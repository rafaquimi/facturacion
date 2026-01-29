# Software de Facturación

Software de facturación sencillo para uso local en PC, desarrollado en Python con interfaz gráfica Tkinter.

## Características

- ✅ Gestión de clientes (crear, editar, eliminar)
- ✅ Configuración de tipos de IVA personalizados
- ✅ Creación y gestión de presupuestos
- ✅ Creación y gestión de facturas
- ✅ Creación automática de facturas desde presupuestos aceptados
- ✅ Generación de PDFs para presupuestos y facturas
- ✅ Impresión directa a impresora
- ✅ Base de datos SQLite local

## Requisitos

- Python 3.7 o superior
- Windows (también funciona en Linux y macOS con pequeñas modificaciones)

## Instalación

1. Clonar o descargar el proyecto

2. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Ejecutar la aplicación:
```bash
python main.py
```

2. La aplicación creará automáticamente:
   - Base de datos SQLite (`facturacion.db`)
   - Directorio `pdfs/` para almacenar los PDFs generados

## Estructura del Proyecto

```
Facturacion/
├── main.py                 # Aplicación principal
├── database.py             # Módulo de base de datos
├── pdf_generator.py        # Generador de PDFs
├── requirements.txt        # Dependencias
├── README.md              # Este archivo
├── ventanas/              # Módulos de ventanas
│   ├── __init__.py
│   ├── clientes.py        # Gestión de clientes
│   ├── ivas.py            # Gestión de IVAs
│   ├── presupuestos.py    # Gestión de presupuestos
│   └── facturas.py        # Gestión de facturas
└── pdfs/                  # Directorio de PDFs (se crea automáticamente)
```

## Funcionalidades Detalladas

### Gestión de Clientes
- Crear nuevos clientes con nombre, NIF, dirección, teléfono y email
- Editar clientes existentes
- Eliminar clientes
- Lista completa de todos los clientes

### Gestión de IVAs
- Crear tipos de IVA personalizados (nombre y porcentaje)
- Editar IVAs existentes
- Desactivar IVAs (no se eliminan para mantener integridad histórica)
- IVAs por defecto: General (21%), Reducido (10%), Superreducido (4%), Sin IVA (0%)

### Presupuestos
- Crear presupuestos asociados a clientes
- Agregar múltiples líneas con concepto, cantidad, precio, IVA y descuento
- Marcar presupuestos como aceptados
- Generar PDF del presupuesto
- Imprimir presupuesto directamente

### Facturas
- Crear facturas nuevas desde cero
- Crear facturas automáticamente desde presupuestos aceptados
- Agregar líneas manualmente
- Generar PDF de la factura
- Imprimir factura directamente

## Notas

- La base de datos se crea automáticamente en el directorio del proyecto
- Los PDFs se guardan en el directorio `pdfs/`
- Los números de presupuesto y factura se generan automáticamente (P000001, F000001, etc.)
- La impresión funciona abriendo el PDF con el visor predeterminado del sistema

## Licencia

Este software es de uso libre para fines educativos y comerciales.
