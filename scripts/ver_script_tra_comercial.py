"""Lee script del app 02_Homenajes_Tra_Comercial y busca cómo se construye Fecha / %PK_Num_Fecha."""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from qlik_mcp.engine_client import SessionManager

APP_ID = '94d509d0-e834-436a-9d78-020cd125ba97'  # 02_Homenajes_Tra_Comercial
OUT    = r'C:\Users\mario_481\qlik-mcp\script_tra_comercial.txt'

async def main():
    mgr = SessionManager()
    s   = await mgr.get(APP_ID)
    res    = await s.call(s.app_handle, 'GetScript', [])
    script = res.get('qScript', '') if isinstance(res, dict) else str(res)

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(script)
    print(f"Script guardado: {len(script)} chars\n")

    # Buscar líneas clave
    keywords = ['Fact_Ejecuciones', 'PK_Num_Fecha', 'Fecha_Exequias',
                'Fecha_Factura', 'FechaFactura', 'Factura_SAP',
                'as Fecha', 'AS Fecha', 'Fecha as', '[Fecha]',
                'Fecha =', 'Store', 'STORE', 'MatrizCostos',
                'Ejecucion', 'Ejecutado', 'ADICIONALES']

    print("=== Líneas relevantes ===")
    for i, line in enumerate(script.splitlines(), 1):
        if any(kw.lower() in line.lower() for kw in keywords):
            print(f"L{i:4d}: {line.rstrip()}")

    await mgr.close_all()

asyncio.run(main())
