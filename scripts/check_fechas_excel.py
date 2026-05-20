import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl
from datetime import datetime, date
from collections import Counter

path = r'C:\Users\mario_481\Downloads\Ejecucion Presupuesto Comercial 30 de abril de 2026.xlsx'
wb = openpyxl.load_workbook(path, data_only=True, read_only=True)

for sheet_name in ['Otros Ingresos actual', 'Facturas directo parque actual']:
    ws = wb[sheet_name]
    fechas = []
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        if i == 1: continue
        if all(c is None for c in row): continue
        fv = row[2]
        if isinstance(fv, datetime): fv = fv.date()
        if isinstance(fv, date): fechas.append(fv)
    cnt = Counter(fechas)
    ultimas = sorted(cnt.keys())[-5:]
    print(f'{sheet_name}:')
    for f in ultimas:
        print(f'  {f}  -> {cnt[f]} registros')
    print()
wb.close()
