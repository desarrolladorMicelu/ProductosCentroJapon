"""
Script de diagnóstico: muestra los primeros productos de la API
para verificar qué campos trae realmente.
"""
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

API_URL = os.getenv('API_URL', '')

print("Consultando API...")
print(f"URL: {API_URL}")
print("-" * 80)

response = requests.get(API_URL, timeout=30)
response.raise_for_status()

data = response.json()

# Ver estructura general
print(f"\nTipo de respuesta: {type(data)}")
print(f"Keys en respuesta: {data.keys() if isinstance(data, dict) else 'Es una lista'}")

# Obtener productos
if isinstance(data, dict):
    productos = data.get('data', data.get('productos', data.get('inventario', [])))
else:
    productos = data

print(f"\nTotal productos recibidos: {len(productos)}")
print("\n" + "=" * 80)
print("PRIMEROS 3 PRODUCTOS (estructura completa):")
print("=" * 80)

for i, prod in enumerate(productos[:3], 1):
    print(f"\n--- Producto {i} ---")
    print(json.dumps(prod, indent=2, ensure_ascii=False))
    print()

# Verificar campos de stock
print("\n" + "=" * 80)
print("ANÁLISIS DE CAMPOS DE STOCK EN LOS PRIMEROS 10:")
print("=" * 80)

campos_stock = ['disponible', 'stock', 'existencia', 'cantidad', 'inventario']

for i, prod in enumerate(productos[:10], 1):
    codigo = prod.get('codigo', prod.get('cod_invent', prod.get('cod_largo', 'SIN_CODIGO')))
    desc = prod.get('descripcion', 'SIN_DESC')[:40]
    
    print(f"\n{i}. {codigo} - {desc}")
    
    for campo in campos_stock:
        valor = prod.get(campo)
        if valor is not None:
            print(f"   {campo}: {valor}")
