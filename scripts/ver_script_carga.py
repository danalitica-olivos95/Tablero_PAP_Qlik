"""Obtiene el script de carga del app Comercial Homenajes y busca campo Fecha."""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from qlik_mcp.engine_client import SessionManager

APP_ID = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'
OUT    = r'C:\Users\mario_481\qlik-mcp\script_carga_out.txt'

async def main():
    mgr = SessionManager()
    s   = await mgr.get(APP_ID)

    res    = await s.call(s.app_handle, 'GetScript', [])
    script = res.get('qScript', res) if isinstance(res, dict) else str(res)

    # Guardar script completo
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(script)

    print(f"Script guardado ({len(script)} chars)")

    # Buscar líneas con Fecha, Fecha_Exequias, MatrizCostos
    keywords = ['Fecha_Exequias', 'Fecha_Factura', 'FechaFactura',
                'MatrizCostos', 'ADICIONALES', 'as Fecha', 'AS Fecha',
                'Fecha as', 'Fecha AS', 'Fecha =', '[Fecha]']
    print("\n=== Lineas relevantes ===")
    for i, line in enumerate(script.splitlines(), 1):
        if any(kw.lower() in line.lower() for kw in keywords):
            print(f"L{i:4d}: {line.rstrip()}")

    await mgr.close_all()

asyncio.run(main())
