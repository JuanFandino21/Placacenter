from decimal import Decimal
from urllib.parse import quote
from django.views.decorators.http import require_GET
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login as dj_login, logout as dj_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView

from rest_framework import viewsets, filters
from authlib.integrations.django_client import OAuth

from .models import Categoria, Proveedor, Producto, MovimientoInventario
from .serializers import CategoriaSerializer, ProveedorSerializer, ProductoSerializer
from .forms import CategoriaForm, ProveedorForm, ProductoForm, EntradaStockForm

@require_GET
def signin_view(request):
    # Solo renderiza tu landing de login. El botón apunta a /login?provider=google
    return render(request, "login.html")

# =============================
#  Auth0 (OAuth / OIDC)
# =============================
oauth = OAuth()
# Evita doble registro bajo autoreloader
if not getattr(oauth, "auth0", None):
    oauth.register(
        name='auth0',
        server_metadata_url=f'https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration',
        client_id=settings.AUTH0_CLIENT_ID,
        client_secret=settings.AUTH0_CLIENT_SECRET,
        client_kwargs={'scope': 'openid profile email'},
    )


def auth_login(request):
    # Si viene ?provider=google, forzamos la conexión 'google-oauth2'
    provider = request.GET.get("provider")
    if provider == "google":
        return oauth.auth0.authorize_redirect(
            request,
            redirect_uri=settings.AUTH0_CALLBACK_URL,
            connection="google-oauth2"
        )
    # Universal Login (lista de proveedores)
    return oauth.auth0.authorize_redirect(request, redirect_uri=settings.AUTH0_CALLBACK_URL)


def auth_callback(request):
    try:
        token = oauth.auth0.authorize_access_token(request)
    except Exception as e:
        return HttpResponseBadRequest(f"Auth error: {e}")

    userinfo = token.get('userinfo') or {}
    email = userinfo.get('email')
    if not email:
        return HttpResponseBadRequest("No se obtuvo email del proveedor.")

    name = userinfo.get('name') or userinfo.get('nickname') or email

    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username=email,
        defaults={'email': email, 'first_name': name[:30]},
    )
    dj_login(request, user)
    return redirect(settings.LOGIN_REDIRECT_URL)


def auth_logout(request):
    dj_logout(request)
    return redirect(
        "https://{domain}/v2/logout?client_id={cid}&returnTo={ret}".format(
            domain=settings.AUTH0_DOMAIN,
            cid=settings.AUTH0_CLIENT_ID,
            ret=quote(settings.AUTH0_LOGOUT_REDIRECT, safe='')
        )
    )


# =============================
#  HTML (protegido con login)
# =============================

# lista de la categoria en html
class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = 'categorias_list.html'


class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'categoria_form.html'

    def get_success_url(self):
        return reverse('categorias_list')


class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'categoria_form.html'

    def get_success_url(self):
        return reverse('categorias_list')


class ProveedorListView(LoginRequiredMixin, ListView):
    model = Proveedor
    template_name = 'proveedores_list.html'


class ProveedorCreateView(LoginRequiredMixin, CreateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'proveedor_form.html'

    def get_success_url(self):
        return reverse('proveedores_list')


class ProveedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'proveedor_form.html'

    def get_success_url(self):
        return reverse('proveedores_list')


class ProductoListView(LoginRequiredMixin, ListView):
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


class ProductoCreateView(LoginRequiredMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_form.html'

    def get_success_url(self):
        return reverse('productos_list')


class ProductoUpdateView(LoginRequiredMixin, UpdateView):
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
                # Actualizar stock y costo promedio
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


# =============================
#  API (sin cambios de permisos por ahora)
# =============================

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
