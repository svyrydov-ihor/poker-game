import random
from typing import List
from app.game.models import Player, Card

class Table:
    def __init__(self):
        self.players: List[Player] = []
        self.community_cards: List[Card] = []

        self.__deck: List[Card] = []
        self.__suits = ['♥️', '♦️', '♠️', '♣️']
        self.__ranks = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
        self.reset_deck()

    def reset_deck(self):
        self.__deck = [Card(s, r) for s in self.__suits for r in self.__ranks]
        random.shuffle(self.__deck)

    def get_cards(self, count)->List[Card]:
        if len(self.__deck) < count:
            return []
        cards = self.__deck[:count]
        self.__deck = self.__deck[count:]
        return cards

    def add_player(self, player: Player):
        if player.id <= 0:
            raise ValueError('Player id must be positive')
        if player.name is None or player.name == "":
            raise ValueError('Player name cannot be empty')
        self.players.append(player)

    def remove_player(self, id: int):
        if id <= 0:
            raise ValueError('Player id must be positive')
        self.players = [p for p in self.players if p.id != id]