"""
Analiza diferencia SAN DIEGO ADICIONALES Qlik vs Excel.
Desglosa por campos disponibles: centro de costos, tipo, fuente.
"""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from qlik_mcp.engine_client import SessionManager

APP_ID = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'

async def hipercubo(s, dims, meds, alto=200):
    """Crea hipercubo y devuelve filas."""
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
    h = await s.create_session_object(defn)
    layout = await s.get_layout(h)
    hc = layout.get('qHyperCube', {})
    rows = hc.get('qDataPages',[{}])[0].get('qMatrix',[])
    return rows, hc

async def main():
    mgr = SessionManager()
    s   = await mgr.get(APP_ID)

    SD_ID = 4  # Id_Sede SAN DIEGO
    # Fechas mayo hasta día 8
    fechas_mayo = [f'{d:02d}/05/2026' for d in range(1, 9)]
    set_f = 'Fecha={' + ','.join(f"'{f}'" for f in fechas_mayo) + '}'
    set_sd = f"Id_Sede={{{SD_ID}}}"
    set_adic = "Ejecucion={'ADICIONALES'}"

    filtro_base = f"{set_adic},{set_f},{set_sd}"

    # 1. Total SAN DIEGO ADICIONALES (confirmación)
    rows, _ = await hipercubo(s, ['Id_Sede'],
        [f"SUM({{<{filtro_base}>}} Ejecutado)*1000"])
    print("=== TOTAL SAN DIEGO ADICIONALES (Qlik) ===")
    for r in rows:
        print(f"  Id_Sede={r[0].get('qText','')}  Ejec={r[1].get('qNum',0):,.0f}")

    # 2. Desglose por campos candidatos a centro de costos
    campos = ['CentroCostos', 'Centro_Costos', 'CentroDeCostos',
              'CC', 'Cod_CC', 'CodigoCentroCostos', 'NombreCentroCostos',
              'Concepto', 'TipoServicio', 'Categoria']

    print("\n=== CAMPOS DISPONIBLES (probando) ===")
    for campo in campos:
        try:
            rows2, hc2 = await hipercubo(s, [campo],
                [f"SUM({{<{filtro_base}>}} Ejecutado)*1000"], alto=50)
            if rows2:
                print(f"\n  CAMPO '{campo}' EXISTE — {len(rows2)} valores:")
                for r in rows2:
                    print(f"    {r[0].get('qText',''):30} {r[1].get('qNum',0):>15,.0f}")
        except Exception:
            pass

    # 3. Desglose por Fecha (ver día a día)
    print("\n=== SAN DIEGO ADICIONALES por FECHA ===")
    rows3, _ = await hipercubo(s, ['Fecha'],
        [f"SUM({{<{set_adic},{set_sd}>}} Ejecutado)*1000"], alto=100)
    for r in rows3:
        f = r[0].get('qText','')
        v = r[1].get('qNum',0)
        if '2026' in f:
            print(f"  {f}  {v:>15,.0f}")

    # 4. Ver si con ADICIONALES JPCLO cambia para SAN DIEGO
    print("\n=== SAN DIEGO con ADICIONALES+ADICIONALES JPCLO ===")
    rows4, _ = await hipercubo(s, ['Id_Sede'],
        [f"SUM({{<Ejecucion={{'ADICIONALES','ADICIONALES JPCLO'}},{set_f},{set_sd}>}} Ejecutado)*1000"])
    for r in rows4:
        print(f"  {r[0].get('qText','')}  {r[1].get('qNum',0):>15,.0f}")

    # 5. SAN DIEGO sin filtro de fecha (mes completo)
    print("\n=== SAN DIEGO ADICIONALES mes completo (sin filtro fecha) ===")
    rows5, _ = await hipercubo(s, ['Fecha'],
        [f"SUM({{<{set_adic},{set_sd}>}} Ejecutado)*1000"], alto=100)
    total = 0
    for r in rows5:
        f = r[0].get('qText','')
        v = r[1].get('qNum',0)
        if '05/2026' in f:
            total += v
            print(f"  {f}  {v:>15,.0f}")
    print(f"  TOTAL MAYO: {total:>15,.0f}")

    await mgr.close_all()

asyncio.run(main())
