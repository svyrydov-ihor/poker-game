from abc import ABC, abstractmethod
from typing import List

from app.game.game_phases import *
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
    async def turn(self, player: Player, turn_options: List[PlayerChoice], amount)->TurnResult:
        pass

class Game:
    def __init__(self, table: Table, game_handler: AbsGameHandler, sb_amount, bb_amount):
        self.table = table
        self.game_handler = game_handler
        self.curr_dealer_pos: int = -1
        self.prev_dealer_pos: int = 0
        self.curr_player_pos: int = 0
        self.pot: float = 0
        self.sb_amount = sb_amount
        self.bb_amount = bb_amount
        self.players: List[Player] = table.players
        self.folded: List[Player] = []
        self.is_game_started = False

    async def start_game(self):
        self.is_game_started = True
        self.prev_dealer_pos = self.curr_dealer_pos
        self.curr_dealer_pos = (self.curr_dealer_pos + 1) % len(self.players)
        self.pot = 0
        self.table.reset_deck()

        await self.game_handler.broadcast(GamePhase.PRE_START, PreStartArgs(
            prev_dealer=self.players[self.prev_dealer_pos],
            curr_dealer=self.players[self.curr_dealer_pos]))
        await self.pre_flop()
        await self.pre_flop_betting()

    async def pre_flop(self):
        for player in self.players:
            player.pocket_cards = self.table.get_cards(2)
            await self.game_handler.send_personal(GamePhase.POCKET_CARDS, player.id, PocketCardsArgs(
                pocket_cards=player.get_poket_cards_dict()))

        #small blind
        self.curr_player_pos = (self.curr_dealer_pos + 1) % len(self.players)
        self.players[self.curr_player_pos].balance -= self.sb_amount
        self.pot += self.sb_amount
        await self.game_handler.broadcast(GamePhase.PRE_FLOP_SB, PreFlopSBArgs(
            sb_amount=self.sb_amount,
            player=self.players[self.curr_player_pos]))

        #big blind
        self.curr_player_pos = (self.curr_player_pos + 1) % len(self.players)
        self.players[self.curr_player_pos].balance -= self.bb_amount
        self.pot += self.bb_amount
        await self.game_handler.broadcast(GamePhase.PRE_FLOP_BB, PreFlopBBArgs(
            bb_amount=self.bb_amount,
            player=self.players[self.curr_player_pos]))

    async def pre_flop_betting(self):
        self.curr_player_pos = (self.curr_player_pos + 1) % len(self.players)
        next_dealer_pos = (self.curr_dealer_pos + 1) % len(self.players)
        bet = self.bb_amount

        turn_options = [PlayerChoice.CALL, PlayerChoice.FOLD, PlayerChoice.RAISE]
        while self.curr_player_pos != next_dealer_pos:
            p_choice = await self.game_handler.turn(self.players[self.curr_player_pos],
                                                    turn_options, bet)