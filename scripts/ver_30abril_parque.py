import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl
from datetime import datetime, date

path = r'C:\Users\mario_481\Downloads\Ejecucion Presupuesto Comercial 30 de abril de 2026.xlsx'
wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
FECHA_30 = date(2026, 4, 30)

# Columnas en Facturas directo parque actual:
# 0:No Interno  1:Fecha ODPC  2:No ODPC  3:No Doc Migr  4:No Fac SAP  5:Nro Fac Impresa
# 6:Fecha Contabilizacion  7:Tercero  8:Nombre  9:Elemento  10:Articulo
# 11:Cantidad  12:Vlr Unt  13:Valor total  14:%Dcto  15:Decto
# 16:Vlr Ingreso Sistema  17:Vlr ingreso Calculado  18:Iva  19:Total+Iva
# 20:Dimension1  21:Dimension2  22:SEDE  23:Nro Nota Credito

ws = wb['Facturas directo parque actual']
print('=== Facturas directo parque actual — registros 30/04/2026 ===\n')
total = 0
count = 0
for i, row in enumerate(ws.iter_rows(values_only=True), 1):
    if i == 1: continue
    if all(c is None for c in row): continue
    try:
        fv = row[6]  # Fecha Contabilizacion
        if isinstance(fv, datetime): fv = fv.date()
        if fv != FECHA_30: continue
        nota = str(row[23]) if len(row) > 23 and row[23] else '0'
        if nota not in ('0','None',''): continue
        dim2 = str(row[21]) if len(row) > 21 and row[21] else ''
        dim1 = str(row[20]) if len(row) > 20 and row[20] else ''
        elem = str(row[9])  if row[9] else ''
        art  = str(row[10]) if row[10] else ''
        vlr  = float(row[17]) if row[17] else 0
        sede = str(row[22]) if len(row) > 22 and row[22] else ''
        fac  = str(row[5])  if row[5] else ''
        print(f'  Fac: {fac:<20} Dim1: {dim1:<6} Dim2: {dim2:<8} Sede: {sede:<15} Elem: {elem:<20} Art: {art[:30]:<30} Valor: {vlr:>12,.0f}')
        total += vlr
        count += 1
    except Exception as e:
        pass

print(f'\n  Registros: {count}')
print(f'  TOTAL Facturas Parque 30/04: $ {total:>12,.0f}')

wb.close()
