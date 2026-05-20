import asyncio, sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'src')
from qlik_mcp.engine_client import SessionManager

# Sin set analysis de fecha — ver todo el presupuesto por categoria/sede para ADICIONALES
SHEET_DEF = {
    'qInfo': {'qType': 'SessionObject'},
    'qHyperCubeDef': {
        'qDimensions': [
            {'qDef': {'qFieldDefs': ['Id_Categoria_Ingresos']}},
            {'qDef': {'qFieldDefs': ['Sede']}}
        ],
        'qMeasures': [
            {'qDef': {
                'qDef': "SUM({<TipoPresupuesto={'I'}, Ejecucion={'ADICIONALES'}, Fecha={'$(=$(vFechaMax))'}>} Presupuesto)",
                'qLabel': 'Ppto vFechaMax'
            }},
        ],
        'qSuppressMissing': True,
        'qSuppressZero': True,
        'qInitialDataFetch': [{'qLeft': 0, 'qTop': 0, 'qWidth': 3, 'qHeight': 200}]
    }
}

async def main():
    app_id = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'
    sessions = SessionManager()
    s = await sessions.get(app_id)

    # Verificar vFechaMax
    r = await s.call(s.app_handle, 'EvaluateEx', ['=$(vFechaMax)'])
    fecha = r.get('qValue', {}).get('qText', '')
    print(f'vFechaMax = {fecha}')
    print()

    handle = await s.create_session_object(SHEET_DEF)
    layout = await s.get_layout(handle)
    rows = layout.get('qHyperCube', {}).get('qDataPages', [{}])[0].get('qMatrix', [])

    print(f'{"Cat":>4} | {"Sede":<15} | {"Ppto":>18}')
    print('-'*45)
    totales = {}
    for row in rows:
        cat  = row[0].get('qText','')
        sede = row[1].get('qText','')
        ppto = row[2].get('qNum', 0)
        totales[cat] = totales.get(cat, 0) + ppto
        print(f'{cat:>4} | {sede:<15} | {ppto*1000:>18,.0f}')

    print()
    print('--- TOTAL POR CATEGORIA ---')
    for cat, tot in sorted(totales.items()):
        print(f'Cat {cat}: {tot*1000:>18,.0f}')

    await sessions.close_all()

asyncio.run(main())
