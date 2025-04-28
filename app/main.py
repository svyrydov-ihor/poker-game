import asyncio
import logging
from http import HTTPStatus
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

from app.game.concrete_game_handler import ConcreteGameHandler
from app.game.connection_manager import ConnectionManager
from app.game.game import Game
from app.game.game_phases import GamePhase, NewPlayerArgs
from app.game.models import Player
from app.game.table import Table


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Debugging: This is a test log message.")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

connection_manager = ConnectionManager()

@app.get("/")
async def root():
    return FileResponse("static/index.html")

class IsPlayerReady(BaseModel):
    is_player_ready: bool

table = Table()

@app.post("/player-ready/{client_id}")
async def player_ready(client_id: int, is_player_ready: IsPlayerReady):
    try:
        for p in table.players:
            if p.id == client_id:
                p.is_ready = is_player_ready.is_player_ready
        log_text = ""
        if is_player_ready.is_player_ready:
            log_text = f"Player {client_id} is ready ✅"
        else:
            log_text = f"Player {client_id} is not ready ❌"
        await connection_manager.log(log_text)

        if all(p.is_ready == True for p in table.players):
             asyncio.create_task(start_game())

    except Exception as e:
        logger.debug(e)

    return HTTPStatus.OK

async def start_game():
    try:
        small_blind = 5
        big_blind = 10
        game_handler = ConcreteGameHandler(table.players, [], small_blind, big_blind, connection_manager)
        game = Game(table, game_handler, small_blind, big_blind)
        await connection_manager.log("Game started ❗")
        await game.start_game()
    except Exception as e:
        logger.debug(e)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await connection_manager.connect(websocket, client_id)

    client_name = str(client_id)[9:]
    player = Player(client_id, client_name, 1000)

    #load existing players for new connection
    '''
    for player_id in connection_manager.active_connections.keys():
        if player_id != client_id:
            existing_player = next((p for p in table.players if p.id == player_id), None)
            await connection_manager.send_personal(client_id,
                {GamePhase.NEW_PLAYER.value: NewPlayerArgs(
                    player=existing_player).dict()})
                    '''

    for existing_player in table.players:
        logger.debug(f"Sending player {existing_player.id} to {client_id}")
        await connection_manager.send_personal(client_id,
               {GamePhase.NEW_PLAYER.value: NewPlayerArgs(
                   player=existing_player).dict()})

    #add new player to everyone
    await connection_manager.broadcast({GamePhase.NEW_PLAYER.value: NewPlayerArgs(player=player).dict()})
    await connection_manager.log(f"Player {client_name} joined")

    table.add_player(player)

    try:
        while True:
            text_data = await websocket.receive_text()

    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
        table.remove_player(client_id)
        await connection_manager.log(f"Player #{client_name} left")

'''
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_level="debug")
'''