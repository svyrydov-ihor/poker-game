import enum
from abc import ABC
from typing import Optional, List, TYPE_CHECKING
from pydantic.v1 import BaseModel
from app.game.models import Player, Card
if TYPE_CHECKING:
    from app.game.game import Game

class GamePhase(enum.Enum):
    NEW_PLAYER = "NEW_PLAYER"
    PRE_START = "PRE_START"
    POCKET_CARDS = "POCKET_CARDS"
    PRE_FLOP_SB = "PRE_FLOP_SB"
    PRE_FLOP_BB = "PRE_FLOP_BB"
    COMMUNITY_CARDS = "COMMUNITY_CARDS"
    TURN_REQUEST = "TURN_REQUEST"
    TURN_HIGHLIGHT = "TURN_HIGHLIGHT"
    TURN_RESULT = "TURN_RESULT"
    POT = "POT"
    IS_READY = "IS_READY"

class PlayerAction(enum.Enum):
    CALL = "CALL"
    CHECK = "CHECK"
    RAISE = "RAISE"
    FOLD = "FOLD"

class HandValue(enum.Enum):
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIRS = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9

class AbsGamePhaseArgs(ABC, BaseModel):
    class Config:
        arbitrary_types_allowed = True

    def dict(self, *args, **kwargs):
        base_dict = super().dict(**kwargs)
        return convert_players_to_dict(base_dict)

def convert_players_to_dict(data):
    if isinstance(data, Player):
        return data.to_dict()
    elif isinstance(data, PlayerAction):
        return data.value
    elif isinstance(data, Card):
        return data.to_dict()
    elif isinstance(data, list):
        return [convert_players_to_dict(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_players_to_dict(value) for key, value in data.items()}
    return data

class NewPlayerArgs(AbsGamePhaseArgs):
    player: Player

class PreStartArgs(AbsGamePhaseArgs):
    prev_dealer: Player
    curr_dealer: Player
    ordered_player_ids: List[int]

class PreFlopSBArgs(AbsGamePhaseArgs):
    sb_amount: float
    player: Player

class PreFlopBBArgs(AbsGamePhaseArgs):
    bb_amount: float
    player: Player

class CommunityCardsArgs(AbsGamePhaseArgs):
    cards: List[Card]

class PocketCardsArgs(AbsGamePhaseArgs):
    pocket_cards: list[dict]

class TurnResultArgs(AbsGamePhaseArgs):
    player: Player
    action: PlayerAction
    amount: float

class TurnHighlightArgs(AbsGamePhaseArgs):
    prev_player: Player
    curr_player: Optional[Player] = None

class PotArgs(AbsGamePhaseArgs):
    pot: float

class TurnRequestArgs(AbsGamePhaseArgs):
    player_bet: float
    prev_bet: float
    prev_raise: float
    options: List[PlayerAction]

class ShowdownWinnerArgs(AbsGamePhaseArgs):
    winner: Player
    won_pot: float
    hand: HandValue

class ShowdownLostArgs(AbsGamePhaseArgs):
    players: dict[Player, HandValue]

class EvaluatedHand(BaseModel):
    hand_value: HandValue
    highest_in_hand_value: int
    highest_in_hand_value_2: Optional[int] = None
    kicker_value: int

class TurnResponse(BaseModel):
    action: PlayerAction
    amount: float

class ProcessedTurn(BaseModel):
    action: PlayerAction
    curr_bet: float
    curr_raise: float

class IsReadyArgs(BaseModel):
    player_id: int
    is_ready: bool

class PlayerActionCommandArgs:
    def __init__(self, game: 'Game', player_acting: Player, turn_response: TurnResponse, to_call: float, prev_raise: float):
        self.game = game
        self.player_acting = player_acting
        self.turn_response = turn_response
        self.to_call = to_call
        self.prev_raise = prev_raise