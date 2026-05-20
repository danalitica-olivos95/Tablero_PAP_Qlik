import asyncio, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'src')
from qlik_mcp.engine_client import SessionManager

SHEET_DEF = {
    'qInfo': {'qType': 'SessionObject'},
    'qHyperCubeDef': {
        'qDimensions': [
            {'qDef': {'qFieldDefs': ['Ejecucion']}},
        ],
        'qMeasures': [
            {'qDef': {
                'qDef': "SUM({<Id_Sede={6}, Fecha={\">=$(=Date(MonthStart($(vFechaMax))))<=$(=Date($(vFechaMax)))\"}>} Ejecutado)",
                'qLabel': 'Ejec'
            }},
        ],
        'qSuppressMissing': True,
        'qSuppressZero': True,
        'qInitialDataFetch': [{'qLeft': 0, 'qTop': 0, 'qWidth': 2, 'qHeight': 50}]
    }
}

async def main():
    app_id = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'
    sessions = SessionManager()
    s = await sessions.get(app_id)
    handle = await s.create_session_object(SHEET_DEF)
    layout = await s.get_layout(handle)
    rows = layout.get('qHyperCube',{}).get('qDataPages',[{}])[0].get('qMatrix',[])
    print('JPCLO (Id_Sede=6) - Ejecucion por categoria:')
    total = 0
    for row in rows:
        cat  = row[0].get('qText','')
        ejec = row[1].get('qNum',0) * 1000
        total += ejec
        print(f'  {cat:<30} {ejec:>18,.0f}')
    print(f'  {"TOTAL":<30} {total:>18,.0f}')
    await sessions.close_all()

asyncio.run(main())
