"""
Módulo de análisis Qlik para Comercial Homenajes — Coopserfun
Uso: from qlik_analytics import QlikAnalytics, SEDES, APP_COMERCIAL
"""
import asyncio, sys, io
sys.path.insert(0, 'src')
from qlik_mcp.engine_client import SessionManager

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────
APP_COMERCIAL = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'

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
    'RED OLIVOS':  12,
}
ID_A_SEDE = {str(v): k for k, v in SEDES.items()}

SEDES_ORDEN = [
    'CHICO','PALERMO','RESTREPO','SAN DIEGO',
    'TEUSAQUILLO','JPCLO','SOACHA','SOGAMOSO','CHIA','RED OLIVOS'
]

# Categorías de ejecución
EJECUCION_ADICIONALES       = "Ejecucion={'ADICIONALES','ADICIONALES JPCLO'}"
EJECUCION_ADICIONALES_PURO  = "Ejecucion={'ADICIONALES'}"
EJECUCION_CONVENIOS         = "Ejecucion={'CONVENIOS'}"
EJECUCION_PARTICULARES      = "Ejecucion={'PARTICULARES'}"

# IDs de medidas de biblioteca (app Comercial Homenajes)
LIB_PPTO_DIA  = '0475214f-125d-4650-a1aa-56144347bf5a'   # Presupuesto día
LIB_EJEC      = 'd3b25431-9b23-44ef-a0cc-2b34615aa511'   # Ejecución Adicionales
LIB_DIM_SEDE  = 'gHSMeud'                                 # Dimensión Sede


# ──────────────────────────────────────────────
# CLASE PRINCIPAL
# ──────────────────────────────────────────────
class QlikAnalytics:
    """
    Cliente de alto nivel para consultar el app Comercial Homenajes.

    Uso típico:
        qa = await QlikAnalytics.connect()
        total = await qa.evaluar("=SUM(Ejecutado)")
        df    = await qa.adicionales_por_sede(fecha='30/04/2026')
        await qa.cerrar()

    O como context manager:
        async with QlikAnalytics.sesion() as qa:
            ...
    """

    def __init__(self, session, app_id=APP_COMERCIAL):
        self._session = session
        self._app_id  = app_id

    # ── Fábrica ──────────────────────────────
    @classmethod
    async def connect(cls, app_id=APP_COMERCIAL):
        mgr = SessionManager()
        s   = await mgr.get(app_id)
        obj = cls(s, app_id)
        obj._mgr = mgr
        return obj

    async def cerrar(self):
        await self._mgr.close_all()

    # ── Primitivas ───────────────────────────
    async def evaluar(self, expresion: str) -> float:
        """Evalúa una expresión Qlik y devuelve el número resultante."""
        expr = expresion if expresion.startswith('=') else f'={expresion}'
        r = await self._session.call(self._session.app_handle, 'EvaluateEx', [expr])
        v = r.get('qValue', {})
        if v.get('qIsNumeric'):
            return v.get('qNumber', 0)
        txt = v.get('qText', '0').replace('.', '').replace(',', '.')
        try:
            return float(txt)
        except:
            return 0.0

    async def variable(self, nombre: str) -> str:
        """Lee el valor de texto de una variable Qlik."""
        r = await self._session.call(self._session.app_handle, 'EvaluateEx', [f'$({nombre})'])
        return r.get('qValue', {}).get('qText', '')

    async def hipercubo(self, dimensiones: list, medidas: list,
                        alto=500, ancho=None) -> list:
        """
        Crea un objeto hipercubo y devuelve todas sus filas.
        dimensiones: lista de field names  p.ej. ['Fecha','Id_Sede']
        medidas:     lista de expresiones  p.ej. ['SUM(Ejecutado)']
        """
        dims = [{'qDef': {'qFieldDefs': [d]}} if isinstance(d, str)
                else d for d in dimensiones]
        meds = [{'qDef': {'qDef': m, 'qLabel': f'M{i}'}} if isinstance(m, str)
                else m for i, m in enumerate(medidas)]
        w = ancho or (len(dims) + len(meds))
        defn = {
            'qInfo': {'qType': 'SessionObject'},
            'qHyperCubeDef': {
                'qDimensions': dims,
                'qMeasures':   meds,
                'qSuppressMissing': True,
                'qSuppressZero':    True,
                'qInitialDataFetch': [{'qLeft': 0, 'qTop': 0, 'qWidth': w, 'qHeight': alto}]
            }
        }
        handle = await self._session.create_session_object(defn)
        layout = await self._session.get_layout(handle)
        hc     = layout.get('qHyperCube', {})
        size   = hc.get('qSize', {}).get('qcy', 0)

        # Leer datos de la carga inicial
        rows = hc.get('qDataPages', [{}])[0].get('qMatrix', [])

        # Paginar si hay más filas que las del fetch inicial
        offset = len(rows)
        page   = 500
        while offset < size:
            res = await self._session.call(
                handle, 'GetHyperCubeData',
                ['/qHyperCubeDef',
                 [{'qLeft': 0, 'qTop': offset, 'qWidth': w, 'qHeight': page}]])
            batch = res.get('qDataPages', [{}])[0].get('qMatrix', [])
            if not batch:
                break
            rows.extend(batch)
            offset += len(batch)
            if len(batch) < page:
                break
        return rows

    # ── Helpers de valor ─────────────────────
    @staticmethod
    def _num(cell) -> float:
        n = cell.get('qNum', 0)
        try:
            v = float(n)
            return 0.0 if v != v else v  # NaN check: NaN != NaN
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _txt(cell) -> str:
        return cell.get('qText', '')

    # ── Consultas de negocio ─────────────────

    async def fecha_max(self) -> str:
        """Devuelve vFechaMax como string 'DD/MM/YYYY'."""
        return await self.variable('vFechaMax')

    async def total_adicionales(self, fecha: str = None,
                                sedes: list = None) -> float:
        """
        Total ejecutado ADICIONALES (incluye ADICIONALES JPCLO).
        fecha:  'DD/MM/YYYY'  o None para vFechaMax
        sedes:  lista de Id_Sede numéricos, o None para todas
        """
        f = fecha or await self.fecha_max()
        set_fecha = f"Fecha={{'{f}'}}"
        set_sedes = (f"Id_Sede={{{','.join(str(s) for s in sedes)}}}"
                     if sedes else '')
        filtros = ','.join(filter(None, [
            EJECUCION_ADICIONALES, set_fecha, set_sedes]))
        v = await self.evaluar(f"SUM({{<{filtros}>}} Ejecutado)")
        return v * 1000

    def _set_fechas(self, fechas) -> str:
        """Construye el set de fechas para set analysis a partir de str o list."""
        if isinstance(fechas, str):
            return f"Fecha={{'{fechas}'}}"
        return f"Fecha={{{','.join(repr(f) for f in fechas)}}}"

    async def _fechas_mes(self, fecha_fin: str = None) -> list:
        """Genera la lista de fechas DD/MM/YYYY desde el 1 del mes hasta fecha_fin."""
        from datetime import date, timedelta
        f = fecha_fin or await self.fecha_max()
        p = f.split('/')
        d0 = date(int(p[2]), int(p[1]), 1)
        d1 = date(int(p[2]), int(p[1]), int(p[0]))
        out, d = [], d0
        while d <= d1:
            out.append(d.strftime('%d/%m/%Y'))
            d += timedelta(days=1)
        return out

    async def adicionales_por_sede(self, fecha=None, mes_completo=False) -> dict:
        """
        Devuelve {nombre_sede: valor_ejecutado} para ADICIONALES.
        fecha:        'DD/MM/YYYY' para un día, o None para vFechaMax
        mes_completo: True para sumar todos los días del mes
        Incluye ADICIONALES JPCLO en JPCLO.
        """
        if mes_completo:
            fechas = await self._fechas_mes(fecha)
        else:
            fechas = fecha or await self.fecha_max()
        set_f = self._set_fechas(fechas)
        rows = await self.hipercubo(
            dimensiones=['Id_Sede'],
            medidas=[f"SUM({{<{EJECUCION_ADICIONALES},{set_f}>}} Ejecutado)"]
        )
        resultado = {}
        for row in rows:
            id_s = str(int(self._num(row[0]))) if row[0].get('qIsNumeric') else self._txt(row[0])
            sede = ID_A_SEDE.get(id_s, f'Id={id_s}')
            resultado[sede] = self._num(row[1]) * 1000
        return resultado

    async def adicionales_diario_mes(self, mes: int = None, anio: int = None) -> dict:
        """
        Devuelve {fecha_str: {sede: valor}} para todos los días del mes.
        Por defecto usa el mes de vFechaMax.
        """
        from datetime import date, timedelta
        fmax = await self.fecha_max()
        p = fmax.split('/')
        m = mes  or int(p[1])
        a = anio or int(p[2])
        d0 = date(a, m, 1)
        d1 = date(a, m, int(p[0])) if not mes else date(a, m, 30)
        fechas = []
        d = d0
        while d <= d1:
            fechas.append(d.strftime('%d/%m/%Y'))
            d += timedelta(days=1)
        set_fechas = ','.join(f"'{f}'" for f in fechas)

        rows = await self.hipercubo(
            dimensiones=['Fecha', 'Id_Sede'],
            medidas=[f"SUM({{<{EJECUCION_ADICIONALES},Fecha={{{set_fechas}}}>}} Ejecutado)"],
            alto=1000
        )
        from collections import defaultdict
        result = defaultdict(dict)
        for row in rows:
            fecha = self._txt(row[0])
            id_s  = str(int(self._num(row[1]))) if row[1].get('qIsNumeric') else self._txt(row[1])
            sede  = ID_A_SEDE.get(id_s, f'Id={id_s}')
            result[fecha][sede] = self._num(row[2]) * 1000
        return dict(result)

    async def presupuesto_mes_por_sede(self, fecha_ref: str = None) -> dict:
        """
        Devuelve {nombre_sede: presupuesto_mensual} usando TipoPresupuesto='I'.
        fecha_ref: cualquier día del mes (default vFechaMax).
        """
        f = fecha_ref or await self.fecha_max()
        rows = await self.hipercubo(
            dimensiones=['Id_Sede'],
            medidas=[
                f"SUM({{<{EJECUCION_ADICIONALES_PURO},TipoPresupuesto={{'I'}},Fecha={{'{f}'}}>}} Presupuesto)"
            ]
        )
        resultado = {}
        for row in rows:
            id_s = str(int(self._num(row[0]))) if row[0].get('qIsNumeric') else self._txt(row[0])
            sede = ID_A_SEDE.get(id_s, f'Id={id_s}')
            resultado[sede] = self._num(row[1]) * 1000
        return resultado

    async def resumen_cumplimiento(self, fecha: str = None) -> list:
        """
        Devuelve lista de dicts con presupuesto, ejecutado y % por sede.
        Presupuesto = total mes. Ejecutado = acumulado mes completo.
        """
        f = fecha or await self.fecha_max()
        ppto = await self.presupuesto_mes_por_sede(f)
        ejec = await self.adicionales_por_sede(f, mes_completo=True)
        filas = []
        for sede in SEDES_ORDEN:
            p = ppto.get(sede, 0)
            e = ejec.get(sede, 0)
            filas.append({
                'sede':        sede,
                'presupuesto': p,
                'ejecutado':   e,
                'pct':         e / p if p else 0,
                'diferencia':  e - p,
            })
        tot_p = sum(f['presupuesto'] for f in filas)
        tot_e = sum(f['ejecutado']   for f in filas)
        filas.append({
            'sede': 'TOTAL',
            'presupuesto': tot_p,
            'ejecutado':   tot_e,
            'pct':         tot_e / tot_p if tot_p else 0,
            'diferencia':  tot_e - tot_p,
        })
        return filas

    def imprimir_resumen(self, filas: list):
        """Imprime en consola el resumen de cumplimiento."""
        sep = '-' * 80
        print(f"\n{'SEDE':<15} | {'PRESUPUESTO':>18} | {'EJECUTADO':>18} | {'%':>8} | {'DIF':>16}")
        print(sep)
        for f in filas:
            pct = f'{f["pct"]*100:>7.1f}%'
            dif = f'{f["diferencia"]:>+16,.0f}'
            print(f"{f['sede']:<15} | {f['presupuesto']:>18,.0f} | "
                  f"{f['ejecutado']:>18,.0f} | {pct} | {dif}")
        print(sep)


# ──────────────────────────────────────────────
# EJECUCIÓN DIRECTA (demo)
# ──────────────────────────────────────────────
async def _demo():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    qa = await QlikAnalytics.connect()
    fecha = await qa.fecha_max()
    print(f'vFechaMax: {fecha}')
    print(f'\nConsultando resumen de cumplimiento ADICIONALES al {fecha}...\n')
    filas = await qa.resumen_cumplimiento()
    qa.imprimir_resumen(filas)
    await qa.cerrar()

if __name__ == '__main__':
    asyncio.run(_demo())
