from decimal import Decimal
from urllib.parse import quote
from types import SimpleNamespace  
import re
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth import login as dj_login, logout as dj_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, F
from collections import OrderedDict
from datetime import datetime, date, timedelta
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.generic import ListView, CreateView, UpdateView
from django.template.loader import render_to_string
from rest_framework import viewsets, filters
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from authlib.integrations.django_client import OAuth
import csv         
import io 
from .models import Categoria, Proveedor, Producto, MovimientoInventario
from .serializers import CategoriaSerializer, ProveedorSerializer, ProductoSerializer
from .forms import CategoriaForm, ProveedorForm, ProductoForm, EntradaStockForm
from .cart import Cart  

User = get_user_model()

#  LOGIN LOCAL + REGISTRO
class SignInForm(forms.Form):
    username = forms.CharField(
        label="Usuario / correo",
        required=True,
        widget=forms.TextInput(attrs={
            "class": "pc-input w-100",
            "placeholder": "Escribe tu usuario o correo",
            "autocomplete": "username",
        })
    )
    password = forms.CharField(
        label="Contraseña",
        required=True,
        min_length=8,
        widget=forms.PasswordInput(attrs={
            "class": "pc-input w-100",
            "placeholder": "Escribe tu contraseña (mínimo 8)",
            "autocomplete": "current-password",
        })
    )

@require_GET
def signin_view(request):
    if request.user.is_authenticated:
        return redirect('principal')
    return render(request, "login.html", {"form": SignInForm()})

def login_local_view(request):
    if request.method != "POST":
        return redirect("signin")

    form = SignInForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Por favor completa los campos correctamente.")
        return render(request, "login.html", {"form": form})

    username_or_email = form.cleaned_data["username"].strip()
    password = form.cleaned_data["password"]

    username = username_or_email
    if "@" in username_or_email:
        try:
            username = User.objects.get(email__iexact=username_or_email).username
        except User.DoesNotExist:
            username = username_or_email

    user = authenticate(request, username=username, password=password)
    if user and user.is_active:
        dj_login(request, user)
        return redirect(request.GET.get("next") or "principal")

    messages.error(request, "Usuario/contraseña inválidos o cuenta inactiva.")
    return render(request, "login.html", {"form": form})


_ALLOWED_DOMAINS = ("gmail", "googlemail", "outlook", "hotmail", "live", "yahoo")
_EMAIL_RE = re.compile(
    r"^[^@\s]+@((?:gmail|googlemail|outlook|hotmail|live|yahoo)\.[A-Za-z.]{2,})$",
    re.IGNORECASE,
)

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        label="Correo",
        required=True,
        help_text="Solo correos: @gmail., @googlemail., @outlook., @hotmail., @live., @yahoo.",
        widget=forms.EmailInput(attrs={"placeholder": "tu_correo@dominio.com"})
    )
    first_name = forms.CharField(
        label="Nombre",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Tu nombre"})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "password1", "password2")

    def init(self, *args, **kwargs):
        super().init(*args, **kwargs)
        field_cfg = {
            "username": {"placeholder": ""},
            "email": {"placeholder": "tu_correo@dominio.com"},
            "first_name": {"placeholder": "Tu nombre"},
            "password1": {"placeholder": ""},
            "password2": {"placeholder": ""},
        }
        for name, field in self.fields.items():
            base = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (base + " pc-input w-100").strip()
            ph = field_cfg.get(name, {}).get("placeholder")
            if ph is not None and not field.widget.attrs.get("placeholder"):
                field.widget.attrs["placeholder"] = ph

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not _EMAIL_RE.match(email):
            raise forms.ValidationError(
                "Correo no permitido. Usa @gmail., @googlemail., @outlook., @hotmail., @live.* o @yahoo.*"
            )
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe un usuario con este correo.")
        return email

    def clean_password1(self):
        pw = self.cleaned_data.get("password1") or ""
        if len(pw) < 8:
            raise forms.ValidationError("La contraseña debe tener mínimo 8 caracteres.")
        return pw

def signup_view(request):
    if request.user.is_authenticated:
        return redirect("principal")

    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email = form.cleaned_data["email"]
        user.first_name = form.cleaned_data["first_name"]
        user.save()
        messages.success(request, "Cuenta creada correctamente. Ahora puedes iniciar sesión.")
        return redirect("signin")

    return render(request, "signup.html", {"form": form})


#  PANTALLAS PRINCIPALES
@login_required
def principal_view(request):
    return render(request, "principal.html")

@login_required
def gestion_home_view(request):
    return redirect("productos_list")

@login_required
def ventas_view(request):
    """
    Ventas:
      - Agrupa por categoría (incluye 'Sin categoría').
      - Búsqueda por nombre o SKU.
    """
    q = (request.GET.get("q") or "").strip()

    base_qs = (
        Producto.objects
        .select_related("categoria")
        .order_by("nombre")
    )
    if q:
        base_qs = base_qs.filter(
            Q(nombre__icontains=q) |
            Q(sku__icontains=q)
        )

    grupos_dict = {}
    for p in base_qs:
        cat = p.categoria
        key = cat.id if cat else None
        if key not in grupos_dict:
            grupos_dict[key] = (cat if cat else SimpleNamespace(nombre="Sin categoría"), [])
        grupos_dict[key][1].append(p)

    grupos = sorted(grupos_dict.values(), key=lambda t: t[0].nombre.lower())
    return render(request, "core/ventas.html", {"grupos": grupos, "q": q})


#  Auth0 (OAuth / OIDC)
oauth = OAuth()
if not getattr(oauth, "auth0", None):
    oauth.register(
        name='auth0',
        server_metadata_url=f'https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration',
        client_id=settings.AUTH0_CLIENT_ID,
        client_secret=settings.AUTH0_CLIENT_SECRET,
        client_kwargs={'scope': 'openid profile email'},
    )

def auth_login(request):
    if request.GET.get("provider") == "google":
        return oauth.auth0.authorize_redirect(
            request,
            redirect_uri=settings.AUTH0_CALLBACK_URL,
            connection="google-oauth2",
        )
    return oauth.auth0.authorize_redirect(request, redirect_uri=settings.AUTH0_CALLBACK_URL)

def auth_callback(request):
    try:
        token = oauth.auth0.authorize_access_token(request)
    except Exception as e:
        return HttpResponseBadRequest(f"Auth error: {e}")

    userinfo = token.get("userinfo") or {}
    email = userinfo.get("email")
    if not email:
        return HttpResponseBadRequest("No se obtuvo email del proveedor.")

    name = userinfo.get("name") or userinfo.get("nickname") or email

    user, _ = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "first_name": name[:30]},
    )
    dj_login(request, user)
    return redirect(settings.LOGIN_REDIRECT_URL)

def auth_logout(request):
    dj_logout(request)
    return redirect(
        "https://{domain}/v2/logout?client_id={cid}&returnTo={ret}".format(
            domain=settings.AUTH0_DOMAIN,
            cid=settings.AUTH0_CLIENT_ID,
            ret=quote(settings.AUTH0_LOGOUT_REDIRECT, safe="")
        )
    )


#  HTML 
class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = "categorias_list.html"

class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "categoria_form.html"
    def get_success_url(self): return reverse("categorias_list")

class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "categoria_form.html"
    def get_success_url(self): return reverse("categorias_list")

class ProveedorListView(LoginRequiredMixin, ListView):
    model = Proveedor
    template_name = "proveedores_list.html"

class ProveedorCreateView(LoginRequiredMixin, CreateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = "proveedor_form.html"
    def get_success_url(self): return reverse("proveedores_list")

class ProveedorUpdateView(LoginRequiredMixin, UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = "proveedor_form.html"
    def get_success_url(self): return reverse("proveedores_list")

class ProductoListView(LoginRequiredMixin, ListView):
    model = Producto
    template_name = "productos_list.html"

    def get_queryset(self):
        qs = super().get_queryset().select_related("categoria", "proveedor")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(sku__icontains=q)
            )
        categoria = self.request.GET.get("categoria")
        if categoria:
            qs = qs.filter(categoria_id=categoria)
        return qs

class ProductoCreateView(LoginRequiredMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = "producto_form.html"
    def get_success_url(self): return reverse("productos_list")

class ProductoUpdateView(LoginRequiredMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = "producto_form.html"
    def get_success_url(self): return reverse("productos_list")

def entrada_stock_view(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    if request.method == "POST":
        form = EntradaStockForm(request.POST)
        if form.is_valid():
            cantidad = form.cleaned_data["cantidad"]
            costo_unitario = form.cleaned_data["costo_unitario"]
            motivo = form.cleaned_data.get("motivo")

            with transaction.atomic():
                MovimientoInventario.objects.create(
                    producto=producto,
                    tipo="ENTRADA",
                    cantidad=cantidad,
                    costo_unitario=costo_unitario,
                    motivo=motivo,
                )
                total_actual = Decimal(producto.costo_promedio) * producto.stock
                total_nuevo = Decimal(costo_unitario) * Decimal(cantidad)
                nuevo_stock = producto.stock + cantidad
                nuevo_costo = (
                    (total_actual + total_nuevo) / Decimal(nuevo_stock)
                    if nuevo_stock else Decimal("0")
                )
                producto.stock = nuevo_stock
                producto.costo_promedio = nuevo_costo.quantize(Decimal("0.01"))
                producto.save()

            return redirect("productos_list")
    else:
        form = EntradaStockForm(initial={"producto": producto.id})

    return render(request, "entrada_stock.html", {"form": form, "producto": producto})

@login_required
def inventario_entradas_view(request):
    """
    Pantalla de inventario:
    - Lista los productos.
    - Permite importar un CSV (acepta coma o punto y coma).
    - Desde aquí también se descarga el PDF.
    """
    productos = (
        Producto.objects
        .select_related("categoria", "proveedor")
        .order_by("nombre")
    )

    # Si se envía un archivo CSV
    if request.method == "POST" and request.FILES.get("csv_file"):
        archivo = request.FILES["csv_file"]

        # Validamos extensión
        if not archivo.name.lower().endswith(".csv"):
            messages.error(request, "Debes subir un archivo .csv")
            return redirect("inventario_entradas")

        # Leemos el contenido del archivo
        contenido_bytes = archivo.read()
        try:
            contenido = contenido_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            contenido = contenido_bytes.decode("latin1")

        if not contenido.strip():
            messages.error(request, "El archivo está vacío.")
            return redirect("inventario_entradas")

        # Detectar si usa ; o ,
        primera_linea = contenido.splitlines()[0]
        if ";" in primera_linea and "," not in primera_linea:
            delimiter = ";"
        else:
            delimiter = ","

        f = io.StringIO(contenido)
        reader = csv.DictReader(f, delimiter=delimiter)

        if not reader.fieldnames:
            messages.error(request, "No se encontraron encabezados en el CSV.")
            return redirect("inventario_entradas")

        # Normalizamos nombres de columnas (quitamos espacios y pasamos a minúsculas)
        headers = [(h or "").strip().lower() for h in reader.fieldnames]
        columnas_obligatorias = ["producto", "categoria", "proveedor", "cantidad", "costo_unitario"]

        if not set(columnas_obligatorias).issubset(set(headers)):
            messages.error(
                request,
                "El CSV debe tener las columnas: producto, categoria, proveedor, cantidad, costo_unitario. "
                "Opcionales: sku, precio_venta."
            )
            return redirect("inventario_entradas")

        creadas_cat = creados_prov = creados_prod = filas_ok = 0

        # Procesamos todo el archivo como una sola transacción
        with transaction.atomic():
            for fila in reader:
                # fila es dict con las columnas, aquí las limpiamos
                fila_norm = {
                    (k or "").strip().lower(): (v or "").strip()
                    for k, v in fila.items()
                }

                nombre_prod = fila_norm.get("producto", "")
                nombre_cat = fila_norm.get("categoria", "")
                nombre_prov = fila_norm.get("proveedor", "")
                sku = fila_norm.get("sku", "")

                if not nombre_prod:
                    # Si no hay nombre de producto, ignoramos la fila
                    continue

                # Cantidad
                try:
                    cantidad = int(fila_norm.get("cantidad") or "0")
                except ValueError:
                    continue
                if cantidad <= 0:
                    continue

                # Costo unitario (costo de compra)
                try:
                    costo_unitario = Decimal(fila_norm.get("costo_unitario") or "0").quantize(Decimal("0.01"))
                except Exception:
                    continue

                # Precio de venta (opcional)
                precio_venta_valor = None
                if fila_norm.get("precio_venta"):
                    try:
                        precio_venta_valor = Decimal(fila_norm["precio_venta"]).quantize(Decimal("0.01"))
                    except Exception:
                        precio_venta_valor = None

                # Categoría
                categoria = None
                if nombre_cat:
                    categoria, creada = Categoria.objects.get_or_create(nombre=nombre_cat)
                    if creada:
                        creadas_cat += 1

                # Proveedor
                proveedor = None
                if nombre_prov:
                    proveedor, creado_prov = Proveedor.objects.get_or_create(nombre=nombre_prov)
                    if creado_prov:
                        creados_prov += 1

                # Producto
                producto = None
                if sku:
                    # Buscamos por SKU si viene
                    producto, creado_prod = Producto.objects.get_or_create(
                        sku=sku,
                        defaults={
                            "nombre": nombre_prod,
                            "categoria": categoria,
                            "proveedor": proveedor,
                            "precio_venta": precio_venta_valor or Decimal("0.00"),
                        }
                    )
                    if creado_prod:
                        creados_prod += 1
                else:
                    # Sin SKU: buscamos por nombre + categoría
                    qs = Producto.objects.filter(nombre__iexact=nombre_prod)
                    if categoria:
                        qs = qs.filter(categoria=categoria)
                    producto = qs.first()

                    if producto is None:
                        nuevo_sku = f"CSV-{Producto.objects.count() + 1}"
                        producto = Producto.objects.create(
                            nombre=nombre_prod,
                            sku=nuevo_sku,
                            categoria=categoria,
                            proveedor=proveedor,
                            precio_venta=precio_venta_valor or Decimal("0.00"),
                        )
                        creados_prod += 1

                # Actualizamos datos básicos
                if categoria:
                    producto.categoria = categoria
                if proveedor:
                    producto.proveedor = proveedor
                if precio_venta_valor is not None:
                    producto.precio_venta = precio_venta_valor
                producto.save()

                # Recalcular costo promedio y stock (misma lógica que la entrada manual)
                total_actual = Decimal(producto.costo_promedio) * producto.stock
                total_nuevo = costo_unitario * Decimal(cantidad)
                nuevo_stock = producto.stock + cantidad
                nuevo_costo = (
                    (total_actual + total_nuevo) / Decimal(nuevo_stock)
                    if nuevo_stock else Decimal("0")
                )

                producto.stock = nuevo_stock
                producto.costo_promedio = nuevo_costo.quantize(Decimal("0.01"))
                producto.save()

                # Guardamos el movimiento
                MovimientoInventario.objects.create(
                    producto=producto,
                    tipo="ENTRADA",
                    cantidad=cantidad,
                    costo_unitario=costo_unitario,
                    motivo="CARGA CSV",
                )

                filas_ok += 1

        messages.success(
            request,
            f"CSV procesado. Filas correctas: {filas_ok}. "
            f"Nuevas categorías: {creadas_cat}. Nuevos proveedores: {creados_prov}. Nuevos productos: {creados_prod}."
        )
        return redirect("inventario_entradas")

    # GET normal: solo mostrar la tabla
    return render(request, "core/inventario_entradas.html", {
        "productos": productos,
    })


@login_required
def inventario_entradas_pdf(request):
    """
    Genera un PDF sencillo con el inventario actual.
    """
    productos = (
        Producto.objects
        .select_related("categoria", "proveedor")
        .order_by("nombre")
    )

    # Importamos aquí para no romper todo el proyecto si falta la librería
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename=\"inventario_placacenter.pdf\"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    y = height - 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, "Inventario actual - Placacenter")

    y -= 25
    p.setFont("Helvetica", 9)
    p.drawString(40, y, "Nombre")
    p.drawString(210, y, "SKU")
    p.drawString(310, y, "Categoría")
    p.drawString(430, y, "Proveedor")
    p.drawString(540, y, "Stock")

    y -= 18

    for prod in productos:
        if y < 40:
            p.showPage()
            y = height - 40
            p.setFont("Helvetica", 9)

        p.drawString(40, y, (prod.nombre or "")[:30])
        p.drawString(210, y, prod.sku or "")
        p.drawString(310, y, (prod.categoria.nombre if prod.categoria else "")[:18])
        p.drawString(430, y, (prod.proveedor.nombre if prod.proveedor else "")[:18])
        p.drawRightString(590, y, f"{prod.stock} {prod.get_unidad_display()}")

        y -= 16

    p.showPage()
    p.save()
    return response


#  VENTAS – acciones del carrito 
@login_required
def cart_partial(request):
    """
    Renderiza el panel del carrito (parcial) desde la sesión actual.
    """
    cart = Cart(request)
    items = []
    for pid, item in cart.items():
        p = get_object_or_404(Producto, pk=int(pid))
        qty = int(item["qty"])
        price = Decimal(item["precio"])
        items.append({
            "id": p.id,
            "nombre": p.nombre,
            "sku": p.sku,
            "precio": str(price),
            "qty": qty,
            "subtotal": float(price * qty),
        })
    html = render_to_string("core/_cart_panel.html", {
        "items": items,
        "total": cart.subtotal(),
    })
    return HttpResponse(html)

@login_required
def cart_add(request, producto_id):
    p = get_object_or_404(Producto, pk=producto_id)
    Cart(request).add(p.id, p.precio_venta, qty=1)
    
    return cart_partial(request)

@login_required
def cart_dec(request, producto_id):
    Cart(request).dec(producto_id, qty=1)
    return cart_partial(request)

@login_required
def cart_remove(request, producto_id):
    Cart(request).remove(producto_id)
    return cart_partial(request)

@login_required
def cart_empty(request):
    Cart(request).empty()
    return cart_partial(request)

@login_required
def reporte_ventas_view(request):

    # Tipo de reporte diario semanal mensual anual
    tipo = request.GET.get("tipo", "diario")
    if tipo not in ("diario", "semanal", "mensual", "anual"):
        tipo = "diario"

    # Fechas desde / hasta 
    desde_str = request.GET.get("desde") or ""
    hasta_str = request.GET.get("hasta") or ""

    desde = None
    hasta = None

    
    try:
        if desde_str:
            desde = datetime.strptime(desde_str, "%Y-%m-%d").date()
    except ValueError:
        desde = None

    try:
        if hasta_str:
            hasta = datetime.strptime(hasta_str, "%Y-%m-%d").date()
    except ValueError:
        hasta = None

    
    if not desde and not hasta:
        hoy = date.today()
        desde = hoy - timedelta(days=30)
        hasta = hoy

    movimientos = MovimientoInventario.objects.filter(
        tipo="SALIDA",
        motivo="VENTA",
    ).select_related("producto").order_by("fecha")

    if desde:
        movimientos = movimientos.filter(fecha__date__gte=desde)
    if hasta:
        movimientos = movimientos.filter(fecha__date__lte=hasta)

    grupos = OrderedDict()
    total_cantidad = 0
    total_venta = Decimal("0.00")
    total_costo = Decimal("0.00")

    for mov in movimientos:
        f = mov.fecha

        # Clave según el tipo de reporte
        if tipo == "diario":
            key = f.date().strftime("%Y-%m-%d")
            etiqueta = f.date().strftime("%d/%m/%Y")
        elif tipo == "semanal":
            year, week, _ = f.isocalendar()
            key = f"{year}-W{week:02d}"
            etiqueta = f"Semana {week} - {year}"
        elif tipo == "mensual":
            key = f.strftime("%Y-%m")
            etiqueta = f.strftime("%m/%Y")
        else:  # anual
            key = f.strftime("%Y")
            etiqueta = key

        if key not in grupos:
            grupos[key] = {
                "periodo": etiqueta,
                "cantidad": 0,
                "total_venta": Decimal("0.00"),
                "total_costo": Decimal("0.00"),
            }

        g = grupos[key]
        # Cantidad vendida
        g["cantidad"] += mov.cantidad

        # Costo de compra lo que ya se guarda MovimientoInventario
        g["total_costo"] += mov.costo_unitario * mov.cantidad

        # Valor de venta usamos el precio_venta actual del producto
        g["total_venta"] += mov.producto.precio_venta * mov.cantidad

    filas = []
    for key, g in grupos.items():
        utilidad = g["total_venta"] - g["total_costo"]
        filas.append({
            "periodo": g["periodo"],
            "cantidad": g["cantidad"],
            "total_venta": g["total_venta"],
            "total_costo": g["total_costo"],
            "utilidad": utilidad,
        })
        total_cantidad += g["cantidad"]
        total_venta += g["total_venta"]
        total_costo += g["total_costo"]

    total_utilidad = total_venta - total_costo

    return render(request, "core/reporte_ventas.html", {
        "tipo": tipo,
        "desde": desde_str,
        "hasta": hasta_str,
        "filas": filas,
        "total_cantidad": total_cantidad,
        "total_venta": total_venta,
        "total_costo": total_costo,
        "total_utilidad": total_utilidad,
    })

@login_required
def ventas_confirmar(request):
    """
    Confirma la venta:
      - Valida stock de todos los ítems del carrito.
      - Descuenta stock en transacción con select_for_update().
      - Registra MovimientoInventario tipo SALIDA al costo promedio.
      - Vacía carrito y muestra comprobante (sin sidebar en la plantilla).
    """
    cart = Cart(request)
    if not cart.items():
        messages.warning(request, "El carrito está vacío.")
        return redirect("ventas")

    
    lineas = []
    insuficientes = []
    for pid, item in cart.items():
        p = get_object_or_404(Producto, pk=int(pid))
        qty = int(item["qty"])
        price = Decimal(item["precio"])
        if p.stock < qty:
            insuficientes.append((p, qty, p.stock))
        lineas.append((p, qty, price))

    if insuficientes:
        msg = "Stock insuficiente para: " + ", ".join(
            [f"{p.nombre} (necesita {need}, disponible {have})" for p, need, have in insuficientes]
        )
        messages.error(request, msg)
        return redirect("ventas")

    resumen = []
    total = Decimal("0.00")
    # Descontar y registrar movimiento
    with transaction.atomic():
        for p, qty, price in lineas:
            prod = Producto.objects.select_for_update().get(pk=p.pk)
            prod.stock = prod.stock - qty
            prod.save(update_fields=["stock"])

            MovimientoInventario.objects.create(
                producto=prod,
                tipo="SALIDA",
                cantidad=qty,
                costo_unitario=prod.costo_promedio,
                motivo="VENTA",
            )

            subtotal = (price * qty).quantize(Decimal("0.01"))
            total += subtotal
            resumen.append({
                "producto": f"{prod.nombre} ({prod.sku})",
                "qty": qty,
                "precio": str(price),
                "subtotal": float(subtotal),
            })

    cart.empty()
    return render(request, "core/venta_confirmada.html", {
        "resumen": resumen,
        "total": float(total),
    })


#  API 

class ProductosStockBajoList(ListAPIView):
    """
    Devuelve productos con stock <= stock_minimo y activos.
    Consumida por la Lambda de AWS para generar la alerta.
    """
    serializer_class = ProductoSerializer
    permission_classes = [AllowAny] 

    def get_queryset(self):
        return (
            Producto.objects
            .select_related("categoria", "proveedor")
            .filter(activo=True, stock__lte=F("stock_minimo"))
            .order_by("nombre")
        )

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nombre"]

class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nombre", "nit"]

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related("categoria", "proveedor").all()
    serializer_class = ProductoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nombre", "sku"]