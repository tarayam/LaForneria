from django.db import models


class Productos(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=300, blank=True, null=True)
    marca = models.CharField(max_length=100, blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    caducidad = models.DateField()
    elaboracion = models.DateField(blank=True, null=True)
    tipo = models.CharField(max_length=100, blank=True, null=True)
    stock_actual = models.IntegerField(blank=True, null=True)
    stock_minimo = models.IntegerField(blank=True, null=True)
    stock_maximo = models.IntegerField(blank=True, null=True)
    presentacion = models.CharField(max_length=100, blank=True, null=True)
    formato = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateTimeField(blank=True, null=True)
    modificado = models.DateTimeField(blank=True, null=True)
    eliminado = models.DateTimeField(blank=True, null=True)
    categorias = models.ForeignKey('Categorias', models.DO_NOTHING)
    nutricional = models.ForeignKey('Nutricional', models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'productos'


class Categorias(models.Model):
    nombre = models.CharField(max_length=100, blank=True, null=True)
    descripcion = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'categorias'


class MovimientosInventario(models.Model):
    tipo_movimiento = models.CharField(max_length=7)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField()
    productos = models.ForeignKey(Productos, models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'movimientos_inventario'


class IngresoStock(models.Model):
    """Metadatos opcionales para movimientos de stock (ingresos/egresos).

    Este modelo es 'managed = True' para permitir crear migraciones si se desea.
    """
    productos = models.ForeignKey(Productos, models.CASCADE)
    movimientos_inventario = models.ForeignKey(MovimientosInventario, models.SET_NULL, blank=True, null=True)
    accion = models.CharField(max_length=10, choices=(('ingreso','Ingreso'),('egreso','Egreso')))
    proveedor = models.CharField(max_length=200, blank=True, null=True)
    documento = models.CharField(max_length=100, blank=True, null=True)
    lote = models.CharField(max_length=100, blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    creado_por = models.CharField(max_length=150, blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'ingreso_stock'


class Nutricional(models.Model):
    calorias = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    proteinas = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    grasas = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    carbohidratos = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    azucares = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sodio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'nutricional'
