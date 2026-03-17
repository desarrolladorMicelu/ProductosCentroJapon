"""
Script para probar la API con el stock corregido
"""
import os
os.environ['DBF_PATH'] = 'DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02'
os.environ['API_KEY'] = 'test-key-123'

from src.api import create_app
import json

print("=" * 80)
print("PRUEBA DE API CON STOCK CORREGIDO")
print("=" * 80)

app = create_app()
client = app.test_client()

# Probar endpoint de inventario
print("\n1. Probando /api/inventario?disponible_solo=true&limit=5")
print("-" * 80)

response = client.get(
    '/api/inventario?disponible_solo=true&limit=5',
    headers={'X-API-Key': 'test-key-123'}
)

print(f"Status: {response.status_code}")
data = response.get_json()

if data['success']:
    print(f"Total productos: {data['total']}")
    print("\nProductos:")
    for i, producto in enumerate(data['data'], 1):
        print(f"\n  {i}. {producto['codigo']} - {producto['descripcion'][:50]}")
        print(f"     Disponible: {producto['disponible']}")
        print(f"     Precio: ${producto['precio_venta_1']:,.2f}")
else:
    print(f"Error: {data.get('error')}")

# Probar un producto específico
print("\n\n2. Probando /api/inventario/000002")
print("-" * 80)

response = client.get(
    '/api/inventario/000002',
    headers={'X-API-Key': 'test-key-123'}
)

print(f"Status: {response.status_code}")
data = response.get_json()

if data['success']:
    producto = data['data']
    print(f"\nProducto: {producto['codigo']}")
    print(f"Descripción: {producto['descripcion']}")
    print(f"Disponible: {producto['disponible']}")
    print(f"Precio Venta 1: ${producto['precio_venta_1']:,.2f}")
    print(f"Costo: ${producto['costo']:,.2f}")
else:
    print(f"Error: {data.get('error')}")

print("\n" + "=" * 80)
print("✓ PRUEBA DE API COMPLETADA")
print("=" * 80)
