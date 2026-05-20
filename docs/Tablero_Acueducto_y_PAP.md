# Tablero Acueducto y PAP — Informe Transformación

> Visión global del tablero. Detalle por app:
> - [Acueducto_y_PAP_Informe_Cargue.md](Acueducto_y_PAP_Informe_Cargue.md)
> - [Acueducto_y_PAP_Informe_Transformacion.md](Acueducto_y_PAP_Informe_Transformacion.md)

## Propósito

Monitorear las ventas de tres convenios — Acueducto y dos PAP — analizando
contratos, vendedores, valor facturado/sin facturar y mapa por barrio de
Bogotá. Sirve como base para seguimiento de cumplimiento contra metas
mensuales del canal PAP.

## Apps que componen el tablero

| App | App ID | Stream | Rol | Frecuencia recarga |
|---|---|---|---|---|
| `Acueducto_y_PAP_Informe_Cargue` | `09f9b467-71ba-4182-9dfe-b34b8cd9096d` | `Dir_Analitica` | Extracción HANA + QVD | 08:00, 12:00, 17:00 |
| `Acueducto_y_PAP_Informe_Transformación` | _pendiente_ | _pendiente_ | Transformación + publicación | _pendiente_ |

## Universos de datos

| Convenio | Etiqueta | Tipo | Tratamiento especial |
|---|---|---|---|
| `46188` | `46188 - Acueducto` | Acueducto | `ValorContrato × 2` (regla R1) |
| `42289` | `42289 - Ind_Anual` | PAP | Filtrado por vendedores cruzados con Acueducto PAP |
| `42290` | `42290 - Ind_Financiado` | PAP | Filtrado por vendedores cruzados con Acueducto PAP |

## Flujo entre apps

```
┌─────────────────────────────────────────────┐
│  SAP HANA                                   │
│  _SYS_BIC.OLIVOS.Qlik.Acueducto/            │
│  OLV_ACUEDUCTO_VENTAS                       │
└────────────────────┬────────────────────────┘
                     │  LIB CONNECT HANA1
                     ▼
┌─────────────────────────────────────────────┐
│  App: Acueducto_y_PAP_Informe_Cargue        │
│  09f9b467-71ba-4182-9dfe-b34b8cd9096d       │
│  • LOAD + SQL SELECT (22 columnas)          │
│  • STORE QVD + CSV                          │
└────────────────────┬────────────────────────┘
                     │
                     ▼
        lib://Extraccion (coopserfun_qlik)/
        Acueducto_Ventas.qvd
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  App: Acueducto_y_PAP_Informe_Transformación│
│  • Aísla 46188 (Acueducto)                  │
│  • Aísla 42289/42290 (PAP)                  │
│  • Cruza vendedores PAP vs. Acueducto       │
│  • Normaliza fechas y montos                │
│  • Clasifica canal final                    │
│  • Une mapa Bogotá (KML)                    │
│  • Tabla Contratos_Base + STORE CSV         │
└────────────────────┬────────────────────────┘
                     ▼
        Hojas y visualizaciones del tablero
```

## Insumos externos

| Insumo | Ruta Qlik | Consumido por |
|---|---|---|
| Vista HANA `OLV_ACUEDUCTO_VENTAS` | conexión `HANA1 (coopserfun_qlik)` | Cargue |
| `Acueducto_Ventas.qvd` | `lib://Extraccion (coopserfun_qlik)/` | Transformación |
| `bta_localidades.kml` (Bogotá) | `lib://Mapas (coopserfun_qlik)/mapa_bogota/` | Transformación |
| `Contratos_Base.csv` (final) | `lib://Transformacion (coopserfun_qlik)/` | Visualizaciones / consumo externo |

## Reglas de negocio centrales

| # | Regla | Dónde se aplica |
|---|---|---|
| R1 | `ValorContrato × 2` solo para convenio `46188` | Transformación, tab `Convenio_acueducto_46188` |
| R2 | Canal `PAP ACUEDUCTO` si `RefContrato` no está vacío | Transformación, R2 |
| R3 | PAP válido solo si su vendedor también es PAP de Acueducto activo | Transformación, R3 (ApplyMap) |
| R4 | `Canal_Venta_PAP_Clasificado`: `PAP` si `RefContrato` len > 1 y no es `'0'`/`'1'` | Transformación, R4 |
| R5 | Importes de HANA llegan como texto con coma decimal → `NUM#(Replace(...,','.'))` | Transformación, R5 |
| R6 | Fechas en HANA como `DD/MM/YYYY` → `Date#(...,'DD/MM/YYYY')` | Transformación, R6 |
| R7 | `Total_Valor_Contrato = ValorContrato × Cuotas` | Transformación, R7 |
| R9 | `Canal_PAP_Final = 'ACUEDUCTO'` cuando no entró al universo PAP | Transformación, R9 |

> Detalle de cada regla en [Acueducto_y_PAP_Informe_Transformacion.md](Acueducto_y_PAP_Informe_Transformacion.md).

## KPIs / métricas previstas

_pendiente — completar tras inspeccionar las hojas del app en el Hub._

| KPI | Definición | Hoja |
|---|---|---|
| Total contratos | `SUM(Total_Contratos)` (cada fila vale 1) | _pendiente_ |
| Valor facturado | `SUM(Valor_Facturado)` | _pendiente_ |
| Valor sin facturar | `SUM(Valor_Sin_Facturar)` | _pendiente_ |
| Cumplimiento meta vendedor | `SUM(Total_Contratos) / Meta_Mes` | _pendiente_ |
| Distribución por barrio | Conteo geográfico (mapa KML) | _pendiente_ |

## Hojas / vistas publicadas

_pendiente — listar después de inspeccionar el app en el Hub._

| Hoja | Objetivo | Dimensiones | Medidas |
|---|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ | _pendiente_ |

## Calendario y metas

| Tabla | Cobertura | Origen | Riesgo |
|---|---|---|---|
| `Calendario_Meses` | 2025-07 → 2026-12 (18 meses) | INLINE en script | Manual; hay que actualizar cada año |
| `Metas_Mensuales` | **2025-07 → 2025-12 (6 meses, Meta_Mes = 60 fijo)** | INLINE en script | **No cubre 2026** — cumplimiento se ve incompleto |

## Issues abiertos del tablero

Referidos desde la doc por app (issue IDs internos):

- **T-Cargue-1** — Doble `LIB CONNECT` al final del tab `Carga` (innecesario)
- **T-Cargue-2** — Colisión de nombre `FechaInicioVigencia` (variable vs columna)
- **T-Transf-1** — Metas solo hasta 2025-12, falta 2026 ([I1](Acueducto_y_PAP_Informe_Transformacion.md#i1--metas_mensuales-solo-cubre-2025-07-a-2025-12))
- **T-Transf-2** — Calendario estático ([I2](Acueducto_y_PAP_Informe_Transformacion.md#i2--calendario_meses-es-estático))
- **T-Transf-3** — Etiqueta inconsistente "Contact Center" vs "Call Center" ([I3](Acueducto_y_PAP_Informe_Transformacion.md#i3--inconsistencia-contact-center-vs-call-center))
- **T-Transf-4** — Regla `× 2` del 46188 sin documentar ([I4](Acueducto_y_PAP_Informe_Transformacion.md#i4--regla-valorcontrato--2-del-convenio-46188))
- **T-Transf-5** — Filtro de estado PAP comentado ([I5](Acueducto_y_PAP_Informe_Transformacion.md#i5--estado-no-filtrado-en-pap))

## Bitácora de cambios

| Fecha | App | Cambio | Por |
|---|---|---|---|
| 2026-05-20 | (repo) | Documentación inicial a partir del script vigente | _pendiente_ |
| 2026-05-20 | Cargue | App ID, Stream y frecuencia recarga llenados | danalitica-olivos95 |
