from app.model.card import Suit, Card
from typing import Optional

RED = "\033[91m"
RESET = "\033[0m"


def format_card(card):
    if isinstance(card, str) and card == "Joker":
        return "🃏"

    # 하트와 다이아몬드는 빨간색으로 표시
    if card.suit in [Suit.HEART, Suit.DIAMOND]:
        return f"{RED}{card}{RESET}"
    return str(card)


def sort_cards(cards, giruda: Optional[Suit] = None):
    # 조커와 일반 카드 분리
    jokers = [card for card in cards if card.suit == Suit.JOKER]
    normal_cards = [card for card in cards if card.suit != Suit.JOKER]

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


def print_cards(cards, giruda: Optional[Suit] = None):
    sorted_cards = sort_cards(cards, giruda)
    # 무늬별로 카드를 그룹화
    suited_cards = {
        Suit.JOKER: [],
        Suit.SPADE: [],
        Suit.DIAMOND: [],
        Suit.HEART: [],
        Suit.CLOVER: [],
    }

    for card in sorted_cards:
        suited_cards[card.suit].append(format_card(card))

    # 무늬별로 출력 문자열 생성
    output = []
    if suited_cards[Suit.JOKER]:
        output.append(" ".join(suited_cards[Suit.JOKER]))

    # 기루다가 있으면 기루다를 먼저 출력
    if giruda:
        if suited_cards[giruda]:
            output.append(" ".join(suited_cards[giruda]))

    # 나머지 무늬 출력
    for suit in [
        s for s in [Suit.SPADE, Suit.DIAMOND, Suit.HEART, Suit.CLOVER] if s != giruda
    ]:
        if suited_cards[suit]:
            output.append(" ".join(suited_cards[suit]))

    return " / ".join(output)


def print_game_status(game):
    print("\n=== 현재 게�� 상태 ===")
    print(f"페이즈: {game.phase}")
    print(f"현재 플레이어: Player {game.current_player_idx}")
    if game.current_bid:
        print(
            f"현재 공약: {game.current_bid.score} ({game.current_bid.suit.value if game.current_bid.suit else 'None'})"
        )
    print(f"기루다: {game.giruda.value if game.giruda else 'None'}")

    print("\n=== 플레이어 카드 ===")
    for i, player in enumerate(game.players):
        if i == game.president_idx:
            print(
                f"\033[91mPlayer {i}\033[0m: {print_cards(player.cards, game.giruda)}"
            )
        elif i == game.friend_player_idx:
            print(
                f"\033[94mPlayer {i}\033[0m: {print_cards(player.cards, game.giruda)}"
            )
        else:
            print(f"Player {i}: {print_cards(player.cards, game.giruda)}")

    if game.current_trick:
        print("\n현재 트릭:", print_cards(game.current_trick, game.giruda))

    if game.friend_card:
        print(f"프렌드 카드: {game.friend_card}")
        if game.friend_player_idx is not None:
            print(f"프렌드: Player {game.friend_player_idx}")
