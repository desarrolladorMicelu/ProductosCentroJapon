"""
Diagnóstico de productos: compara API Centro Japón vs Shopify
Genera un CSV con ambas listas para identificar qué productos coinciden
y cuáles están duplicados, sin SKU, o son exclusivos de un sistema.
"""
import os
import sys
import csv
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_STORE     = os.getenv('SHOPIFY_STORE', '')
SHOPIFY_CLIENT_ID = os.getenv('SHOPIFY_CLIENT_ID', '')
SHOPIFY_CLIENT_SECRET = os.getenv('SHOPIFY_CLIENT_SECRET', '')
API_URL           = os.getenv('API_URL', '')
API_VERSION       = '2024-01'

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  SHOPIFY – OBTENER TOKEN
# ──────────────────────────────────────────────
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
    log.info("Token de Shopify obtenido")
    return token


# ──────────────────────────────────────────────
#  SHOPIFY – DESCARGAR TODOS LOS PRODUCTOS
# ──────────────────────────────────────────────
def obtener_shopify(token):
    headers = {"X-Shopify-Access-Token": token}
    base = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}"
    url  = f"{base}/products.json?limit=250&fields=id,title,variants"
    productos = []

    while url:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        lote = r.json().get('products', [])
        for p in lote:
            for v in p.get('variants', []):
                productos.append({
                    'shopify_product_id': p['id'],
                    'shopify_title':      p['title'],
                    'shopify_variant_id': v['id'],
                    'shopify_sku':        v.get('sku', '') or '',
                    'shopify_price':      v.get('price', ''),
                })
        # Paginación
        link = r.headers.get('Link', '')
        url = None
        for part in link.split(','):
            if 'rel="next"' in part:
                url = part.strip().split(';')[0].strip().strip('<>')
                break

    log.info(f"Productos Shopify descargados: {len(productos)}")
    return productos


# ──────────────────────────────────────────────
#  API CENTRO JAPÓN
# ──────────────────────────────────────────────
def obtener_api():
    log.info("Descargando productos de la API...")
    r = requests.get(API_URL, timeout=120)
    r.raise_for_status()
    data = r.json()
    productos = data if isinstance(data, list) else data.get('productos', data.get('inventario', []))
    log.info(f"Productos API: {len(productos)}")
    return productos


# ──────────────────────────────────────────────
#  REPORTE
# ──────────────────────────────────────────────
def generar_reporte(api_prods, shopify_prods):
    # Índice Shopify por SKU (para ver coincidencias exactas)
    shopify_por_sku   = {p['shopify_sku']: p for p in shopify_prods if p['shopify_sku']}
    # Índice Shopify por título normalizado
    shopify_por_titulo = {}
    for p in shopify_prods:
        titulo_norm = p['shopify_title'].strip().upper()
        shopify_por_titulo.setdefault(titulo_norm, []).append(p)

    filas = []

    # ── 1. Productos de la API y su estado en Shopify ──
    for prod in api_prods:
        codigo      = str(prod.get('codigo', '') or '')
        descripcion = str(prod.get('descripcion', '') or '').strip()
        precio      = prod.get('precio_venta_2', prod.get('precio_venta_1', ''))
        disponible  = prod.get('disponible', prod.get('stock', ''))

        match_sku    = shopify_por_sku.get(codigo)
        match_titulo = shopify_por_titulo.get(descripcion.upper(), [])

        if match_sku:
            estado = 'COINCIDE_SKU'
            shopify_id    = match_sku['shopify_product_id']
            shopify_titulo = match_sku['shopify_title']
            shopify_sku   = match_sku['shopify_sku']
        elif match_titulo:
            # Puede haber más de uno con el mismo título
            estado = f'COINCIDE_TITULO({len(match_titulo)})'
            shopify_id     = match_titulo[0]['shopify_product_id']
            shopify_titulo = match_titulo[0]['shopify_title']
            shopify_sku    = match_titulo[0]['shopify_sku']
        else:
            estado = 'SOLO_EN_API'
            shopify_id = shopify_titulo = shopify_sku = ''

        filas.append({
            'estado':           estado,
            'api_codigo':       codigo,
            'api_descripcion':  descripcion,
            'api_precio':       precio,
            'api_disponible':   disponible,
            'shopify_id':       shopify_id,
            'shopify_titulo':   shopify_titulo,
            'shopify_sku':      shopify_sku,
        })

    # ── 2. Productos de Shopify que NO están en la API ──
    codigos_api = {str(p.get('codigo', '')) for p in api_prods}
    for sp in shopify_prods:
        sku = sp['shopify_sku']
        if sku and sku in codigos_api:
            continue  # Ya está en el reporte
        if not sku:
            # Ver si el título coincide
            titulo_norm = sp['shopify_title'].strip().upper()
            coincide = any(
                str(p.get('descripcion', '')).strip().upper() == titulo_norm
                for p in api_prods
            )
            if coincide:
                continue  # Ya está en el reporte
            filas.append({
                'estado':          'SOLO_EN_SHOPIFY_SIN_SKU',
                'api_codigo':       '',
                'api_descripcion':  '',
                'api_precio':       '',
                'api_disponible':   '',
                'shopify_id':       sp['shopify_product_id'],
                'shopify_titulo':   sp['shopify_title'],
                'shopify_sku':      sp['shopify_sku'],
            })

    # ── Escribir CSV ──
    archivo = 'diagnostico_productos.csv'
    campos = ['estado', 'api_codigo', 'api_descripcion', 'api_precio',
              'api_disponible', 'shopify_id', 'shopify_titulo', 'shopify_sku']

    with open(archivo, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)

    # ── Resumen en consola ──
    from collections import Counter
    conteo = Counter(r['estado'].split('(')[0] for r in filas)

    print("\n" + "="*55)
    print("  RESUMEN DEL DIAGNÓSTICO")
    print("="*55)
    print(f"  Total filas generadas:         {len(filas)}")
    print(f"  COINCIDE_SKU:                  {conteo.get('COINCIDE_SKU', 0)}")
    print(f"  COINCIDE_TITULO:               {conteo.get('COINCIDE_TITULO', 0)}")
    print(f"  SOLO_EN_API (se crearían):     {conteo.get('SOLO_EN_API', 0)}")
    print(f"  SOLO_EN_SHOPIFY_SIN_SKU:       {conteo.get('SOLO_EN_SHOPIFY_SIN_SKU', 0)}")
    print("="*55)
    print(f"\n  Reporte guardado en: {archivo}")
    print("  Abre este archivo en Excel para revisar.\n")

    return archivo


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────
if __name__ == '__main__':
    if not all([SHOPIFY_STORE, SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET, API_URL]):
        log.error("Faltan variables en .env. Revisa SHOPIFY_STORE, SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET, API_URL")
        sys.exit(1)

    token       = obtener_token()
    shopify     = obtener_shopify(token)
    api         = obtener_api()
    generar_reporte(api, shopify)
