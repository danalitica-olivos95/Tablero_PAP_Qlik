"""Módulo de análisis Qlik para Comercial Homenajes — Coopserfun."""
import sys, asyncio
sys.path.insert(0, 'src')
from qlik_mcp.engine_client import SessionManager
from datetime import date, timedelta
from collections import defaultdict

APP_COMERCIAL = '6094b586-82ff-4dd1-9a0e-45c4eb67ef16'

SEDES = {
    'CHICO': 1, 'PALERMO': 2, 'RESTREPO': 3, 'SAN DIEGO': 4,
    'TEUSAQUILLO': 5, 'JPCLO': 6, 'SOACHA': 7,
    'SOGAMOSO': 8, 'CHIA': 10, 'RED OLIVOS': 12,
}
ID_A_SEDE  = {str(v): k for k, v in SEDES.items()}
SEDES_ORDEN = ['CHICO','PALERMO','RESTREPO','SAN DIEGO','TEUSAQUILLO',
               'JPCLO','SOACHA','SOGAMOSO','CHIA','RED OLIVOS']

EJEC_ADICIONALES = "Ejecucion={'ADICIONALES','ADICIONALES JPCLO'}"
EJEC_PURO        = "Ejecucion={'ADICIONALES'}"


class QlikAnalytics:
    def __init__(self, session, app_id=APP_COMERCIAL):
        self._s   = session
        self._aid = app_id

    @classmethod
    async def connect(cls, app_id=APP_COMERCIAL):
        mgr = SessionManager()
        s   = await mgr.get(app_id)
        obj = cls(s, app_id)
        obj._mgr = mgr
        return obj

    async def cerrar(self):
        await self._mgr.close_all()

    @staticmethod
    def _num(cell) -> float:
        n = cell.get('qNum', 0)
        try:
            v = float(n)
            return 0.0 if v != v else v
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _txt(cell) -> str:
        return cell.get('qText', '')

    async def evaluar(self, expr: str) -> float:
        e = expr if expr.startswith('=') else f'={expr}'
        r = await self._s.call(self._s.app_handle, 'EvaluateEx', [e])
        v = r.get('qValue', {})
        if v.get('qIsNumeric'):
            return v.get('qNumber', 0)
        txt = v.get('qText', '0').replace('.', '').replace(',', '.')
        try:    return float(txt)
        except: return 0.0

    async def evaluar_texto(self, expr: str) -> str:
        e = expr if expr.startswith('=') else f'={expr}'
        r = await self._s.call(self._s.app_handle, 'EvaluateEx', [e])
        v = r.get('qValue', {})
        return v.get('qText', str(v.get('qNumber', '')))

    async def variable(self, nombre: str) -> str:
        r = await self._s.call(self._s.app_handle, 'EvaluateEx', [f'$({nombre})'])
        return r.get('qValue', {}).get('qText', '')

    async def hipercubo(self, dimensiones, medidas, alto=500) -> list:
        dims = [{'qDef': {'qFieldDefs': [d]}} if isinstance(d, str) else d
                for d in dimensiones]
        meds = [{'qDef': {'qDef': m, 'qLabel': f'M{i}'}} if isinstance(m, str) else m
                for i, m in enumerate(medidas)]
        w = len(dims) + len(meds)
        defn = {
            'qInfo': {'qType': 'SessionObject'},
            'qHyperCubeDef': {
                'qDimensions': dims, 'qMeasures': meds,
                'qSuppressMissing': True, 'qSuppressZero': True,
                'qInitialDataFetch': [{'qLeft':0,'qTop':0,'qWidth':w,'qHeight':alto}]
            }
        }
        handle = await self._s.create_session_object(defn)
        layout = await self._s.get_layout(handle)
        hc     = layout.get('qHyperCube', {})
        size   = hc.get('qSize', {}).get('qcy', 0)
        rows   = hc.get('qDataPages', [{}])[0].get('qMatrix', [])
        offset = len(rows)
        while offset < size:
            res = await self._s.call(handle, 'GetHyperCubeData',
                ['/qHyperCubeDef',
                 [{'qLeft':0,'qTop':offset,'qWidth':w,'qHeight':500}]])
            batch = res.get('qDataPages',[{}])[0].get('qMatrix',[])
            if not batch: break
            rows.extend(batch)
            offset += len(batch)
            if len(batch) < 500: break
        return rows

    async def fecha_max(self) -> str:
        return await self.variable('vFechaMax')

    async def _fechas_mes(self, fecha_fin=None) -> list:
        f  = fecha_fin or await self.fecha_max()
        p  = f.split('/')
        d0 = date(int(p[2]), int(p[1]), 1)
        d1 = date(int(p[2]), int(p[1]), int(p[0]))
        out, d = [], d0
        while d <= d1:
            out.append(d.strftime('%d/%m/%Y'))
            d += timedelta(days=1)
        return out

    def _set_fechas(self, fechas) -> str:
        if isinstance(fechas, str):
            return f"Fecha={{'{fechas}'}}"
        return f"Fecha={{{','.join(repr(f) for f in fechas)}}}"

    async def adicionales_por_sede(self, fecha=None, mes_completo=False) -> dict:
        fechas = await self._fechas_mes(fecha) if mes_completo else (fecha or await self.fecha_max())
        set_f  = self._set_fechas(fechas)
        rows   = await self.hipercubo(
            ['Id_Sede'],
            [f"SUM({{<{EJEC_ADICIONALES},{set_f}>}} Ejecutado)"]
        )
        result = {}
        for row in rows:
            id_s = str(int(self._num(row[0]))) if row[0].get('qIsNumeric') else self._txt(row[0])
            sede = ID_A_SEDE.get(id_s, f'Id={id_s}')
            result[sede] = self._num(row[1]) * 1000
        return result

    async def presupuesto_mes_por_sede(self, fecha_ref=None) -> dict:
        f    = fecha_ref or await self.fecha_max()
        rows = await self.hipercubo(
            ['Id_Sede'],
            [f"SUM({{<{EJEC_PURO},TipoPresupuesto={{'I'}},Fecha={{'{f}'}}>}} Presupuesto)"]
        )
        result = {}
        for row in rows:
            id_s = str(int(self._num(row[0]))) if row[0].get('qIsNumeric') else self._txt(row[0])
            sede = ID_A_SEDE.get(id_s, f'Id={id_s}')
            result[sede] = self._num(row[1]) * 1000
        return result

    async def resumen_cumplimiento(self, fecha=None) -> list:
        f    = fecha or await self.fecha_max()
        ppto = await self.presupuesto_mes_por_sede(f)
        ejec = await self.adicionales_por_sede(f, mes_completo=True)
        filas = []
        for sede in SEDES_ORDEN:
            p = ppto.get(sede, 0)
            e = ejec.get(sede, 0)
            filas.append({'sede': sede, 'presupuesto': p, 'ejecutado': e,
                          'pct': e/p if p else 0, 'diferencia': e-p})
        tp = sum(f['presupuesto'] for f in filas)
        te = sum(f['ejecutado']   for f in filas)
        filas.append({'sede':'TOTAL','presupuesto':tp,'ejecutado':te,
                      'pct':te/tp if tp else 0,'diferencia':te-tp})
        return filas
