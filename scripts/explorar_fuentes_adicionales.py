"""
Explora campos de Contabilidad_Otros_Ingresos y Detalle_Facturas_Orden_Parque
para encontrar clave de join con MatrizCostos (Numero_Servicio / Fecha_Exequias).
Solo lectura. App transformacion: 94d509d0-e834-436a-9d78-020cd125ba97
"""
import asyncio, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from qlik_mcp.engine_client import SessionManager

APP_TRA = '94d509d0-e834-436a-9d78-020cd125ba97'
OUT     = r'C:\Users\mario_481\qlik-mcp\fuentes_adicionales.txt'

async def hc(s, dims, meds, alto=15):
    w = len(dims) + len(meds)
    defn = {
        'qInfo': {'qType': 'x'},
        'qHyperCubeDef': {
            'qDimensions': [{'qDef': {'qFieldDefs': [d]}} for d in dims],
            'qMeasures':   [{'qDef': {'qDef': m}}          for m in meds],
            'qInitialDataFetch': [{'qLeft': 0, 'qTop': 0, 'qWidth': w, 'qHeight': alto}],
        }
    }
    h = await s.create_session_object(defn)
    layout = await s.get_layout(h)
    pages = layout.get('qHyperCube', {}).get('qDataPages', [])
    return pages[0].get('qMatrix', []) if pages else []

def t(row, i): return row[i].get('qText', '') if i < len(row) else ''
def n(row, i): return row[i].get('qNum',  0)  if i < len(row) else 0

async def main():
    mgr = SessionManager()
    s   = await mgr.get(APP_TRA)
    lines = []

    def p(x=''):
        lines.append(x)
        print(x)

    # ── 1. Factura_SAP — valores reales (sin filtro de sede) ──────────────────
    p("=" * 65)
    p("Factura_SAP — primeros 15 valores distintos (sin filtro)")
    p("=" * 65)
    rows = await hc(s, ['Factura_SAP'], ['COUNT(1)'], alto=15)
    for r in rows:
        p(f"  {t(r,0)!r:<35}  count={n(r,1):,.0f}")

    # ── 2. Campos SAP de Contabilidad: Pedido / Orden / NumeroPedido ──────────
    p()
    p("=" * 65)
    p("Campos candidatos en Contabilidad_Otros_Ingresos")
    p("(busco campo con numero de servicio tipo '374258')")
    p("=" * 65)
    campos_coi = ['Pedido', 'Orden', 'OrdenSAP', 'NumeroPedido', 'NumPedido',
                  'Referencia', 'Documento', 'NumeroOrden', 'PedidoVenta',
                  'NroServicio', 'NumeroServicio']
    for c in campos_coi:
        rows2 = await hc(s, [c], ['SUM(Vlr_Ingreso_Calculado)'], alto=5)
        vals  = [t(r, 0) for r in rows2 if t(r, 0) not in ('', '-', '0', 'NULL')]
        if vals:
            p(f"  OK  {c:<20}  ej: {vals[:5]}")

    # ── 3. Contabilidad_COI: Factura_SAP con Id_Sede=4 (SAN DIEGO) ───────────
    p()
    p("=" * 65)
    p("ContabilidadOtrosIngresos: Factura_SAP con Id_Sede=4 SAN DIEGO")
    p("=" * 65)
    rows3 = await hc(s,
        ['Factura_SAP'],
        ["SUM({<Id_Sede={4}, Ejecucion={'ADICIONALES'}>} Ejecutado_COI)"],
        alto=20
    )
    for r in rows3:
        val = n(r, 1)
        if abs(val) > 0:
            p(f"  SAP={t(r,0)!r:<30}  val={val:,.0f}")

    # ── 4. Detalle_Facturas_Orden_Parque — campos con valores no-cero ─────────
    p()
    p("=" * 65)
    p("Detalle_Facturas_Orden_Parque — campos con valores reales")
    p("(busco campo con numero de servicio tipo '374258')")
    p("=" * 65)
    campos_parque = ['Pedido', 'Orden', 'OrdenSAP', 'NumeroPedido', 'NumPedido',
                     'Referencia', 'Documento', 'NumeroOrden', 'PedidoVenta',
                     'NroServicio', 'NumeroServicio', 'Cliente', 'NIT',
                     'NombreCliente', 'TipoDocumento', 'Posicion']
    for c in campos_parque:
        rows4 = await hc(s, [c], ['SUM(VlrIngresoCalculado)'], alto=5)
        vals  = [t(r, 0) for r in rows4 if t(r, 0) not in ('', '-', '0', 'NULL')]
        if vals:
            p(f"  OK  {c:<20}  ej: {vals[:5]}")

    # ── 5. Numero_Servicio (MatrizCostos) vs muestra de '6 digitos' ──────────
    p()
    p("=" * 65)
    p("MatrizCostos: muestra Numero_Servicio y Factura_Convenio")
    p("=" * 65)
    rows5 = await hc(s,
        ['Numero_Servicio', 'Factura_Convenio', 'Factura_Excedentes'],
        ['COUNT(Numero_Servicio)'], alto=10)
    for r in rows5:
        p(f"  NS={t(r,0):<12}  FacConv={t(r,1):<20}  FacExc={t(r,2):<20}")

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"\nGuardado en {OUT}")
    await mgr.close_all()

asyncio.run(main())
