# Tablero Acueducto y PAP — Informe Transformación

> Visión global del tablero. Para detalle por app, ver:
> - [Acueducto_y_PAP_Informe_Cargue.md](Acueducto_y_PAP_Informe_Cargue.md)
> - [Acueducto_y_PAP_Informe_Transformacion.md](Acueducto_y_PAP_Informe_Transformacion.md)

## Propósito del tablero

_pendiente_ — describir en 1-3 frases qué responde el tablero al negocio.
Ej: "Permite a la dirección financiera de Coopserfun monitorear el cargue
y la transformación de los PAP de Acueducto, validando consistencia entre
las fuentes de origen y los resultados publicados."

## Arquitectura — flujo entre apps

```
┌──────────────────────────────────────┐       ┌──────────────────────────────────────┐
│  Acueducto_y_PAP_Informe_Cargue      │       │  Acueducto_y_PAP_Informe_            │
│  ───────────────────────────────     │       │  Transformación                      │
│  • Lee archivos fuente               │       │  ───────────────────────────────     │
│  • Valida estructura                 │ QVD → │  • Aplica reglas de transformación   │
│  • Genera QVDs estandarizados        │       │  • Calcula KPIs                      │
│                                      │       │  • Publica hojas y visualizaciones   │
└──────────────────────────────────────┘       └──────────────────────────────────────┘
       ↑                                                       ↓
   Excel / SAP / SFTP                                Usuarios finales en Hub Qlik
```

_pendiente_ — confirmar QVDs específicos que se transfieren entre las dos apps.

## Apps que componen el tablero

| App | ID Qlik | Rol | Frecuencia recarga |
|---|---|---|---|
| `Acueducto_y_PAP_Informe_Cargue` | _pendiente_ | Ingesta y validación | _pendiente_ |
| `Acueducto_y_PAP_Informe_Transformación` | _pendiente_ | Cálculo y publicación | _pendiente_ |

## KPIs principales del tablero

_pendiente_ — listar los KPIs clave que muestra el tablero al usuario final.

| KPI | Definición | Expresión Qlik | Hoja donde aparece |
|---|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ | _pendiente_ |

## Hojas / vistas publicadas

_pendiente_ — listar las hojas que ve el usuario final.

| Hoja | Objetivo | Dimensiones | Medidas |
|---|---|---|---|
| _pendiente_ | _pendiente_ | _pendiente_ | _pendiente_ |

## Reglas de negocio centrales

_pendiente_ — describir las reglas que el tablero aplica:
- Criterios de inclusión/exclusión de PAP
- Manejo de fechas (corte, vigencia, transformación)
- Cálculos especiales (provisiones, ajustes, conciliaciones)

## Validaciones y conciliaciones

_pendiente_ — checks que se ejecutan al cargar y al transformar:
- Totales de control contra fuente
- Diferencias permitidas
- Acciones cuando una validación falla

## Hallazgos y diferencias conocidas

_pendiente_ — bitácora de discrepancias entre el tablero y las fuentes,
y su causa raíz (estilo del bloque de "Diagnóstico" en `CLAUDE.md` para
Comercial Homenajes).

## Bitácora de cambios

| Fecha | App | Cambio | Por |
|---|---|---|---|
| 2026-05-20 | (repo) | Documentación inicial creada | _pendiente_ |
