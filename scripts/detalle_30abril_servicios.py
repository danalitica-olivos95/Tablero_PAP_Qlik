import asyncio, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'src')
from qlik_mcp.engine_client import SessionManager

async def main():
    app_id = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'
    sessions = SessionManager()
    s = await sessions.get(app_id)

    # Detalle por Sede + Numero_Servicio para Fecha=30/04/2026, Ejecucion=ADICIONALES
    SHEET_DEF = {
        'qInfo': {'qType': 'SessionObject'},
        'qHyperCubeDef': {
            'qDimensions': [
                {'qDef': {'qFieldDefs': ['Id_Sede']}},
                {'qDef': {'qFieldDefs': ['Numero_Servicio']}},
            ],
            'qMeasures': [{'qDef': {
                'qDef': "SUM({<Fecha={'30/04/2026'}, Ejecucion={'ADICIONALES'}>} Ejecutado)",
                'qLabel': 'Ejec30'
            }}],
            'qSuppressMissing': True,
            'qSuppressZero': True,
            'qInitialDataFetch': [{'qLeft': 0, 'qTop': 0, 'qWidth': 3, 'qHeight': 200}]
        }
    }

    SEDES_MAP = {'1':'CHICO','2':'PALERMO','3':'RESTREPO','4':'SAN DIEGO',
                 '5':'TEUSAQUILLO','6':'JPCLO','7':'SOACHA','8':'SOGAMOSO','10':'CHIA','12':'RED OLIVOS'}

    handle = await s.create_session_object(SHEET_DEF)
    layout = await s.get_layout(handle)
    rows = layout.get('qHyperCube',{}).get('qDataPages',[{}])[0].get('qMatrix',[])

    print('SEDE           | SERVICIO      | ADICIONALES 30/04')
    print('-'*55)
    total = 0
    for row in rows:
        id_s  = str(int(row[0]['qNum'])) if row[0].get('qIsNumeric') else row[0].get('qText','?')
        sede  = SEDES_MAP.get(id_s, f'Id={id_s}')
        svc   = row[1].get('qText','')
        val   = row[2].get('qNum',0) * 1000
        total += val
        print(f'{sede:<15}| {svc:<14}| $ {val:>14,.0f}')
    print('-'*55)
    print(f'{"TOTAL":<15}| {"":14}| $ {total:>14,.0f}')

    await sessions.close_all()

asyncio.run(main())
