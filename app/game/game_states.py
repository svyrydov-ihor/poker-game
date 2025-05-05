from abc import ABC, abstractmethod

from starlette.responses import RangeNotSatisfiable
from typing_extensions import override

from app.game.game_schema import *
from typing import TYPE_CHECKING, List, Set, Dict

from app.game.hand_evaluator import RoyalFlushEvaluator
from app.game.player_action_commands import *

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

        # setup defined by hooks
        await self._before_betting_round_action()
        turn_options = self._get_init_turn_options()
        #last_raiser_pos = self._get_init_aggressor_pos()
        curr_player_pos = self._get_starting_pos()
        prev_player_pos = (curr_player_pos - 1 + len(self.game.players)) % len(self.game.players)
        curr_bet = self._get_init_bet()
        last_raise_by = self._get_min_raise()

        active_players = [p for p in self.game.players if p not in self.game.folded]
        if len(active_players) <= 1: return

        needs_to_act: Set[int] = {p.id for p in active_players}
        action_opened = False

        while len(needs_to_act) > 0:
            player_to_act = self.game.players[curr_player_pos]

            if player_to_act.id in self.game.folded or player_to_act.id not in needs_to_act:
                curr_player_pos = (curr_player_pos + 1) % len(self.game.players)
                continue # move to the next player

            curr_turn_options = list(turn_options)
            if not action_opened: # hook for pre-flop BB position
                curr_turn_options = self._change_turn_options(curr_player_pos, turn_options)

            player_who_acted_pos = curr_player_pos

            processed_turn = await self._process_turn(
                curr_player_pos=curr_player_pos,
                prev_player_pos=prev_player_pos,
                curr_bet=curr_bet,
                prev_raise=last_raise_by,
                options=curr_turn_options)

            player_who_acted = player_to_act
            needs_to_act.remove(player_who_acted.id)

            if player_who_acted in self.game.folded:
                active_players = [p for p in self.game.players if p not in self.game.folded]
                if len(active_players) <= 1:
                    needs_to_act.clear()

            elif processed_turn.action == PlayerAction.RAISE:
                action_opened = True
                curr_bet = processed_turn.curr_bet
                last_raise_by = processed_turn.curr_raise
                #last_raiser_pos = player_who_acted_pos
                needs_to_act = {p.id for p in active_players if p.id != player_who_acted.id}
                turn_options = [PlayerAction.CALL, PlayerAction.RAISE, PlayerAction.FOLD]

            else:
                pass

            prev_player_pos = player_who_acted_pos
            curr_player_pos = (curr_player_pos + 1) % len(self.game.players)

        await self.game.game_handler.broadcast(GamePhase.TURN_HIGHLIGHT, TurnHighlightArgs(
            prev_player=self.game.players[prev_player_pos]))

    @abstractmethod
    async def _before_betting_round_action(self):
        """hook"""
        pass

    @abstractmethod
    def _get_init_turn_options(self):
        """hook"""
        pass

    @abstractmethod
    def _get_init_aggressor_pos(self):
        """hook"""
        pass

    @abstractmethod
    def _get_starting_pos(self):
        """hook"""
        pass

    def _get_init_bet(self):
        """hook"""
        return 0

    def _get_min_raise(self):
        """hook"""
        return self.game.min_raise

    def _change_turn_options(self, curr_player_pos, turn_options: List[PlayerAction])->List[PlayerAction]:
        """
        overridden in PreFlopState
        """
        return turn_options

    async def _process_turn(self, curr_player_pos, prev_player_pos, curr_bet, prev_raise, options: List[PlayerAction])->ProcessedTurn:
        await self.game.game_handler.broadcast(GamePhase.TURN_HIGHLIGHT, TurnHighlightArgs(
                prev_player=self.game.players[prev_player_pos],
                curr_player=self.game.players[curr_player_pos]))

        player_acting = self.game.players[curr_player_pos]

        turn_response = await self.game.game_handler.turn(self.game.players[curr_player_pos],
                                                TurnRequestArgs(
                                                    player_bet=player_acting.bet,
                                                    prev_bet=curr_bet,
                                                    prev_raise=prev_raise,
                                                    options=options
                                                ))
        to_call = curr_bet - player_acting.bet

        command_invoker = CommandInvoker()
        command_args = PlayerActionCommandArgs(
            game=self.game,
            player_acting=player_acting,
            turn_response=turn_response,
            to_call=to_call,
            prev_raise=prev_raise)

        match turn_response.action:
            case PlayerAction.CALL:
                command_invoker.set_player_action_command(CallCommand(command_args))
            case PlayerAction.RAISE:
                command_invoker.set_player_action_command(RaiseCommand(command_args))
            case PlayerAction.FOLD:
                command_invoker.set_player_action_command(FoldCommand(command_args))
            case PlayerAction.CHECK:
                command_invoker.set_player_action_command(CheckCommand(command_args))

        return await command_invoker.player_action_command.process_turn()

    async def _deal_community_cards(self, number: int):
        self.game.table.community_cards += self.game.table.get_cards(number)
        await self.game.game_handler.broadcast(GamePhase.COMMUNITY_CARDS, CommunityCardsArgs(
            cards=self.game.table.community_cards))

class PreFlopState(AbsGameState):
    def _get_init_turn_options(self):
        return [PlayerAction.CALL, PlayerAction.FOLD, PlayerAction.RAISE]

    def _get_init_aggressor_pos(self):
        return (self.game.bb_pos + 1) % len(self.game.players)

    @override
    def _get_starting_pos(self):
        return (self.game.bb_pos + 1) % len(self.game.players)

    @override
    def _get_init_bet(self):
        return self.game.bb_amount

    @override
    def _change_turn_options(self, curr_player_pos, turn_options: List[PlayerAction])->List[PlayerAction]:
        if curr_player_pos == self.game.bb_pos: return [PlayerAction.CHECK, PlayerAction.FOLD, PlayerAction.RAISE]
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

class FlopState(AbsGameState):
    def _get_init_turn_options(self):
        return [PlayerAction.CHECK, PlayerAction.FOLD, PlayerAction.RAISE]

    def _get_init_aggressor_pos(self):
        return self.game.sb_pos

    def _get_starting_pos(self):
        return self.game.sb_pos

    async def _before_betting_round_action(self):
        for p in self.game.players: p.bet = 0

    async def start_flow(self):
        await self._deal_community_cards(3)
        await self.run_betting_round()

        next_state = TurnState(self.game)
        self.game.set_game_state(next_state)
        await next_state.start_flow()

class TurnState(FlopState):
    @override
    async def start_flow(self):
        await self._deal_community_cards(1)
        await self.run_betting_round()

        next_state = RiverState(self.game)
        self.game.set_game_state(next_state)
        await next_state.start_flow()

class RiverState(FlopState):
    @override
    async def start_flow(self):
        await self._deal_community_cards(1)
        await self.run_betting_round()

        next_state = ShowdownState(self.game)
        self.game.set_game_state(next_state)
        await next_state.start_flow()

class ShowdownState(AbsGameState):
    @override
    async def start_flow(self):
        (winners, losers) = self.process_showdown()
        await self.broadcast_showdown_results(winners, losers)

    def evaluate_hands(self)->EvaluatedHands:
        players_hands: Dict[Player, EvaluatedHand] = {}
        leading_hands: List[Tuple[Player, EvaluatedHand]] = [None]
        active_players = [p for p in self.game.players if p not in self.game.folded]
        for player in active_players:
            evaluator = RoyalFlushEvaluator()
            hand = evaluator.evaluate_hand(community_cards=self.game.table.community_cards,
                                    pocket_cards=player.get_poket_cards())
            if leading_hands[0] is None:
                leading_hands = [(player, hand)]
            elif hand > leading_hands[0][1]:
                leading_hands = [(player, hand)]
            elif hand == leading_hands[0][1]:
                leading_hands.append((player, hand))
            players_hands[player] = hand
        return EvaluatedHands(
            players_hands=players_hands,
            leading_hands=leading_hands)

    def process_showdown(self)->(ShowdownWinnerListArgs, ShowdownLoserListArgs):
        evaluated_hands = self.evaluate_hands()
        players_hands = evaluated_hands.players_hands
        leading_hands = evaluated_hands.leading_hands
        winning_players: List[Player] = [hand[0] for hand in leading_hands if hand[0] not in self.game.folded]

        winners: List[ShowdownWinnerArgs] = []
        if len(leading_hands) > 1:
            divided_pot = self.game.pot // len(leading_hands)
            remainder = self.game.pot % len(leading_hands)
            winners_count = 0

            curr_pos = self.game.sb_pos
            while winners_count != len(leading_hands):
                curr_player = self.game.players[curr_pos]
                if curr_player in winning_players:
                    won_pot = divided_pot
                    if winners_count == 0:
                        won_pot += remainder
                    curr_player.balance += won_pot
                    winners_count += 1
                    winners.append(ShowdownWinnerArgs(
                        winner=curr_player,
                        won_pot=won_pot,
                        hand=players_hands[curr_player].hand_value,
                        pocket_cards=curr_player.get_poket_cards()
                    ))
        else:
            winner = winning_players[0]
            winner.balance += self.game.pot
            winners.append(ShowdownWinnerArgs(
                winner=winner,
                won_pot=self.game.pot,
                hand=players_hands[winner].hand_value,
                pocket_cards=winner.get_poket_cards()
            ))

        losers: List[ShowdownLoserArgs] = []
        lost_players = [p for p in players_hands.keys() if p not in winning_players]
        for player in lost_players:
            losers.append(ShowdownLoserArgs(
                player=player,
                hand=players_hands[player].hand_value,
                pocket_cards=player.get_poket_cards()
            ))

        return ShowdownWinnerListArgs(winners=winners), ShowdownLoserListArgs(losers=losers)

    async def broadcast_showdown_results(self, winners: ShowdownWinnerListArgs, losers: ShowdownLoserListArgs):
        await self.game.game_handler.broadcast(GamePhase.SHOWDOWN_WINNERS, winners)
        await self.game.game_handler.broadcast(GamePhase.SHOWDOWN_LOSERS, losers)

    async def _before_betting_round_action(self):
        pass

    def _get_init_turn_options(self):
        pass

    def _get_init_aggressor_pos(self):
        pass

    def _get_starting_pos(self):
        pass