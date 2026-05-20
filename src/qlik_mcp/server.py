import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from .qrs_client import QRSClient
from .engine_client import SessionManager
from .tools import apps, script, sheets, metadata, data_model

app = Server("qlik-mcp")
qrs = QRSClient()
sessions = SessionManager()


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_apps",
            description="Lista todas las aplicaciones Qlik Sense disponibles con su ID, nombre y stream.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_app_script",
            description="Obtiene el script de carga completo (load script) de una app Qlik.",
            inputSchema={
                "type": "object",
                "properties": {"app_id": {"type": "string", "description": "ID GUID de la aplicación"}},
                "required": ["app_id"],
            },
        ),
        types.Tool(
            name="set_app_script",
            description="Reemplaza el script de carga de una app y guarda. PRECAUCIÓN: acción irreversible.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string"},
                    "script": {"type": "string", "description": "Script de carga completo nuevo"},
                },
                "required": ["app_id", "script"],
            },
        ),
        types.Tool(
            name="get_app_sheets",
            description="Lista todas las hojas (sheets) de una aplicación con su ID, título y orden.",
            inputSchema={
                "type": "object",
                "properties": {"app_id": {"type": "string"}},
                "required": ["app_id"],
            },
        ),
        types.Tool(
            name="get_sheet_objects",
            description="Lista los objetos (gráficos, tablas, KPIs) dentro de una hoja específica.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string"},
                    "sheet_id": {"type": "string", "description": "ID de la hoja obtenido con get_app_sheets"},
                },
                "required": ["app_id", "sheet_id"],
            },
        ),
        types.Tool(
            name="get_object_properties",
            description="Obtiene las propiedades completas de un objeto: expresiones, dimensiones, medidas, colores, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {"type": "string"},
                    "object_id": {"type": "string", "description": "ID del objeto obtenido con get_sheet_objects"},
                },
                "required": ["app_id", "object_id"],
            },
        ),
        types.Tool(
            name="get_app_measures",
            description="Lista todas las medidas maestras de la app con su expresión Qlik y etiqueta.",
            inputSchema={
                "type": "object",
                "properties": {"app_id": {"type": "string"}},
                "required": ["app_id"],
            },
        ),
        types.Tool(
            name="get_app_dimensions",
            description="Lista todas las dimensiones maestras de la app con sus campos.",
            inputSchema={
                "type": "object",
                "properties": {"app_id": {"type": "string"}},
                "required": ["app_id"],
            },
        ),
        types.Tool(
            name="get_data_model",
            description="Obtiene el modelo de datos de la app: tablas, campos, claves y relaciones.",
            inputSchema={
                "type": "object",
                "properties": {"app_id": {"type": "string"}},
                "required": ["app_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "list_apps":
        return await apps.list_apps(qrs)
    elif name == "get_app_script":
        return await script.get_app_script(sessions, arguments["app_id"])
    elif name == "set_app_script":
        return await script.set_app_script(sessions, arguments["app_id"], arguments["script"])
    elif name == "get_app_sheets":
        return await sheets.get_app_sheets(sessions, arguments["app_id"])
    elif name == "get_sheet_objects":
        return await sheets.get_sheet_objects(sessions, arguments["app_id"], arguments["sheet_id"])
    elif name == "get_object_properties":
        return await sheets.get_object_properties(sessions, arguments["app_id"], arguments["object_id"])
    elif name == "get_app_measures":
        return await metadata.get_app_measures(sessions, arguments["app_id"])
    elif name == "get_app_dimensions":
        return await metadata.get_app_dimensions(sessions, arguments["app_id"])
    elif name == "get_data_model":
        return await data_model.get_data_model(sessions, arguments["app_id"])
    else:
        return [types.TextContent(type="text", text=f"Herramienta desconocida: {name}")]


async def main():
    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    finally:
        await sessions.close_all()


if __name__ == "__main__":
    asyncio.run(main())
