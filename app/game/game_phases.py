import enum
from abc import ABC

from pydantic.v1 import BaseModel

from app.game.models import Player

class GamePhase(enum.Enum):
    NEW_PLAYER = "NEW_PLAYER"
    PRE_START = "PRE_START"
    POCKET_CARDS = "POCKET_CARDS"
    PRE_FLOP_SB = "PRE_FLOP_SB"
    PRE_FLOP_BB = "PRE_FLOP_BB"
    TURN = "TURN"

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

class PreFlopSBArgs(AbsGamePhaseArgs):
    sb_amount: float
    player: Player

class PreFlopBBArgs(AbsGamePhaseArgs):
    bb_amount: float
    player: Player

class PocketCardsArgs(AbsGamePhaseArgs):
    pocket_cards: list[dict]

class TurnArgs(AbsGamePhaseArgs):
    curr_player: Player
    player_choice: PlayerChoice
    amount: float

class TurnResult(BaseModel):
    player_choice: PlayerChoice
    amount: float