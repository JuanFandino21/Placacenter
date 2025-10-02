from django.contrib import admin
from .models import Categoria, Proveedor, Producto, MovimientoInventario

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "nit", "telefono")
    search_fields = ("nombre", "nit")

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "codigo_producto", "categoria", "precio_venta", "stock", "stock_minimo", "activo")
    list_filter = ("categoria", "activo")
    search_fields = ("nombre", "codigo_producto")

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ("id", "producto", "tipo", "cantidad", "costo_unitario", "fecha")
    list_filter = ("tipo", "producto")
    search_fields = ("producto__nombre", "producto__codigo_producto")
