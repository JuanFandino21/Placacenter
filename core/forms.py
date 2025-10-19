from django import forms
from .models import Categoria, Proveedor, Producto

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Tornillería"}),
        }

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre", "nit", "telefono"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del proveedor"}),
            "nit": forms.TextInput(attrs={"class": "form-control", "placeholder": "NIT"}),
            "telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "Teléfono"}),
        }

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "nombre", "sku", "categoria", "proveedor", "precio_venta",
            "costo_promedio", "stock", "stock_minimo", "unidad", "activo"
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Tornillo 1/4\""}),
            "sku": forms.TextInput(attrs={"class": "form-control", "placeholder": "Código/SKU"}),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "proveedor": forms.Select(attrs={"class": "form-select"}),
            "precio_venta": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "costo_promedio": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "stock_minimo": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "unidad": forms.Select(attrs={"class": "form-select"}),
            
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class EntradaStockForm(forms.Form):
    producto = forms.IntegerField(widget=forms.HiddenInput)
    cantidad = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}))
    costo_unitario = forms.DecimalField(
        min_value=0, decimal_places=2, max_digits=12,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )
    motivo = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Motivo (opcional)"}))
