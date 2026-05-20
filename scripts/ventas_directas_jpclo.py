import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'src')
from qlik_mcp.engine_client import SessionManager
from datetime import date, timedelta

APP_ID = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'
ID_A_SEDE = {'1':'CHICO','2':'PALERMO','3':'RESTREPO','4':'SAN DIEGO',
             '5':'TEUSAQUILLO','6':'JPCLO','7':'SOACHA','8':'SOGAMOSO','10':'CHIA','12':'RED OLIVOS'}

EXCEL_PARQUE = {
    'PRENECESIDAD':    285417034,
    'PALERMO':          27111584,
    'RESTREPO':          9827057,
    'JPCLO':             5573630,
    'CALL CENTER':       5398421,
    'SAN DIEGO':         4741550,
    'PARQUE CEMENTERIO': 3497815,
    'TEUSAQUILLO':       1026000,
    'CHICO':              200000,
}

def _num(cell):
    n = cell.get('qNum', 0)
    try:
        v = float(n)
        return 0.0 if v != v else v
    except:
        return 0.0

def _parse_eval(r):
    v = r.get('qValue', {})
    if v.get('qIsNumeric'):
        return v.get('qNumber', 0)
    txt = v.get('qText', '0').replace('.', '').replace(',', '.')
    try:
        return float(txt)
    except:
        return 0.0

# Fechas del mes de abril
d0 = date(2026, 4, 1); d1 = date(2026, 4, 30)
fechas = []
d = d0
while d <= d1:
    fechas.append(d.strftime('%d/%m/%Y'))
    d += timedelta(days=1)
SET_MES = "Fecha={" + ",".join(f"'{f}'" for f in fechas) + "}"
SET_HOY = "Fecha={'30/04/2026'}"
EJEC_VD = "Ejecucion={'VENTAS DIRECTAS JPCLO'}"

PPTO_EXPR = f"SUM({{<{SET_HOY}, TipoPresupuesto={{'I'}}, {EJEC_VD}>}}Presupuesto)"
EJEC_EXPR = f"SUM({{<{SET_MES}, {EJEC_VD}>}}Ejecutado)"

async def hipercubo(s, dims, meds, alto=500):
    d = [{'qDef': {'qFieldDefs': [x]}} for x in dims]
    m = [{'qDef': {'qDef': x, 'qLabel': f'M{i}'}} for i, x in enumerate(meds)]
    w = len(d) + len(m)
    defn = {
        'qInfo': {'qType': 'SessionObject'},
        'qHyperCubeDef': {
            'qDimensions': d, 'qMeasures': m,
            'qSuppressMissing': True, 'qSuppressZero': False,
            'qInitialDataFetch': [{'qLeft': 0, 'qTop': 0, 'qWidth': w, 'qHeight': alto}]
        }
    }
    h = await s.create_session_object(defn)
    lay = await s.get_layout(h)
    hc = lay.get('qHyperCube', {})
    return hc.get('qDataPages', [{}])[0].get('qMatrix', [])

async def main():
    mgr = SessionManager()
    s   = await mgr.get(APP_ID)

    r_ppto = await s.call(s.app_handle, 'EvaluateEx', ['=' + PPTO_EXPR])
    r_ejec = await s.call(s.app_handle, 'EvaluateEx', ['=' + EJEC_EXPR])
    ppto_n = _parse_eval(r_ppto) * 1000
    ejec_n = _parse_eval(r_ejec) * 1000
    pct    = ejec_n / ppto_n * 100 if ppto_n else 0

    print('=== VENTAS DIRECTAS JPCLO — Totales Qlik vs Excel ===')
    print(f'  Presupuesto mes Qlik  : ${ppto_n:>15,.0f}')
    print(f'  Ejecucion mes   Qlik  : ${ejec_n:>15,.0f}')
    print(f'  Ejecucion mes   Excel : ${sum(EXCEL_PARQUE.values()):>15,.0f}')
    print(f'  Diferencia            : ${ejec_n - sum(EXCEL_PARQUE.values()):>+15,.0f}')
    print(f'  Cumplimiento Qlik     : {pct:.1f}%')
    print()

    # Por sede
    rows = await hipercubo(s, ['Id_Sede'], [PPTO_EXPR, EJEC_EXPR])

    print(f"{'SEDE':<22} {'PPTO Qlik':>14} {'EJEC Qlik':>14} {'EJEC Excel':>14} {'DIFERENCIA':>14}")
    print('-' * 82)
    total_qe = 0
    for row in rows:
        try:
            id_s = str(int(_num(row[0])))
        except:
            id_s = row[0].get('qText', '')
        sede  = ID_A_SEDE.get(id_s, f'Id={id_s}')
        ppto  = _num(row[1]) * 1000
        ejec  = _num(row[2]) * 1000
        ex_e  = EXCEL_PARQUE.get(sede, 0)
        diff  = ejec - ex_e
        total_qe += ejec
        print(f'{sede:<22} {ppto:>14,.0f} {ejec:>14,.0f} {ex_e:>14,.0f} {diff:>+14,.0f}')

    total_excel = sum(EXCEL_PARQUE.values())
    print('-' * 82)
    print(f"{'TOTAL':<22} {'':>14} {total_qe:>14,.0f} {total_excel:>14,.0f} {total_qe-total_excel:>+14,.0f}")

    await mgr.close_all()

asyncio.run(main())
