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
| `Acueducto_y_PAP_Informe_Transformación` | `f9047ec0-c8b9-4b14-ba82-3579359a8dca` | `PAP` | Transformación + 5 hojas de análisis | Encadenada con Cargue |

> Descripción oficial (Transformación): _"Reporte de ventas de Acueducto-PAP,
> donde están las transformaciones y seguimiento a los empleados por ventas
> en los diferentes canales. Permite identificar las ventas netas del convenio
> con la EAAB-ESP; **no representa el estado de cierre mensual**."_

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
│  f9047ec0-c8b9-4b14-ba82-3579359a8dca       │
│  Stream: PAP                                │
│  • Aísla 46188 (Acueducto)                  │
│  • Aísla 42289/42290 (PAP)                  │
│  • Cruza vendedores PAP vs. Acueducto       │
│  • Normaliza fechas y montos                │
│  • Clasifica canal final                    │
│  • Une mapa Bogotá (KML)                    │
│  • Tabla Contratos_Base + STORE CSV         │
│  • Publica 5 hojas al Hub                   │
└────────────────────┬────────────────────────┘
                     ▼
        Hub Qlik — 5 hojas:
        01 Contratos · 02 Estados_Cancelados ·
        03 Vendedores · 04 Producción · 05 Caracterización
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

## KPIs / métricas del tablero

| KPI | Definición | Hoja |
|---|---|---|
| Ventas Totales | `SUM(Total_Contratos)` | 01 |
| Ventas Acueducto | `SUM({<Canal_PAP_Final={'ACUEDUCTO'}>} Total_Contratos)` | 01 |
| Ventas PAP | `SUM({<Canal_PAP_Final={'PAP'}>} Total_Contratos)` | 01 |
| % Canceladas | `SUM({<Estado=...>} Total_Contratos) / SUM(Total_Contratos)` | 02 |
| Ventas Canceladas (Acueducto/PAP) | Análogo a Ventas Totales pero sobre estados de cancelación | 02 |
| Producción Facturada | `SUM(Valor_Facturado)` | 04 |
| Producción Sin Facturar | `SUM(Valor_Sin_Facturar)` | 04 |
| Cumplimiento Meta | `SUM(Total_Contratos) / Meta_Mes` | 03 |
| Distribución por Barrio | Conteo geográfico (mapa KML Bogotá) | 05 |
| Distribución por Estrato / Edad / Género | Conteos demográficos | 05 |

## Hojas publicadas (5)

| # | Hoja | Objetivo | Screenshot |
|---|---|---|---|
| 01 | `Contratos_Acueducto_PAP` | Volumen total y por convenio/canal, series temporales | [img](Acueducto_y_PAP_Informe_Transformacion.md#hoja-01--contratos_acueducto_pap) |
| 02 | `Estados_Cancelados` | % cancelación, ventas perdidas Acueducto/PAP | [img](Acueducto_y_PAP_Informe_Transformacion.md#hoja-02--estados_cancelados) |
| 03 | `Vendedores_Acueducto` | Ranking vendedor + cumplimiento meta | [img](Acueducto_y_PAP_Informe_Transformacion.md#hoja-03--vendedores_acueducto) |
| 04 | `Cantidad_y_Producción` | Cuotas y producción ($) por vendedor/convenio | [img](Acueducto_y_PAP_Informe_Transformacion.md#hoja-04--cantidad_y_producción) |
| 05 | `Caracterización` | Perfil demográfico (estrato, edad, género, barrio) y mapa | [img](Acueducto_y_PAP_Informe_Transformacion.md#hoja-05--caracterización) |

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
- **T-Transf-8** — La app advierte explícitamente "no representa el estado de cierre mensual" — difundir a consumidores ([I8](Acueducto_y_PAP_Informe_Transformacion.md#i8--descripción-del-app-advierte-que-no-es-estado-de-cierre-mensual))

## Bitácora de cambios

| Fecha | App | Cambio | Por |
|---|---|---|---|
| 2026-05-20 | (repo) | Documentación inicial a partir del script vigente | _pendiente_ |
| 2026-05-20 | Cargue | App ID, Stream y frecuencia recarga llenados | danalitica-olivos95 |
| 2026-05-20 | Transformación | App ID, descripción EAAB-ESP y 5 hojas con screenshots documentadas | _pendiente_ |
