"""
Script para analizar la estructura de archivos DBF de FoxPro
"""
import os
from dbfread import DBF

# Ruta a los archivos DBF
dbf_path = r"DbfRed 2025-12-09 17;02;02\DbfRed 2025-12-09 17;02;02"

# Archivos clave para analizar (inventario, productos, ventas, costos)
key_files = [
    'Producto.DBF',
    'movimien.dbf',
    'MovMes.DBF',
    'clientes.DBF',
    'proveedo.DBF',
    'ventae01.DBF',
    'venta01.DBF'
]

print("=" * 80)
print("ANÁLISIS DE ESTRUCTURA DE ARCHIVOS DBF")
print("=" * 80)

for filename in key_files:
    filepath = os.path.join(dbf_path, filename)
    if os.path.exists(filepath):
        try:
            table = DBF(filepath, encoding='latin-1', ignore_missing_memofile=True)
            print(f"\n{'=' * 80}")
            print(f"Archivo: {filename}")
            print(f"Total de registros: {len(table)}")
            print(f"\nCampos:")
            print("-" * 80)
            for field in table.fields:
                print(f"  {field.name:20s} | Tipo: {field.type:5s} | Longitud: {field.length}")
            
            # Mostrar primeros 2 registros como ejemplo
            print(f"\nPrimeros registros (muestra):")
            print("-" * 80)
            for i, record in enumerate(table):
                if i >= 2:
                    break
                print(f"\nRegistro {i+1}:")
                for key, value in record.items():
                    if value is not None and str(value).strip():
                        print(f"  {key}: {value}")
        except Exception as e:
            print(f"\nError al leer {filename}: {str(e)}")
    else:
        print(f"\n{filename} no encontrado")

print("\n" + "=" * 80)
