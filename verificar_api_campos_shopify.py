"""
Verificar que la API envía los campos que necesita Shopify
"""
import os
os.environ['DBF_PATH'] = 'DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02'

from src.dbf_reader import DBFReader
import json

print("=" * 100)
print("VERIFICACIÓN: ¿LA API ENVÍA LOS CAMPOS QUE NECESITA SHOPIFY?")
print("=" * 100)

dbf_path = 'DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02'
reader = DBFReader(dbf_path)

print("\n1. OBTENIENDO DATOS DE LA API...")
print("-" * 100)

inventario = reader.get_inventario_con_precios()
print(f"Total productos: {len(inventario)}")

# Verificar primeros 10 productos
print("\n\n2. VERIFICANDO CAMPOS EN LOS PRIMEROS 10 PRODUCTOS:")
print("-" * 100)

for i, producto in enumerate(inventario[:10], 1):
    print(f"\n{i}. Código: {producto['codigo']}")
    print(f"   Descripción: {producto['descripcion'][:50]}")
    print(f"   cod_largo: {producto.get('cod_largo', 'NO EXISTE')} {'✓' if producto.get('cod_largo') else '⚠ VACÍO'}")
    print(f"   cod_invent: {producto.get('cod_invent', 'NO EXISTE')} {'✓' if producto.get('cod_invent') else '⚠ VACÍO'}")
    print(f"   precio_venta_2: {producto.get('precio_venta_2', 'NO EXISTE')}")
    print(f"   disponible: {producto.get('disponible', 'NO EXISTE')}")
    print(f"   activo: {producto.get('activo', 'NO EXISTE')}")

# Simular lo que haría el script de Shopify
print("\n\n3. SIMULACIÓN DE LO QUE RECIBIRÍA SHOPIFY:")
print("-" * 100)

def obtener_sku_producto(producto: dict) -> str:
    """Lógica exacta del script de Shopify"""
    return (
        (producto.get('cod_largo') or '').strip()
        or (producto.get('cod_invent') or '').strip()
    ).upper()

for i, producto in enumerate(inventario[:10], 1):
    sku = obtener_sku_producto(producto)
    titulo = (producto.get('descripcion') or '').strip()
    precio = str(producto.get('precio_venta_2', 0))
    stock = max(0, int(producto.get('disponible', 0)))
    
    print(f"\n{i}. Producto que se crearía/actualizaría en Shopify:")
    print(f"   Title: {titulo}")
    print(f"   SKU: {sku} {'⚠ VACÍO - NO SE SINCRONIZARÁ' if not sku else '✓'}")
    print(f"   Price: ${precio}")
    print(f"   Stock: {stock}")

# Estadísticas
print("\n\n4. ESTADÍSTICAS DE CAMPOS:")
print("-" * 100)

con_cod_largo = sum(1 for p in inventario if p.get('cod_largo'))
con_cod_invent = sum(1 for p in inventario if p.get('cod_invent'))
sin_sku = sum(1 for p in inventario if not obtener_sku_producto(p))

print(f"Total productos: {len(inventario)}")
print(f"Con cod_largo: {con_cod_largo} ({con_cod_largo/len(inventario)*100:.1f}%)")
print(f"Con cod_invent: {con_cod_invent} ({con_cod_invent/len(inventario)*100:.1f}%)")
print(f"Sin SKU (no se sincronizarán): {sin_sku} ({sin_sku/len(inventario)*100:.1f}%)")

# Verificar estructura JSON completa de un producto
print("\n\n5. ESTRUCTURA JSON COMPLETA DE UN PRODUCTO (ejemplo):")
print("-" * 100)
print(json.dumps(inventario[1], indent=2, ensure_ascii=False))

print("\n" + "=" * 100)
print("✓ VERIFICACIÓN COMPLETADA")
print("=" * 100)
