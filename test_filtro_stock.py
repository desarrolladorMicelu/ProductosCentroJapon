"""
Probar que solo se retornan productos con stock > 0
"""
import os
os.environ['DBF_PATH'] = 'DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02'

from src.dbf_reader import DBFReader

print("=" * 100)
print("PRUEBA: FILTRO DE PRODUCTOS CON STOCK > 0")
print("=" * 100)

dbf_path = 'DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02'
reader = DBFReader(dbf_path)

print("\nObteniendo inventario con precios...")
inventario = reader.get_inventario_con_precios()

print(f"\nTotal productos retornados: {len(inventario)}")

# Verificar que TODOS tienen stock > 0
con_stock = [p for p in inventario if p['disponible'] > 0]
sin_stock = [p for p in inventario if p['disponible'] <= 0]

print(f"  Con stock > 0: {len(con_stock)}")
print(f"  Con stock <= 0: {len(sin_stock)}")

if sin_stock:
    print("\n⚠ ERROR: Se encontraron productos con stock <= 0:")
    for p in sin_stock[:5]:
        print(f"  - {p['codigo']}: {p['descripcion'][:40]} (stock: {p['disponible']})")
else:
    print("\n✓ CORRECTO: Todos los productos tienen stock > 0")

# Mostrar estadísticas de stock
stocks = [p['disponible'] for p in inventario]
print(f"\nEstadísticas de stock:")
print(f"  Mínimo: {min(stocks)}")
print(f"  Máximo: {max(stocks)}")
print(f"  Promedio: {sum(stocks)/len(stocks):.2f}")
print(f"  Total: {sum(stocks):,.0f}")

# Mostrar algunos ejemplos
print("\n\nEjemplos de productos retornados:")
print("-" * 100)
for i, p in enumerate(inventario[:10], 1):
    print(f"{i}. {p['codigo']} - {p['descripcion'][:50]}")
    print(f"   Stock: {p['disponible']} | Precio: ${p['precio_venta_2']:,.0f}")

print("\n" + "=" * 100)
print("✓ PRUEBA COMPLETADA")
print("=" * 100)
