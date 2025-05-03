import enum
from abc import ABC
from typing import Optional, List

from pydantic.v1 import BaseModel

from app.game.models import Player, Card


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

class PlayerChoice(enum.Enum):
    CALL = "CALL"
    CHECK = "CHECK"
    RAISE = "RAISE"
    FOLD = "FOLD"

class AbsGamePhaseArgs(ABC, BaseModel):
    class Config:
        arbitrary_types_allowed = True

    def dict(self, *args, **kwargs):
        base_dict = super().dict(**kwargs)
        return convert_players_to_dict(base_dict)

def convert_players_to_dict(data):
    if isinstance(data, Player):
        return data.to_dict()
    elif isinstance(data, PlayerChoice):
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
    choice: PlayerChoice
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
    options: List[PlayerChoice]

class TurnResponse(BaseModel):
    choice: PlayerChoice
    amount: float

class ProcessedTurn(BaseModel):
    choice: PlayerChoice
    curr_bet: float
    curr_raise: float

class IsReadyArgs(BaseModel):
    player_id: int
    is_ready: bool
