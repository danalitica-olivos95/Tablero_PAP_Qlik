import asyncio, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'src')
from qlik_mcp.engine_client import SessionManager

SEDES_MAP = {'1':'CHICO','2':'PALERMO','3':'RESTREPO','4':'SAN DIEGO',
             '5':'TEUSAQUILLO','6':'JPCLO','7':'SOACHA','8':'SOGAMOSO','10':'CHIA','12':'RED OLIVOS'}

async def main():
    app_id = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'
    sessions = SessionManager()
    s = await sessions.get(app_id)

    # Total del dia 30
    r = await s.call(s.app_handle, 'EvaluateEx',
        ["=SUM({<Fecha={'30/04/2026'}, Ejecucion={'ADICIONALES'}, Id_Sede={1,2,3,4,5,6,7,8,10,12}>} Ejecutado)"])
    print(f"Total ADICIONALES 30/04: $ {float(r['qValue']['qNumber'])*1000:,.0f}")
    print()

    # Por sede
    SHEET_DEF = {
        'qInfo': {'qType': 'SessionObject'},
        'qHyperCubeDef': {
            'qDimensions': [{'qDef': {'qFieldDefs': ['Id_Sede']}}],
            'qMeasures': [{'qDef': {
                'qDef': "SUM({<Fecha={'30/04/2026'}, Ejecucion={'ADICIONALES'}>} Ejecutado)",
                'qLabel': 'Ejec30'
            }}],
            'qSuppressMissing': True,
            'qSuppressZero': True,
            'qInitialDataFetch': [{'qLeft': 0, 'qTop': 0, 'qWidth': 2, 'qHeight': 50}]
        }
    }
    handle = await s.create_session_object(SHEET_DEF)
    layout = await s.get_layout(handle)
    rows = layout.get('qHyperCube',{}).get('qDataPages',[{}])[0].get('qMatrix',[])

    print('SEDE             | EJECUTADO 30/04')
    print('-'*40)
    total = 0
    for row in rows:
        id_s = str(int(row[0]['qNum'])) if row[0].get('qIsNumeric') else row[0].get('qText','?')
        sede = SEDES_MAP.get(id_s, f'Id={id_s}')
        val  = row[1].get('qNum',0) * 1000
        total += val
        print(f'{sede:<17}| $ {val:>15,.0f}')
    print('-'*40)
    print(f'{"TOTAL":<17}| $ {total:>15,.0f}')

    await sessions.close_all()

asyncio.run(main())
