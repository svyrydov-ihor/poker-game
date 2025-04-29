from typing import List

from app.game.connection_manager import ConnectionManager
from app.game.game import AbsGameHandler
from app.game.game_phases import *
from app.game.models import Player, Card

class ConcreteGameHandler(AbsGameHandler):
    def __init__(self, players: List[Player], spectators, sb_amount, bb_amount, connection_manager: ConnectionManager):
        super().__init__(players, spectators, sb_amount, bb_amount)
        self.connection_manager = connection_manager

    async def broadcast(self, game_phase: GamePhase, abs_game_phase_args: AbsGamePhaseArgs)->None:
        await self.connection_manager.broadcast({game_phase.value: abs_game_phase_args.dict()})

    async def send_personal(self, game_phase: GamePhase, player_id: int, abs_game_phase_args: AbsGamePhaseArgs)->None:
        await self.connection_manager.send_personal(player_id, {game_phase.value: abs_game_phase_args.dict()})

    async def turn(self, player: Player, turn_options: List[PlayerChoice], amount: float)->TurnResponse:
        """Requests a turn action from the player and waits for their response."""
        return await self.connection_manager.request_turn(player.id, turn_options, amount)