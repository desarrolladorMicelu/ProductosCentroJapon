from src.dbf_reader import DBFReader

reader = DBFReader('DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02')
inventario = reader.get_inventario_con_precios()

# Buscar productos específicos
codigos = ['048051', '048052', '000002']
for producto in inventario:
    if producto['codigo'] in codigos:
        print(f"\nCódigo: {producto['codigo']}")
        print(f"  Descripción: {producto['descripcion']}")
        print(f"  Disponible: {producto['disponible']}")
        print(f"  Precio: {producto['precio_venta_2']}")
