from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView
from rest_framework import viewsets, filters

from .models import Categoria, Proveedor, Producto, MovimientoInventario
from .serializers import CategoriaSerializer, ProveedorSerializer, ProductoSerializer
from .forms import CategoriaForm, ProveedorForm, ProductoForm, EntradaStockForm


# ======= HTML =======

class CategoriaListView(ListView):
    model = Categoria
    template_name = 'categorias_list.html'


class CategoriaCreateView(CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'categoria_form.html'

    def get_success_url(self):
        return reverse('categorias_list')


class CategoriaUpdateView(UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'categoria_form.html'

    def get_success_url(self):
        return reverse('categorias_list')


class ProveedorListView(ListView):
    model = Proveedor
    template_name = 'proveedores_list.html'


class ProveedorCreateView(CreateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'proveedor_form.html'

    def get_success_url(self):
        return reverse('proveedores_list')


class ProveedorUpdateView(UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'proveedor_form.html'

    def get_success_url(self):
        return reverse('proveedores_list')


class ProductoListView(ListView):
    model = Producto
    template_name = 'productos_list.html'

    def get_queryset(self):
        qs = super().get_queryset().select_related('categoria', 'proveedor')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(sku__icontains=q))
        categoria = self.request.GET.get('categoria')
        if categoria:
            qs = qs.filter(categoria_id=categoria)
        return qs


class ProductoCreateView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_form.html'

    def get_success_url(self):
        return reverse('productos_list')


class ProductoUpdateView(UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_form.html'

    def get_success_url(self):
        return reverse('productos_list')


def entrada_stock_view(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    if request.method == 'POST':
        form = EntradaStockForm(request.POST)
        if form.is_valid():
            cantidad = form.cleaned_data['cantidad']
            costo_unitario = form.cleaned_data['costo_unitario']
            motivo = form.cleaned_data.get('motivo')

            with transaction.atomic():
                MovimientoInventario.objects.create(
                    producto=producto,
                    tipo='ENTRADA',
                    cantidad=cantidad,
                    costo_unitario=costo_unitario,
                    motivo=motivo,
                )
                # Actualizar stock y costo promedio (promedio ponderado simple)
                total_actual = Decimal(producto.costo_promedio) * producto.stock
                total_nuevo = Decimal(costo_unitario) * Decimal(cantidad)
                nuevo_stock = producto.stock + cantidad
                nuevo_costo = (
                    (total_actual + total_nuevo) / Decimal(nuevo_stock)
                    if nuevo_stock else Decimal('0')
                )
                producto.stock = nuevo_stock
                producto.costo_promedio = nuevo_costo.quantize(Decimal('0.01'))
                producto.save()

            return redirect('productos_list')
    else:
        form = EntradaStockForm(initial={'producto': producto.id})

    return render(request, 'entrada_stock.html', {'form': form, 'producto': producto})


# ======= API (DRF) =======

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'nit']


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related('categoria', 'proveedor').all()
    serializer_class = ProductoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'sku']
