import asyncio
import itertools
import json
from typing import Any
import websockets
from . import config


class EngineSession:
    """Una sesión WebSocket con el Engine API de Qlik (JSON-RPC 2.0)."""

    def __init__(self, app_id: str):
        self.app_id = app_id
        self.app_handle: int | None = None
        self._ws = None
        self._pending: dict[int, asyncio.Future] = {}
        self._counter = itertools.count(1)
        self._listener: asyncio.Task | None = None

    async def connect(self):
        ssl_ctx = config.build_ssl_context()
        uri = f"wss://{config.QLIK_HOST}:{config.ENGINE_PORT}/app/{self.app_id}"
        headers = {"X-Qlik-User": config.qlik_user_header()}
        self._ws = await websockets.connect(uri, ssl=ssl_ctx, additional_headers=headers)
        self._listener = asyncio.create_task(self._listen())
        result = await self.call(-1, "OpenDoc", [self.app_id])
        self.app_handle = result["qReturn"]["qHandle"]
        return self

    async def _listen(self):
        try:
            async for raw in self._ws:
                msg = json.loads(raw)
                req_id = msg.get("id")
                if req_id and req_id in self._pending:
                    fut = self._pending.pop(req_id)
                    if not fut.done():
                        fut.set_result(msg)
        except Exception:
            for fut in self._pending.values():
                if not fut.done():
                    fut.cancel()

    async def call(self, handle: int, method: str, params: list = None) -> Any:
        req_id = next(self._counter)
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "handle": handle,
            "params": params or [],
        }
        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[req_id] = fut
        await self._ws.send(json.dumps(payload))
        msg = await asyncio.wait_for(fut, timeout=30)
        if "error" in msg:
            raise RuntimeError(f"Engine API error: {msg['error']}")
        return msg.get("result", {})

    async def create_session_object(self, definition: dict) -> int:
        result = await self.call(self.app_handle, "CreateSessionObject", [definition])
        return result["qReturn"]["qHandle"]

    async def get_layout(self, handle: int) -> dict:
        result = await self.call(handle, "GetLayout")
        return result.get("qLayout", result)

    async def close(self):
        if self._listener:
            self._listener.cancel()
        if self._ws:
            await self._ws.close()


class SessionManager:
    """Caché de sesiones Engine abiertas por app_id."""

    def __init__(self):
        self._sessions: dict[str, EngineSession] = {}

    async def get(self, app_id: str) -> EngineSession:
        if app_id not in self._sessions:
            session = EngineSession(app_id)
            await session.connect()
            self._sessions[app_id] = session
        return self._sessions[app_id]

    async def close_all(self):
        for s in self._sessions.values():
            await s.close()
        self._sessions.clear()
