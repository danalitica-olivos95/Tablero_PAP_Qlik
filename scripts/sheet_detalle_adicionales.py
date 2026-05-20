"""
Hoja 'Detalle Ejecución' — objetos y sección Adicionales.
"""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from qlik_mcp.engine_client import SessionManager

APP_ID   = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'
SHEET_ID = '943ca884-6001-4ce4-8d85-8b22c0bd6afd'

async def main():
    mgr = SessionManager()
    s   = await mgr.get(APP_ID)

    # Obtener handle de la hoja
    res = await s.call(s.app_handle, 'GetObject', [SHEET_ID])
    sh_handle = res['qReturn']['qHandle']

    # Layout de la hoja → qChildList contiene los objetos
    layout = await s.get_layout(sh_handle)
    cells  = layout.get('qChildList', {}).get('qItems', [])

    print(f"Objetos en 'Detalle Ejecución': {len(cells)}\n")
    for i, cell in enumerate(cells):
        info  = cell.get('qInfo', {})
        meta  = cell.get('qMeta', {})
        data  = cell.get('qData', {})
        title = (meta.get('title') or data.get('title') or
                 data.get('qSubTitle') or info.get('qId', '?'))
        otype = info.get('qType', '')
        print(f"  [{i:2d}] {info.get('qId','')} | {otype:20} | {title}")

    # Buscar objetos con 'adicional' en título
    print("\n--- Filtrando 'adicional' ---")
    encontrados = []
    for cell in cells:
        info  = cell.get('qInfo', {})
        meta  = cell.get('qMeta', {})
        data  = cell.get('qData', {})
        title = (meta.get('title') or data.get('title') or
                 data.get('qSubTitle') or '').lower()
        if 'adicional' in title:
            encontrados.append((info.get('qId',''), title))
            print(f"  ✓ {info.get('qId','')} — {title}")

    # Si no hay con título, mostrar propiedades de TODOS para encontrar por expresión
    if not encontrados:
        print("  (ningún título contiene 'adicional' — revisando expresiones de medidas)")
        for cell in cells[:10]:  # primeros 10
            info = cell.get('qInfo', {})
            oid  = info.get('qId', '')
            otype= info.get('qType', '')
            if otype not in ('barchart','table','text-image','kpi','combochart',
                             'pivot-table','straight-table','linechart'):
                continue
            try:
                res2 = await s.call(s.app_handle, 'GetObject', [oid])
                oh   = res2['qReturn']['qHandle']
                props= await s.call(oh, 'GetProperties', [])
                hcd  = props.get('qHyperCubeDef', {})
                meds = [m.get('qDef',{}).get('qDef','') for m in hcd.get('qMeasures',[])]
                dims = [d.get('qDef',{}).get('qFieldDefs',['']) for d in hcd.get('qDimensions',[])]
                titulo = props.get('title','') or props.get('qMetaDef',{}).get('title','')
                if any('adicional' in str(m).lower() for m in meds) or 'adicional' in titulo.lower():
                    print(f"  ✓ {oid} | título: {titulo}")
                    print(f"    dims: {dims}")
                    print(f"    meds: {meds[:3]}")
            except Exception as e:
                print(f"  ! {oid}: {e}")

    await mgr.close_all()

asyncio.run(main())
