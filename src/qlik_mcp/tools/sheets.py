import json
from mcp import types
from ..engine_client import SessionManager

_SHEET_LIST_DEF = {
    "qInfo": {"qType": "SheetList"},
    "qAppObjectListDef": {
        "qType": "sheet",
        "qData": {"title": "/qMetaDef/title", "rank": "/rank"},
    },
}


async def get_app_sheets(sessions: SessionManager, app_id: str) -> list[types.TextContent]:
    s = await sessions.get(app_id)
    handle = await s.create_session_object(_SHEET_LIST_DEF)
    layout = await s.get_layout(handle)
    items = layout.get("qAppObjectList", {}).get("qItems", [])
    sheets = [
        {"id": i["qInfo"]["qId"], "title": i.get("qData", {}).get("title", ""), "rank": i.get("qData", {}).get("rank", 0)}
        for i in items
    ]
    sheets.sort(key=lambda x: x["rank"])
    return [types.TextContent(type="text", text=json.dumps(sheets, indent=2, ensure_ascii=False))]


async def get_sheet_objects(sessions: SessionManager, app_id: str, sheet_id: str) -> list[types.TextContent]:
    s = await sessions.get(app_id)
    result = await s.call(s.app_handle, "GetObject", [sheet_id])
    sheet_handle = result["qReturn"]["qHandle"]
    layout = await s.get_layout(sheet_handle)
    children = layout.get("qChildList", {}).get("qItems", [])
    objects = [
        {
            "id": c["qInfo"]["qId"],
            "type": c["qInfo"]["qType"],
            "title": c.get("qMeta", {}).get("title", ""),
        }
        for c in children
    ]
    return [types.TextContent(type="text", text=json.dumps(objects, indent=2, ensure_ascii=False))]


async def get_object_properties(sessions: SessionManager, app_id: str, object_id: str) -> list[types.TextContent]:
    s = await sessions.get(app_id)
    result = await s.call(s.app_handle, "GetObject", [object_id])
    obj_handle = result["qReturn"]["qHandle"]
    props_result = await s.call(obj_handle, "GetEffectiveProperties")
    props = props_result.get("qProp", props_result)
    return [types.TextContent(type="text", text=json.dumps(props, indent=2, ensure_ascii=False))]
