"""
WebSocket connection manager.
Хранит активные соединения по user_id.
"""
import asyncio
from collections import defaultdict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active: dict[int, list[WebSocket]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        async with self._lock:
            self.active[user_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: int):
        async with self._lock:
            if websocket in self.active.get(user_id, []):
                self.active[user_id].remove(websocket)
            if not self.active.get(user_id):
                self.active.pop(user_id, None)

    async def send_personal(self, user_id: int, data: dict):
        """Отправить сообщение всем соединениям пользователя."""
        connections = list(self.active.get(user_id, []))
        dead = []
        for ws in connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws, user_id)

    async def broadcast(self, data: dict):
        for user_id in list(self.active.keys()):
            await self.send_personal(user_id, data)


manager = ConnectionManager()
