"""
Script para debuggear el stock en el servidor remoto
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_URL = "https://api-centro-japon.onrender.com/api/inventario?limit=50"

headers = {'X-API-Key': API_KEY}

print("Consultando API remota...")
response = requests.get(API_URL, headers=headers, timeout=60)
response.raise_for_status()

data = response.json()
productos = data.get('data', [])

print(f"\nTotal productos recibidos: {len(productos)}")
print("\n" + "="*80)

# Contar productos con stock
con_stock = [p for p in productos if p.get('disponible', 0) > 0]
sin_stock = [p for p in productos if p.get('disponible', 0) == 0]

print(f"Productos CON stock (>0): {len(con_stock)}")
print(f"Productos SIN stock (=0): {len(sin_stock)}")

if con_stock:
    print("\n" + "="*80)
    print("PRODUCTOS CON STOCK:")
    print("="*80)
    for p in con_stock[:10]:
        print(f"\nCódigo: {p['codigo']}")
        print(f"  Descripción: {p['descripcion'][:50]}")
        print(f"  Disponible: {p['disponible']}")
        print(f"  Precio: ${p['precio_venta_2']:,.0f}")
else:
    print("\n⚠️  NINGÚN PRODUCTO TIENE STOCK")
    print("\nMuestra de productos sin stock:")
    for p in productos[:5]:
        print(f"\n  {p['codigo']} - {p['descripcion'][:40]}")
