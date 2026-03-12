"""
Ver productos actuales de Shopify con todos sus campos.
Genera un CSV/Excel para revisar qué campos están llenos y cuáles vacíos.
"""
import os
import sys
import csv
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_STORE         = os.getenv('SHOPIFY_STORE', '')
SHOPIFY_CLIENT_ID     = os.getenv('SHOPIFY_CLIENT_ID', '')
SHOPIFY_CLIENT_SECRET = os.getenv('SHOPIFY_CLIENT_SECRET', '')
API_VERSION           = '2024-01'

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)


def obtener_token():
    url = f"https://{SHOPIFY_STORE}/admin/oauth/access_token"
    r = requests.post(url, json={
        "client_id": SHOPIFY_CLIENT_ID,
        "client_secret": SHOPIFY_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }, timeout=30)
    r.raise_for_status()
    token = r.json().get('access_token')
    if not token:
        log.error("No se recibió token de Shopify")
        sys.exit(1)
    log.info("Token obtenido")
    return token


def obtener_todos_los_productos(token):
    headers = {"X-Shopify-Access-Token": token}
    base = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}"
    # Pedimos todos los campos disponibles (sin restricción de fields=)
    url  = f"{base}/products.json?limit=250"
    productos = []

    while url:
        r = requests.get(url, headers=headers, timeout=60)
        r.raise_for_status()
        lote = r.json().get('products', [])
        productos.extend(lote)
        log.info(f"  Descargados {len(productos)} productos...")

        link = r.headers.get('Link', '')
        url = None
        for part in link.split(','):
            if 'rel="next"' in part:
                url = part.strip().split(';')[0].strip().strip('<>')
                break

    log.info(f"Total: {len(productos)} productos")
    return productos


def exportar_csv(productos):
    archivo = 'shopify_productos_actuales.csv'

    filas = []
    for p in productos:
        # Un producto puede tener varias variantes. Hacemos una fila por variante.
        variantes = p.get('variants', [{}])
        for v in variantes:
            filas.append({
                # ── Producto ──
                'producto_id':        p.get('id', ''),
                'titulo':             p.get('title', ''),
                'tipo':               p.get('product_type', ''),
                'proveedor':          p.get('vendor', ''),
                'estado':             p.get('status', ''),
                'tags':               p.get('tags', ''),
                'descripcion_html':   '(tiene)' if p.get('body_html') else '',
                'imagen':             p['images'][0]['src'] if p.get('images') else '',
                'fecha_creacion':     p.get('created_at', ''),
                'fecha_actualizacion': p.get('updated_at', ''),
                # ── Variante ──
                'variante_id':        v.get('id', ''),
                'sku':                v.get('sku', '') or '',
                'precio':             v.get('price', ''),
                'precio_comparacion': v.get('compare_at_price', '') or '',
                'inventario_policy':  v.get('inventory_management', '') or '',
                'cantidad_inventario': v.get('inventory_quantity', ''),
                'barcode':            v.get('barcode', '') or '',
                'peso':               v.get('weight', ''),
                'opcion1':            v.get('option1', '') or '',
                'opcion2':            v.get('option2', '') or '',
                'opcion3':            v.get('option3', '') or '',
                'inventory_item_id':  v.get('inventory_item_id', ''),
            })

    campos = [
        'producto_id', 'titulo', 'tipo', 'proveedor', 'estado', 'tags',
        'descripcion_html', 'imagen', 'fecha_creacion', 'fecha_actualizacion',
        'variante_id', 'sku', 'precio', 'precio_comparacion',
        'inventario_policy', 'cantidad_inventario', 'barcode', 'peso',
        'opcion1', 'opcion2', 'opcion3', 'inventory_item_id',
    ]

    with open(archivo, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)

    # ── Resumen ──
    total        = len(filas)
    con_sku      = sum(1 for r in filas if r['sku'])
    sin_sku      = total - con_sku
    con_precio   = sum(1 for r in filas if r['precio'])
    con_imagen   = sum(1 for r in filas if r['imagen'])
    con_tipo     = sum(1 for r in filas if r['tipo'])
    con_barcode  = sum(1 for r in filas if r['barcode'])

    print("\n" + "="*50)
    print("  PRODUCTOS EN SHOPIFY")
    print("="*50)
    print(f"  Total filas (variantes):  {total}")
    print(f"  Con SKU:                  {con_sku}")
    print(f"  Sin SKU:                  {sin_sku}  ← estos son el problema")
    print(f"  Con precio:               {con_precio}")
    print(f"  Con imagen:               {con_imagen}")
    print(f"  Con tipo de producto:     {con_tipo}")
    print(f"  Con barcode:              {con_barcode}")
    print("="*50)
    print(f"\n  Archivo generado: {archivo}")
    print("  Ábrelo en Excel para revisar cada producto.\n")


if __name__ == '__main__':
    if not all([SHOPIFY_STORE, SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET]):
        log.error("Faltan variables en .env: SHOPIFY_STORE, SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET")
        sys.exit(1)

    token     = obtener_token()
    productos = obtener_todos_los_productos(token)
    exportar_csv(productos)
