import asyncio
from abc import ABC, abstractmethod
from typing import List

from app.game.game_phases import *
from app.game.game_states import PreFlopState, AbsGameState
from app.game.models import Player, Card
from app.game.table import Table

class AbsGameHandler(ABC):
    def __init__(self, players: List[Player], spectators, sb_amount, bb_amount):
        self.players = players
        self.spectators = spectators
        self.sb_amount = sb_amount
        self.bb_amount = bb_amount

    @abstractmethod
    async def broadcast(self, game_phase: GamePhase, abs_game_phase_args: AbsGamePhaseArgs)->None:
        pass
    @abstractmethod
    async def send_personal(self, game_phase: GamePhase, player_id: int, abs_game_phase_args: AbsGamePhaseArgs)->None:
        pass
    @abstractmethod
    async def turn(self, player: Player, turn_request_args: TurnRequestArgs)->TurnResponse:
        pass

class Game:
    def __init__(self, table: Table, game_handler: AbsGameHandler, sb_amount, bb_amount):
        self.table = table
        self.game_handler = game_handler
        self.curr_dealer_pos: int = -1
        self.prev_dealer_pos: int = 0
        self.pot: float = 0
        self.sb_amount = sb_amount
        self.bb_amount = bb_amount
        self.min_raise = sb_amount
        self.players: List[Player] = table.players
        self.folded: List[Player] = []
        self.sb_pos = -1
        self.bb_pos = -1
        self.is_game_started = False
        self.game_state = None

    def set_game_state(self, game_state: AbsGameState):
        self.game_state = game_state

    async def start_game(self):
        self.is_game_started = True
        self.prev_dealer_pos = self.curr_dealer_pos
        self.curr_dealer_pos = (self.curr_dealer_pos + 1) % len(self.players)
        self.pot = 0
        self.table.reset_deck()
        ordered_ids = [p.id for p in self.players]

        await self.game_handler.broadcast(GamePhase.PRE_START, PreStartArgs(
            prev_dealer=self.players[self.prev_dealer_pos],
            curr_dealer=self.players[self.curr_dealer_pos],
            ordered_player_ids=ordered_ids))

        self.set_game_state(PreFlopState(self))
        await self.game_state.start_flow()