from abc import ABC, abstractmethod

from typing_extensions import override

from app.game.game_phases import *
from typing import TYPE_CHECKING, List, Set

if TYPE_CHECKING:
    from app.game.game import Game

class AbsGameState(ABC):
    """
    State pattern for game flow
    """
    def __init__(self, game: 'Game'):
        self.game = game

    @abstractmethod
    async def start_flow(self):
        pass

    async def run_betting_round(self):
        """
        Template method for betting round
        """
        await self._before_betting_round_action() # hook
        turn_options = self._get_init_turn_options() # hook
        aggressor_pos = self._get_init_aggressor_pos() # hook
        curr_player_pos = self._get_starting_pos() #hook
        prev_player_pos = (curr_player_pos - 1 + len(self.game.players)) % len(self.game.players)
        min_raise = self._get_min_raise() # hook
        is_raised = False

        while True:
            if not is_raised: turn_options = self._change_turn_options(curr_player_pos, turn_options)
            processed_turn = await self._process_turn(
                curr_player_pos=curr_player_pos,
                prev_player_pos=prev_player_pos,
                prev_raise=min_raise,
                options=turn_options)

            if processed_turn.is_raised:
                aggressor_pos = curr_player_pos
                min_raise = processed_turn.curr_raise
                turn_options = [PlayerChoice.CALL, PlayerChoice.FOLD, PlayerChoice.RAISE]
                is_raised = True

            prev_player_pos = curr_player_pos
            curr_player_pos = (curr_player_pos + 1) % len(self.game.players)

            if curr_player_pos == aggressor_pos:
                break
        await self.game.game_handler.broadcast(GamePhase.TURN_HIGHLIGHT, TurnHighlightArgs(
            prev_player=self.game.players[prev_player_pos]))

    @abstractmethod
    async def _before_betting_round_action(self):
        pass

    @abstractmethod
    def _get_init_turn_options(self):
        pass

    @abstractmethod
    def _get_init_aggressor_pos(self):
        pass

    @abstractmethod
    def _get_starting_pos(self):
        pass

    def _get_min_raise(self):
        return self.game.min_raise

    def _change_turn_options(self, curr_player_pos, turn_options: List[PlayerChoice])->List[PlayerChoice]:
        """
        overridden in PreFlopState
        """
        return turn_options

    async def _deal_community_cards(self, number: int):
        self.game.table.community_cards += self.game.table.get_cards(number)
        await self.game.game_handler.broadcast(GamePhase.COMMUNITY_CARDS, CommunityCardsArgs(
            cards=self.game.table.community_cards
        ))

    async def _process_turn(self, curr_player_pos, prev_player_pos, prev_raise, options: List[PlayerChoice])->ProcessedTurn:
        await self.game.game_handler.broadcast(GamePhase.TURN_HIGHLIGHT, TurnHighlightArgs(
                prev_player=self.game.players[prev_player_pos],
                curr_player=self.game.players[curr_player_pos]))

        p_choice = await self.game.game_handler.turn(self.game.players[curr_player_pos],
                                                TurnRequestArgs(
                                                    player_bet=self.game.players[curr_player_pos].bet,
                                                    prev_bet=self.game.players[prev_player_pos].bet,
                                                    prev_raise=prev_raise,
                                                    options=options
                                                ))
        to_call = self.game.players[prev_player_pos].bet - self.game.players[curr_player_pos].bet

        is_raised = False
        curr_raise = prev_raise

        match p_choice.choice:
            case PlayerChoice.CALL:
                self.game.players[curr_player_pos].bet += p_choice.amount
                self.game.players[curr_player_pos].balance -= p_choice.amount
                self.game.pot += p_choice.amount
            case PlayerChoice.RAISE:
                self.game.players[curr_player_pos].bet += to_call + p_choice.amount
                self.game.players[curr_player_pos].balance -= to_call + p_choice.amount
                self.game.pot += to_call + p_choice.amount
                curr_raise = p_choice.amount
                is_raised = True
            case PlayerChoice.FOLD:
                self.game.folded.append(self.game.players[curr_player_pos])
            case PlayerChoice.CHECK:
                pass

        await self.game.game_handler.broadcast(GamePhase.TURN_RESULT, TurnResultArgs(
            player=self.game.players[curr_player_pos],
            choice=p_choice.choice,
            amount=self.game.players[curr_player_pos].bet,
        ))
        await self.game.game_handler.broadcast(GamePhase.POT, PotArgs(pot=self.game.pot))

        return ProcessedTurn(
            is_raised=is_raised,
            curr_bet=self.game.players[curr_player_pos].bet,
            curr_raise=curr_raise
        )

class PreFlopState(AbsGameState):
    def _get_init_turn_options(self):
        return [PlayerChoice.CALL, PlayerChoice.FOLD, PlayerChoice.RAISE]

    def _get_init_aggressor_pos(self):
        return (self.game.bb_pos + 1) % len(self.game.players)

    @override
    def _get_starting_pos(self):
        return (self.game.bb_pos + 1) % len(self.game.players)

    def _get_min_raise(self):
        return self.game.min_raise

    def _change_turn_options(self, curr_player_pos, turn_options: List[PlayerChoice])->List[PlayerChoice]:
        if curr_player_pos == self.game.bb_pos: return [PlayerChoice.CHECK, PlayerChoice.FOLD, PlayerChoice.RAISE]
        else: return turn_options

    async def start_flow(self):
        await self.deal_player_cards()
        await self.run_betting_round()
        next_state = FlopState(self.game)
        self.game.set_game_state(next_state)
        await next_state.start_flow()

    async def deal_player_cards(self):
        for player in self.game.players:
            player.pocket_cards = self.game.table.get_cards(2)
            await self.game.game_handler.send_personal(GamePhase.POCKET_CARDS, player.id, PocketCardsArgs(
                pocket_cards=player.get_poket_cards_dict()))

    async def _before_betting_round_action(self):
        # small blind
        self.game.sb_pos = (self.game.curr_dealer_pos + 1) % len(self.game.players)
        self.game.players[self.game.sb_pos].balance -= self.game.sb_amount
        self.game.players[self.game.sb_pos].bet = self.game.sb_amount
        self.game.pot += self.game.sb_amount
        await self.game.game_handler.broadcast(GamePhase.PRE_FLOP_SB, PreFlopSBArgs(
            sb_amount=self.game.sb_amount,
            player=self.game.players[self.game.sb_pos]))
        await self.game.game_handler.broadcast(GamePhase.POT, PotArgs(pot=self.game.pot))

        # big blind
        self.game.bb_pos = (self.game.sb_pos + 1) % len(self.game.players)
        self.game.players[self.game.bb_pos].balance -= self.game.bb_amount
        self.game.players[self.game.bb_pos].bet = self.game.bb_amount
        self.game.pot += self.game.bb_amount
        await self.game.game_handler.broadcast(GamePhase.PRE_FLOP_BB, PreFlopBBArgs(
            bb_amount=self.game.bb_amount,
            player=self.game.players[self.game.bb_pos]))
        await self.game.game_handler.broadcast(GamePhase.POT, PotArgs(pot=self.game.pot))

    @override
    def _change_turn_options(self, curr_player_pos, turn_options: List[PlayerChoice])->List[PlayerChoice]:
        if curr_player_pos == self.game.bb_pos: return [PlayerChoice.CHECK, PlayerChoice.FOLD, PlayerChoice.RAISE]
        else: return turn_options

class FlopState(AbsGameState):
    def _get_init_turn_options(self):
        return [PlayerChoice.CHECK, PlayerChoice.FOLD, PlayerChoice.RAISE]

    def _get_init_aggressor_pos(self):
        return self.game.sb_pos

    def _get_starting_pos(self):
        return self.game.sb_pos

    async def _before_betting_round_action(self):
        for p in self.game.players: p.bet = 0

    async def start_flow(self):
        await self._deal_community_cards(3)
        await self.run_betting_round()