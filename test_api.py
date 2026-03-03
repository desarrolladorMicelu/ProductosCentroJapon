"""
Script de prueba para validar la API
"""
import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5000"

def print_section(title):
    """Imprime una sección"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_endpoint(method, endpoint, description):
    """Prueba un endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{description}")
    print(f"  {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, timeout=30)
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Respuesta exitosa")
            
            # Mostrar información relevante
            if 'total' in data:
                print(f"  Total registros: {data['total']}")
            
            if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                print(f"  Primer registro:")
                print(f"    {json.dumps(data['data'][0], indent=4, ensure_ascii=False)[:500]}...")
        else:
            print(f"  ✗ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"  ✗ Error: No se pudo conectar al servidor")
        print(f"  Asegúrate de que el servidor esté corriendo en {BASE_URL}")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")

def main():
    """Función principal de pruebas"""
    print_section("PRUEBAS DE API - CENTRO JAPÓN")
    print(f"Fecha: {datetime.now().isoformat()}")
    print(f"URL Base: {BASE_URL}")
    
    # Test 1: Información de la API
    print_section("1. Información de la API")
    test_endpoint("GET", "/", "Obtener información general")
    
    # Test 2: Health Check
    print_section("2. Health Check")
    test_endpoint("GET", "/health", "Verificar estado del servicio")
    
    # Test 3: Inventario completo
    print_section("3. Inventario Completo")
    test_endpoint("GET", "/api/inventario?limit=5", "Obtener inventario (primeros 5)")
    
    # Test 4: Inventario con stock
    print_section("4. Inventario con Stock")
    test_endpoint("GET", "/api/inventario?disponible_solo=true&limit=5", 
                  "Obtener solo productos con stock")
    
    # Test 5: Producto específico
    print_section("5. Producto Específico")
    test_endpoint("GET", "/api/inventario/000001", "Obtener producto 000001")
    
    # Test 6: Lista de productos
    print_section("6. Lista de Productos")
    test_endpoint("GET", "/api/productos?limit=5", "Obtener productos (primeros 5)")
    
    # Test 7: Precios
    print_section("7. Precios de Venta")
    test_endpoint("GET", "/api/precios?limit=5", "Obtener precios (primeros 5)")
    
    # Test 8: Limpiar caché
    print_section("8. Limpiar Caché")
    test_endpoint("POST", "/api/cache/clear", "Limpiar caché manualmente")
    
    print_section("PRUEBAS COMPLETADAS")
    print("\nSi todos los tests pasaron, la API está funcionando correctamente.")
    print("Puedes acceder a la documentación en: http://localhost:5000/")

if __name__ == "__main__":
    main()
