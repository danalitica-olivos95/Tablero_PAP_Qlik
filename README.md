# qlik-mcp

Servidor MCP + utilidades para consultar apps de Qlik Sense de Coopserfun
(Comercial Homenajes, Acueducto_y_PAP_Informe_Transformación, etc.) vía
Engine API y QRS.

## Requisitos

- Python 3.13+
- Acceso al Qlik Sense interno (host `bi.coopserfun.com.co`)
- Certificados cliente exportados desde QMC en `certs/` (no incluidos en el repo)

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # editar valores si difieren
```

Colocar `root.pem`, `client.pem` y `client_key.pem` dentro de `certs/`.

## Estructura

```
qlik-mcp/
├─ src/qlik_mcp/        Servidor MCP (engine_client, qrs_client, tools, server)
├─ scripts/             Scripts ad-hoc de análisis (uno por consulta puntual)
├─ docs/                Documentación por app de Qlik
│   ├─ Comercial_Homenajes.md
│   └─ Acueducto_y_PAP_Informe_Transformacion.md
├─ certs/               Certificados (ignorado por git)
├─ .env                 Variables de entorno (ignorado por git)
├─ CLAUDE.md            Notas operativas para Claude
└─ requirements.txt
```

## Apps documentadas

| App | ID | Documentación |
|---|---|---|
| Comercial Homenajes | `6094b586-82ff-4dd1-9a0e-45c4eb67ef16` | [CLAUDE.md](CLAUDE.md) |
| Acueducto y PAP — Informe Transformación | _pendiente_ | [docs/Acueducto_y_PAP_Informe_Transformacion.md](docs/Acueducto_y_PAP_Informe_Transformacion.md) |

## Uso rápido

```python
import asyncio, sys
sys.path.insert(0, 'src')
from qlik_mcp.engine_client import EngineClient

async def main():
    async with EngineClient() as eng:
        apps = await eng.list_apps()
        for a in apps:
            print(a['qDocId'], a['qTitle'])

asyncio.run(main())
```

## Seguridad

- `certs/`, `.env` y todos los Excel/CSV/Parquet están en `.gitignore`.
- Antes de cada push verifica `git status` para no subir credenciales ni datos sensibles.
