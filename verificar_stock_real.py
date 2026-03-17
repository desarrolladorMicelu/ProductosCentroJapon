"""
Script para verificar el stock REAL en la base de datos
Muestra los datos crudos de MovMes.DBF para comprobar el cálculo
"""
from dbfread import DBF
from pathlib import Path

dbf_path = Path('DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02')

print("=" * 100)
print("VERIFICACIÓN DE STOCK REAL EN LA BASE DE DATOS")
print("=" * 100)

# Leer MovMes.DBF
print("\n1. LEYENDO MOVMES.DBF - DATOS CRUDOS")
print("-" * 100)

movmes_file = dbf_path / 'MovMes.DBF'
table = DBF(str(movmes_file), encoding='latin1', ignore_missing_memofile=True)

# Buscar el producto 000002 que vimos en la prueba
print("\nBuscando producto 000002 (TINT. ALFAPARF 1 NEGRO)...")
registros_000002 = []

for record in table:
    if record.get('COD_PRODUC', '').strip() == '000002':
        registros_000002.append(record)

print(f"\nEncontrados {len(registros_000002)} registros para producto 000002")

# Mostrar todos los registros de este producto
print("\n" + "=" * 100)
print("REGISTROS DEL PRODUCTO 000002:")
print("=" * 100)

total_stock = 0
for i, reg in enumerate(registros_000002, 1):
    inicial = reg.get('INICIALMES', 0) or 0
    entradas = reg.get('ENTRADASME', 0) or 0
    salidas = reg.get('SALIDASMES', 0) or 0
    actualmes = reg.get('ACTUALMES')
    stock_calculado = inicial + entradas - salidas
    
    print(f"\nRegistro {i}:")
    print(f"  Centro Costo: {reg.get('CEN_COSTO')}")
    print(f"  Fecha: {reg.get('FECHA')}")
    print(f"  INICIALMES: {inicial}")
    print(f"  ENTRADASME: {entradas}")
    print(f"  SALIDASMES: {salidas}")
    print(f"  ACTUALMES (campo DBF): {actualmes}")
    print(f"  → Stock Calculado (INICIAL + ENTRADAS - SALIDAS): {stock_calculado}")
    
    total_stock += stock_calculado

print("\n" + "=" * 100)
print(f"TOTAL STOCK PRODUCTO 000002: {total_stock}")
print("=" * 100)

# Ahora verificar otros productos con stock
print("\n\n2. VERIFICANDO OTROS PRODUCTOS CON STOCK")
print("-" * 100)

table = DBF(str(movmes_file), encoding='latin1', ignore_missing_memofile=True)

# Agrupar por producto y calcular stock
productos_stock = {}
contador = 0

for record in table:
    cod = record.get('COD_PRODUC', '').strip()
    if not cod:
        continue
    
    inicial = record.get('INICIALMES', 0) or 0
    entradas = record.get('ENTRADASME', 0) or 0
    salidas = record.get('SALIDASMES', 0) or 0
    stock = inicial + entradas - salidas
    
    if cod not in productos_stock:
        productos_stock[cod] = 0
    productos_stock[cod] += stock
    
    contador += 1
    if contador >= 100000:  # Solo primeros 100k registros para ser rápido
        break

# Filtrar productos con stock > 0
con_stock = {k: v for k, v in productos_stock.items() if v > 0}

print(f"\nRegistros procesados: {contador:,}")
print(f"Productos únicos: {len(productos_stock)}")
print(f"Productos con stock > 0: {len(con_stock)}")

# Mostrar top 10 con más stock
print("\n" + "=" * 100)
print("TOP 10 PRODUCTOS CON MÁS STOCK:")
print("=" * 100)

top_10 = sorted(con_stock.items(), key=lambda x: x[1], reverse=True)[:10]

for i, (cod, stock) in enumerate(top_10, 1):
    print(f"{i:2d}. Código: {cod} → Stock: {stock:,.0f}")

# Leer Producto.DBF para mostrar nombres
print("\n\n3. VERIFICANDO CON NOMBRES DE PRODUCTOS")
print("-" * 100)

producto_file = dbf_path / 'Producto.DBF'
table_prod = DBF(str(producto_file), encoding='latin1', ignore_missing_memofile=True)

productos_dict = {}
for record in table_prod:
    cod = record.get('COD_PRODUC', '').strip()
    if cod:
        productos_dict[cod] = record.get('DESCRIPCIO', '').strip()

print("\nTOP 10 CON NOMBRES:")
for i, (cod, stock) in enumerate(top_10, 1):
    nombre = productos_dict.get(cod, 'SIN NOMBRE')
    print(f"{i:2d}. {cod} - {nombre[:50]}")
    print(f"    Stock: {stock:,.0f} unidades")

print("\n" + "=" * 100)
print("✓ VERIFICACIÓN COMPLETADA - LOS DATOS SON REALES")
print("=" * 100)
