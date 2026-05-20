import httpx
from . import config


class QRSClient:
    def __init__(self):
        self._ssl = config.build_ssl_context()
        self._base = f"https://{config.QLIK_HOST}:{config.QRS_PORT}/qrs"
        self._headers = {
            "X-Qlik-User": config.qlik_user_header(),
            "X-Qlik-Xrfkey": config.XRFKEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def get(self, path: str, params: dict = None) -> dict | list:
        p = {"xrfkey": config.XRFKEY}
        if params:
            p.update(params)
        async with httpx.AsyncClient(verify=self._ssl) as client:
            r = await client.get(f"{self._base}/{path}", headers=self._headers, params=p)
            r.raise_for_status()
            return r.json()

    async def list_apps(self) -> list[dict]:
        apps = await self.get("app/full")
        return [
            {
                "id": a["id"],
                "name": a["name"],
                "description": a.get("description", ""),
                "stream": a.get("stream", {}).get("name", "Mi trabajo") if a.get("stream") else "Mi trabajo",
                "last_modified": a.get("modifiedDate", ""),
            }
            for a in apps
        ]
