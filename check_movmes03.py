from dbfread import DBF

table = DBF('DbfRed 2025-12-09 17;02;02/DbfRed 2025-12-09 17;02;02/MovMes03.DBF', encoding='latin1')

codigos = ['048051', '048052', '000002']
encontrados = []

for record in table:
    cod = (record.get('COD_PRODUC') or '').strip()
    if cod in codigos:
        print(f"\nCÓDIGO: {cod}")
        print(f"  FECHA: {record.get('FECHA')}")
        print(f"  INICIALMES: {record.get('INICIALMES')}")
        print(f"  ENTRADASME: {record.get('ENTRADASME')}")
        print(f"  SALIDASMES: {record.get('SALIDASMES')}")
        print(f"  ACTUALMES: {record.get('ACTUALMES')}")
        print(f"  CEN_COSTO: {record.get('CEN_COSTO')}")
        encontrados.append(cod)

print(f"\n\nEncontrados: {encontrados}")
print(f"No encontrados: {[c for c in codigos if c not in encontrados]}")
