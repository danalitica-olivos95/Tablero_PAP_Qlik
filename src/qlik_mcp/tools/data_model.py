import json
from mcp import types
from ..engine_client import SessionManager

_TABLE_LIST_DEF = {"qInfo": {"qType": "TableList"}, "qTableListDef": {}}

_FIELD_LIST_DEF = {
    "qInfo": {"qType": "FieldList"},
    "qFieldListDef": {"qShowSystem": False, "qShowSemantic": True, "qShowDerivedFields": True},
}


async def get_data_model(sessions: SessionManager, app_id: str) -> list[types.TextContent]:
    s = await sessions.get(app_id)

    tbl_handle = await s.create_session_object(_TABLE_LIST_DEF)
    tbl_layout = await s.get_layout(tbl_handle)
    tables_raw = tbl_layout.get("qTableList", {}).get("qItems", [])

    fld_handle = await s.create_session_object(_FIELD_LIST_DEF)
    fld_layout = await s.get_layout(fld_handle)
    fields_raw = fld_layout.get("qFieldList", {}).get("qItems", [])

    tables = [
        {
            "name": t.get("qName", ""),
            "no_of_rows": t.get("qNoOfRows", 0),
            "fields": [f.get("qName") for f in t.get("qFields", [])],
            "is_synthetic": t.get("qIsSynthetic", False),
        }
        for t in tables_raw
    ]

    fields = [
        {
            "name": f.get("qName", ""),
            "tables": [t.get("qName") for t in f.get("qTables", [])],
            "is_key": f.get("qIsKey", False),
            "total_count": f.get("qCardinal", 0),
        }
        for f in fields_raw
    ]

    result = {"tables": tables, "fields": fields}
    return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
