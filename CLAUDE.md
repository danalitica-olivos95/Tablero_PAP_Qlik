# Contexto Qlik — Coopserfun / Comercial Homenajes

## Conexión
- **Host:** bi.coopserfun.com.co  (QRS: 4242 · Engine: 4747)
- **Certs:** `C:/Users/mario_481/qlik-mcp/certs`
- **Usuario:** sa_engine (INTERNAL)
- **App principal:** Comercial Homenajes  
  ID: `6094b586-82ff-4dd1-9a0e-45c4eb67ef16`

## Módulo principal
`qlik_analytics.py` — importar siempre así:

```python
import asyncio, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'src')
from qlik_analytics import QlikAnalytics, SEDES, SEDES_ORDEN, APP_COMERCIAL

async def main():
    qa = await QlikAnalytics.connect()
    # ... consultas ...
    await qa.cerrar()

asyncio.run(main())
```

## Métodos disponibles en QlikAnalytics

| Método | Qué hace |
|--------|----------|
| `await qa.fecha_max()` | Devuelve vFechaMax como 'DD/MM/YYYY' |
| `await qa.evaluar(expr)` | Evalúa expresión Qlik, devuelve float |
| `await qa.variable(nombre)` | Lee variable Qlik como texto |
| `await qa.hipercubo(dims, medidas)` | Hipercubo genérico, devuelve filas |
| `await qa.total_adicionales(fecha)` | Total $ ejecutado ADICIONALES del día |
| `await qa.adicionales_por_sede(fecha)` | Dict {sede: valor} del día |
| `await qa.adicionales_diario_mes()` | Dict {fecha: {sede: valor}} del mes |
| `await qa.presupuesto_mes_por_sede()` | Dict {sede: presupuesto_mes} |
| `await qa.resumen_cumplimiento()` | Lista con ppto, ejec, % por sede |
| `qa.imprimir_resumen(filas)` | Imprime tabla en consola |

## Sedes y sus IDs

| Sede | Id_Sede |
|------|---------|
| CHICO | 1 |
| PALERMO | 2 |
| RESTREPO | 3 |
| SAN DIEGO | 4 |
| TEUSAQUILLO | 5 |
| JPCLO | 6 |
| SOACHA | 7 |
| SOGAMOSO | 8 |
| CHIA | 10 |
| RED OLIVOS | 12 |

## Variables clave del app
- `vFechaMax` — fecha del último día con datos (ej. '30/04/2026')
- `vFinMes`   — fin de mes (¡ojo: puede mostrar 31/12 en lugar del mes actual, bug conocido)

## Categorías de Ejecución (campo `Ejecucion`)
- `ADICIONALES` — servicios de todas las sedes (fuente: MatrizCostos)
- `ADICIONALES JPCLO` — ejecución especial de JPCLO (parque cementerio)
- `CONVENIOS` — servicios de convenio
- `PARTICULARES` — servicios particulares

> **IMPORTANTE:** Para JPCLO usar siempre `Ejecucion={'ADICIONALES','ADICIONALES JPCLO'}`
> para capturar su ejecución real. Con solo `ADICIONALES` aparece ~$5.4M en lugar de ~$44M.

## Fuentes de datos ADICIONALES
1. **MatrizCostos** — servicios fúnebres (usa `Fecha_Exequias`, no fecha factura)
2. **Contabilidad_Otros_Ingresos.qvd** — otros ingresos contabilidad
3. **Detalle_Facturas_Orden_Parque.qvd** — facturas parque cementerio

## Excel de referencia
- Ruta: `C:\Users\mario_481\Downloads\Ejecucion Presupuesto Comercial 30 de abril de 2026.xlsx`
- **ADICIONALES total** → hoja `RESUMEN CUMPLIMIENTO`, fila 35
- **ADICIONALES JPCLO** → hoja `SALAS`, fila 93
- **MatrizCostos raw** → hoja `MatrizMes actual` (una fila por servicio fúnebre)
- Columna fecha en `Facturas directo parque actual` → col 6 (no col 2)

## Exportar a Excel
Usar `exportar_matriz_excel.py` — genera `Matriz_Adicionales_Qlik_30abril2026_v2.xlsx`
con hojas: `ADICIONALES DIARIO` (cruzada fecha×sede) y `ADICIONALES MENSUAL` (resumen).

## Scripts de análisis disponibles
| Script | Para qué |
|--------|----------|
| `qlik_analytics.py` | Módulo principal reutilizable |
| `exportar_matriz_excel.py` | Genera Excel diario + mensual |
| `diff_30abril.py` | Detalle por sede de un día específico |
| `detalle_30abril_servicios.py` | Detalle por N° de servicio |
| `leer_excel.py` | Lee fuentes Excel (Otros Ingresos + Parque) |
| `reporte_adicionales_hoy.py` | Comparación referencia vs Qlik |

## Hallazgos previos (30/04/2026)
- Diferencia Excel vs Qlik: +$2,118,479 — servicios del 30/04 aún no en Excel
- 6 servicios del 30/04: 374258(CHICO $561K), 374177(PALERMO $342K),
  374281(SAN DIEGO $390K), 374383(RESTREPO $299K), 374361(RESTREPO $864K),
  374416(RESTREPO $91K)
- Total ejecutado ADICIONALES+JPCLO al 30/04: $514,664,987
- Presupuesto mes: $738,216,814 → 69.7% cumplimiento

## Estructura del Excel RESUMEN CUMPLIMIENTO
Hoja: `RESUMEN CUMPLIMIENTO` — estructura de filas clave:

| Fila | Concepto | Ppto/Mes | Ejecutado |
|------|----------|----------:|----------:|
| 14 | INGRESOS TOTALES (Salas+Parque+Prenecesidad) | $2,788M | $2,146M |
| 17 | CUMPLIMIENTO SEDES (solo salas) | $2,147M | $1,734M |
| 18 | CUMPLIMIENTO PRENECESIDAD | $394M | $250M |
| 19 | CUMPLIMIENTO DESTINO FINAL JPCLO (cementerio) | $219M | $162M |
| 21-30 | DISCRIMINADO SEDES (por sede, solo salas) | — | — |
| 33 | PARTICULARES | $897M | $657M |
| 34 | CONVENIO | $512M | $603M |
| 35 | ADICIONALES | $738M | $474M |

- `DISCRIMINADO SEDES` (filas 22-30) = PARTICULARES + CONVENIOS + ADICIONALES por sede
- **Excluye**: CREMACIÓN, LOTE, BÓVEDA (van al campo santo, no a salas)
- JPCLO en DISCRIMINADO SEDES = solo sus salas fúnebres ($66.6M), NO el cementerio

## JPCLO — Doble negocio (pendiente resolver en Qlik)
JPCLO tiene dos negocios separados que el Excel trata de forma distinta:

| Negocio | Excel (fila) | Ejecutado | Qlik |
|---------|-------------|----------:|------|
| Salas fúnebres | DISCRIMINADO SEDES fila 27 | $66,608,046 | Mezclado con cementerio |
| Cementerio/parque | DESTINO FINAL JPCLO fila 19 | $161,753,666 | `Ejecucion={'VENTAS DIRECTAS JPCLO'}` |
| **Total JPCLO** | | **$228,361,712** | $159,980,666 (solo cementerio) |

- En Qlik, `VENTAS DIRECTAS JPCLO` viene de `Detalle_Facturas_Orden_Parque.qvd`
- Se distribuye en Sede='DIRECTO DF JPCLO' ($101.2M) y Sede='-' ($58.8M, canal prenecesidad)
- Diferencia Qlik vs Excel DESTINO FINAL: **-$1,773,000** (servicios 30/04 post-cierre Excel)

## Diagnóstico diferencias Qlik vs Excel (30/04/2026)

### Causa 1 — Excel excluye CREMACIÓN, LOTE, BÓVEDA
El `DISCRIMINADO SEDES` solo muestra PARTICULARES+CONVENIOS+ADICIONALES.
Qlik sin ese filtro muestra más. Filtro correcto en Qlik:
```
Ejecucion={'ADICIONALES','PARTICULARES','CONVENIOS','ADICIONALES JPCLO'}
```

### Causa 2 — Desfase $1.77M por cierre anticipado del Excel
El Excel se cerró antes del reload final de Qlik (20:00 del 30/04).
Aparece en: PALERMO (+$1,773,000), SAN DIEGO (+$307,664), VENTAS DIRECTAS JPCLO (+$1,773,000).
**No es error** — Qlik tiene el dato más reciente. Se normaliza al día siguiente.

### Causa 3 — ADICIONALES JPCLO contamina bloque de salas
`ADICIONALES JPCLO` ($38.7M, de Detalle_Facturas_Orden_Parque) se asienta bajo
`Id_Sede=6` (JPCLO) inflando el bloque de salas. En Excel ese monto va a DESTINO FINAL.
**Solución**: separar expresiones — salas con `Id_Sede IN (1..8,10,12)` + categorías salas;
cementerio con `Ejecucion={'VENTAS DIRECTAS JPCLO'}`.

### Sedes que cuadran exactamente (tras aplicar filtro correcto)
CHICO ✓ | RESTREPO ✓ | TEUSAQUILLO ✓ | SOACHA ✓ | SOGAMOSO ✓ | CHIA ✓
Presupuesto todas las sedes ✓ | Presupuesto VENTAS DIRECTAS JPCLO ✓

## Diagnóstico diferencias Qlik vs Excel ADICIONALES (08/05/2026)

### Causa raíz — Tres fuentes con criterios de fecha distintos
`Fact_Ejecuciones_Ppto` mezcla tres fuentes para ADICIONALES:
| Fuente | Fecha usada | Cuadra con Excel |
|--------|-------------|-----------------|
| MatrizCostos | `Fecha_Exequias` | Sí |
| `Contabilidad_Otros_Ingresos.qvd` | `Fecha_Contabilizacion` | No |
| `Detalle_Facturas_Orden_Parque.qvd` | `Fecha` (factura) | No |

### Impacto medido mayo 2026
| Sede | MatrizCostos | Contabilidad+Parque | Total Qlik |
|------|-------------|---------------------|-----------|
| SAN DIEGO | 13,765K | 3,030K | 16,795K |
| CHICO | 33,361K | 15,644K | 49,006K |

- **SAN DIEGO**: Excel > Qlik ~841K — registros de Contabilidad/Parque con fechas desfasadas
- **CHICO**: Qlik > Excel ~timing — servicios 08/05 cargados después del corte del Excel

### Causa técnica confirmada
`IF(LEN(TRIM(%PK_Num_Fecha))>0, Ejecutado, 0)` distingue fuentes:
- `%PK_Num_Fecha` != NULL → MatrizCostos
- `%PK_Num_Fecha` == NULL → Contabilidad o Parque

### Fix pendiente — requerimiento a equipo de extracción
Los QVDs de Contabilidad y Parque no tienen `Numero_Servicio`.
**Solución**: pedir que se añada ese campo a los dos QVDs de extracción.
Una vez disponible, el fix en la transformación usa `ApplyMap`:
```qlik
MapFechaExequias:
Mapping Load [Numero_Servicio], [Fecha_Exequias] Resident MatrizCostos;

// En cada LOAD problemático, reemplazar la línea de Fecha por:
ApplyMap('MapFechaExequias', Numero_Servicio, <fecha_original>) as Fecha,
```
Archivos listos:
- `requerimiento_extraccion.txt` — para el equipo SAP
- `cambios_script_tra_comercial.txt` — cambios exactos al script de transformación
