from abc import abstractmethod
from app.game.game_schema import *
from app.game.game_states import PreFlopState, AbsGameState
from app.game.models import Player
from app.game.table import Table

class AbsGameHandler(ABC):
    """
    Implementation for Bridge pattern between game and game handler
    """
    def __init__(self, players: List[Player], spectators: List[Player], sb_amount: float, bb_amount: float):
        self.players: List[Player] = players
        self.spectators: List[Player] = spectators
        self.sb_amount: float = sb_amount
        self.bb_amount: float = bb_amount

    @abstractmethod
    async def broadcast(self, game_phase: GamePhase, abs_game_phase_args: AbsGamePhaseArgs)->None:
        pass
    @abstractmethod
    async def send_personal(self, game_phase: GamePhase, player_id: int, abs_game_phase_args: AbsGamePhaseArgs)->None:
        pass
    @abstractmethod
    async def turn(self, player: Player, turn_request_args: TurnRequestArgs)->TurnResponse:
        pass

class AbsGameBuilder(ABC):
    """
    Builder pattern
    """
    @abstractmethod
    def set_game_handler(self, game_handler: AbsGameHandler)->None:
        pass

    @abstractmethod
    def set_table(self, table: Table)->None:
        pass

    @abstractmethod
    def set_small_blind_amount(self, sb_amount: float)->None:
        pass

    @abstractmethod
    def set_big_blind_amount(self, bb_amount: float)->None:
        pass

    @abstractmethod
    def set_min_raise_amount(self, min_raise: float)->None:
        pass

    @abstractmethod
    def get_built_game(self)->'Game':
        pass

class ConcreteGameBuilder(AbsGameBuilder):
    def __init__(self):
        self._game = Game()
        self.reset()

    def reset(self):
        self._game = Game()

    def set_game_handler(self, game_handler: AbsGameHandler) -> None:
        self._game.game_handler = game_handler

    def set_table(self, table: Table) -> None:
        self._game.table = table
        self._game.players = table.players
        self._game.folded = []

    def set_small_blind_amount(self, sb_amount: float) -> None:
        if sb_amount <= 0:
            raise ValueError("Small blind value must be positive")
        self._game.sb_amount = sb_amount

    def set_big_blind_amount(self, bb_amount: float) -> None:
        if bb_amount <= 0:
            raise ValueError("Big blind value must be positive")
        elif bb_amount <= self._game.sb_amount:
            raise ValueError("Big blind must be bigger than small blind")
        self._game.bb_amount = bb_amount

    def set_min_raise_amount(self, min_raise: float) -> None:
        if min_raise <= 0:
            raise ValueError("Minimum raise amount must be positive")
        self._game.min_raise = min_raise

    def get_built_game(self) -> 'Game':
        return self._game

class Game:
    """
    Should be constructed using AbsGameBuilder implementations
    Abstraction for Bridge pattern between game and game handler
    """
    def __init__(self):
        self.table: Table = Table()
        self.game_handler: AbsGameHandler = None
        self.curr_dealer_pos: int = -1
        self.prev_dealer_pos: int = 0
        self.pot: float = 0
        self.sb_amount: float = 0
        self.bb_amount: float = 0
        self.min_raise: float = 0
        self.players: List[Player] = []
        self.folded: List[Player] = []
        self.sb_pos: int = -1
        self.bb_pos: int = -1
        self.is_game_started: bool = False
        self.game_state: AbsGameState = None

    def set_game_state(self, game_state: AbsGameState):
        self.game_state = game_state

    async def start_game(self):
        self.is_game_started = True
        self.players = self.table.players
        self.prev_dealer_pos = self.curr_dealer_pos
        self.curr_dealer_pos = (self.curr_dealer_pos + 1) % len(self.players)
        self.pot = 0
        self.folded = []
        self.table.community_cards = []
        self.table.reset_deck()
        ordered_ids = [p.id for p in self.players]

        await self.game_handler.broadcast(GamePhase.PRE_START, PreStartArgs(
            prev_dealer=self.players[self.prev_dealer_pos],
            curr_dealer=self.players[self.curr_dealer_pos],
            ordered_player_ids=ordered_ids))

        self.set_game_state(PreFlopState(self))
        await self.game_state.start_flow()
        await self.reset_players_ready()

    async def reset_players_ready(self):
        for player in self.table.players:
            player.is_ready = False
        self.is_game_started = False
        await self.game_handler.broadcast(GamePhase.PLAY_AGAIN, PotArgs(pot=self.pot))