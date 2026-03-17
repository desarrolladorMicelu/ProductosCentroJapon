"""
Script para analizar la estructura de MovMes y entender el problema del stock
"""
from dbfread import DBF
from pathlib import Path

# Ruta a la BD de ejemplo
dbf_path = Path('DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02')

print("=" * 80)
print("ANÁLISIS DE MOVMES - DIAGNÓSTICO DE STOCK EN 0")
print("=" * 80)

# 1. Analizar MovMes.DBF
print("\n1. ESTRUCTURA DE MovMes.DBF:")
print("-" * 80)
movmes_file = dbf_path / 'MovMes.DBF'
if movmes_file.exists():
    table = DBF(str(movmes_file), encoding='latin1', ignore_missing_memofile=True)
    print(f"Columnas: {list(table.field_names)}")
    
    records = list(table)
    print(f"\nTotal registros: {len(records)}")
    
    if records:
        print("\nPrimeros 3 registros:")
        for i, record in enumerate(records[:3]):
            print(f"\n  Registro {i+1}:")
            for key, value in record.items():
                print(f"    {key}: {value}")
        
        # Analizar campos de stock
        print("\n  Análisis de campos de stock:")
        campos_stock = ['ACTUALMES', 'INICIALMES', 'ENTRADASME', 'SALIDASMES']
        for campo in campos_stock:
            valores = [r.get(campo, 0) for r in records if r.get(campo) is not None]
            if valores:
                print(f"    {campo}: min={min(valores)}, max={max(valores)}, promedio={sum(valores)/len(valores):.2f}")
            else:
                print(f"    {campo}: NO TIENE DATOS")
else:
    print("  ⚠ MovMes.DBF NO EXISTE")

# 2. Analizar MovMes03.DBF (marzo)
print("\n\n2. ESTRUCTURA DE MovMes03.DBF (Marzo):")
print("-" * 80)
movmes03_file = dbf_path / 'MovMes03.DBF'
if movmes03_file.exists():
    table = DBF(str(movmes03_file), encoding='latin1', ignore_missing_memofile=True)
    print(f"Columnas: {list(table.field_names)}")
    
    records = list(table)
    print(f"\nTotal registros: {len(records)}")
    
    if records:
        print("\nPrimeros 3 registros:")
        for i, record in enumerate(records[:3]):
            print(f"\n  Registro {i+1}:")
            for key, value in record.items():
                print(f"    {key}: {value}")
        
        # Analizar campos de stock
        print("\n  Análisis de campos de stock:")
        campos_stock = ['ACTUALMES', 'INICIALMES', 'ENTRADASME', 'SALIDASMES']
        for campo in campos_stock:
            valores = [r.get(campo, 0) for r in records if r.get(campo) is not None]
            if valores:
                print(f"    {campo}: min={min(valores)}, max={max(valores)}, promedio={sum(valores)/len(valores):.2f}")
            else:
                print(f"    {campo}: NO TIENE DATOS")
        
        # Contar productos con stock > 0
        productos_con_stock = sum(1 for r in records if (r.get('ACTUALMES') or 0) > 0)
        print(f"\n  Productos con ACTUALMES > 0: {productos_con_stock} de {len(records)}")
else:
    print("  ⚠ MovMes03.DBF NO EXISTE")

# 3. Verificar qué archivos MovMes existen
print("\n\n3. ARCHIVOS MOVMES DISPONIBLES:")
print("-" * 80)
for mes in range(1, 13):
    archivo = dbf_path / f'MovMes{mes:02d}.DBF'
    if archivo.exists():
        size = archivo.stat().st_size
        table = DBF(str(archivo), encoding='latin1', ignore_missing_memofile=True)
        records = list(table)
        con_stock = sum(1 for r in records if (r.get('ACTUALMES') or 0) > 0)
        print(f"  ✓ MovMes{mes:02d}.DBF - {len(records)} registros, {con_stock} con stock, {size:,} bytes")

# 4. Comparar con Producto.DBF
print("\n\n4. COMPARACIÓN CON PRODUCTO.DBF:")
print("-" * 80)
producto_file = dbf_path / 'Producto.DBF'
if producto_file.exists():
    table = DBF(str(producto_file), encoding='latin1', ignore_missing_memofile=True)
    productos = list(table)
    activos = [p for p in productos if p.get('ACTIVO')]
    print(f"  Total productos: {len(productos)}")
    print(f"  Productos activos: {len(activos)}")
    
    if activos:
        print("\n  Ejemplo de producto activo:")
        ejemplo = activos[0]
        print(f"    COD_PRODUC: {ejemplo.get('COD_PRODUC')}")
        print(f"    DESCRIPCIO: {ejemplo.get('DESCRIPCIO')}")
        print(f"    VENTA1: {ejemplo.get('VENTA1')}")
        print(f"    COSTO: {ejemplo.get('COSTO')}")
        print(f"    ACTIVO: {ejemplo.get('ACTIVO')}")

print("\n" + "=" * 80)
print("FIN DEL ANÁLISIS")
print("=" * 80)
