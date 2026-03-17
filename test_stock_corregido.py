"""
Script para probar la corrección del cálculo de stock
"""
from src.dbf_reader import DBFReader
from pathlib import Path

print("=" * 80)
print("PRUEBA DE CORRECCIÓN DE STOCK")
print("=" * 80)

# Usar la BD de ejemplo
dbf_path = 'DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02'
reader = DBFReader(dbf_path)

print("\nObteniendo inventario con precios...")
inventario = reader.get_inventario_con_precios()

print(f"\nTotal productos: {len(inventario)}")

# Filtrar productos con stock > 0
con_stock = [p for p in inventario if p['disponible'] > 0]
print(f"Productos con stock > 0: {len(con_stock)}")

# Mostrar algunos ejemplos
print("\n" + "=" * 80)
print("EJEMPLOS DE PRODUCTOS CON STOCK:")
print("=" * 80)

for i, producto in enumerate(con_stock[:10]):
    print(f"\n{i+1}. {producto['codigo']} - {producto['descripcion'][:50]}")
    print(f"   Disponible: {producto['disponible']}")
    print(f"   Precio Venta 1: ${producto['precio_venta_1']:,.2f}")
    print(f"   Costo: ${producto['costo']:,.2f}")

# Estadísticas
if con_stock:
    stocks = [p['disponible'] for p in con_stock]
    print("\n" + "=" * 80)
    print("ESTADÍSTICAS DE STOCK:")
    print("=" * 80)
    print(f"  Stock mínimo: {min(stocks)}")
    print(f"  Stock máximo: {max(stocks)}")
    print(f"  Stock promedio: {sum(stocks)/len(stocks):.2f}")
    print(f"  Stock total: {sum(stocks):,.0f}")

# Productos sin stock
sin_stock = [p for p in inventario if p['disponible'] == 0]
print(f"\nProductos con stock = 0: {len(sin_stock)}")

print("\n" + "=" * 80)
print("✓ PRUEBA COMPLETADA")
print("=" * 80)
