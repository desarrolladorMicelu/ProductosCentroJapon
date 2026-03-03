"""
Ejemplo de uso de la API Centro Japón
"""
import requests
import json

# URL base de la API
BASE_URL = "http://localhost:5000"

print("=" * 80)
print("EJEMPLO DE USO - API CENTRO JAPÓN")
print("=" * 80)

# 1. Verificar que la API está funcionando
print("\n1. Verificando estado de la API...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    if response.status_code == 200:
        print("   ✓ API funcionando correctamente")
        health = response.json()
        print(f"   Estado: {health['status']}")
    else:
        print("   ✗ API no responde correctamente")
        exit(1)
except Exception as e:
    print(f"   ✗ Error conectando a la API: {e}")
    print("   Asegúrate de que la API esté corriendo (python app.py)")
    exit(1)

# 2. Obtener inventario completo (primeros 5)
print("\n2. Obteniendo inventario (primeros 5 productos)...")
response = requests.get(f"{BASE_URL}/api/inventario?limit=5")
data = response.json()

if data['success']:
    print(f"   ✓ Total productos en sistema: {data['total']}")
    print("\n   Primeros 5 productos:")
    for i, producto in enumerate(data['data'], 1):
        print(f"\n   {i}. {producto['codigo']} - {producto['descripcion']}")
        print(f"      Disponible: {producto['disponible']} unidades")
        print(f"      Costo: ${producto['costo']:,.2f}")
        print(f"      Precio Venta 1: ${producto['precio_venta_1']:,.2f}")
        print(f"      IVA: {producto['iva']}%")
else:
    print(f"   ✗ Error: {data.get('error')}")

# 3. Buscar un producto específico
print("\n3. Buscando producto específico (código 000001)...")
codigo = "000001"
response = requests.get(f"{BASE_URL}/api/inventario/{codigo}")
result = response.json()

if result['success']:
    producto = result['data']
    print(f"   ✓ Producto encontrado:")
    print(f"\n   Código: {producto['codigo']}")
    print(f"   Descripción: {producto['descripcion']}")
    print(f"   Referencia: {producto['referencia']}")
    print(f"   Disponible: {producto['disponible']} unidades")
    print(f"   Costo: ${producto['costo']:,.2f}")
    print(f"   Precio Venta 1: ${producto['precio_venta_1']:,.2f}")
    print(f"   Precio Venta 2: ${producto['precio_venta_2']:,.2f}")
    print(f"   Precio Venta 3: ${producto['precio_venta_3']:,.2f}")
else:
    print(f"   ✗ Producto no encontrado")

# 4. Obtener solo productos con stock
print("\n4. Obteniendo productos con stock (primeros 10)...")
response = requests.get(f"{BASE_URL}/api/inventario?disponible_solo=true&limit=10")
data = response.json()

if data['success']:
    print(f"   ✓ Productos con stock: {data['total']}")
    print("\n   Primeros 10 con disponibilidad:")
    for i, producto in enumerate(data['data'], 1):
        print(f"   {i}. {producto['codigo']}: {producto['descripcion'][:40]:40s} | Stock: {producto['disponible']:>6.0f}")
else:
    print(f"   ✗ Error: {data.get('error')}")

# 5. Calcular estadísticas
print("\n5. Calculando estadísticas del inventario...")
response = requests.get(f"{BASE_URL}/api/inventario")
data = response.json()

if data['success']:
    productos = data['data']
    
    # Productos con stock
    con_stock = [p for p in productos if p['disponible'] > 0]
    
    # Valor total del inventario
    valor_total = sum(p['disponible'] * p['costo'] for p in productos)
    
    # Productos con bajo stock (menos de 10)
    bajo_stock = [p for p in con_stock if p['disponible'] < 10]
    
    print(f"   ✓ Estadísticas:")
    print(f"      Total productos: {len(productos)}")
    print(f"      Productos con stock: {len(con_stock)}")
    print(f"      Productos con bajo stock (<10): {len(bajo_stock)}")
    print(f"      Valor total inventario: ${valor_total:,.2f}")
    
    if bajo_stock:
        print(f"\n   ⚠ Productos con bajo stock:")
        for p in bajo_stock[:5]:  # Mostrar primeros 5
            print(f"      - {p['codigo']}: {p['descripcion'][:40]} | Stock: {p['disponible']}")

# 6. Obtener precios
print("\n6. Obteniendo precios (primeros 5)...")
response = requests.get(f"{BASE_URL}/api/precios?limit=5")
data = response.json()

if data['success']:
    print(f"   ✓ Total precios: {data['total']}")
    print("\n   Primeros 5 productos con precios:")
    for i, producto in enumerate(data['data'], 1):
        print(f"\n   {i}. {producto['codigo']} - {producto['descripcion'][:40]}")
        print(f"      Costo: ${producto['costo']:,.2f}")
        print(f"      PV1: ${producto['precio_venta_1']:,.2f} | PV2: ${producto['precio_venta_2']:,.2f} | PV3: ${producto['precio_venta_3']:,.2f}")
        print(f"      Utilidad: {producto['utilidad_porcentaje']}%")

print("\n" + "=" * 80)
print("EJEMPLO COMPLETADO")
print("=" * 80)
print("\nPuedes usar estos endpoints en tu aplicación:")
print(f"  - Inventario completo: {BASE_URL}/api/inventario")
print(f"  - Producto específico: {BASE_URL}/api/inventario/<codigo>")
print(f"  - Precios: {BASE_URL}/api/precios")
print(f"  - Health check: {BASE_URL}/health")
print("\nRevisa GUIA_USO.md para más ejemplos y documentación completa.")
