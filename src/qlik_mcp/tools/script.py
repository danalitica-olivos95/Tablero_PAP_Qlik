from mcp import types
from ..engine_client import SessionManager


async def get_app_script(sessions: SessionManager, app_id: str) -> list[types.TextContent]:
    s = await sessions.get(app_id)
    result = await s.call(s.app_handle, "GetScript")
    script = result.get("qScript", "")
    return [types.TextContent(type="text", text=script)]


async def set_app_script(sessions: SessionManager, app_id: str, script: str) -> list[types.TextContent]:
    if not script.strip():
        return [types.TextContent(type="text", text="ERROR: El script no puede estar vacío.")]
    s = await sessions.get(app_id)
    await s.call(s.app_handle, "SetScript", [script])
    await s.call(s.app_handle, "DoSave")
    return [types.TextContent(type="text", text="Script guardado correctamente.")]
