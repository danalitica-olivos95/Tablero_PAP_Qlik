# App auxiliar: `Map_Barrios_Bogota`

> Tercera app del [Tablero Acueducto y PAP](Tablero_Acueducto_y_PAP.md).
> Trae el maestro **Barrio → Localidad** desde una fuente pública oficial
> (Datos Abiertos Bogotá / IDECA), aplica limpieza de texto y publica el QVD
> `Map_Barrio_Localidad.qvd` que consume
> [`Acueducto_y_PAP_Informe_Transformación`](Acueducto_y_PAP_Informe_Transformacion.md)
> para enriquecer la columna `Barrio` con la `Localidad` correspondiente.

## Por qué existe

La columna `Barrio` que viene desde HANA es heterogénea: mezcla nombres de
**localidades** (BOSA, KENNEDY, FONTIBON), **barrios** (BALBANERA, VENECIA,
LA FLORESTA…), prefijos (`BRR VILLA ALSACIA`), nombres compuestos
(`MODELIA - MALLORCA`), typos (`NUENA CASTILLA`, `GARDIN`) y valores
genéricos (`BOGOTA`, `NO INFORMA`). El KML `bta_localidades.kml` solo tiene
polígonos de las 20 localidades, así que sin una tabla de equivalencia el
mapa no pinta el grueso de los registros.

Esta app aísla esa responsabilidad para que:
- El mapeo se actualice **automáticamente** desde una fuente oficial.
- La lógica viva fuera del script de Transformación (separación de concerns).
- Otras apps futuras puedan reutilizar el mismo QVD.

## Identificación

| Campo | Valor |
|---|---|
| Nombre propuesto | `Map_Barrios_Bogota` |
| App ID (qDocId) | _pendiente_ — generado al crear el app |
| Stream propuesto | `Dir_Analitica` |
| Frecuencia recarga | 06:00 (antes del trigger 08:00 de Cargue) |

## Fuente pública

| Fuente | Endpoint | Auth | Frecuencia actualización |
|---|---|---|---|
| **Datos Abiertos Bogotá (Socrata)** | `https://datosabiertos.bogota.gov.co/dataset/...` (buscar "barrios" o "sector catastral") | Pública, sin auth | Distrital, cambia esporádicamente |
| **IDECA — Catastro Distrital** | `https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/...` | Pública | Catastral, oficial |

> El **dataset ID exacto** depende del que escoja Coopserfun. Pasos para fijarlo:
> 1. Entrar a `https://datosabiertos.bogota.gov.co`.
> 2. Buscar `"barrios"` o `"sector catastral"`.
> 3. Tomar el dataset con columnas mínimas `nombre_barrio` y `localidad`.
> 4. Copiar la URL de la API JSON (botón "API" → "View API Docs").
> 5. Reemplazar `<DATASET_ID>` y `<SOCRATA_HOST>` en el script de abajo.

## Configuración del REST Connector (Qlik)

En el QMC → **Data connections** → **Create new** → **Qlik REST Connector**:

| Parámetro | Valor |
|---|---|
| Nombre conexión | `DatosAbiertos_Bogota_REST` |
| URL | `https://datosabiertos.bogota.gov.co/api/views/<DATASET_ID>/rows.json?accessType=DOWNLOAD` |
| Method | GET |
| Authentication | None |
| Query parameters | (vacío o `$limit=50000` si se usa SODA `/resource/`) |
| Pagination | Offset (`$offset`), step 50000 |
| Headers | `Accept: application/json` |

## Script Qlik para crear el app

Pegar tal cual al nuevo app. Recuerda crear primero la conexión REST y la
carpeta `Mapeo (coopserfun_qlik)` en QMC.

```qlik
///$tab Main
SET ThousandSep=',';
SET DecimalSep='.';
SET DateFormat='D/M/YYYY';
SET MonthNames='ene;feb;mar;abr;may;jun;jul;ago;sept;oct;nov;dic';
SET DayNames='lun;mar;mié;jue;vie;sáb;dom';
SET CollationLocale='es-419';

///$tab Maestro_Bogota
// Trae barrios oficiales de Bogotá desde Datos Abiertos
LIB CONNECT TO 'DatosAbiertos_Bogota_REST';

RestSrc:
SQL SELECT
    "nombre_barrio"   AS Barrio_Oficial,
    "localidad"       AS Localidad_Oficial
FROM JSON (wrap on) "root";

TRACE Filas crudas desde API: $(=NoOfRows('RestSrc'));

///$tab Limpieza
// Normaliza: mayúsculas, sin tildes, sin espacios dobles
Map_Barrio_Localidad_Tmp:
LOAD
    Upper(Trim(
        Replace(Replace(Replace(Replace(Replace(
            Barrio_Oficial,
            'Á','A'),'É','E'),'Í','I'),'Ó','O'),'Ú','U')
    ))                                              AS Barrio_Key,
    Barrio_Oficial                                  AS Barrio_Original,
    Upper(Trim(Localidad_Oficial))                  AS Localidad
RESIDENT RestSrc
WHERE Len(Trim(Barrio_Oficial)) > 0
  AND Len(Trim(Localidad_Oficial)) > 0;

DROP TABLE RestSrc;

// Deduplicar (un Barrio puede aparecer varias veces si hay sub-divisiones)
Map_Barrio_Localidad:
LOAD DISTINCT
    Barrio_Key,
    Barrio_Original,
    Localidad,
    SubStringCount(Barrio_Key, ' ') + 1             AS Palabras_En_Barrio
RESIDENT Map_Barrio_Localidad_Tmp;

DROP TABLE Map_Barrio_Localidad_Tmp;

TRACE Barrios únicos cargados: $(=NoOfRows('Map_Barrio_Localidad'));

///$tab Excepciones_Manuales
// Tabla para los typos conocidos que la API no detecta.
// Editar acá según vayan apareciendo en SIN_MAPEAR.
Map_Excepciones:
LOAD * INLINE [
Barrio_Key, Localidad
NUENA CASTILLA, ENGATIVA
GARDIN, FONTIBON
COOTRADECUN, KENNEDY
BRR VILLA ALSACIA, KENNEDY
MODELIA MALLORCA, FONTIBON
];

// Las excepciones tienen prioridad: concatenar con prefijo y luego DISTINCT
Concatenate(Map_Barrio_Localidad)
LOAD
    Barrio_Key,
    'EXCEPCION_MANUAL'  AS Barrio_Original,
    Localidad,
    SubStringCount(Barrio_Key, ' ') + 1 AS Palabras_En_Barrio
RESIDENT Map_Excepciones;

DROP TABLE Map_Excepciones;

///$tab Publicar
// QVD que consume Transformación
STORE Map_Barrio_Localidad
INTO [lib://Mapeo (coopserfun_qlik)/Map_Barrio_Localidad.qvd] (qvd);

TRACE *** Map_Barrio_Localidad.qvd publicado correctamente ***;
```

## Cambios en `Acueducto_y_PAP_Informe_Transformación`

Agregar un **nuevo tab** llamado `Mapeo_Barrios` antes del tab `Limpieza_estandarización_variables`:

```qlik
///$tab Mapeo_Barrios

// Mapa principal: match exacto Upper+Trim
MapBarrioExacto:
MAPPING LOAD
    Barrio_Key,
    Localidad
FROM [lib://Mapeo (coopserfun_qlik)/Map_Barrio_Localidad.qvd] (qvd);

// Mapa por "primera palabra significativa" — captura
// "SUBA LOMBARDIA" → SUBA, "BRR VILLA ALSACIA" → VILLA ALSACIA
MapBarrioPrimeraPalabra:
MAPPING LOAD
    SubField(Barrio_Key, ' ', 1) AS Barrio_PrimeraPalabra,
    Localidad
FROM [lib://Mapeo (coopserfun_qlik)/Map_Barrio_Localidad.qvd] (qvd)
WHERE Palabras_En_Barrio = 1;  // solo barrios mono-palabra como anclas
```

Luego, en el tab `Limpieza_estandarización_variables`, modificar el LOAD
de `Contratos_Base` para que el campo `Barrio` venga acompañado de
`Localidad` y `Localidad_Fuente`:

```qlik
// Llave normalizada del barrio
SET vBarrioKey = Upper(Trim(
    Replace(Replace(Replace(Replace(Replace(Replace(Replace(Replace(Replace(Replace(
        $1,
        'BRR ', ''),
        'BARRIO ', ''),
        'Á','A'),'É','E'),'Í','I'),'Ó','O'),'Ú','U'),
        '  ', ' '),
        ' - ', ' '),
        '-', ' ')
));

// Dentro del LOAD de Contratos_Base, agregar:
    Barrio,
    $(vBarrioKey(Barrio))            AS Barrio_Key,

    // Paso 1: match exacto
    IF(
        ApplyMap('MapBarrioExacto', $(vBarrioKey(Barrio)), '') <> '',
        ApplyMap('MapBarrioExacto', $(vBarrioKey(Barrio)), ''),

    // Paso 2: primera palabra del barrio (anclas localidad mono-palabra)
    IF(
        ApplyMap('MapBarrioPrimeraPalabra',
                 SubField($(vBarrioKey(Barrio)), ' ', 1),
                 '') <> '',
        ApplyMap('MapBarrioPrimeraPalabra',
                 SubField($(vBarrioKey(Barrio)), ' ', 1),
                 ''),

    // Paso 3: nada matchea
        'SIN_MAPEAR'
    )) AS Localidad,

    // Trazabilidad: de dónde salió la localidad
    IF(
        ApplyMap('MapBarrioExacto', $(vBarrioKey(Barrio)), '') <> '',
        'EXACTO',
    IF(
        ApplyMap('MapBarrioPrimeraPalabra',
                 SubField($(vBarrioKey(Barrio)), ' ', 1),
                 '') <> '',
        'PRIMERA_PALABRA',
        'SIN_MAPEAR'
    )) AS Localidad_Fuente,
```

Y al final del script, agregar un TRACE de cobertura:

```qlik
///$tab Cobertura_Mapeo
Cobertura:
LOAD
    Localidad_Fuente,
    Count(*) AS Registros
RESIDENT Contratos_Base
GROUP BY Localidad_Fuente;

TRACE === Cobertura de mapeo de Localidad ===;
FOR i = 0 TO NoOfRows('Cobertura') - 1
    TRACE   $(=Peek('Localidad_Fuente', $(i), 'Cobertura'))
          : $(=Peek('Registros', $(i), 'Cobertura'));
NEXT i;

// Top 20 barrios sin mapear para revisión humana
Top_SinMapear:
LOAD
    Barrio,
    Count(*) AS Registros
RESIDENT Contratos_Base
WHERE Localidad = 'SIN_MAPEAR'
GROUP BY Barrio
ORDER BY Registros DESC;

TRACE === Top 20 barrios SIN_MAPEAR ===;
FOR i = 0 TO Min(NoOfRows('Top_SinMapear') - 1, 19)
    TRACE   $(=Peek('Barrio', $(i), 'Top_SinMapear'))
          : $(=Peek('Registros', $(i), 'Top_SinMapear'));
NEXT i;

DROP TABLE Cobertura;
DROP TABLE Top_SinMapear;
```

## Tarea de recarga en QMC

| Campo | Valor sugerido |
|---|---|
| Nombre tarea | `Reload task of Map_Barrios_Bogota` |
| Trigger 1 | `Recarga 06:00` (diario) |
| Task session timeout | 60 min |
| Max retries | 2 (la API externa puede fallar) |

### Encadenamiento con Cargue

Agregar a la tarea `Reload task of Acueducto_y_PAP_Informe_Cargue`:
- Un trigger adicional **`On previous task succeeded`** apuntando a la tarea
  de `Map_Barrios_Bogota` → fuerza orden: Map antes que Cargue.

Alternativa más simple: dejar Map a las 06:00 fijo y confiar en que termina
antes de las 08:00.

## Operación: ciclo de vida del mapeo

```
┌──────────────────────────────────────────────────────────────┐
│ Día 1 — primer reload                                        │
│ • API trae N barrios oficiales                               │
│ • Transformación: 60% EXACTO, 25% PRIMERA_PALABRA, 15% SIN   │
│ • TRACE lista los 20 top SIN_MAPEAR                          │
└─────────────────────────────────┬────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────┐
│ Día 2 — analista revisa TRACE                                │
│ • Agrega 20 entradas al tab Excepciones_Manuales             │
│ • Recarga Map_Barrios_Bogota                                 │
└─────────────────────────────────┬────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────┐
│ Día 3+ — cobertura sube                                      │
│ • EXACTO + EXCEPCION_MANUAL + PRIMERA_PALABRA = >95%         │
│ • SIN_MAPEAR estable < 5% (long tail)                        │
└──────────────────────────────────────────────────────────────┘
```

## Pendientes (al implementar)

| # | Pendiente | Bloquea |
|---|---|---|
| 1 | Confirmar dataset ID en Datos Abiertos Bogotá | Crear la conexión REST |
| 2 | Crear conexión `DatosAbiertos_Bogota_REST` en QMC | Reload del app |
| 3 | Crear carpeta lib `Mapeo (coopserfun_qlik)` | STORE del QVD |
| 4 | Crear app `Map_Barrios_Bogota` y pegar el script | Todo |
| 5 | Modificar script de `Acueducto_y_PAP_Informe_Transformación` con los cambios mostrados | Mapeo en uso |
| 6 | Crear tarea QMC `Reload task of Map_Barrios_Bogota` y trigger 06:00 | Auto-sync |

## Bitácora de cambios

| Fecha | Cambio | Por |
|---|---|---|
| 2026-05-20 | Doc inicial — arquitectura, REST Connector y scripts listos | _pendiente_ |
