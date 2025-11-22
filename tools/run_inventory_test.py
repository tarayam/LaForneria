import os
import sys
import django

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Forneria.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.conf import settings

# Ensure test client host is allowed
if not isinstance(settings.ALLOWED_HOSTS, (list, tuple)):
    settings.ALLOWED_HOSTS = ['testserver']
elif 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver']

def main():
    User = get_user_model()
    username = 'testadmin'
    password = 'TestPass123!'

    client = Client()
    logged = client.login(username=username, password=password)
    print('login:', logged)
    # mark session as reauthenticated to pass @reauth_required
    import time
    s = client.session
    s['reauthenticated_at'] = time.time()
    s.save()

    # Search products
    resp = client.get('/inventario/api/products/?q=')
    print('GET /inventario/api/products/ status:', resp.status_code)
    try:
        data = resp.json()
    except Exception:
        data = None
    print('products payload keys:', list(data.keys()) if isinstance(data, dict) else type(data))

    first_id = None
    if isinstance(data, dict) and data.get('results'):
        first = data['results'][0]
        first_id = first.get('id')
        print('first product id:', first_id)

    # If no product exists, create a minimal product to test POST
    if not first_id:
        print('No product found — creating test Categoria, Nutricional and Producto...')
        from apps.inventario.models import Categorias, Nutricional, Productos
        import datetime
        cat, _ = Categorias.objects.get_or_create(nombre='TestCat')
        nut, _ = Nutricional.objects.get_or_create(calorias=0)
        prod = Productos.objects.create(
            nombre='Producto Test', descripcion='Creado por script', marca='Marca',
            precio=1000, caducidad=(datetime.date.today()), tipo='test',
            stock_actual=10, stock_minimo=1, stock_maximo=100,
            presentacion='unidad', formato='u', creado=None, modificado=None, eliminado=None,
            categorias=cat, nutricional=nut
        )
        first_id = prod.pk
        print('Created product id:', first_id)

    # Post a movement (ingreso)
    post_data = {
        'producto_id': first_id,
        'action': 'ingreso',
        'cantidad': 1,
        'proveedor': 'ScriptTest',
        'documento': 'TST-001',
    }
    resp2 = client.post('/inventario/', post_data)
    print('POST /inventario/ status:', resp2.status_code)
    # try parse json
    try:
        print('POST response json:', resp2.json())
    except Exception:
        print('POST response content length:', len(resp2.content or b''))
    # verify movimiento created
    try:
        from apps.inventario.models import MovimientosInventario
        mov_count = MovimientosInventario.objects.filter(productos_id=first_id).count()
        print('Movimientos count for product:', mov_count)
    except Exception as e:
        print('Could not verify movimientos:', e)

if __name__ == '__main__':
    main()
