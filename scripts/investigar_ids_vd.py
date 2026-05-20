import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'src')
from qlik_mcp.engine_client import SessionManager
from datetime import date

APP_ID = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'

fechas = [date(2026, 4, i).strftime('%d/%m/%Y') for i in range(1, 31)]
SET_MES   = "Fecha={" + ",".join(f"'{f}'" for f in fechas) + "}"
EJEC_VD   = "Ejecucion={'VENTAS DIRECTAS JPCLO'}"
EJEC_EXPR = f"SUM({{<{SET_MES},{EJEC_VD}>}}Ejecutado)"


def _num(cell):
    n = cell.get('qNum', 0)
    try:
        v = float(n)
        return 0.0 if v != v else v
    except:
        return 0.0


async def hipercubo(s, dims, meds, alto=500):
    d2 = [{'qDef': {'qFieldDefs': [x]}} for x in dims]
    m2 = [{'qDef': {'qDef': x, 'qLabel': f'M{i}'}} for i, x in enumerate(meds)]
    w  = len(d2) + len(m2)
    defn = {
        'qInfo': {'qType': 'SessionObject'},
        'qHyperCubeDef': {
            'qDimensions': d2, 'qMeasures': m2,
            'qSuppressMissing': True, 'qSuppressZero': True,
            'qInitialDataFetch': [{'qLeft': 0, 'qTop': 0, 'qWidth': w, 'qHeight': alto}]
        }
    }
    h2  = await s.create_session_object(defn)
    lay = await s.get_layout(h2)
    return lay.get('qHyperCube', {}).get('qDataPages', [{}])[0].get('qMatrix', [])


async def main():
    mgr = SessionManager()
    s   = await mgr.get(APP_ID)

    for campo in ['tipo_destino', 'nombre_cementerio', 'canal_venta', 'idsede']:
        try:
            rows = await hipercubo(s, ['Sede', campo], [EJEC_EXPR], alto=200)
            print(f'=== Sede x {campo} ({len(rows)} filas) ===')
            for row in rows:
                if len(row) < 3:
                    print(f'  row corta: {[c.get("qText") for c in row]}')
                    continue
                sede  = row[0].get('qText', '')
                val   = row[1].get('qText', '')
                ejec  = _num(row[2]) * 1000
                print(f'  {sede!r:<25} {val!r:<30} ${ejec:>14,.0f}')
            print()
        except Exception as e:
            print(f'  {campo}: error - {e}')

    # Tambien ver sin dimension Sede - solo tipo_destino
    print('=== Solo tipo_destino (todos) ===')
    try:
        rows = await hipercubo(s, ['tipo_destino'], [EJEC_EXPR], alto=100)
        for row in rows:
            print(f'  {row[0].get("qText")!r:<35} ${_num(row[1])*1000:>14,.0f}')
    except Exception as e:
        print(f'  error: {e}')

    print()
    print('=== Solo nombre_cementerio ===')
    try:
        rows = await hipercubo(s, ['nombre_cementerio'], [EJEC_EXPR], alto=100)
        for row in rows:
            print(f'  {row[0].get("qText")!r:<35} ${_num(row[1])*1000:>14,.0f}')
    except Exception as e:
        print(f'  error: {e}')

    await mgr.close_all()

asyncio.run(main())
