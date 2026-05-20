# Tablero Acueducto y PAP — Informe Transformación

Documentación funcional y técnica del tablero de Qlik Sense usado para el
seguimiento del proceso de **Acueducto y PAP (Patrimonios Autónomos Públicos)**
de Coopserfun.

El tablero se compone de **dos apps de Qlik Sense** que trabajan en cadena:

| # | App de Qlik | Rol | Documentación |
|---|---|---|---|
| 1 | `Acueducto_y_PAP_Informe_Cargue` | Carga, validación e ingesta de archivos fuente al modelo de datos | [docs/Acueducto_y_PAP_Informe_Cargue.md](docs/Acueducto_y_PAP_Informe_Cargue.md) |
| 2 | `Acueducto_y_PAP_Informe_Transformación` | Transformación, cálculo de métricas y publicación de visualizaciones | [docs/Acueducto_y_PAP_Informe_Transformacion.md](docs/Acueducto_y_PAP_Informe_Transformacion.md) |

Visión global del tablero (KPIs, flujo entre apps, hojas y vistas):
[**docs/Tablero_Acueducto_y_PAP.md**](docs/Tablero_Acueducto_y_PAP.md)

## Estructura del repositorio

```
Tablero_PAP_Qlik/
├─ docs/                         Documentación del tablero y de cada app
│   ├─ Tablero_Acueducto_y_PAP.md
│   ├─ Acueducto_y_PAP_Informe_Cargue.md
│   └─ Acueducto_y_PAP_Informe_Transformacion.md
├─ src/qlik_mcp/                 Servidor MCP usado para consultar las apps (herramienta)
├─ scripts/                      Scripts de descubrimiento y validación
├─ explorer/                     TUI de exploración del modelo
├─ CLAUDE.md                     Notas operativas
├─ .env.example                  Plantilla de variables de entorno
└─ requirements.txt
```

> El código en `src/qlik_mcp/`, `scripts/` y `explorer/` es la **herramienta**
> usada para consultar Qlik y mantener la documentación al día. El producto
> documentado es el **tablero** descrito en `docs/`.

## Cómo se mantiene la documentación

1. Conectarse al Qlik vía la herramienta (`src/qlik_mcp/`) o directamente en el QMC.
2. Ejecutar scripts de descubrimiento (`scripts/buscar_app_transformacion.py`,
   `scripts/ver_script_carga.py`, etc.) para extraer modelo, variables y métricas.
3. Volcar los hallazgos en los `.md` correspondientes dentro de `docs/`.
4. Commit + push.

## Requisitos para correr la herramienta

- Python 3.13+
- Acceso al Qlik Sense interno (`bi.coopserfun.com.co`)
- Certificados cliente en `certs/` (no incluidos)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## Seguridad

Excluidos del repo: `certs/*.pem`, `.env`, archivos Excel/CSV/Parquet y todos
los `*.txt` de exploración. Ver `.gitignore`.
