# App: Acueducto_y_PAP_Informe_Cargue

> Primera app del [Tablero Acueducto y PAP](Tablero_Acueducto_y_PAP.md).
> Lee los archivos fuente (Excel, SAP, SFTP, etc.), valida estructura y
> contenido, y publica QVDs estandarizados que consume la app de
> [`Acueducto_y_PAP_Informe_Transformación`](Acueducto_y_PAP_Informe_Transformacion.md).

## Identificación

| Campo | Valor |
|---|---|
| Nombre | `Acueducto_y_PAP_Informe_Cargue` |
| App ID (qDocId) | 09f9b467-71ba-4182-9dfe-b34b8cd9096d |
| Stream | Dir_Analitica |
| Última recarga | about 3 hours ago |
| Owner | Dec 4, 2025 5:00 PM |
| Frecuencia recarga | Esta aplicación se actualiza automáticamente tres veces al día: 8:00 AM, 12:00 PM y 5:00 PM|

### Cómo descubrir el App ID

```python
import asyncio, sys
sys.path.insert(0, 'src')
from qlik_mcp.qrs_client import QrsClient

async def main():
    async with QrsClient() as qrs:
        apps = await qrs.list_apps()
        for a in apps:
            if 'Cargue' in a.get('name', ''):
                print(a['id'], '·', a['name'], '·', a.get('stream', {}).get('name'))

asyncio.run(main())
```

## Fuentes de datos

_pendiente_ — listar los orígenes que esta app lee.

| Origen | Tipo | Ruta / conexión | Periodicidad |
|---|---|---|---|
| _pendiente_ | Excel / SAP / SFTP / QVD | _pendiente_ | _pendiente_ |

## Validaciones aplicadas

_pendiente_ — describir los checks que ejecuta la app durante el cargue.

| # | Validación | Si falla | Severidad |
|---|---|---|---|
| 1 | _pendiente_ | _pendiente_ | _pendiente_ |

## Modelo de datos en memoria (intermedio)

### Tablas
| Tabla | Origen | Llaves | Notas |
|---|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ | _pendiente_ |

### Variables del app
| Variable | Valor / fórmula | Uso |
|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ |

## Salidas (QVDs que consume Transformación)

_pendiente_ — listar QVDs publicados que la siguiente app lee.

| QVD | Tabla origen | Campos | Ruta de publicación |
|---|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ | _pendiente_ |

## Hallazgos / Issues conocidos

_pendiente_ — registrar fallos de cargue, archivos faltantes, diferencias
de schema, etc.

## Bitácora de cambios al script de cargue

| Fecha | Cambio | Por |
|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ |
