"""Lee la tabla ADICIONALES (AFJrPTt) del app Comercial Homenajes."""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from qlik_mcp.engine_client import SessionManager

APP_ID   = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'
OBJ_ID   = 'AFJrPTt'

async def main():
    mgr = SessionManager()
    s   = await mgr.get(APP_ID)

    res  = await s.call(s.app_handle, 'GetObject', [OBJ_ID])
    oh   = res['qReturn']['qHandle']

    # Propiedades: dimensiones y medidas
    props = await s.call(oh, 'GetProperties', [])
    hcd   = props.get('qHyperCubeDef', {})
    dims  = [d.get('qDef',{}).get('qFieldDefs', d.get('qDef',{}).get('qLabel','?'))
             for d in hcd.get('qDimensions',[])]
    meds  = [(m.get('qDef',{}).get('qLabel','') or m.get('qDef',{}).get('qDef','?'))
             for m in hcd.get('qMeasures',[])]
    print(f"Titulo: {props.get('title','')}")
    print(f"Dimensiones: {dims}")
    print(f"Medidas: {meds}\n")

    # Layout con datos
    layout = await s.get_layout(oh)
    hc     = layout.get('qHyperCube', {})
    size   = hc.get('qSize', {})
    print(f"Filas x Cols: {size.get('qcy','?')} x {size.get('qcx','?')}")

    # Encabezados
    col_names = [d.get('qFallbackTitle','') for d in hc.get('qDimensionInfo',[])]
    col_names += [m.get('qFallbackTitle','') for m in hc.get('qMeasureInfo',[])]
    print(f"\n{' | '.join(f'{c:>20}' for c in col_names)}")
    print('-' * (23 * len(col_names)))

    # Pedir datos explícitamente
    ncols = size.get('qcx', 6)
    nrows = size.get('qcy', 50)
    res2  = await s.call(oh, 'GetHyperCubeData',
                         ['/qHyperCubeDef',
                          [{'qLeft': 0, 'qTop': 0, 'qWidth': ncols, 'qHeight': nrows}]])
    rows  = res2.get('qDataPages', [{}])[0].get('qMatrix', [])
    for row in rows:
        vals = [cell.get('qText', str(cell.get('qNum', ''))) for cell in row]
        print(' | '.join(f'{v:>20}' for v in vals))

    print(f"\nTotal filas: {len(rows)}")
    await mgr.close_all()

asyncio.run(main())
