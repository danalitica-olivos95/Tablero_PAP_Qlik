import asyncio, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'src')
from qlik_mcp.engine_client import SessionManager

SEDES = {
    'CHICO':       1,
    'PALERMO':     2,
    'RESTREPO':    3,
    'SAN DIEGO':   4,
    'TEUSAQUILLO': 5,
    'JPCLO':       6,
    'SOACHA':      7,
    'SOGAMOSO':    8,
    'CHIA':        10,
}
REFERENCIA = {
    'CHICO':       (343647539, 227792892),
    'PALERMO':     (105203010, 66300832),
    'RESTREPO':    (92482751,  72576662),
    'SAN DIEGO':   (47673783,  32401295),
    'TEUSAQUILLO': (29745753,  29209235),
    'JPCLO':       (60293864,  28461080),
    'SOACHA':      (15810428,  6157918),
    'SOGAMOSO':    (16342444,  9186000),
    'CHIA':        (2409870,   1805078),
}
ORDEN = ['CHICO','PALERMO','RESTREPO','SAN DIEGO','TEUSAQUILLO','JPCLO','SOACHA','SOGAMOSO','CHIA']

async def main():
    app_id = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'
    sessions = SessionManager()
    s = await sessions.get(app_id)

    resultados = {}
    for sede, id_sede in SEDES.items():
        expr_ppto = f"SUM({{<Id_Sede={{{id_sede}}}, Fecha={{'29/04/2026'}}, TipoPresupuesto={{'I'}}, Ejecucion={{'ADICIONALES'}}>}} Presupuesto)"
        expr_ejec = f"SUM({{<Id_Sede={{{id_sede}}}, Fecha={{'01/04/2026','02/04/2026','03/04/2026','04/04/2026','05/04/2026','06/04/2026','07/04/2026','08/04/2026','09/04/2026','10/04/2026','11/04/2026','12/04/2026','13/04/2026','14/04/2026','15/04/2026','16/04/2026','17/04/2026','18/04/2026','19/04/2026','20/04/2026','21/04/2026','22/04/2026','23/04/2026','24/04/2026','25/04/2026','26/04/2026','27/04/2026','28/04/2026','29/04/2026'}}, Ejecucion={{'ADICIONALES'}}>}} Ejecutado)"

        r_p = await s.call(s.app_handle, 'EvaluateEx', [f'={expr_ppto}'])
        r_e = await s.call(s.app_handle, 'EvaluateEx', [f'={expr_ejec}'])

        def parse_val(r):
            v = r.get('qValue', {})
            if v.get('qIsNumeric'):
                return v.get('qNumber', 0)
            txt = v.get('qText', '0').replace('.','').replace(',','.')
            try: return float(txt)
            except: return 0.0

        ppto = parse_val(r_p) * 1000
        ejec = parse_val(r_e) * 1000
        resultados[sede] = (round(ppto), round(ejec))

    sep = '-' * 114
    print('Comparación corte 29/04/2026  —  Referencia vs Qlik\n')
    print(f"{'SEDE':<15} | {'REF PPTO':>18} | {'QLIK PPTO':>18} | {'DIF PPTO':>14} | {'REF EJEC':>18} | {'QLIK EJEC':>18} | {'DIF EJEC':>12}")
    print(sep)

    tot = {'rp':0,'qp':0,'re':0,'qe':0}
    for sede in ORDEN:
        r_ppto, r_ejec = REFERENCIA[sede]
        q_ppto, q_ejec = resultados[sede]
        d_ppto = q_ppto - r_ppto
        d_ejec = q_ejec - r_ejec
        tot['rp'] += r_ppto; tot['qp'] += q_ppto
        tot['re'] += r_ejec; tot['qe'] += q_ejec
        ok_p = '           ✓' if abs(d_ppto) < 1000 else f'{d_ppto:>+14,.0f}'
        ok_e = '         ✓' if abs(d_ejec) < 1000 else f'{d_ejec:>+12,.0f}'
        print(f"{sede:<15} | {r_ppto:>18,.0f} | {q_ppto:>18,.0f} | {ok_p} | {r_ejec:>18,.0f} | {q_ejec:>18,.0f} | {ok_e}")

    print(sep)
    dp = tot['qp']-tot['rp']; de = tot['qe']-tot['re']
    ok_tp = '           ✓' if abs(dp) < 1000 else f'{dp:>+14,.0f}'
    ok_te = '         ✓' if abs(de) < 1000 else f'{de:>+12,.0f}'
    print(f"{'TOTAL':<15} | {tot['rp']:>18,.0f} | {tot['qp']:>18,.0f} | {ok_tp} | {tot['re']:>18,.0f} | {tot['qe']:>18,.0f} | {ok_te}")
    print()
    print('✓ = diferencia menor a $1.000 (solo redondeo)')

    await sessions.close_all()

asyncio.run(main())
