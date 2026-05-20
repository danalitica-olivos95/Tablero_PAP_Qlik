"""Busca apps de transformación Homenajes en el servidor Qlik."""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from qlik_mcp.qrs_client import QRSClient

OUT = r'C:\Users\mario_481\qlik-mcp\apps_transformacion.txt'

async def main():
    qrs  = QRSClient()
    apps = await qrs.list_apps()

    keywords = ['transf', 'homenaj', 'comercial', 'ejecuc', 'matriz',
                'fact_', 'ppto', 'presupuesto', 'etl']

    lines = [f"Total apps: {len(apps)}\n"]
    lines.append("=== Apps relacionadas con transformación / homenajes ===\n")

    matches = []
    for a in apps:
        name = a.get('name', '').lower()
        if any(k in name for k in keywords):
            matches.append(a)
            lines.append(f"  [{a.get('id','')}]")
            lines.append(f"    Nombre:  {a.get('name','')}")
            lines.append(f"    Stream:  {a.get('stream','')}")
            lines.append(f"    Modified:{a.get('modifiedDate','')[:10]}")
            lines.append("")

    lines.append(f"\nTotal encontrados: {len(matches)}")

    txt = '\n'.join(lines)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(txt)
    print(txt)

asyncio.run(main())
