from typing import List

class Player:
    def __init__(self, id: int, name, balance: float):
        self.id = id
        self.name = name
        self.balance = balance
        self.pocket_cards: List[Card] = []
        self.is_ready = False

    def get_poket_cards(self):
        return self.pocket_cards

    def get_poket_cards_dict(self):
        return [c.to_dict() for c in self.pocket_cards]

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "balance": self.balance,
            "is_ready": self.is_ready
        }

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.value = self.__rank_value(rank)

    def __rank_value(self, rank) -> int:
        rank_value_mapping = {'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        if rank in rank_value_mapping.keys():
            return rank_value_mapping[rank]
        return int(rank)

    def to_dict(self):
        return {"suit": self.suit, "rank": self.rank, "value": self.value}