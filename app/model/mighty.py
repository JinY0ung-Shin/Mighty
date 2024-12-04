from enum import Enum
from typing import List, Dict, Optional, Union
import random
from .card import Card, Suit
from .player import Player

MIN_BID = 13


class Bid:
    def __init__(self, player_idx: int, score: int, suit: Optional[Suit]):
        self.player_idx = player_idx
        self.score = score
        self.suit = suit


class MightyGame:
    def __init__(self):
        self.players: List[Player] = []
        self.deck: List[Card] = []
        self.current_player_idx = 0
        self.giruda: Optional[Suit] = None
        self.mighty_card: Optional[Card] = None
        self.current_trick: List[Card] = []
        self.current_bid: Optional[Bid] = None
        self.president_idx: Optional[int] = None
        self.pass_count = 0
        self.bid_history: List[Bid] = []
        self.first_player_idx = 0
        self.passed_players = set()
        self.kitty: List[Card] = []
        self.discarded_cards: List[Card] = []
        self.joker_suit = None  # 조커로 지정한 무늬 저장
        self.friend_card: Optional[Card] = None  # 프렌드 카드
        self.friend_player_idx: Optional[int] = None  # 프렌드 플레이어 인덱스
        self.phase = (
            "bidding"  # bidding, discarding, friend_selection, playing으로 수정
        )
        self.joker_called_in_this_trick = False  # 현재 트릭에서 조커콜 발동 여부

    def initialize_deck(self):
        self.deck = []
        # 모든 카드 생성 (조커 포함)
        for suit in Suit:
            if suit == Suit.JOKER:
                self.deck.append(Card(suit, 0))  # 조커는 rank 0
            else:
                for rank in range(2, 15):  # 2부터 A까지
                    self.deck.append(Card(suit, rank))

    def add_player(self, name: str):
        if len(self.players) < 5:
            self.players.append(Player(name))
            return True
        return False

    def deal_cards(self):
        while True:  # 적절한 패가 나올 때까지 반복
            random.shuffle(self.deck)
            # 각 플레이어에게 10장씩 카드 배분
            cards_per_player = 10
            temp_hands = []  # 임시로 패를 저장

            for i in range(5):  # 5명의 플레이어
                start_idx = i * cards_per_player
                end_idx = start_idx + cards_per_player
                hand = self.deck[start_idx:end_idx]
                temp_hands.append(hand)

            # 남은 3장은 kitty에 저장
            self.kitty = self.deck[50:]

            # 각 플레이어의 패 검증
            valid_distribution = True
            for hand in temp_hands:
                if not self._is_valid_hand(hand):
                    valid_distribution = False
                    break

            if valid_distribution:
                # 유효한 패 분배면 플레이어들에게 할당
                for player, hand in zip(self.players, temp_hands):
                    player.cards = hand
                break

    def _is_valid_hand(self, hand: List[Union[Card, str]]) -> bool:
        """
        유효한 패인지 검사
        - 마이티를 제외한 점수 카드가 최소 1장은 있어야 함
        """
        point_cards = 0
        mighty = None

        # 마이티 카드 결정 (초기에는 기루다가 없으므로 스페이드A가 마이티)
        if self.giruda == Suit.SPADE:
            mighty = (Suit.DIAMOND, 14)  # 다이아A
        else:
            mighty = (Suit.SPADE, 14)  # 스페이드A

        for card in hand:
            if isinstance(card, Card):
                # 마이티가 아닌 점수 카드 개수 세기
                if card.is_point_card() and not (
                    card.suit == mighty[0] and card.rank == mighty[1]
                ):
                    point_cards += 1

        return point_cards > 0  # 마이티 제외 점수카드가 1장 이상이면 유효

    def submit_bid(
        self, player_idx: int, score: Optional[int], suit: Optional[Suit]
    ) -> bool:
        if self.phase != "bidding":
            print("비딩 중이 아닙니다.")
            return False
        if player_idx != self.current_player_idx:
            print(
                f"현재 플레이어가 아닙니다. {player_idx} != {self.current_player_idx}"
            )
            return False

        # 이미 패스한 플레이어는 자동으로 패스 처리하고 다음 플레이어로 넘어감
        if player_idx in self.passed_players:
            self.current_player_idx = (self.current_player_idx + 1) % 5
            return True

        # 패스인 경우
        if score is None:
            self.pass_count += 1
            self.passed_players.add(player_idx)  # 패스한 플레이어 기록
            self.bid_history.append(Bid(player_idx, 0, None))

            # 모든 플레이어가 패스한 경우
            if self.pass_count == 5:
                # 선 플레이어가 자동으로 MIN_BID로 스페이드 공약
                self.current_bid = Bid(self.first_player_idx, MIN_BID, Suit.SPADE)
                self.bid_history.append(self.current_bid)
                self.president_idx = self.first_player_idx
                self.giruda = Suit.SPADE
                self.phase = "discarding"
                self.current_player_idx = self.first_player_idx
                return True
            # 4명이 패스하고 마지막 비드가 있는 경우
            elif self.pass_count == 4 and self.current_bid:
                self.president_idx = self.current_bid.player_idx
                self.giruda = self.current_bid.suit
                self.phase = "discarding"
                self.current_player_idx = self.president_idx
                return True

        # 공약 제시하는 경우
        else:
            # 점수 범위 체크 (MIN_BID~20)
            if score < MIN_BID or score > 20:
                print("13 이상 20 이하의 점수를 공약해야 하여야 합니다.")
                return False

            # 이전 공약보다 높아야 함
            if self.current_bid and score <= self.current_bid.score:
                print("이전 공약보다 높은 점수를 공약해야 하여야 합니다.")
                return False

            # suit는 반드시 선택해야 함
            if suit is None:
                # 노기루 나중에 구현
                return False

            # 새로운 비드 생성
            new_bid = Bid(player_idx, score, suit)
            self.current_bid = new_bid
            self.bid_history.append(new_bid)

            # 20점 공약이 나오면 즉시 비딩 종료
            #
            if score == 20 or self.pass_count == 4:
                self.president_idx = player_idx
                self.giruda = suit
                self.phase = "discarding"
                self.current_player_idx = player_idx
                return True
        # 다음 플레이어로 턴 넘기기
        while True:
            self.current_player_idx = (self.current_player_idx + 1) % 5
            if self.current_player_idx not in self.passed_players:
                break
        return True

    def get_bid_state(self) -> Dict:
        """
        현재 비딩 상태 반환
        """
        return {
            "current_player": self.current_player_idx,
            "current_bid": (
                {
                    "player": self.current_bid.player_idx,
                    "score": self.current_bid.score,
                    "suit": (
                        self.current_bid.suit.value
                        if self.current_bid and self.current_bid.suit
                        else None
                    ),
                }
                if self.current_bid
                else None
            ),
            "pass_count": self.pass_count,
            "bid_history": [
                {
                    "player": bid.player_idx,
                    "score": bid.score,
                    "suit": bid.suit.value if bid.suit else None,
                }
                for bid in self.bid_history
            ],
        }

    def play_card(
        self,
        player_idx: int,
        card: Card,
        joker_suit: Optional[Suit] = None,
        call_joker: bool = False,
    ) -> bool:
        if self.phase != "playing":
            return False
        if player_idx != self.current_player_idx:
            return False

        player = self.players[player_idx]
        if card not in player.cards:
            return False

        # 첫커콜 처리
        if not self.current_trick:  # 첫 카드일 때
            if card.suit == Suit.CLOVER and card.rank == 3:  # 클로버3으로 시작
                if call_joker:
                    self.joker_called_in_this_trick = True
                    print("조커콜!")
        elif self.joker_called_in_this_trick:  # 조커콜된 트릭에서
            has_joker = any(c.is_joker() for c in player.cards)
            if has_joker and not card.is_joker():  # 조커 있는데 안냈으면
                return False

        # 첫 카드가 조커인 경우, 무늬를 지정해야 함
        if not self.current_trick and card.is_joker():
            if joker_suit is None or joker_suit == Suit.JOKER:
                return False
            self.joker_suit = joker_suit

        # 첫 카드가 아닌 경우, 선카드 무늬를 따라야 함
        if self.current_trick:
            leading_suit = (
                self.joker_suit
                if self.current_trick[0].is_joker()
                else self.current_trick[0].suit
            )

            # 마이티나 조커는 아무 때나 낼 수 있음
            if not (card.is_joker() or card.is_mighty(self.giruda)):
                # 선카드 무늬를 가지고 있는지 확인 (마이티와 조커 제외)
                has_leading_suit = any(
                    c.suit == leading_suit
                    for c in player.cards
                    if not (c.is_joker() or c.is_mighty(self.giruda))
                )
                # 선카드 무늬가 있는데 다른 무늬를 낸 경우
                if has_leading_suit and card.suit != leading_suit:
                    return False

        # 카드 플레이
        player.remove_card(card)
        self.current_trick.append(card)

        # 다음 플레이어로 턴 넘기기
        self.current_player_idx = (self.current_player_idx + 1) % 5

        # 한 트릭이 끝났는지 확인
        if len(self.current_trick) == 5:
            self._resolve_trick()
            self.joker_suit = None  # 트릭이 끝나면 조커 무늬 초기화

        # 프렌드 카드가 공개되면 프렌드 플레이어 설정
        if (
            self.friend_card
            and not self.friend_player_idx
            and (
                (self.friend_card.suit == Suit.JOKER and card.is_joker())  # 조커인 경우
                or (
                    card.suit == self.friend_card.suit
                    and card.rank == self.friend_card.rank
                )
            )
        ):  # 일반 카드인 경우
            self.friend_player_idx = player_idx
            print(f"프렌드가 공개되었습니다! Player {player_idx}")

        # 게임이 종료 되었는지 확인 후 player total score 업데이트
        # total score update 계산법
        # 주공팀 승리시
        # 기본 점수 (주공점수 + 프렌드 점수 -공약 점수) + (공약 점수-최소 공약)*2 = 여당 득점 + 공약 점수 - 최소 공약*2점
        # 주공은 위 점수의 2배를 얻고 프렌드는 1배 획득
        # 나머지 플레이어는 위 점수 맡큼 잃는다
        # 노프렌드의 경우 주공은 위점수에 4배를 얻고 나머지는 위 점수 만큼 잃는다
        # 주공팀 패배시
        # 기본 점수 (공약 점수 - 획득점수)
        # 주공은 위 점수의 2배를 잃고 프렌드는 1배를 잃음
        # 나머지 플레이어는 위 점수 만큼 얻는다
        # 노프렌드시 주공은 위점수의 4배를 잃고 나머지는 위 점수 만큼 얻는다
        if all(len(player.cards) == 0 for player in self.players):
            self.phase = "game_over"
            print("최종 점수 업데이트###########################")
            self._update_total_score()

        return True

    def _update_total_score(self):
        """
        최종 점수 업데이트
        """
        # 주공과 프렌드 점수 합이 공약 점수보다 높거나 면 주공팀 승리
        score = self.players[self.president_idx].points + (
            self.players[self.friend_player_idx].points
            if self.friend_player_idx is not None
            else 0
        )
        if score >= self.current_bid.score:
            base_score = (score - self.current_bid.score) + (
                self.current_bid.score - MIN_BID
            ) * 2
            if self.friend_player_idx is not None:
                self.players[self.president_idx].update_total_score(base_score * 2)
                self.players[self.friend_player_idx].update_total_score(base_score)
            else:
                self.players[self.president_idx].update_total_score(base_score * 4)
            for i, player in enumerate(self.players):
                if i != self.president_idx and i != self.friend_player_idx:
                    player.update_total_score(-base_score)

        else:
            base_score = self.current_bid.score - score
            if self.friend_player_idx is not None:
                self.players[self.president_idx].update_total_score(-base_score * 2)
                self.players[self.friend_player_idx].update_total_score(-base_score)
            else:
                self.players[self.president_idx].update_total_score(-base_score * 4)
            for i, player in enumerate(self.players):
                if i != self.president_idx and i != self.friend_player_idx:
                    player.update_total_score(base_score)

    def _resolve_trick(self):
        """
        트릭이 끝났을 때 처리하는 메서드
        - 승자 결정
        - 점수 카드 계산
        - 승자의 점수 업데이트
        """
        # 트릭의 승자 결정
        winner_idx = self._determine_trick_winner()

        # 점수 계산 (A, K, Q, J, 10 각각 1점)
        trick_points = sum(1 for card in self.current_trick if card.is_point_card())

        # 승자의 점수 추가
        self.players[winner_idx].points += trick_points

        # 현재 트릭 초기화하고 승자를 다음 선플레이어로 설정
        self.current_trick = []
        self.current_player_idx = winner_idx
        self.joker_called_in_this_trick = False  # 트릭 종료시 초기화

    def _determine_trick_winner(self) -> int:
        """
        트릭의 승자를 결정하는 로직
        우선순위: 마이티 > 조커(조커콜 아닐 때) > 기루다 >  카드와 같은 무늬
        """
        first_card = self.current_trick[0]
        leading_suit = first_card.suit if isinstance(first_card, Card) else None
        highest_power = -1
        winner_idx = 0

        for i, card in enumerate(self.current_trick):
            power = self._calculate_card_power(card, leading_suit)
            if power > highest_power:
                highest_power = power
                winner_idx = (self.current_player_idx - (5 - i)) % 5

        return winner_idx

    def _calculate_card_power(self, card: Card, leading_suit: Optional[Suit]) -> int:
        """
        카드의 파워(강함)를 계산
        Returns:
            1000: 마이티
            900: 조커
            800-814: 기루다
            700-714: 선카드와 같은 무늬
            1-14: 나머지 카드
        """
        # 조커콜된 트릭에서 조커는 가장 약한 카드
        if self.joker_called_in_this_trick and card.is_joker():
            return 0

        # 조커인 경우
        if card.is_joker():
            # 조커콜 구현 필요
            return 900

        # 마이티 카드인 경우
        if card.is_mighty(self.giruda):
            return 1000

        # 기루다인 ���우
        if card.suit == self.giruda:
            return 800 + card.rank

        # 선카드와 같은 무늬인 경우
        if card.suit == leading_suit:
            return 700 + card.rank

        # 그 외의 카드
        return card.rank

    def get_game_state(self) -> Dict:
        state = {
            "phase": self.phase,
            "current_player": self.current_player_idx,
            "president": self.president_idx,
            "giruda": self.giruda.value if self.giruda else None,
            "current_trick": [str(card) for card in self.current_trick],
            "players": [
                {
                    "name": player.name,
                    "cards": [str(card) for card in player.cards],
                    "points": player.points,  # 직접 points 사용
                }
                for i, player in enumerate(self.players)
            ],
            "joker_suit": (
                self.joker_suit.value if self.joker_suit else None
            ),  # 조커 무늬 정보 추가
            "friend_card": str(self.friend_card) if self.friend_card else None,
            "friend_player": self.friend_player_idx,
        }

        # 현재 공약 정보 추가
        if self.current_bid:
            state["current_bid"] = {
                "player": self.current_bid.player_idx,
                "score": self.current_bid.score,
                "suit": self.current_bid.suit.value if self.current_bid.suit else None,
            }

        # 주공에게만 kitty와 버려진 카드 정보 제공
        if self.phase == "discarding" and self.president_idx is not None:
            state["kitty"] = [str(card) for card in self.kitty]
            state["discarded_cards"] = [str(card) for card in self.discarded_cards]

        return state

    def give_kitty_to_president(self) -> List[Card]:
        """주공에게 남은 3장의 카드를 보여줌"""
        if self.phase != "discarding" or self.president_idx is None:
            return []
        return self.kitty

    def discard_cards(
        self, player_idx: int, cards_to_discard: List[Union[Card, str, dict]]
    ) -> bool:
        """
        주공이 카드 3장을 버리는 메서드
        버린 카드 중 점수 카드는 주공의 점수로 계산
        """
        if self.phase != "discarding":
            return False
        if player_idx != self.president_idx:
            return False
        if len(cards_to_discard) != 3:
            return False

        if isinstance(cards_to_discard[0], dict):
            mapping = {
                "♠": Suit.SPADE,
                "♦": Suit.DIAMOND,
                "♥": Suit.HEART,
                "♣": Suit.CLOVER,
                "🃏": Suit.JOKER,
            }
            cards_to_discard = [
                Card(mapping[card["suit"]], card["rank"]) for card in cards_to_discard
            ]

        print(cards_to_discard)

        president = self.players[self.president_idx]

        # 버릴 카드가 실제로 주공의 패에 있는지 확인
        all_cards = president.cards + self.kitty
        for card in cards_to_discard:
            if card not in all_cards:
                print(f"버릴 카드가 주공의 패에 없습니다: {card.suit} {card.rank}")
                return False

        # 버린 카드의 점수 계산 (A, K, Q, J, 10 각각 1점)
        discarded_points = sum(1 for card in cards_to_discard if card.is_point_card())
        president.points += discarded_points  # 주공의 점수에 추가

        # 카드 버리기
        self.discarded_cards = cards_to_discard

        # 주공의 새로운 패 설정
        new_hand = [card for card in all_cards if card not in cards_to_discard]
        president.cards = new_hand

        # 게임 페이즈를 공약 수정으로 변경
        self.phase = "modify_bid"
        return True

    def modify_final_bid(
        self, player_idx: int, score: Optional[int], suit: Optional[Suit]
    ) -> bool:
        """
        주공이 최종 공약을 수정하는 메서드
        """
        if self.phase != "modify_bid":
            return False
        if player_idx != self.president_idx:
            return False
        if score is None:  # 수정하지 않고 진행
            self.phase = "friend_selection"  # playing 대신 friend_selection으로 변경
            return True

        # 이전과 동일하면 수정하지 않고 진행
        if score == self.current_bid.score and suit == self.current_bid.suit:
            self.phase = "friend_selection"
            return True

        # 공약 수정 규칙 검증
        if score < self.current_bid.score + 2 and score != 20:
            return False  # 2점 이상 올리거나 20점이어야 함
        if score > 20:
            return False

        # 새로운 공약으로 업데이트
        self.current_bid = Bid(player_idx, score, suit)
        self.giruda = suit
        self.phase = "friend_selection"  # playing 대신 friend_selection으로 변경
        return True

    def get_player_points(self, player_idx: int) -> int:
        """
        특정 플레이어의 총 점수를 반환
        """
        return self.players[player_idx].points

    def select_friend(
        self, player_idx: int, suit: Optional[Suit] = None, rank: Optional[int] = None
    ) -> bool:
        """
        프렌드 카드를 선택하는 메서드
        suit와 rank가 None이면 노프렌드
        """
        if self.phase != "friend_selection":
            return False
        if player_idx != self.president_idx:
            return False

        # 노프렌드인 경우
        if suit is None or rank is None:
            self.friend_card = None
            self.friend_player_idx = None
            self.phase = "playing"
            return True

        # suit와 rank가 유효한지 확인
        print(suit, rank)
        if not Card.is_valid_card(suit, rank):
            return False

        # 주공 자신의 카드는 프렌드 카드로 선택할 수 없음
        if any(
            c.suit == suit and c.rank == rank for c in self.players[player_idx].cards
        ):
            return False

        # 프렌드 카드가 버려진 카드에 있는지 확인
        if any(c.suit == suit and c.rank == rank for c in self.discarded_cards):
            return False

        # 게임 페이즈를 공약 수정으로 변경
        self.friend_card = Card(suit, rank)
        self.friend_player_idx = next(
            (
                i
                for i, p in enumerate(self.players)
                if any(c.suit == suit and c.rank == rank for c in p.cards)
            ),
            None,
        )
        self.phase = "playing"
        return True

    def reset_game(self):
        """게임을 초기화하되 플레이어는 유지"""
        self.deck = []
        self.current_player_idx = 0
        self.giruda = None
        self.mighty_card = None
        self.current_trick = []
        self.current_bid = None
        self.president_idx = None
        self.pass_count = 0
        self.bid_history = []
        self.first_player_idx = 0
        self.passed_players = set()
        self.kitty = []
        self.discarded_cards = []
        self.joker_suit = None
        self.friend_card = None
        self.friend_player_idx = None
        self.phase = "bidding"
        self.joker_called_in_this_trick = False

        # 플레이어들의 카드와 점수 초기화
        for player in self.players:
            player.cards = []
            player.points = 0

    def get_player_cards(self, player_name: str) -> List[Card]:
        """
        특정 플레이어의 카드 목록을 반환합니다.

        Args:
            player_name (str): 카드를 조회할 플레이어의 이름

        Returns:
            List[Card]: 플레이어가 가지고 있는 카드 목록
        """
        player = next((p for p in self.players if p.name == player_name), None)
        return player.cards if player else []

    def get_current_player(self) -> Optional[Player]:
        return (
            self.players[self.current_player_idx]
            if self.current_player_idx is not None
            else None
        )

    def sort_cards(self, cards: List[Card]) -> List[Card]:
        giruda = self.giruda

        def get_card_power(card: Card) -> tuple:
            # 마이티 카드
            if card.is_mighty(giruda):
                return (0, 0, 0)  # 가장 높은 우선순위

            # 조커
            if card.suit == Suit.JOKER:
                return (1, 0, 0)

            # 기루다
            if giruda and card.suit == giruda:
                return (2, card.suit.value, -card.rank)

            # 일반 카드 (스페이드 > 다이아 > 하트 > 클로버)
            suit_order = {Suit.SPADE: 0, Suit.DIAMOND: 1, Suit.HEART: 2, Suit.CLOVER: 3}
            return (3, suit_order[card.suit], -card.rank)

        # 카드 정렬
        sorted_cards = sorted(cards, key=get_card_power)

        return sorted_cards
