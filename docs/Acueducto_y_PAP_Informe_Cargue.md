# App: Acueducto_y_PAP_Informe_Cargue

> Primera app del [Tablero Acueducto y PAP](Tablero_Acueducto_y_PAP.md).
> Extrae las ventas de Acueducto desde SAP HANA y publica un QVD
> estandarizado que consume la app de
> [`Acueducto_y_PAP_Informe_Transformación`](Acueducto_y_PAP_Informe_Transformacion.md).

## Identificación

| Campo | Valor |
|---|---|
| Nombre | `Acueducto_y_PAP_Informe_Cargue` |
| App ID (qDocId) | `09f9b467-71ba-4182-9dfe-b34b8cd9096d` |
| Stream | `Dir_Analitica` |
| Owner | _pendiente_ (creado: 4 dic 2025 17:00) |
| Frecuencia recarga | Automática 3 veces al día: 08:00, 12:00 y 17:00 |
| Última recarga | Dinámica — ver QMC |

## Tarea de recarga en QMC

| Campo | Valor |
|---|---|
| Nombre de la tarea | `Reload task of Acueducto_y_PAP_Informe_Cargue` |
| App asociada | `Acueducto_y_PAP_Informe_Cargue` |
| Enabled | ✅ Sí |
| Partial reload | ❌ No |
| Task session timeout | 1440 min (24 h) |
| Max retries | 0 (no reintenta si falla) |

### Triggers programados

| Nombre | Tipo | Habilitado | Hora |
|---|---|---|---|
| `Recarga 08am` | Schedule | ✅ | 08:00 |
| `Recarga 12:00` | Schedule | ✅ | 12:00 |
| `Recarga 17:00` | Schedule | ✅ | 17:00 |

> Los tres triggers están activos. **No hay reintentos** configurados — si
> un reload falla, el siguiente trigger lo intentará de nuevo (sin
> notificación automática). Recomendado: agregar `Max retries ≥ 1` o un
> trigger condicional "on previous task failure".

## Fuente de datos — SAP HANA

| Atributo | Valor |
|---|---|
| Conexión Qlik | `HANA1 (coopserfun_qlik)` |
| Esquema | `_SYS_BIC` |
| Vista | `OLIVOS.Qlik.Acueducto/OLV_ACUEDUCTO_VENTAS` |
| Tabla destino en memoria | `Acueducto_Ventas` |

Después del `STORE` la app hace `LIB CONNECT TO 'HANA'` (cambia a otra
conexión que ya no se usa en esta app — revisar si es necesario).

## Campos cargados desde HANA (22)

| # | Campo origen | Alias en Qlik | Tipo / notas |
|---|---|---|---|
| 1  | `Convenio` | `Convenio` | Texto; valores conocidos: `46188`, `42289`, `42290` |
| 2  | `NroContrato` | `Contrato` | **Renombrado** en LOAD |
| 3  | `Estado` | `Estado` | `ACT`, `ACTFALLEC`, otros |
| 4  | `Documento_Titular` | `Documento_Titular` | |
| 5  | `FechaInicioVigencia` | `FechaInicioVigencia` | Texto `DD/MM/YYYY` (se parsea en Transformación) |
| 6  | `CuentaContrato` | `CuentaContrato` | Formato `xxx-yyy` (split en Transformación) |
| 7  | `RefContrato` | `RefContrato` | Vacío ⇒ "Contact Center"; con valor ⇒ "PAP ACUEDUCTO" |
| 8  | `Ciclo` | `Ciclo` | |
| 9  | `CodVendedor` | `CodVendedor` | Llave para identificar vendedor |
| 10 | `NomVendedor` | `NomVendedor` | |
| 11 | `TienePago` | `TienePago` | |
| 12 | `ValorContrato` | `ValorContrato` | Texto con `,` decimal (se convierte en Transformación) |
| 13 | `Cuotas` | `Cuotas` | |
| 14 | `Cuotas_Facturadas` | `Cuotas_Facturadas` | |
| 15 | `Valor_Facturado` | `Valor_Facturado` | Texto con `,` decimal |
| 16 | `Cuotas_Sin_Facturar` | `Cuotas_Sin_Facturar` | |
| 17 | `Valor_Sin_Facturar` | `Valor_Sin_Facturar` | Texto con `,` decimal |
| 18 | `Ingreso_Recibido` | `Ingreso_Recibido` | Texto con `,` decimal |
| 19 | `Edad_Titular` | `Edad_Titular` | |
| 20 | `Sexo` | `Sexo` | `F` / `M` |
| 21 | `Estrato` | `Estrato` | |
| 22 | `Barrio` | `Barrio` | Llave para cruzar con `bta_localidades.kml` en Transformación |

## Salidas (QVD/CSV)

| Archivo | Ruta | Formato |
|---|---|---|
| `Acueducto_Ventas.qvd` | `lib://Extraccion (coopserfun_qlik)/Acueducto_Ventas.qvd` | QVD nativo |
| `Acueducto_Ventas.csv` | `lib://Extraccion (coopserfun_qlik)/Acueducto_Ventas.csv` | Texto delimitado |

> El QVD es el insumo principal de la app de Transformación.
> El CSV es respaldo / inspección manual.

## Variables del app

| Variable | Asignación | Uso |
|---|---|---|
| `FechaInicioVigencia` | `Timestamp(Now(), 'YYYY-MM-DD hh:mm:ss')` | Sello del momento de recarga. **Cuidado**: el nombre choca con la columna del mismo nombre — revisar si es intencional. |

## Validaciones aplicadas

_Actualmente el script no aplica validaciones explícitas durante el cargue._
Todas las normalizaciones (parseo de fechas, números con coma decimal, etc.)
ocurren en la app de Transformación. Sugerido agregar aquí:

- Conteo `NoOfRows('Acueducto_Ventas')` con `TRACE`
- Validación mínima: que cada Convenio cargado esté en `{42289, 42290, 46188}`
- Alarma si filas = 0

## Estructura del script (tabs)

| Tab | Contenido |
|---|---|
| `Main` | `SET` de formato Es-419 (decimales con `.`, miles con `,`, meses/días en español) |
| `Carga` | `LIB CONNECT` HANA + `LOAD ... SQL SELECT` + `STORE` QVD/CSV |
| `Sección` | Bloque inspectivo comentado (lectura del QVD para verificar filas) |
| `Variables` | `LET FechaInicioVigencia = Timestamp(Now(), ...)` |
| `Exit` | `//Exit Script` (comentado) |

## Issues conocidos

- **Doble `LIB CONNECT`**: al final del tab `Carga` se hace `LIB CONNECT TO 'HANA'` después del cargue. Esa segunda conexión no se usa — revisar si es residual.
- **Colisión de nombre `FechaInicioVigencia`**: variable y columna comparten nombre, puede confundir.

## Bitácora de cambios al script de cargue

| Fecha | Cambio | Por |
|---|---|---|
| 2026-05-20 | Documentación inicial generada a partir del script vigente | _pendiente_ |
