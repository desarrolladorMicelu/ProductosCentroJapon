"""
Verificar qué campos se usan como SKU en Shopify
"""
from dbfread import DBF
from pathlib import Path

dbf_path = Path('DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02')

print("=" * 100)
print("VERIFICACIÓN DE CAMPOS SKU PARA SHOPIFY")
print("=" * 100)

producto_file = dbf_path / 'Producto.DBF'
table = DBF(str(producto_file), encoding='latin1', ignore_missing_memofile=True)

print("\n1. ANÁLISIS DE CAMPOS COD_LARGO Y COD_INVENT")
print("-" * 100)

con_cod_largo = 0
con_cod_invent = 0
con_ambos = 0
sin_ninguno = 0
ejemplos = []

for i, record in enumerate(table):
    if i >= 1000:  # Primeros 1000
        break
    
    cod_largo = (record.get('COD_LARGO') or '').strip()
    cod_invent = (record.get('COD_INVENT') or '').strip()
    cod_produc = record.get('COD_PRODUC', '').strip()
    descripcion = record.get('DESCRIPCIO', '').strip()
    
    tiene_largo = bool(cod_largo)
    tiene_invent = bool(cod_invent)
    
    if tiene_largo and tiene_invent:
        con_ambos += 1
    elif tiene_largo:
        con_cod_largo += 1
    elif tiene_invent:
        con_cod_invent += 1
    else:
        sin_ninguno += 1
    
    # Guardar ejemplos
    if len(ejemplos) < 10:
        ejemplos.append({
            'cod_produc': cod_produc,
            'descripcion': descripcion[:40],
            'cod_largo': cod_largo or 'VACÍO',
            'cod_invent': cod_invent or 'VACÍO'
        })

print(f"Registros analizados: 1000")
print(f"  Con COD_LARGO solamente: {con_cod_largo}")
print(f"  Con COD_INVENT solamente: {con_cod_invent}")
print(f"  Con ambos: {con_ambos}")
print(f"  Sin ninguno: {sin_ninguno}")

print("\n\n2. EJEMPLOS DE PRODUCTOS:")
print("-" * 100)

for ej in ejemplos:
    print(f"\nCódigo: {ej['cod_produc']}")
    print(f"  Descripción: {ej['descripcion']}")
    print(f"  COD_LARGO: {ej['cod_largo']}")
    print(f"  COD_INVENT: {ej['cod_invent']}")

# Simular qué SKU usaría Shopify
print("\n\n3. SIMULACIÓN DE SKU PARA SHOPIFY:")
print("-" * 100)

table = DBF(str(producto_file), encoding='latin1', ignore_missing_memofile=True)

for i, record in enumerate(list(table)[:10]):
    cod_produc = record.get('COD_PRODUC', '').strip()
    descripcion = record.get('DESCRIPCIO', '').strip()[:40]
    cod_largo = (record.get('COD_LARGO') or '').strip()
    cod_invent = (record.get('COD_INVENT') or '').strip()
    
    # Lógica del script de Shopify
    sku = (cod_largo or cod_invent).upper()
    
    print(f"\n{i+1}. {cod_produc} - {descripcion}")
    print(f"   SKU que usaría Shopify: '{sku}' {'⚠ VACÍO' if not sku else '✓'}")

print("\n" + "=" * 100)
print("✓ VERIFICACIÓN COMPLETADA")
print("=" * 100)
