# App: Acueducto_y_PAP_Informe_Transformación

> Segunda app del [Tablero Acueducto y PAP](Tablero_Acueducto_y_PAP.md).
> Toma los QVDs publicados por
> [`Acueducto_y_PAP_Informe_Cargue`](Acueducto_y_PAP_Informe_Cargue.md),
> aplica reglas de transformación, calcula KPIs y publica las hojas que
> consume el usuario final.

## Identificación

| Campo | Valor |
|---|---|
| Nombre | `Acueducto_y_PAP_Informe_Transformación` |
| App ID (qDocId) | _pendiente_ |
| Stream | _pendiente_ |
| Última recarga | _pendiente_ |
| Owner | _pendiente_ |
| Frecuencia recarga | _pendiente_ |

### Cómo descubrir el App ID

```python
import asyncio, sys
sys.path.insert(0, 'src')
from qlik_mcp.qrs_client import QrsClient

async def main():
    async with QrsClient() as qrs:
        apps = await qrs.list_apps()
        for a in apps:
            if 'Transformaci' in a.get('name', ''):
                print(a['id'], '·', a['name'], '·', a.get('stream', {}).get('name'))

asyncio.run(main())
```

## Entradas (desde la app de Cargue)

_pendiente_ — listar los QVDs producidos por la app de Cargue que esta app consume.

| QVD | Origen | Campos relevantes |
|---|---|---|
| _pendiente_ | `Acueducto_y_PAP_Informe_Cargue` | _pendiente_ |

## Modelo de datos resultante

### Tablas
| Tabla | Origen | Llaves | Notas |
|---|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ | _pendiente_ |

### Variables del app
| Variable | Valor / fórmula | Uso |
|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ |

## Reglas de transformación

_pendiente_ — describir cada transformación importante del script de carga
(qué hace, sobre qué tabla, condiciones).

| # | Regla | Tabla destino | Fuente del script |
|---|---|---|---|
| 1 | _pendiente_ | _pendiente_ | _pendiente_ |

## Métricas y expresiones publicadas

| Métrica | Expresión Qlik | Hoja/Visual |
|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ |

## Hojas publicadas

| Hoja | Objetivo | Dimensiones | Medidas |
|---|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ | _pendiente_ |

## Hallazgos / Issues conocidos

_pendiente_ — bugs detectados, diferencias con fuente, fixes aplicados o pendientes.

## Bitácora de cambios al script de transformación

| Fecha | Cambio | Por |
|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ |
