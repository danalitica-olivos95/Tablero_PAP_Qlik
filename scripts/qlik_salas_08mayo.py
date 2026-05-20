"""Consulta Qlik: ejecucion SALAS por sede al 08/05/2026."""
import asyncio, sys, io, os, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/src')
from qlik_analytics import QlikAnalytics, SEDES, SEDES_ORDEN, APP_COMERCIAL

async def main():
    qa = await QlikAnalytics.connect()
    try:
        fecha = await qa.fecha_max()
        print(f"FechaMax Qlik: {fecha}")

        # Presupuesto por sede
        ppto = await qa.presupuesto_mes_por_sede()
        print("\n=== PRESUPUESTO MES POR SEDE ===")
        for sede, val in ppto.items():
            print(f"  {sede}: {val:,.0f}")

        # Resumen cumplimiento
        resumen = await qa.resumen_cumplimiento()
        print("\n=== RESUMEN CUMPLIMIENTO ===")
        print(f"{'SEDE':<15} {'PPTO':>15} {'EJEC':>15} {'%':>8}")
        print("-"*55)
        for r in resumen:
            print(f"  {r['sede']:<13} {r['presupuesto']:>15,.0f} {r['ejecutado']:>15,.0f} {r['pct']:>7.1f}%")

        # Adicionales por sede (hoy)
        adic = await qa.adicionales_por_sede(fecha)
        print(f"\n=== ADICIONALES DIA {fecha} POR SEDE ===")
        for sede, val in adic.items():
            print(f"  {sede}: {val:,.0f}")

        # Total adicionales
        total = await qa.total_adicionales(fecha)
        print(f"\nTotal ADICIONALES acumulado mes: {total:,.0f}")

    finally:
        await qa.cerrar()

asyncio.run(main())
