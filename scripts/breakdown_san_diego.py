"""
Cuantifica cuánto del delta SAN DIEGO ADICIONALES viene de cada fuente.
Solo lectura — no modifica ningún QVD.

Lógica:
  - Registros con %PK_Num_Fecha != null  → MatrizCostos (usa Fecha_Exequias)
  - Registros con %PK_Num_Fecha == null  → Contabilidad + Parque (fechas distintas)

Usa hipercubo (no EvaluateEx) para que el set analysis funcione correctamente.
"""
import asyncio, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from qlik_analytics import QlikAnalytics

OUT = r'C:\Users\mario_481\qlik-mcp\san_diego_breakdown.txt'

def num(row, i):
    if i >= len(row):
        return 0.0
    v = row[i].get('qNum', 0)
    try:
        f = float(v)
        return 0.0 if f != f else f   # NaN → 0
    except:
        return 0.0

async def main():
    qa = await QlikAnalytics.connect()
    lines = []

    def p(s=''):
        lines.append(s)
        print(s)

    # ── SAN DIEGO: total vs MatrizCostos por fecha ────────────────────────────
    p("=" * 65)
    p("SAN DIEGO (Id_Sede=4)  ADICIONALES — desglose por fuente")
    p("=" * 65)
    p(f"{'Fecha':<14} {'Total':>12} {'MatrizCostos':>14} {'Contab+Parque':>15}")
    p("-" * 65)

    rows_sd = await qa.hipercubo(
        ['Fecha'],
        [
            "SUM({<Ejecucion={'ADICIONALES'}, Id_Sede={4}>} Ejecutado)",
            # IF trick para distinguir rows con %PK_Num_Fecha (MatrizCostos) vs NULL (Contab+Parque)
            "SUM({<Ejecucion={'ADICIONALES'}, Id_Sede={4}>} IF(LEN(TRIM(%PK_Num_Fecha))>0, Ejecutado, 0))",
        ]
    )

    tot_sd = tot_sd_mz = 0.0
    for r in rows_sd:
        fecha = r[0].get('qText', '?')
        total = num(r, 1)
        mz    = num(r, 2)
        otros = total - mz
        if abs(total) >= 1:
            p(f"{fecha:<14} {total:>12,.0f} {mz:>14,.0f} {otros:>15,.0f}")
            tot_sd    += total
            tot_sd_mz += mz

    p("-" * 65)
    p(f"{'TOTAL':<14} {tot_sd:>12,.0f} {tot_sd_mz:>14,.0f} {tot_sd - tot_sd_mz:>15,.0f}")

    # ── Solo mayo ─────────────────────────────────────────────────────────────
    p()
    p("--- Solo mayo 2026 ---")
    may_sd = may_sd_mz = 0.0
    for r in rows_sd:
        if '/05/2026' not in r[0].get('qText', ''):
            continue
        total = num(r, 1)
        mz    = num(r, 2)
        may_sd    += total
        may_sd_mz += mz

    p(f"  Total Qlik mayo    : {may_sd:>10,.0f}")
    p(f"  MatrizCostos       : {may_sd_mz:>10,.0f}")
    p(f"  Contabilidad+Parque: {may_sd - may_sd_mz:>10,.0f}")

    # ── CHICO: solo verificación timing ──────────────────────────────────────
    p()
    p("=" * 65)
    p("CHICO (Id_Sede=1)  ADICIONALES — mayo 2026 (verificacion timing)")
    p("=" * 65)

    rows_ch = await qa.hipercubo(
        ['Fecha'],
        [
            "SUM({<Ejecucion={'ADICIONALES'}, Id_Sede={1}>} Ejecutado)",
            "SUM({<Ejecucion={'ADICIONALES'}, Id_Sede={1}>} IF(LEN(TRIM(%PK_Num_Fecha))>0, Ejecutado, 0))",
        ]
    )

    may_ch = may_ch_mz = 0.0
    for r in rows_ch:
        if '/05/2026' not in r[0].get('qText', ''):
            continue
        fecha = r[0].get('qText', '?')
        total = num(r, 1)
        mz    = num(r, 2)
        otros = total - mz
        p(f"  {fecha}: total={total:,.0f}  MatrizCostos={mz:,.0f}  Contab+Parque={otros:,.0f}")
        may_ch    += total
        may_ch_mz += mz

    p(f"  --- TOTAL mayo ---")
    p(f"  Total Qlik: {may_ch:,.0f}  MatrizCostos: {may_ch_mz:,.0f}  Contab+Parque: {may_ch - may_ch_mz:,.0f}")

    # ── Guardar ──────────────────────────────────────────────────────────────
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"\nGuardado en {OUT}")

    await qa.cerrar()

asyncio.run(main())
