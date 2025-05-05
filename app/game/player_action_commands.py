from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from app.game.game_schema import TurnResponse, ProcessedTurn, GamePhase, PotArgs, TurnResultArgs, PlayerAction, \
    PlayerActionCommandArgs
from app.game.models import Player

if TYPE_CHECKING:
    from app.game.game import Game

class CommandInvoker:
    """
    Command invoker for Command pattern
    """
    def __init__(self):
        self.player_action_command = None

    def set_player_action_command(self, command: 'AbsPlayerActionCommands'):
        self.player_action_command = command

class AbsPlayerActionCommands(ABC):
    """
    Command pattern for handling player actions
    """
    def __init__(self, args: PlayerActionCommandArgs):
        self.game: 'Game' = args.game
        self.player_acting: Player = args.player_acting
        self.turn_response: TurnResponse = args.turn_response
        self.to_call: float = args.to_call
        self.prev_raise: float = args.prev_raise

    @abstractmethod
    async def process_turn(self)->ProcessedTurn:
        pass

    async def broadcast_turn_result(self):
        await self.game.game_handler.broadcast(GamePhase.TURN_RESULT, TurnResultArgs(
            player=self.player_acting,
            action=self.turn_response.action,
            amount=self.player_acting.bet,
        ))
        await self.game.game_handler.broadcast(GamePhase.POT, PotArgs(pot=self.game.pot))

class CallCommand(AbsPlayerActionCommands):
    async def process_turn(self) -> ProcessedTurn:
        self.player_acting.bet += self.turn_response.amount
        self.player_acting.balance -= self.turn_response.amount
        self.game.pot += self.turn_response.amount

        await self.broadcast_turn_result()
        return ProcessedTurn(
            action=PlayerAction.CALL,
            curr_bet=self.player_acting.bet,
            curr_raise=self.prev_raise)

class RaiseCommand(AbsPlayerActionCommands):
    async def process_turn(self) -> ProcessedTurn:
        self.player_acting.bet += self.to_call + self.turn_response.amount
        self.player_acting.balance -= self.to_call + self.turn_response.amount
        self.game.pot += self.to_call + self.turn_response.amount

        await self.broadcast_turn_result()
        return ProcessedTurn(
            action=PlayerAction.RAISE,
            curr_bet=self.player_acting.bet,
            curr_raise=self.turn_response.amount)

class FoldCommand(AbsPlayerActionCommands):
    async def process_turn(self) -> ProcessedTurn:
        self.game.folded.append(self.player_acting)

        await self.broadcast_turn_result()
        return ProcessedTurn(
            action=PlayerAction.FOLD,
            curr_bet=self.player_acting.bet,
            curr_raise=self.prev_raise)

class CheckCommand(AbsPlayerActionCommands):
    async def process_turn(self) -> ProcessedTurn:
        await self.broadcast_turn_result()
        return ProcessedTurn(
            action=PlayerAction.FOLD,
            curr_bet=self.player_acting.bet,
            curr_raise=self.prev_raise)