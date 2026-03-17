"""
Script para verificar de dónde viene la descripción y si se extrae bien
"""
from dbfread import DBF
from pathlib import Path

dbf_path = Path('DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02')

print("=" * 100)
print("VERIFICACIÓN DE DESCRIPCIÓN EN PRODUCTO.DBF")
print("=" * 100)

# Leer Producto.DBF
producto_file = dbf_path / 'Producto.DBF'
table = DBF(str(producto_file), encoding='latin1', ignore_missing_memofile=True)

print("\n1. ESTRUCTURA DE PRODUCTO.DBF")
print("-" * 100)
print(f"Columnas disponibles: {list(table.field_names)}")

# Buscar campos que puedan contener descripción
campos_descripcion = [campo for campo in table.field_names if 'DESC' in campo.upper() or 'NOMBRE' in campo.upper()]
print(f"\nCampos relacionados con descripción: {campos_descripcion}")

# Leer algunos registros
print("\n\n2. EJEMPLOS DE PRODUCTOS (primeros 10)")
print("-" * 100)

records = list(table)[:10]

for i, record in enumerate(records, 1):
    print(f"\n{i}. Código: {record.get('COD_PRODUC', 'N/A')}")
    
    # Mostrar todos los campos que puedan ser descripción
    for campo in campos_descripcion:
        valor = record.get(campo)
        if isinstance(valor, bytes):
            try:
                valor = valor.decode('latin1').strip()
            except:
                valor = str(valor)
        print(f"   {campo}: {valor}")
    
    # Mostrar otros campos relevantes
    print(f"   REFERENCIA: {record.get('REFERENCIA', 'N/A')}")
    print(f"   ACTIVO: {record.get('ACTIVO', 'N/A')}")
    print(f"   VENTA1: {record.get('VENTA1', 'N/A')}")

# Verificar el campo DESCRIPCIO específicamente
print("\n\n3. ANÁLISIS DEL CAMPO 'DESCRIPCIO'")
print("-" * 100)

table = DBF(str(producto_file), encoding='latin1', ignore_missing_memofile=True)
descripciones = []
vacias = 0
con_datos = 0

for record in list(table)[:1000]:  # Primeros 1000 registros
    desc = record.get('DESCRIPCIO')
    
    if desc:
        if isinstance(desc, bytes):
            try:
                desc = desc.decode('latin1').strip()
            except:
                desc = str(desc)
        else:
            desc = str(desc).strip()
        
        if desc:
            con_datos += 1
            if len(descripciones) < 20:
                descripciones.append((record.get('COD_PRODUC'), desc))
        else:
            vacias += 1
    else:
        vacias += 1

print(f"Registros analizados: 1000")
print(f"Con descripción: {con_datos}")
print(f"Sin descripción o vacías: {vacias}")

print("\n\n4. EJEMPLOS DE DESCRIPCIONES EXTRAÍDAS:")
print("-" * 100)

for cod, desc in descripciones:
    print(f"  {cod}: {desc}")

# Verificar si hay caracteres especiales o problemas de encoding
print("\n\n5. VERIFICACIÓN DE ENCODING")
print("-" * 100)

table = DBF(str(producto_file), encoding='latin1', ignore_missing_memofile=True)
problemas = []

for record in list(table)[:100]:
    desc = record.get('DESCRIPCIO')
    if desc:
        if isinstance(desc, bytes):
            try:
                desc_str = desc.decode('latin1')
            except Exception as e:
                problemas.append((record.get('COD_PRODUC'), str(e)))
        else:
            desc_str = str(desc)
        
        # Buscar caracteres raros
        if any(ord(c) < 32 and c not in '\n\r\t' for c in desc_str):
            problemas.append((record.get('COD_PRODUC'), "Caracteres de control"))

if problemas:
    print(f"⚠ Encontrados {len(problemas)} productos con problemas de encoding:")
    for cod, problema in problemas[:10]:
        print(f"  {cod}: {problema}")
else:
    print("✓ No se encontraron problemas de encoding en los primeros 100 registros")

# Comparar con lo que retorna la API
print("\n\n6. COMPARACIÓN CON LA API")
print("-" * 100)

from src.dbf_reader import DBFReader

reader = DBFReader(str(dbf_path))
inventario = reader.get_inventario_con_precios()

print(f"Total productos en API: {len(inventario)}")

# Mostrar algunos ejemplos
print("\nEjemplos de lo que retorna la API:")
for i, producto in enumerate(inventario[:10], 1):
    print(f"\n{i}. Código: {producto['codigo']}")
    print(f"   Descripción: {producto['descripcion']}")
    print(f"   Referencia: {producto['referencia']}")
    print(f"   Disponible: {producto['disponible']}")

print("\n" + "=" * 100)
print("✓ VERIFICACIÓN COMPLETADA")
print("=" * 100)
