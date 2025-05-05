import asyncio
from typing import Dict
from starlette.websockets import WebSocket
from app.game.game_schema import TurnResponse, PlayerAction, GamePhase, TurnRequestArgs

class ConnectionManager:
    """
    Manages WebSocket connections and turn requests for players in a game
    Similar to Observer pattern, but with concrete subscribers (WebSockets)
    """
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.pending_turns: Dict[int, asyncio.Future[TurnResponse]] = {}

    async def connect(self, websocket: WebSocket, id):
        await websocket.accept()
        self.active_connections[id] = websocket

    def disconnect(self, id):
        if id in self.pending_turns:
            if not self.pending_turns[id].done():
                self.pending_turns[id].set_result(TurnResponse(action=PlayerAction.FOLD, amount=0))
            del self.pending_turns[id]
        self.active_connections.pop(id)

    async def send_personal(self, id, json_dict: dict):
        await self.active_connections[id].send_json(json_dict)

    async def broadcast(self, json_dict: dict):
        for connection in self.active_connections.values():
            await connection.send_json(json_dict)

    async def log(self, msg):
        await self.broadcast({"LOG": msg})

    async def request_turn(self, player_id: int, turn_request_args: TurnRequestArgs) -> TurnResponse:
        """
        Sends a turn request to a player and waits for their response
        """
        if player_id not in self.active_connections:
            return TurnResponse(action=PlayerAction.FOLD, amount=0)

        await self.send_personal(player_id, {
            GamePhase.TURN_REQUEST.value: turn_request_args.dict()})

        # Wait for the player's response
        try:
            # Create a new future for this turn if one doesn't exist or is already done
            if player_id not in self.pending_turns or self.pending_turns[player_id].done():
                self.pending_turns[player_id] = asyncio.Future()

            result = await self.pending_turns[player_id]
            return result
        except asyncio.CancelledError:
            return TurnResponse(action=PlayerAction.FOLD, amount=0)

    def process_turn_response(self, player_id: int, turn_response: TurnResponse):
        """
        Processes the turn response received from a player
        """
        if player_id in self.pending_turns and not self.pending_turns[player_id].done():
            turn_result = TurnResponse(action=turn_response.action, amount=turn_response.amount)
            self.pending_turns[player_id].set_result(turn_result)