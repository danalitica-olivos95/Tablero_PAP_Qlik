import json
from mcp import types
from ..engine_client import SessionManager

_MEASURE_LIST_DEF = {
    "qInfo": {"qType": "MeasureList"},
    "qMeasureListDef": {
        "qType": "measure",
        "qData": {
            "title": "/qMetaDef/title",
            "expression": "/qMeasure/qDef",
            "label": "/qMeasure/qLabel",
            "description": "/qMetaDef/description",
        },
    },
}

_DIMENSION_LIST_DEF = {
    "qInfo": {"qType": "DimensionList"},
    "qDimensionListDef": {
        "qType": "dimension",
        "qData": {
            "title": "/qMetaDef/title",
            "fields": "/qDim/qFieldDefs",
            "label": "/qDim/qFieldLabels",
            "description": "/qMetaDef/description",
        },
    },
}


async def get_app_measures(sessions: SessionManager, app_id: str) -> list[types.TextContent]:
    s = await sessions.get(app_id)
    handle = await s.create_session_object(_MEASURE_LIST_DEF)
    layout = await s.get_layout(handle)
    items = layout.get("qMeasureList", {}).get("qItems", [])
    measures = [
        {
            "id": i["qInfo"]["qId"],
            "title": i.get("qData", {}).get("title", ""),
            "expression": i.get("qData", {}).get("expression", ""),
            "label": i.get("qData", {}).get("label", ""),
            "description": i.get("qData", {}).get("description", ""),
        }
        for i in items
    ]
    return [types.TextContent(type="text", text=json.dumps(measures, indent=2, ensure_ascii=False))]


async def get_app_dimensions(sessions: SessionManager, app_id: str) -> list[types.TextContent]:
    s = await sessions.get(app_id)
    handle = await s.create_session_object(_DIMENSION_LIST_DEF)
    layout = await s.get_layout(handle)
    items = layout.get("qDimensionList", {}).get("qItems", [])
    dimensions = [
        {
            "id": i["qInfo"]["qId"],
            "title": i.get("qData", {}).get("title", ""),
            "fields": i.get("qData", {}).get("fields", []),
            "labels": i.get("qData", {}).get("label", []),
            "description": i.get("qData", {}).get("description", ""),
        }
        for i in items
    ]
    return [types.TextContent(type="text", text=json.dumps(dimensions, indent=2, ensure_ascii=False))]
