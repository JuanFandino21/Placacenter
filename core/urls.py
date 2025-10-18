from django.urls import path
from django.shortcuts import redirect
from .views import (
    signin_view,
    CategoriaListView, CategoriaCreateView, CategoriaUpdateView,
    ProveedorListView, ProveedorCreateView, ProveedorUpdateView,
    ProductoListView, ProductoCreateView, ProductoUpdateView,
    entrada_stock_view,
)

urlpatterns = [
    path('', lambda r: redirect('productos_list') if r.user.is_authenticated else redirect('signin'), name='home'),
    path('signin/', signin_view, name='signin'),

    path('categorias/', CategoriaListView.as_view(), name='categorias_list'),
    path('categorias/nueva/', CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', CategoriaUpdateView.as_view(), name='categoria_update'),

    path('proveedores/', ProveedorListView.as_view(), name='proveedores_list'),
    path('proveedores/nuevo/', ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedores/<int:pk>/editar/', ProveedorUpdateView.as_view(), name='proveedor_update'),

    path('productos/', ProductoListView.as_view(), name='productos_list'),
    path('productos/nuevo/', ProductoCreateView.as_view(), name='producto_create'),
    path('productos/<int:pk>/editar/', ProductoUpdateView.as_view(), name='producto_update'),

    path('inventario/entrada/<int:producto_id>/', entrada_stock_view, name='entrada_stock'),
]
