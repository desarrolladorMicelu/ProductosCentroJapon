from dbfread import DBF
import datetime

# Leer MovMes
table = DBF('DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02/MovMes.DBF', encoding='latin1')

mes_actual = datetime.datetime.now().month
print(f"Mes actual: {mes_actual} (Marzo)")
print(f"Total registros en MovMes: {len(list(table))}")
print("\n" + "="*80)

# Buscar productos específicos
table = DBF('DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02/MovMes.DBF', encoding='latin1')
codigos_buscar = ['048051', '048052', '000002']

print(f"\nBuscando productos: {codigos_buscar}")
print("="*80)

for record in table:
    cod = (record.get('COD_PRODUC') or '').strip()
    if cod in codigos_buscar:
        print(f"\nCÓDIGO: {cod}")
        print(f"  FECHA: {record.get('FECHA')}")
        print(f"  INICIALMES: {record.get('INICIALMES')}")
        print(f"  ENTRADASME: {record.get('ENTRADASME')}")
        print(f"  SALIDASMES: {record.get('SALIDASMES')}")
        print(f"  ACTUALMES: {record.get('ACTUALMES')}")
        print(f"  CEN_COSTO: {record.get('CEN_COSTO')}")
        codigos_buscar.remove(cod)
        if not codigos_buscar:
            break

print("\n" + "="*80)
