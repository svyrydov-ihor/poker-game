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
    async def turn(self, player: Player, turn_options: List[PlayerChoice], amount)->TurnResponse:
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
        self.players: List[Player] = table.players
        self.folded: List[Player] = []
        self.sb_pos = -1
        self.bb_pos = -1
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
        self.sb_pos = (self.curr_dealer_pos + 1) % len(self.players)
        self.players[self.sb_pos].balance -= self.sb_amount
        self.pot += self.sb_amount
        await self.game_handler.broadcast(GamePhase.PRE_FLOP_SB, PreFlopSBArgs(
            sb_amount=self.sb_amount,
            player=self.players[self.sb_pos]))
        await self.game_handler.broadcast(GamePhase.POT, PotArgs(pot=self.pot))

        #big blind
        self.bb_pos = (self.sb_pos + 1) % len(self.players)
        self.players[self.bb_pos].balance -= self.bb_amount
        self.pot += self.bb_amount
        await self.game_handler.broadcast(GamePhase.PRE_FLOP_BB, PreFlopBBArgs(
            bb_amount=self.bb_amount,
            player=self.players[self.bb_pos]))
        await self.game_handler.broadcast(GamePhase.POT, PotArgs(pot=self.pot))

    async def pre_flop_betting(self):
        curr_player_pos = (self.bb_pos + 1) % len(self.players)
        prev_player_pos = self.bb_pos
        bb_next_pos = (self.bb_pos + 1) % len(self.players)
        bet = self.bb_amount

        turn_options = [PlayerChoice.CALL, PlayerChoice.FOLD, PlayerChoice.RAISE]

        while True:
            if curr_player_pos == self.sb_pos:
                bet = self.sb_amount
            elif curr_player_pos == self.bb_pos:
                turn_options = [PlayerChoice.CHECK, PlayerChoice.FOLD, PlayerChoice.RAISE]

            await self.game_handler.broadcast(GamePhase.TURN_HIGHLIGHT, TurnHighlightArgs(
                prev_player=self.players[prev_player_pos],
                curr_player=self.players[curr_player_pos]
            ))
            p_choice = await self.game_handler.turn(self.players[curr_player_pos],
                                                    turn_options, bet)

            match p_choice.choice:
                case PlayerChoice.CALL:
                    self.players[curr_player_pos].balance -= bet
                    self.pot += bet
                case PlayerChoice.CHECK:
                    pass
                case PlayerChoice.FOLD:
                    self.folded.append(self.players[curr_player_pos])
            await self.game_handler.broadcast(GamePhase.TURN_RESULT, TurnResultArgs(
                player = self.players[curr_player_pos],
                choice = p_choice.choice,
                amount = p_choice.amount,
            ))
            await self.game_handler.broadcast(GamePhase.POT, PotArgs(pot=self.pot))

            prev_player_pos = curr_player_pos
            curr_player_pos = (curr_player_pos + 1) % len(self.players)

            if curr_player_pos == bb_next_pos:
                break
        await self.game_handler.broadcast(GamePhase.TURN_HIGHLIGHT, TurnHighlightArgs(
            prev_player=self.players[prev_player_pos]
        ))