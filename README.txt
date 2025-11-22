# Placacenter – Sistema de gestión de inventario y ventas

Aplicación web para la ferretería **Placacenter**, que permite llevar control de inventario, registrar ventas con carrito, generar reportes por periodo y autenticarse usando **Google** a través de **Auth0**.

## Funcionalidades principales

- **Inventario**
  - Registro y edición de productos (nombre, SKU, categoría, proveedor, precios, stock).
  - Entradas de inventario manuales y por carga masiva desde CSV.
  - Cálculo automático de **costo promedio** y actualización de stock.
  - Configuración de **stock mínimo** por producto.

- **Ventas**
  - Búsqueda de productos por nombre o SKU.
  - Carrito de venta con actualización de totales en tiempo real.
  - Confirmación de venta con validación de stock.
  - Registro de movimientos de inventario tipo **SALIDA** por cada venta.

- **Reportes**
  - Reporte de ventas por periodo: **diario, semanal, mensual y anual**.
  - Totales por periodo: cantidad, total de venta, total costo y utilidad.
  - Exportación a PDF/CSV (según lo definido en el proyecto).

- **Autenticación**
  - Inicio de sesión con **Google** usando **Auth0**.
  - Manejo de usuarios basado en el sistema de autenticación de Django.

## Stack tecnológico

- **Backend:** Python 3.11, Django 5, Django REST Framework.
- **Base de datos:** PostgreSQL (servicio gestionado en Railway).
- **Autenticación externa:** Auth0 (login con Google).
- **Frontend:** Templates Django + HTML/CSS (estilo oscuro adaptado al cliente).
- **Despliegue:** Railway (Docker + Gunicorn + Whitenoise).
- **Control de versiones:** Git + GitHub.

---

## 1. Requisitos previos

Para ejecutar el proyecto en un equipo nuevo necesitas:

- Python **3.11** instalado.
- Git instalado.
- Acceso a:
  - El repositorio de GitHub.
  - Una base de datos PostgreSQL (local o en la nube, por ejemplo Railway).
  - Credenciales de Auth0 (dominio, client id, client secret y URLs de callback/logout).


## 2. Instalación y ejecución en local

### 2.1. Clonar el repositorio
git clone https://github.com/JuanFandino21/Placacenter.git
cd Placacenter

##3 Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

macOS / Linux (bash):
python3 -m venv .venv
source .venv/bin/activate

##4 instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

##5 Aplicar migraciones
python manage.py migrate

##6 Ejecutar el servidor de desarrollo
python manage.py runserver

luego abrir en el navegador
http://127.0.0.1:8000/