from app.game.connection_manager import ConnectionManager
from app.game.game import AbsGameHandler
from app.game.game_schema import *
from app.game.models import Player

class ConcreteGameHandler(AbsGameHandler):
    """
    Concrete implementation for Bridge pattern between game and game handler
    """
    def __init__(self, players: List[Player], spectators, sb_amount, bb_amount, connection_manager: ConnectionManager):
        super().__init__(players, spectators, sb_amount, bb_amount)
        self.connection_manager = connection_manager

    async def broadcast(self, game_phase: GamePhase, abs_game_phase_args: AbsGamePhaseArgs)->None:
        await self.connection_manager.broadcast({game_phase.value: abs_game_phase_args.dict()})

    async def send_personal(self, game_phase: GamePhase, player_id: int, abs_game_phase_args: AbsGamePhaseArgs)->None:
        await self.connection_manager.send_personal(player_id, {game_phase.value: abs_game_phase_args.dict()})

    async def turn(self, player: Player, turn_request_args: TurnRequestArgs)->TurnResponse:
        """
        Requests a turn action from the player and waits for their response
        """
        return await self.connection_manager.request_turn(player.id, turn_request_args)