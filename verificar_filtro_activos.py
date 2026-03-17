"""
Verificar si el código filtra productos inactivos
"""
from dbfread import DBF
from pathlib import Path
import os
os.environ['DBF_PATH'] = 'DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02'

from src.dbf_reader import DBFReader

dbf_path = Path('DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02')

print("=" * 100)
print("VERIFICACIÓN: ¿SE FILTRAN PRODUCTOS INACTIVOS?")
print("=" * 100)

# 1. Verificar en la BD cuántos productos hay activos vs inactivos
print("\n1. ANÁLISIS DE PRODUCTO.DBF:")
print("-" * 100)

producto_file = dbf_path / 'Producto.DBF'
table = DBF(str(producto_file), encoding='latin1', ignore_missing_memofile=True)

total = 0
activos = 0
inactivos = 0

for record in table:
    total += 1
    if record.get('ACTIVO'):
        activos += 1
    else:
        inactivos += 1

print(f"Total productos en BD: {total}")
print(f"  Activos (ACTIVO = True): {activos} ({activos/total*100:.1f}%)")
print(f"  Inactivos (ACTIVO = False): {inactivos} ({inactivos/total*100:.1f}%)")

# 2. Verificar qué retorna la API
print("\n\n2. ANÁLISIS DE LA API:")
print("-" * 100)

reader = DBFReader(str(dbf_path))
inventario = reader.get_inventario_con_precios()

print(f"Total productos retornados por API: {len(inventario)}")

# Verificar si todos son activos
todos_activos = all(p.get('activo') for p in inventario)
print(f"¿Todos los productos son activos? {todos_activos}")

# Contar activos e inactivos en la respuesta
activos_api = sum(1 for p in inventario if p.get('activo'))
inactivos_api = sum(1 for p in inventario if not p.get('activo'))

print(f"  Activos en API: {activos_api}")
print(f"  Inactivos en API: {inactivos_api}")

# 3. Buscar ejemplos de productos inactivos en la BD
print("\n\n3. EJEMPLOS DE PRODUCTOS INACTIVOS EN LA BD:")
print("-" * 100)

table = DBF(str(producto_file), encoding='latin1', ignore_missing_memofile=True)
inactivos_ejemplos = []

for record in table:
    if not record.get('ACTIVO'):
        inactivos_ejemplos.append({
            'codigo': record.get('COD_PRODUC'),
            'descripcion': record.get('DESCRIPCIO', '').strip()[:50]
        })
        if len(inactivos_ejemplos) >= 5:
            break

if inactivos_ejemplos:
    print(f"Encontrados {len(inactivos_ejemplos)} ejemplos de productos inactivos:")
    for ej in inactivos_ejemplos:
        print(f"  - {ej['codigo']}: {ej['descripcion']}")
    
    # Verificar si estos productos están en la API
    print("\n  ¿Estos productos inactivos están en la API?")
    codigos_api = {p['codigo'] for p in inventario}
    for ej in inactivos_ejemplos:
        esta = ej['codigo'] in codigos_api
        print(f"    {ej['codigo']}: {'SÍ ⚠' if esta else 'NO ✓'}")
else:
    print("No se encontraron productos inactivos en la BD")

# 4. Conclusión
print("\n\n4. CONCLUSIÓN:")
print("-" * 100)

if activos == len(inventario):
    print("✓ LA API FILTRA CORRECTAMENTE")
    print(f"  - BD tiene {activos} productos activos")
    print(f"  - API retorna {len(inventario)} productos")
    print(f"  - Coinciden perfectamente")
else:
    print("⚠ HAY UNA DIFERENCIA")
    print(f"  - BD tiene {activos} productos activos")
    print(f"  - API retorna {len(inventario)} productos")
    print(f"  - Diferencia: {abs(activos - len(inventario))}")

print("\n" + "=" * 100)
print("✓ VERIFICACIÓN COMPLETADA")
print("=" * 100)
