from rest_framework import serializers
from .models import Categoria, Proveedor, Producto


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre']


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = ['id', 'nombre', 'nit', 'telefono']


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    proveedor_nombre = serializers.ReadOnlyField(source='proveedor.nombre')


    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'sku', 'categoria', 'categoria_nombre', 'proveedor', 'proveedor_nombre',
            'precio_venta', 'costo_promedio', 'stock', 'stock_minimo', 'unidad', 'activo'
            ]