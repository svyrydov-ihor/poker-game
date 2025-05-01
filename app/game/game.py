import asyncio
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
        await self.pre_flop()
        await self.pre_flop_betting()
        await self.flop()

    async def pre_flop(self):
        for player in self.players:
            player.pocket_cards = self.table.get_cards(2)
            await self.game_handler.send_personal(GamePhase.POCKET_CARDS, player.id, PocketCardsArgs(
                pocket_cards=player.get_poket_cards_dict()))

        #small blind
        self.sb_pos = (self.curr_dealer_pos + 1) % len(self.players)
        self.players[self.sb_pos].balance -= self.sb_amount
        self.players[self.sb_pos].bet = self.sb_amount
        self.pot += self.sb_amount
        await self.game_handler.broadcast(GamePhase.PRE_FLOP_SB, PreFlopSBArgs(
            sb_amount=self.sb_amount,
            player=self.players[self.sb_pos]))
        await self.game_handler.broadcast(GamePhase.POT, PotArgs(pot=self.pot))

        #big blind
        self.bb_pos = (self.sb_pos + 1) % len(self.players)
        self.players[self.bb_pos].balance -= self.bb_amount
        self.players[self.bb_pos].bet = self.bb_amount
        self.pot += self.bb_amount
        await self.game_handler.broadcast(GamePhase.PRE_FLOP_BB, PreFlopBBArgs(
            bb_amount=self.bb_amount,
            player=self.players[self.bb_pos]))
        await self.game_handler.broadcast(GamePhase.POT, PotArgs(pot=self.pot))

    async def pre_flop_betting(self):
        curr_player_pos = (self.bb_pos + 1) % len(self.players)
        prev_player_pos = self.bb_pos
        bb_next_pos = (self.bb_pos + 1) % len(self.players)

        turn_options = [PlayerChoice.CALL, PlayerChoice.FOLD, PlayerChoice.RAISE]
        while True:
            if curr_player_pos == self.bb_pos:
                turn_options = [PlayerChoice.CHECK, PlayerChoice.FOLD, PlayerChoice.RAISE]

            processed_turn = await self.process_turn(curr_player_pos, prev_player_pos, self.min_raise, turn_options)
            prev_player_pos = curr_player_pos

            if processed_turn.is_raised:
                await self.betting(curr_player_pos, processed_turn.curr_raise)
                break

            prev_player_pos = curr_player_pos
            curr_player_pos = (curr_player_pos + 1) % len(self.players)

            if curr_player_pos == bb_next_pos:
                break
        await self.game_handler.broadcast(GamePhase.TURN_HIGHLIGHT, TurnHighlightArgs(
            prev_player=self.players[prev_player_pos]
        ))

    async def betting(self, bet_player_pos, raise_amount):
        curr_player_pos = (bet_player_pos + 1) % len(self.players)
        prev_player_pos = bet_player_pos
        while True:
            turn_options = [PlayerChoice.CALL, PlayerChoice.FOLD, PlayerChoice.RAISE]

            processed_turn = await self.process_turn(curr_player_pos, prev_player_pos, raise_amount, turn_options)

            prev_player_pos = curr_player_pos

            if processed_turn.is_raised:
                await self.betting(curr_player_pos, processed_turn.curr_raise)
                break

            curr_player_pos = (curr_player_pos + 1) % len(self.players)

            if curr_player_pos == bet_player_pos:
                break
        await self.game_handler.broadcast(GamePhase.TURN_HIGHLIGHT, TurnHighlightArgs(
            prev_player=self.players[prev_player_pos]
        ))

    async def process_turn(self, curr_player_pos, prev_player_pos, prev_raise, options: List[PlayerChoice])->ProcessedTurn:
        await self.game_handler.broadcast(GamePhase.TURN_HIGHLIGHT, TurnHighlightArgs(
                prev_player=self.players[prev_player_pos],
                curr_player=self.players[curr_player_pos]))

        p_choice = await self.game_handler.turn(self.players[curr_player_pos],
                                                TurnRequestArgs(
                                                    player_bet=self.players[curr_player_pos].bet,
                                                    prev_bet=self.players[prev_player_pos].bet,
                                                    prev_raise=prev_raise,
                                                    options=options
                                                ))
        to_call = self.players[prev_player_pos].bet - self.players[curr_player_pos].bet

        is_raised = False
        curr_raise = prev_raise

        match p_choice.choice:
            case PlayerChoice.CALL:
                self.players[curr_player_pos].bet += p_choice.amount
                self.players[curr_player_pos].balance -= p_choice.amount
                self.pot += p_choice.amount
            case PlayerChoice.RAISE:
                self.players[curr_player_pos].bet += to_call + p_choice.amount
                self.players[curr_player_pos].balance -= to_call + p_choice.amount
                self.pot += to_call + p_choice.amount
                curr_raise = p_choice.amount
                is_raised = True
            case PlayerChoice.FOLD:
                self.folded.append(self.players[curr_player_pos])
            case PlayerChoice.CHECK:
                pass

        await self.game_handler.broadcast(GamePhase.TURN_RESULT, TurnResultArgs(
            player=self.players[curr_player_pos],
            choice=p_choice.choice,
            amount=self.players[curr_player_pos].bet,
        ))
        await self.game_handler.broadcast(GamePhase.POT, PotArgs(pot=self.pot))

        return ProcessedTurn(
            is_raised=is_raised,
            curr_bet=self.players[curr_player_pos].bet,
            curr_raise=curr_raise
        )

    async def flop(self):
        self.table.community_cards += self.table.get_cards(3)
        await self.game_handler.broadcast(GamePhase.COMMUNITY_CARDS, CommunityCardsArgs(
            cards=self.table.community_cards
        ))

        for player in self.players: player.bet = 0

        prev_player_pos = self.curr_dealer_pos
        curr_player_pos = (self.curr_dealer_pos + 1) % len(self.players)
        next_to_dealer = curr_player_pos

        while True:
            turn_options = [PlayerChoice.CHECK, PlayerChoice.FOLD, PlayerChoice.RAISE]

            processed_turn = await self.process_turn(curr_player_pos, prev_player_pos, self.min_raise, turn_options)

            prev_player_pos = curr_player_pos

            if processed_turn.is_raised:
                await self.betting(curr_player_pos, processed_turn.curr_raise)
                break

            curr_player_pos = (curr_player_pos + 1) % len(self.players)

            if curr_player_pos == next_to_dealer:
                break
        await self.game_handler.broadcast(GamePhase.TURN_HIGHLIGHT, TurnHighlightArgs(
            prev_player=self.players[prev_player_pos]
        ))

