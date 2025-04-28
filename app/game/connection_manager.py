import asyncio
from typing import Dict, Optional

from starlette.websockets import WebSocket

from app.game.game_phases import TurnResult, PlayerChoice

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.pending_turns: Dict[int, asyncio.Future[TurnResult]] = {}

    async def connect(self, websocket: WebSocket, id):
        await websocket.accept()
        self.active_connections[id] = websocket

    def disconnect(self, id):
        if id in self.pending_turns:
            if not self.pending_turns[id].done():
                self.pending_turns[id].set_result(TurnResult(player_choice=PlayerChoice.FOLD, amount=0))
            del self.pending_turns[id]
        self.active_connections.pop(id)

    async def send_personal(self, id, json_dict: dict):
        await self.active_connections[id].send_json(json_dict)

    async def broadcast(self, json_dict: dict):
        for connection in self.active_connections.values():
            await connection.send_json(json_dict)

    async def log(self, msg):
        await self.broadcast({"LOG": msg})

