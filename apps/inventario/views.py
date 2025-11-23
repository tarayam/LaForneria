from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from project_utils.auth_helpers import reauth_required
from django.utils import timezone
from django.db import models
from django.contrib import messages

from .models import Productos, MovimientosInventario, IngresoStock
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@login_required
@reauth_required
def inventario_dashboard(request):
	"""Lista productos y permite registrar ingresos de inventario.

	GET: muestra formulario con productos y movimientos recientes.
	POST: recibe 'producto_id' y 'cantidad' y crea un movimiento de tipo 'ingreso'.
	"""
	message = None

	# Restrict access: only staff or superuser may use inventory
	if not request.user.is_staff and not request.user.is_superuser:
		# Redirect sellers to POS with an error message
		try:
			messages.error(request, 'No tienes permiso para acceder al módulo de Inventario.')
		except Exception:
			pass
		return redirect('pos_ventas')

	if request.method == 'POST':
		try:
			producto_id = int(request.POST.get('producto_id'))
			cantidad = int(request.POST.get('cantidad'))
			action = request.POST.get('action', 'ingreso')
			proveedor = request.POST.get('proveedor')
			documento = request.POST.get('documento')
			lote = request.POST.get('lote')
			precio_unitario = request.POST.get('precio_unitario')
			fecha_vencimiento = request.POST.get('fecha_vencimiento')
			observaciones = request.POST.get('observaciones')
		except (TypeError, ValueError):
			message = 'Datos inválidos. Asegúrate de seleccionar un producto y una cantidad numérica.'
		else:
			try:
				producto = Productos.objects.get(pk=producto_id)
			except Productos.DoesNotExist:
				message = 'Producto no encontrado.'
			else:
				# gestionar ingreso o egreso
				if action == 'egreso':
					# comprobar stock suficiente
					current = producto.stock_actual or 0
					if cantidad > current:
						message = f'No hay stock suficiente. Stock actual: {current}.'
						productos = Productos.objects.all().order_by('nombre')
						movimientos = MovimientosInventario.objects.select_related('productos').order_by('-fecha')[:20]
						low_stock = Productos.objects.filter(stock_actual__lte=models.F('stock_minimo'))
						return render(request, 'inventario/prueba.html', {
							'productos': productos,
							'movimientos': movimientos,
							'message': message,
							'low_stock': low_stock,
						})
					delta = -abs(cantidad)
					tipo = 'egreso'
				else:
					delta = abs(cantidad)
					tipo = 'ingreso'

				# crear movimiento
				mov = MovimientosInventario(
					tipo_movimiento=tipo,
					cantidad=cantidad,
					fecha=timezone.now(),
					productos=producto
				)
				mov.save()

				# crear metadatos en IngresoStock
				try:
					ingreso = IngresoStock.objects.create(
						productos=producto,
						movimientos_inventario=mov,
						accion=tipo,
						proveedor=proveedor or None,
						documento=documento or None,
						lote=lote or None,
						precio_unitario=precio_unitario or None,
						fecha_vencimiento=fecha_vencimiento or None,
						observaciones=observaciones or None,
						creado_por=(request.user.username if request.user.is_authenticated else None)
					)
				except Exception:
					ingreso = None

				# actualizar stock_actual
				try:
					if producto.stock_actual is None:
						producto.stock_actual = 0
					producto.stock_actual = producto.stock_actual + delta
					producto.save()
				except Exception:
					pass

				message = f'{"Egreso" if tipo=="egreso" else "Ingreso"} registrado: {cantidad} unidades de {producto.nombre}.'

				# If AJAX request, return JSON with updated stock
				if request.headers.get('x-requested-with') == 'XMLHttpRequest':
					return JsonResponse({
						'status': 'ok',
						'producto_id': producto.pk,
						'stock_actual': producto.stock_actual,
						'message': message,
						'ingreso_id': ingreso.pk if ingreso else None,
					})

	# búsqueda por q
	q = request.GET.get('q', '').strip()
	productos_qs = Productos.objects.all()
	if q:
		productos_qs = productos_qs.filter(nombre__icontains=q)

	productos = productos_qs.order_by('nombre')

	movimientos_qs = MovimientosInventario.objects.select_related('productos').order_by('-fecha')
	paginator = Paginator(movimientos_qs, 15)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)

	low_stock = Productos.objects.filter(stock_actual__lte=models.F('stock_minimo'))

	return render(request, 'inventario/prueba.html', {
		'productos': productos,
		'movimientos': page_obj,
		'message': message,
		'low_stock': low_stock,
		'query': q,
	})


@require_GET
def product_search_api(request):
	"""Simple API to return product matches for AJAX/autocomplete."""
	q = request.GET.get('q', '').strip()
	qs = Productos.objects.all()
	if q:
		qs = qs.filter(nombre__icontains=q)
	results = []
	for p in qs.order_by('nombre')[:20]:
		results.append({
			'id': p.pk,
			'nombre': p.nombre,
			'stock_actual': p.stock_actual,
		})
	return JsonResponse({'results': results})
