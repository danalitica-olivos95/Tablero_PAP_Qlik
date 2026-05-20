"""
Consulta Qlik: PARTICULARES + CONVENIOS + ADICIONALES + DF JPCLO
por sede, mes completo — para comparar con hoja SALAS del Excel.
"""
import asyncio, sys, io, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from qlik_analytics import QlikAnalytics, SEDES_ORDEN, APP_COMERCIAL

# Datos Excel 08/05/2026 (hoja SALAS)
EXCEL = {
    'PARTICULARES': {
        'CHICO': 58963575, 'PALERMO': 24963050, 'RESTREPO': 55781678,
        'SAN DIEGO': 47908575, 'TEUSAQUILLO': 9667000, 'JPCLO': 10218200,
        'SOACHA': 6322450, 'SOGAMOSO': 0, 'CHIA': 0,
    },
    'CONVENIOS': {
        'CHICO': 134832198, 'PALERMO': 13274990.5, 'RESTREPO': 12391000,
        'SAN DIEGO': 32162889, 'TEUSAQUILLO': 0, 'JPCLO': -119570,
        'SOACHA': 1944000, 'SOGAMOSO': 0, 'CHIA': 0,
    },
    'ADICIONALES': {
        'CHICO': 48580526.9, 'PALERMO': 12041837, 'RESTREPO': 22126409,
        'SAN DIEGO': 17635859, 'TEUSAQUILLO': 3378641, 'JPCLO': 6692294,
        'SOACHA': 2910950, 'SOGAMOSO': 5281018, 'CHIA': 2788000,
    },
    'DF_JPCLO': 33999634.62,
    'GENERAL': {   # F37-F46: sum de las tres categorias
        'CHICO': 242376299.9, 'PALERMO': 50279877.5, 'RESTREPO': 90299087,
        'SAN DIEGO': 97707323, 'TEUSAQUILLO': 13045641, 'JPCLO': 16790924,
        'SOACHA': 11177400, 'SOGAMOSO': 5281018, 'CHIA': 2788000,
    },
}

SEDES = ['CHICO','PALERMO','RESTREPO','SAN DIEGO','TEUSAQUILLO',
         'JPCLO','SOACHA','SOGAMOSO','CHIA']

async def main():
    qa = await QlikAnalytics.connect()
    try:
        fecha = await qa.fecha_max()
        print(f"FechaMax: {fecha}\n")

        # Todas las fechas del mes
        fechas = await qa._fechas_mes(fecha)
        set_f  = f"Fecha={{{','.join(repr(f) for f in fechas)}}}"

        # ── Hipercubos por categoría ────────────────
        def expr(filtro):
            return f"SUM({{<{filtro},{set_f}>}} Ejecutado)"

        rows_part = await qa.hipercubo(
            ['Id_Sede'], [expr("Ejecucion={'PARTICULARES'}")])
        rows_conv = await qa.hipercubo(
            ['Id_Sede'], [expr("Ejecucion={'CONVENIOS'}")])
        rows_adic = await qa.hipercubo(
            ['Id_Sede'], [expr("Ejecucion={'ADICIONALES'}")])
        rows_ajpclo = await qa.hipercubo(
            ['Id_Sede'], [expr("Ejecucion={'ADICIONALES JPCLO'}")])
        rows_vd = await qa.hipercubo(
            ['Id_Sede'], [expr("Ejecucion={'VENTAS DIRECTAS JPCLO'}")])

        ID_A = {str(v): k for k, v in {
            'CHICO':1,'PALERMO':2,'RESTREPO':3,'SAN DIEGO':4,
            'TEUSAQUILLO':5,'JPCLO':6,'SOACHA':7,'SOGAMOSO':8,
            'CHIA':10,'RED OLIVOS':12}.items()}

        def parse(rows):
            d = {}
            for row in rows:
                try:
                    n = float(row[0].get('qNum', 0))
                    id_s = str(int(n)) if n == n else None  # NaN check
                except (TypeError, ValueError):
                    id_s = None
                if id_s is None:
                    continue
                sede = ID_A.get(id_s, f'Id={id_s}')
                val = row[1].get('qNum', 0)
                try:
                    v = float(val)
                    d[sede] = (v if v == v else 0.0) * 1000
                except (TypeError, ValueError):
                    d[sede] = 0.0
            return d

        part   = parse(rows_part)
        conv   = parse(rows_conv)
        adic   = parse(rows_adic)
        ajpclo = parse(rows_ajpclo)
        vd     = parse(rows_vd)

        # ── Imprimir comparación GENERAL (P+C+A) ───
        print("=" * 90)
        print(f"{'':18} {'── QLIK ──':^30}  {'── EXCEL ──':^20}  {'DIF':>12}")
        print(f"{'SEDE':<14} {'PART':>12} {'CONV':>12} {'ADIC':>12}  {'TOTAL Q':>12}  {'TOTAL E':>12}  {'DIFER':>12}")
        print("=" * 90)

        for s in SEDES:
            p = part.get(s, 0)
            c = conv.get(s, 0)
            a = adic.get(s, 0)
            aj= ajpclo.get(s, 0)
            tq = p + c + a + aj
            te = EXCEL['GENERAL'].get(s, 0)
            dif = tq - te
            flag = " ◄" if abs(dif) > 100 else ""
            print(f"{s:<14} {p:>12,.0f} {c:>12,.0f} {a:>12,.0f}  {tq:>12,.0f}  {te:>12,.0f}  {dif:>+12,.0f}{flag}")

        print("=" * 90)

        # Totales
        tq_tot = sum(part.get(s,0)+conv.get(s,0)+adic.get(s,0)+ajpclo.get(s,0) for s in SEDES)
        te_tot = sum(EXCEL['GENERAL'].get(s,0) for s in SEDES)
        print(f"{'TOTAL':<14} {sum(part.get(s,0) for s in SEDES):>12,.0f} "
              f"{sum(conv.get(s,0) for s in SEDES):>12,.0f} "
              f"{sum(adic.get(s,0) for s in SEDES):>12,.0f}  "
              f"{tq_tot:>12,.0f}  {te_tot:>12,.0f}  {tq_tot-te_tot:>+12,.0f}")

        # ── ADICIONALES solo ───────────────────────
        print("\n\n--- ADICIONALES detalle (Qlik vs Excel) ---")
        print(f"{'SEDE':<14} {'ADIC_QLIK':>15} {'AJPCLO_QLIK':>15} {'SUM':>15}  {'EXCEL':>15}  {'DIF':>12}")
        print("-" * 85)
        for s in SEDES:
            a  = adic.get(s, 0)
            aj = ajpclo.get(s, 0)
            sm = a + aj
            e  = EXCEL['ADICIONALES'].get(s, 0)
            print(f"{s:<14} {a:>15,.0f} {aj:>15,.0f} {sm:>15,.0f}  {e:>15,.0f}  {sm-e:>+12,.0f}")

        # ── DESTINO FINAL JPCLO ────────────────────
        total_vd = sum(vd.values())
        print(f"\n--- DESTINO FINAL JPCLO ---")
        print(f"  Qlik (VENTAS DIRECTAS JPCLO): {total_vd:>15,.0f}")
        print(f"  Excel (DF JPCLO F102):         {EXCEL['DF_JPCLO']:>15,.0f}")
        print(f"  Diferencia:                    {total_vd - EXCEL['DF_JPCLO']:>+15,.0f}")
        print(f"  Por sede en Qlik: {vd}")

    finally:
        await qa.cerrar()

asyncio.run(main())
