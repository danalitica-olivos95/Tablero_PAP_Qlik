"""Lee SALAS con pandas - alternativa a openpyxl."""
import pandas as pd, warnings
warnings.filterwarnings('ignore')

EXCEL = r'C:\Users\mario_481\qlik-mcp\Ejecucion Presupuesto Comercial 08 de Mayo de 2026.xlsx'
OUT   = r'C:\Users\mario_481\qlik-mcp\salas_pd_out.txt'

# Leer primeras 120 filas, 12 columnas
df = pd.read_excel(EXCEL, sheet_name='SALAS', header=None, nrows=120, usecols=range(12))
print(f'Shape: {df.shape}', flush=True)

lines = [f'Shape: {df.shape}']
for i, row in df.iterrows():
    vals = row.tolist()
    if any(v == v and v is not None for v in vals):  # not NaN
        lines.append(f'F{i+1:3d}: {vals}')
        print(f'F{i+1:3d}: {vals}', flush=True)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('DONE', flush=True)
