from enum import Enum
from typing import Optional


class Suit(Enum):
    SPADE = "♠"
    DIAMOND = "♦"
    HEART = "♥"
    CLOVER = "♣"
    JOKER = "🃏"


class Card:
    def __init__(self, suit: Suit, rank: int):
        self.suit = suit
        self.rank = rank  # 2-14 (11=J, 12=Q, 13=K, 14=A), 조커는 rank=0

    def __str__(self):
        if self.suit == Suit.JOKER:
            return self.suit.value
        rank_str = {11: "J", 12: "Q", 13: "K", 14: "A"}.get(self.rank, str(self.rank))
        return f"{self.suit.value}{rank_str}"

    def is_joker(self) -> bool:
        return self.suit == Suit.JOKER

    def is_point_card(self) -> bool:
        """점수 카드인지 확인 (A, K, Q, J, 10)"""
        return not self.is_joker() and self.rank >= 10

    def is_mighty(self, giruda: Optional[Suit]) -> bool:
        """마이티 카드인지 확인"""
        if giruda == Suit.SPADE:
            return self.suit == Suit.DIAMOND and self.rank == 14  # 다이아 A
        return self.suit == Suit.SPADE and self.rank == 14  # 스페이드 A

    @classmethod
    def is_valid_card(cls, suit: Suit, rank: int) -> bool:
        """
        53장 중 유효한 카드인지 확인
        조커이거나 4개 무늬와 숫자 2-14 중 하나인 경우 유효
        type check 추가
        """
        if suit == Suit.JOKER and rank == 0:
            return True
        if isinstance(suit, Suit) and isinstance(rank, int):
            return (
                suit in [Suit.SPADE, Suit.DIAMOND, Suit.HEART, Suit.CLOVER]
                and 2 <= rank <= 14
            )
        return False

    def __eq__(self, other):
        return self.suit == other.suit and self.rank == other.rank
