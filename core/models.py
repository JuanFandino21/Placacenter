from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    nombre = models.CharField(max_length=120)
    nit = models.CharField(max_length=30, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    UNIDADES = [
        ('und', 'Unidad'),
        ('mt', 'Metro'),
        ('lt', 'Litro'),
        ('kg', 'Kilogramo'),
    ]

    nombre = models.CharField(max_length=120)
    sku = models.CharField(max_length=50, unique=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    costo_promedio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    unidad = models.CharField(max_length=5, choices=UNIDADES, default='und')
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        unique_together = [('nombre', 'sku')]

    def __str__(self):
        return f"{self.nombre} ({self.sku})"


class MovimientoInventario(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
    ]
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.PositiveIntegerField()
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    motivo = models.CharField(max_length=120, blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo} {self.cantidad} de {self.producto}"