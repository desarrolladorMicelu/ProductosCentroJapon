"""
Sincronización de productos: API Centro Japón → Shopify
Consulta inventario desde la API y crea/actualiza productos en Shopify.
"""
import os
import sys
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
#  CONFIGURACIÓN
# ──────────────────────────────────────────────
SHOPIFY_STORE = os.getenv('SHOPIFY_STORE', '')
SHOPIFY_CLIENT_ID = os.getenv('SHOPIFY_CLIENT_ID', '')
SHOPIFY_CLIENT_SECRET = os.getenv('SHOPIFY_CLIENT_SECRET', '')
API_URL = os.getenv('API_URL', '')
API_VERSION = '2024-01'
SYNC_LIMIT = int(os.getenv('SYNC_LIMIT', '0'))

# ──────────────────────────────────────────────
#  LOGGING
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sync.log', encoding='utf-8')
    ]
)
log = logging.getLogger(__name__)


# ══════════════════════════════════════════════
#  FUNCIONES AUXILIARES
# ══════════════════════════════════════════════

def validar_config():
    """Valida que todas las variables de entorno estén configuradas."""
    requeridas = {
        'SHOPIFY_STORE': SHOPIFY_STORE,
        'SHOPIFY_CLIENT_ID': SHOPIFY_CLIENT_ID,
        'SHOPIFY_CLIENT_SECRET': SHOPIFY_CLIENT_SECRET,
        'API_URL': API_URL
    }
    faltantes = [k for k, v in requeridas.items() if not v]
    if faltantes:
        log.error(f"Variables de entorno faltantes: {', '.join(faltantes)}")
        log.error("Copia .env.example a .env y completa los valores.")
        sys.exit(1)

    if SYNC_LIMIT < 0:
        log.error("SYNC_LIMIT no puede ser negativo")
        sys.exit(1)


def headers_shopify(token: str) -> dict:
    """Headers de autenticación para Shopify Admin API."""
    return {
        'X-Shopify-Access-Token': token,
        'Content-Type': 'application/json'
    }


def esperar_rate_limit(response: requests.Response) -> bool:
    """
    Maneja el rate limiting de Shopify.
    Retorna True si se debe reintentar el request.
    """
    if response.status_code == 429:
        retry = float(response.headers.get('Retry-After', 2))
        log.warning(f"Rate limit alcanzado, esperando {retry}s...")
        time.sleep(retry)
        return True

    limit = response.headers.get('X-Shopify-Shop-Api-Call-Limit', '')
    if limit:
        actual, maximo = map(int, limit.split('/'))
        if actual >= maximo - 3:
            time.sleep(1)
    return False


def obtener_url_siguiente(response: requests.Response):
    """Extrae la URL de la página siguiente del header Link (paginación Shopify)."""
    link = response.headers.get('Link', '')
    if 'rel="next"' not in link:
        return None
    for parte in link.split(','):
        if 'rel="next"' in parte:
            return parte.split(';')[0].strip().strip('<>')
    return None


def shopify_request(method: str, url: str, token: str, **kwargs):
    """
    Ejecuta un request a Shopify con reintentos automáticos por rate limit.
    Soporta GET, POST, PUT.
    """
    hdrs = headers_shopify(token)
    max_intentos = 5

    for intento in range(max_intentos):
        resp = requests.request(method, url, headers=hdrs, timeout=60, **kwargs)

        if esperar_rate_limit(resp):
            continue

        resp.raise_for_status()
        return resp

    raise Exception(f"Se excedieron {max_intentos} intentos por rate limit en {url}")


# ══════════════════════════════════════════════
#  OBTENER TOKEN DE SHOPIFY
# ══════════════════════════════════════════════

def obtener_token_shopify() -> str:
    """
    Obtiene un token OAuth temporal de Shopify usando client_credentials.
    Se genera uno nuevo en cada ejecución porque expira.
    """
    url = f"https://{SHOPIFY_STORE}/admin/oauth/access_token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': SHOPIFY_CLIENT_ID,
        'client_secret': SHOPIFY_CLIENT_SECRET
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    log.info("Obteniendo token de Shopify...")
    resp = requests.post(url, data=data, headers=headers, timeout=30)
    resp.raise_for_status()

    token_data = resp.json()
    token = token_data.get('access_token')
    if not token:
        raise Exception(f"No se recibió access_token: {token_data}")

    log.info("Token de Shopify obtenido correctamente")
    return token


# ══════════════════════════════════════════════
#  CONSULTAR API DE INVENTARIO
# ══════════════════════════════════════════════

def obtener_productos_api() -> list:
    """Consulta la API de inventario de Centro Japón."""
    log.info("Consultando API de inventario...")
    resp = requests.get(API_URL, timeout=120)
    resp.raise_for_status()

    data = resp.json()
    if not data.get('success', True):
        raise Exception(f"Error en API: {data.get('error')}")

    productos = data.get('data', [])
    log.info(f"Recibidos {len(productos)} productos de la API")
    return productos


# ══════════════════════════════════════════════
#  OBTENER PRODUCTOS EXISTENTES DE SHOPIFY
# ══════════════════════════════════════════════

def obtener_productos_shopify(token: str) -> list:
    """Obtiene TODOS los productos de Shopify manejando paginación."""
    productos = []
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/products.json?limit=250"

    log.info("Descargando productos existentes de Shopify...")
    pagina = 1

    while url:
        resp = shopify_request('GET', url, token)
        lote = resp.json().get('products', [])
        productos.extend(lote)
        log.info(f"  Página {pagina}: {len(lote)} productos (total: {len(productos)})")

        url = obtener_url_siguiente(resp)
        pagina += 1

    log.info(f"Total productos en Shopify: {len(productos)}")
    return productos


def construir_indice_sku(productos_shopify: list) -> dict:
    """
    Construye un diccionario SKU → {product_id, variant_id, inventory_item_id}
    para búsqueda rápida de duplicados.
    """
    indice = {}
    for producto in productos_shopify:
        for variante in producto.get('variants', []):
            sku = (variante.get('sku') or '').strip().upper()
            if sku:
                indice[sku] = {
                    'product_id': producto['id'],
                    'variant_id': variante['id'],
                    'inventory_item_id': variante.get('inventory_item_id')
                }
    log.info(f"Índice SKU construido: {len(indice)} SKUs únicos en Shopify")
    return indice


def obtener_sku_producto(producto: dict) -> str:
    """Obtiene el SKU a usar en Shopify: cod_largo o cod_invent únicamente."""
    return (
        (producto.get('cod_largo') or '').strip()
        or (producto.get('cod_invent') or '').strip()
    ).upper()


# ══════════════════════════════════════════════
#  UBICACIÓN DE INVENTARIO
# ══════════════════════════════════════════════

def obtener_location_id(token: str) -> int:
    """Obtiene el ID de la ubicación principal de Shopify (para inventario)."""
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/locations.json"
    resp = shopify_request('GET', url, token)

    locations = resp.json().get('locations', [])
    if not locations:
        raise Exception("No se encontraron ubicaciones en Shopify")

    location = locations[0]
    log.info(f"Ubicación principal: {location['name']} (ID: {location['id']})")
    return location['id']


# ══════════════════════════════════════════════
#  CREAR / ACTUALIZAR PRODUCTOS
# ══════════════════════════════════════════════

def crear_producto(token: str, producto: dict) -> dict:
    """Crea un nuevo producto en Shopify."""
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/products.json"
    payload = {
        'product': {
            'title': producto['descripcion'].strip(),
            'status': 'active' if producto.get('activo') else 'draft',
            'variants': [{
                'sku': obtener_sku_producto(producto),
                'price': str(producto.get('precio_venta_2', 0)),
                'inventory_management': 'shopify'
            }]
        }
    }

    resp = shopify_request('POST', url, token, json=payload)
    return resp.json()['product']


def actualizar_producto(token: str, product_id: int, variant_id: int, producto: dict) -> dict:
    """Actualiza título y precio de un producto existente en Shopify."""
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/products/{product_id}.json"
    payload = {
        'product': {
            'id': product_id,
            'title': producto['descripcion'].strip(),
            'variants': [{
                'id': variant_id,
                'price': str(producto.get('precio_venta_2', 0))
            }]
        }
    }

    resp = shopify_request('PUT', url, token, json=payload)
    return resp.json()['product']


def actualizar_inventario(token: str, location_id: int, inventory_item_id: int, cantidad: int):
    """Establece el nivel de inventario de una variante en Shopify."""
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/inventory_levels/set.json"
    payload = {
        'location_id': location_id,
        'inventory_item_id': inventory_item_id,
        'available': max(0, int(cantidad))
    }

    shopify_request('POST', url, token, json=payload)


# ══════════════════════════════════════════════
#  SINCRONIZACIÓN PRINCIPAL
# ══════════════════════════════════════════════

def sincronizar():
    """Función principal: consulta la API y sincroniza todo hacia Shopify."""
    log.info("=" * 60)
    log.info("SINCRONIZACIÓN API → SHOPIFY")
    log.info("=" * 60)

    validar_config()

    # 1. Obtener token fresco de Shopify
    token = obtener_token_shopify()

    # 2. Obtener productos de la API de inventario
    productos_api = obtener_productos_api()
    if not productos_api:
        log.warning("No se recibieron productos de la API. Nada que sincronizar.")
        return

    if SYNC_LIMIT > 0:
        productos_api = productos_api[:SYNC_LIMIT]
        log.info(f"Modo prueba activo: solo se sincronizarán {len(productos_api)} productos")

    # 3. Obtener productos existentes en Shopify y construir índice por SKU
    productos_shopify = obtener_productos_shopify(token)
    indice_sku = construir_indice_sku(productos_shopify)

    # 4. Obtener ubicación principal (necesaria para actualizar inventario)
    location_id = obtener_location_id(token)

    # 5. Sincronizar producto por producto
    creados = 0
    actualizados = 0
    errores = 0
    total = len(productos_api)

    log.info(f"Iniciando sincronización de {total} productos...")
    log.info("-" * 60)

    for i, producto in enumerate(productos_api, 1):
        sku = obtener_sku_producto(producto)
        nombre = (producto.get('descripcion') or '').strip()

        if not sku:
            log.warning(f"  [{i}/{total}] Producto sin cod_largo/cod_invent, saltando: {nombre}")
            errores += 1
            continue

        try:
            cantidad = producto.get('disponible', 0)

            if sku in indice_sku:
                # ─── ACTUALIZAR producto existente ───
                info = indice_sku[sku]
                actualizar_producto(token, info['product_id'], info['variant_id'], producto)

                if info.get('inventory_item_id'):
                    actualizar_inventario(token, location_id, info['inventory_item_id'], cantidad)

                actualizados += 1
                log.info(f"  [{i}/{total}] ACTUALIZADO: {sku} - {nombre} (stock: {cantidad})")

            else:
                # ─── CREAR producto nuevo ───
                nuevo = crear_producto(token, producto)

                variant = nuevo['variants'][0]
                if variant.get('inventory_item_id'):
                    actualizar_inventario(token, location_id, variant['inventory_item_id'], cantidad)

                # Agregar al índice para evitar duplicados en esta misma ejecución
                indice_sku[sku] = {
                    'product_id': nuevo['id'],
                    'variant_id': variant['id'],
                    'inventory_item_id': variant.get('inventory_item_id')
                }

                creados += 1
                log.info(f"  [{i}/{total}] CREADO: {sku} - {nombre} (stock: {cantidad})")

        except requests.exceptions.HTTPError as e:
            errores += 1
            detalle = e.response.text[:200] if e.response else str(e)
            log.error(f"  [{i}/{total}] ERROR HTTP en {sku}: {e.response.status_code} - {detalle}")

        except Exception as e:
            errores += 1
            log.error(f"  [{i}/{total}] ERROR en {sku}: {e}")

    # ─── Resumen final ───
    log.info("=" * 60)
    log.info("SINCRONIZACIÓN COMPLETADA")
    log.info(f"  Creados:      {creados}")
    log.info(f"  Actualizados: {actualizados}")
    log.info(f"  Errores:      {errores}")
    log.info(f"  Total:        {total}")
    log.info("=" * 60)


# ══════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ══════════════════════════════════════════════

if __name__ == '__main__':
    try:
        sincronizar()
    except KeyboardInterrupt:
        log.info("\nSincronización cancelada por el usuario")
    except Exception as e:
        log.error(f"Error fatal: {e}")
        sys.exit(1)
