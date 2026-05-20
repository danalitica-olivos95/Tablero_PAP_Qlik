import json
from mcp import types
from ..qrs_client import QRSClient


async def list_apps(qrs: QRSClient) -> list[types.TextContent]:
    apps = await qrs.list_apps()
    return [types.TextContent(type="text", text=json.dumps(apps, indent=2, ensure_ascii=False))]
