"""Analiza SAN DIEGO diferencia - output a archivo para evitar encoding."""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from qlik_mcp.engine_client import SessionManager

APP_ID = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'
OUT    = r'C:\Users\mario_481\qlik-mcp\sd_analysis.txt'

async def hipercubo(s, dims, meds, alto=200):
    d_def = [{'qDef': {'qFieldDefs': [d]}} for d in dims]
    m_def = [{'qDef': {'qDef': m, 'qLabel': f'M{i}'}} for i, m in enumerate(meds)]
    w = len(dims) + len(meds)
    defn = {
        'qInfo': {'qType': 'SessionObject'},
        'qHyperCubeDef': {
            'qDimensions': d_def, 'qMeasures': m_def,
            'qSuppressMissing': True, 'qSuppressZero': True,
            'qInitialDataFetch': [{'qLeft':0,'qTop':0,'qWidth':w,'qHeight':alto}]
        }
    }
    h  = await s.create_session_object(defn)
    lo = await s.get_layout(h)
    hc = lo.get('qHyperCube', {})
    return hc.get('qDataPages',[{}])[0].get('qMatrix',[])

async def main():
    mgr = SessionManager()
    s   = await mgr.get(APP_ID)

    lines = []
    SD    = "Id_Sede={4}"
    ADIC  = "Ejecucion={'ADICIONALES'}"
    MAYO  = "Fecha={'01/05/2026','02/05/2026','03/05/2026','04/05/2026','05/05/2026','06/05/2026','07/05/2026','08/05/2026'}"

    def num(row, i): return row[i].get('qNum', 0) if i < len(row) else 0
    def txt(row, i): return row[i].get('qText', '') if i < len(row) else ''

    # 1. Total confirmacion
    r = await hipercubo(s, ['Id_Sede'], [f"SUM({{<{ADIC},{MAYO},{SD}>}} Ejecutado)*1000"])
    lines.append(f"Total SD ADIC con filtro fecha: {num(r[0],1):,.0f}" if r else "sin datos")

    # 2. Desglose por NombreCentroCostos
    lines.append("\n=== Por NombreCentroCostos ===")
    rows = await hipercubo(s, ['NombreCentroCostos'],
                           [f"SUM({{<{ADIC},{MAYO},{SD}>}} Ejecutado)*1000"], alto=100)
    for row in rows:
        lines.append(f"  {txt(row,0):40} {num(row,1):>15,.0f}")

    # 3. Desglose por Cod_CC
    lines.append("\n=== Por Cod_CC ===")
    rows = await hipercubo(s, ['Cod_CC'],
                           [f"SUM({{<{ADIC},{MAYO},{SD}>}} Ejecutado)*1000"], alto=100)
    for row in rows:
        lines.append(f"  {txt(row,0):20} {num(row,1):>15,.0f}")

    # 4. Desglose por Concepto
    lines.append("\n=== Por Concepto ===")
    rows = await hipercubo(s, ['Concepto'],
                           [f"SUM({{<{ADIC},{MAYO},{SD}>}} Ejecutado)*1000"], alto=100)
    for row in rows:
        lines.append(f"  {txt(row,0):40} {num(row,1):>15,.0f}")

    # 5. Servicios individuales SAN DIEGO (N_Servicio o similar)
    lines.append("\n=== Por N_Servicio / Servicio ===")
    for campo in ['N_Servicio', 'Num_Servicio', 'NumServicio', 'Servicio',
                  'N_Orden', 'OrdenServicio', 'Folio']:
        try:
            rows = await hipercubo(s, [campo],
                                   [f"SUM({{<{ADIC},{MAYO},{SD}>}} Ejecutado)*1000"], alto=50)
            if rows:
                lines.append(f"\n  CAMPO '{campo}' — {len(rows)} registros:")
                for row in rows[:20]:
                    lines.append(f"    {txt(row,0):20} {num(row,1):>15,.0f}")
        except:
            pass

    # 6. Ver con Fecha_Exequias en lugar de Fecha
    lines.append("\n=== Por Fecha_Exequias (SAN DIEGO ADIC) ===")
    try:
        rows = await hipercubo(s, ['Fecha_Exequias'],
                               [f"SUM({{<{ADIC},{SD}>}} Ejecutado)*1000"], alto=100)
        for row in rows:
            f = txt(row, 0)
            v = num(row, 1)
            if '2026' in f:
                lines.append(f"  {f}  {v:>15,.0f}")
    except Exception as e:
        lines.append(f"  Error: {e}")

    # 7. Comparar: cuánto tiene SAN DIEGO sin filtro de fecha
    lines.append("\n=== Total SD ADIC SIN filtro fecha ===")
    rows = await hipercubo(s, ['Id_Sede'], [f"SUM({{<{ADIC},{SD}>}} Ejecutado)*1000"])
    for row in rows:
        lines.append(f"  {txt(row,0)}  {num(row,1):,.0f}")

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print('\n'.join(lines))
    await mgr.close_all()

asyncio.run(main())
