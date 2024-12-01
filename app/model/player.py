from .card import Card
from typing import List


class Player:
    def __init__(self, name: str, sid: str = None):
        self.name = name
        self.sid = sid
        self.cards: List[Card] = []
        self.points: int = 0
        self.total_score: int = 0

    def add_card(self, card: Card):
        self.cards.append(card)

    def remove_card(self, card: Card):
        self.cards.remove(card)

    def update_total_score(self, points: int):
        self.total_score += points

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name
