# Acueducto y PAP — Informe Transformación

> Documentación de la app de Qlik. **Pendiente completar con valores reales** —
> los campos marcados con `_pendiente_` se llenan ejecutando el script de
> descubrimiento (ver más abajo).

## Identificación

| Campo | Valor |
|---|---|
| Nombre app | `Acueducto_y_PAP_Informe_Transformación` |
| App ID (qDocId) | _pendiente_ |
| Stream | _pendiente_ |
| Última recarga | _pendiente_ |
| Owner | _pendiente_ |

## Descubrir el App ID

Desde la raíz del repo, con el entorno virtual activo y `certs/` configurado:

```python
import asyncio, sys
sys.path.insert(0, 'src')
from qlik_mcp.qrs_client import QrsClient

async def main():
    async with QrsClient() as qrs:
        apps = await qrs.list_apps()
        for a in apps:
            if 'Acueducto' in a.get('name', ''):
                print(a['id'], '·', a['name'], '·', a.get('stream', {}).get('name'))

asyncio.run(main())
```

Copiar el `id` impreso en la fila **App ID** de la tabla anterior y en `.env`
o en una constante del módulo correspondiente.

## Modelo de datos

### Tablas principales
| Tabla | Origen (QVD/Excel) | Llaves | Notas |
|---|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ | _pendiente_ |

### Campos clave
- _pendiente_

### Variables del app
| Variable | Valor / fórmula | Uso |
|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ |

## Métricas y expresiones documentadas

| Métrica | Expresión Qlik | Hoja/Visual donde aparece |
|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ |

## Hallazgos / Issues conocidos

_pendiente — se registran aquí discrepancias, bugs del script de carga,
diferencias con Excel de referencia, etc._

## Cambios recientes en el script de transformación

_pendiente — fechas y resumen de cambios al script de carga._
