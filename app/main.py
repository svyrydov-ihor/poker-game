import asyncio
import logging
from http import HTTPStatus
from typing import Optional

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

from app.game.concrete_game_handler import ConcreteGameHandler
from app.game.connection_manager import ConnectionManager
from app.game.game import Game
from app.game.game_phases import GamePhase, NewPlayerArgs, TurnResponse, PlayerChoice
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

game_instance: Optional[Game] = None

async def start_game():
    global game_instance
    try:
        if len(table.players) < 4:
             await connection_manager.log("Not enough players to start.")
             return

        small_blind = 5
        big_blind = 10
        game_handler = ConcreteGameHandler(table.players, [], small_blind, big_blind, connection_manager)
        game_instance = Game(table, game_handler, small_blind, big_blind)
        await connection_manager.log("Game started ❗")
        asyncio.create_task(game_instance.start_game())
    except Exception as e:
        logger.exception("Error starting game:" + e)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await connection_manager.connect(websocket, client_id)

    client_name = str(client_id)[9:]
    player = Player(client_id, client_name, 1000)

    #load existing players for new connection
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
            # Receive messages from the client
            data = await websocket.receive_json()
            logger.debug(f"Received data from client {client_id}: {data}")

            # Handle incoming turn responses
            if "TURN_RESPONSE" in data:
                try:
                    # Validate the incoming data using the Pydantic model
                    turn_response_data = TurnResponse(**data["TURN_RESPONSE"])
                    # Convert the validated model to a TurnResult object
                    turn_result = TurnResponse(
                        choice=turn_response_data.choice,
                        amount=turn_response_data.amount
                    )
                    # Process the turn response using the connection manager
                    connection_manager.process_turn_response(client_id, turn_result)
                except Exception as e:
                    logger.error(f"Invalid turn response format from client {client_id}: {e}")
                    # Optionally, send an error back to the client or assume a FOLD
                    connection_manager.process_turn_response(client_id,
                                                             TurnResponse(choice=PlayerChoice.FOLD, amount=0))
            # Add other message handling logic here as needed
            else:
                logger.warning(f"Received unknown message format from client {client_id}: {data}")


    except WebSocketDisconnect:
        logger.info(f"Player {client_id} disconnected.")
        connection_manager.disconnect(client_id)
        table.remove_player(client_id)
        await connection_manager.log(f"Player {client_name} left")
    except Exception as e:
        logger.exception(f"Error in websocket connection with client {client_id}:" + e)


'''
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_level="debug")
'''