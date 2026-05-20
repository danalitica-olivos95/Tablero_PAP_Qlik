import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from qlik_mcp.engine_client import SessionManager

APP_ID = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'

async def main():
    mgr = SessionManager()
    s = await mgr.get(APP_ID)
    result = await s.call(s.app_handle, 'GetObjects', [{
        'qTypes': ['sheet'], 'qIncludeSessionObjects': False
    }])
    sheets = result if isinstance(result, list) else result.get('qList', [])
    print(f"Total hojas: {len(sheets)}")
    for sh in sheets:
        info = sh.get('qInfo', {})
        meta = sh.get('qMeta', {})
        data = sh.get('qData', {})
        title = (meta.get('title') or meta.get('qTitle') or
                 data.get('title') or info.get('qId', '?'))
        print(f"  [{info.get('qId','')}] {title}")
        # imprimir estructura completa de la primera hoja para diagnóstico
    if sheets:
        print(f"\nEstructura hoja[0]: {sheets[0]}")
    await mgr.close_all()

asyncio.run(main())
