

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=80, unique=True)),
            ],
            options={
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Proveedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=120)),
                ('nit', models.CharField(blank=True, max_length=30, null=True)),
                ('telefono', models.CharField(blank=True, max_length=30, null=True)),
            ],
            options={
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=120)),
                ('sku', models.CharField(max_length=50, unique=True)),
                ('precio_venta', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('costo_promedio', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('stock', models.IntegerField(default=0)),
                ('stock_minimo', models.IntegerField(default=0)),
                ('unidad', models.CharField(choices=[('und', 'Unidad'), ('mt', 'Metro'), ('lt', 'Litro'), ('kg', 'Kilogramo')], default='und', max_length=5)),
                ('activo', models.BooleanField(default=True)),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='productos', to='core.categoria')),
                ('proveedor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.proveedor')),
            ],
            options={
                'ordering': ['nombre'],
                'unique_together': {('nombre', 'sku')},
            },
        ),
        migrations.CreateModel(
            name='MovimientoInventario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('ENTRADA', 'Entrada')], max_length=10)),
                ('cantidad', models.PositiveIntegerField()),
                ('costo_unitario', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('motivo', models.CharField(blank=True, max_length=120, null=True)),
                ('fecha', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimientos', to='core.producto')),
            ],
            options={
                'ordering': ['-fecha'],
            },
        ),
    ]
