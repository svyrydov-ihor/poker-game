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
from app.game.game import Game, ConcreteGameBuilder
from app.game.game_schema import GamePhase, NewPlayerArgs, TurnResponse, PlayerAction, IsReadyArgs
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
    global table
    if game_instance is not None and game_instance.is_game_started:
        return HTTPStatus.CONFLICT

    is_ready = is_player_ready.is_player_ready

    for p in table.players:
        print(p.name)
        print(p.is_ready)
        print("\n-----\n")
        if p.id == client_id:
            p.is_ready = is_ready

    if is_ready:
        log_text = f"Player {client_id} is ready ✅"
    else:
        log_text = f"Player {client_id} is not ready ❌"
    await connection_manager.log(log_text)
    await connection_manager.broadcast({GamePhase.IS_READY.value: IsReadyArgs(
        player_id=client_id,
        is_ready=is_ready
    ).dict()})

    if all(p.is_ready == True for p in table.players):
         asyncio.create_task(start_game())

    return HTTPStatus.OK

game_instance: Optional[Game] = None

async def start_game():
    global game_instance
    try:
        if len(table.players) < 4:
             await connection_manager.log("Not enough players to start.")
             return

        if game_instance is None:
            game_instance = build_game()

        await connection_manager.log("Game started ❗")
        asyncio.create_task(game_instance.start_game())
    except Exception as e:
        logger.exception("Error starting game:" + e)

def build_game() -> Game:
    game_handler = ConcreteGameHandler(table.players, [], 5, 10, connection_manager)
    game_builder = ConcreteGameBuilder()
    game_builder.set_game_handler(game_handler)
    game_builder.set_table(table)
    game_builder.set_small_blind_amount(5)
    game_builder.set_big_blind_amount(10)
    game_builder.set_min_raise_amount(5)
    return game_builder.get_built_game()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await connection_manager.connect(websocket, client_id)

    client_name = str(client_id)[9:]
    player = Player(client_id, client_name, 1000)

    #load existing players for new connection
    for existing_player in table.players:
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
                        action=turn_response_data.action,
                        amount=turn_response_data.amount
                    )
                    # Process the turn response using the connection manager
                    connection_manager.process_turn_response(client_id, turn_result)
                except Exception as e:
                    logger.error(f"Invalid turn response format from client {client_id}: {e}")
                    # Optionally, send an error back to the client or assume a FOLD
                    connection_manager.process_turn_response(client_id,
                                                             TurnResponse(action=PlayerAction.FOLD, amount=0))
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