from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    CategoriaViewSet,
    ProveedorViewSet,
    ProductoViewSet,
    ProductosStockBajoList,
)

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet)
router.register(r'proveedores', ProveedorViewSet)
router.register(r'productos',  ProductoViewSet)

urlpatterns = [
    # NUEVO: endpoint para la Lambda
    path('alertas/stock-bajo/', ProductosStockBajoList.as_view(), name='alertas-stock-bajo'),

    # Rutas de los viewsets
    path('', include(router.urls)),
]