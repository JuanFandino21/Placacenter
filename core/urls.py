from django.urls import path
from django.shortcuts import redirect
from .views import (
    signin_view, login_local_view, signup_view,
    principal_view, gestion_home_view, ventas_view,
    CategoriaListView, CategoriaCreateView, CategoriaUpdateView,
    ProveedorListView, ProveedorCreateView, ProveedorUpdateView,
    ProductoListView, ProductoCreateView, ProductoUpdateView,
    entrada_stock_view,
    # carrito
    cart_partial, cart_add, cart_dec, cart_remove, cart_empty, ventas_confirmar,
    # para inventario
    inventario_entradas_view, inventario_entradas_pdf,

    #reporte de ventas
    reporte_ventas_view,
)

urlpatterns = [
    path('', lambda r: redirect('principal') if r.user.is_authenticated else redirect('signin'), name='home'),

    # Auth local
    path('signin/', signin_view, name='signin'),
    path('signin/local/', login_local_view, name='login_local'),
    path('signup/', signup_view, name='signup'),

    # Principal
    path('principal/', principal_view, name='principal'),
    path('gestion/', gestion_home_view, name='gestion_home'),

    # Ventas
    path('ventas/', ventas_view, name='ventas'),
    path('ventas/', ventas_view, name='ventas_home'),

    # Carrito 
    path('ventas/cart/', cart_partial, name='cart_partial'),
    path('ventas/add/<int:producto_id>/', cart_add, name='cart_add'),
    path('ventas/dec/<int:producto_id>/', cart_dec, name='cart_dec'),
    path('ventas/remove/<int:producto_id>/', cart_remove, name='cart_remove'),
    path('ventas/empty/', cart_empty, name='cart_empty'),
    path('ventas/confirmar/', ventas_confirmar, name='ventas_confirmar'),
    

    # Gestión
    path('categorias/', CategoriaListView.as_view(), name='categorias_list'),
    path('categorias/nueva/', CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', CategoriaUpdateView.as_view(), name='categoria_update'),

    path('proveedores/', ProveedorListView.as_view(), name='proveedores_list'),
    path('proveedores/nuevo/', ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedores/<int:pk>/editar/', ProveedorUpdateView.as_view(), name='proveedor_update'),

    path('productos/', ProductoListView.as_view(), name='productos_list'),
    path('productos/nuevo/', ProductoCreateView.as_view(), name='producto_create'),
    path('productos/<int:pk>/editar/', ProductoUpdateView.as_view(), name='producto_update'),

    path('inventario/', inventario_entradas_view, name='inventario_entradas'),
    path('inventario/pdf/', inventario_entradas_pdf, name='inventario_entradas_pdf'),
    path('inventario/entrada/<int:producto_id>/', entrada_stock_view, name='entrada_stock'),
    
    #reporte de ventas
    path('reportes/ventas/', reporte_ventas_view, name='reporte_ventas'),
]