import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd

path = r'C:\Users\mario_481\Downloads\Ejecucion Presupuesto Comercial 30 de abril de 2026.xlsx'
df = pd.read_excel(path, sheet_name='Facturas directo parque actual', header=0)

print('=== TOTAL POR SEDE ===')
por_sede = df.groupby('SEDE')['Valor total'].sum().sort_values(ascending=False)
for sede, total in por_sede.items():
    print(f'  {sede:<20} ${total:>15,.0f}')
print(f'  {"TOTAL":<20} ${por_sede.sum():>15,.0f}')

print()
print('=== TOTAL POR ELEMENTO (todos) ===')
por_elem = df.groupby('Elemento')['Valor total'].sum().sort_values(ascending=False)
for elem, total in por_elem.items():
    print(f'  {elem:<30} ${total:>15,.0f}')

print()
print('=== SOLO JPCLO — por Elemento ===')
jpclo = df[df['SEDE'] == 'JPCLO']
if not jpclo.empty:
    por_e = jpclo.groupby('Elemento')['Valor total'].sum().sort_values(ascending=False)
    for elem, total in por_e.items():
        print(f'  {elem:<30} ${total:>15,.0f}')
    print(f'  {"TOTAL JPCLO":<30} ${jpclo["Valor total"].sum():>15,.0f}')
else:
    print('  Sin registros con SEDE=JPCLO')
    print('  Valores únicos de SEDE:', df['SEDE'].unique().tolist())
