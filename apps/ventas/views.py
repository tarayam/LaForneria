from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from project_utils.auth_helpers import reauth_required
from apps.inventario.models import Productos
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
import json
from .models import Ventas, DetalleVenta, Clientes
from apps.inventario.models import MovimientosInventario, IngresoStock


@login_required
@reauth_required
def pos_ventas(request):
    # Renderiza el template de Punto de Venta — requiere autenticación y reauth reciente
    productos = Productos.objects.all().order_by('nombre')
    return render(request, "ventas/prueba.html", { 'productos': productos })


@login_required
@reauth_required
@require_POST
def checkout(request):
    """Endpoint que procesa el ticket enviado por el POS.

    Espera JSON: { items: [{product_id, cantidad, precio_unitario, descuento_pct?}], totals: {...} }
    Crea Venta/DetalleVenta, valida stock y descuenta dentro de una transacción.
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)

    items = payload.get('items') or []
    totals = payload.get('totals', {})
    if not items:
        return JsonResponse({'status': 'error', 'message': 'El ticket está vacío.'}, status=400)

    with transaction.atomic():
        # asegurar cliente 'Consumidor Final' existe
        cliente, _ = Clientes.objects.get_or_create(nombre='Consumidor Final', defaults={'rut': '', 'correo': ''})

        venta = Ventas.objects.create(
            fecha=timezone.now(),
            total_sin_iva=totals.get('total_sin_iva', 0),
            total_iva=totals.get('total_iva', 0),
            descuento=totals.get('descuento', 0),
            total_con_iva=totals.get('total', 0),
            canal_venta=totals.get('canal', 'pos'),
            folio=totals.get('folio') or '',
            monto_pagado=totals.get('monto_pagado') or 0,
            vuelto=totals.get('vuelto') or 0,
            clientes=cliente
        )

        # procesar items
        for it in items:
            pid = it.get('product_id')
            qty = int(it.get('cantidad') or 0)
            price = it.get('precio_unitario') or 0
            discount = it.get('descuento_pct')

            prod = Productos.objects.select_for_update().get(pk=pid)
            current = prod.stock_actual or 0
            if qty > current:
                raise ValueError(f'Stock insuficiente para {prod.nombre}.')

            detalle = DetalleVenta.objects.create(
                cantidad=qty,
                precio_unitario=price,
                descuento_pct=discount,
                ventas=venta,
                productos=prod
            )

            # crear movimiento de inventario (egreso)
            mov = MovimientosInventario.objects.create(
                tipo_movimiento='egreso',
                cantidad=qty,
                fecha=timezone.now(),
                productos=prod
            )
            IngresoStock.objects.create(
                productos=prod,
                movimientos_inventario=mov,
                accion='egreso',
                creado_por=(request.user.username if request.user.is_authenticated else None)
            )

            # descontar stock
            prod.stock_actual = current - qty
            prod.save()

    return JsonResponse({'status': 'ok', 'venta_id': venta.pk})
