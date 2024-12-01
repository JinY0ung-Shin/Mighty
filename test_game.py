from app.model.mighty import MightyGame, Suit, Card
from app.model.player import Player
import random
from typing import Optional

# ANSI 색상 코드
RED = "\033[91m"
RESET = "\033[0m"

# 전역 변수로 게임 객체 관리
current_game = None


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


def print_game_result(game):
    print("\n=== 게임 결과 ===")
    president = game.players[game.president_idx]

    # 주공과 프렌드의 점수 합산
    president_team_points = president.points
    if (
        game.friend_player_idx is not None
        and game.friend_player_idx != game.president_idx
    ):
        friend = game.players[game.friend_player_idx]
        president_team_points += friend.points

    print(
        f"주공(Player {game.president_idx}) 공약: {game.current_bid.score} {game.current_bid.suit.value}"
    )
    if game.friend_player_idx is not None:
        print(f"프렌드: Player {game.friend_player_idx}")
    else:
        print("노프렌드")

    print(f"\n획득 점수:")
    for i, player in enumerate(game.players):
        team_status = ""
        if i == game.president_idx:
            team_status = "(주공)"
        elif i == game.friend_player_idx:
            team_status = "(프렌드)"
        print(f"Player {i}{team_status}: {player.points}점")

    print(f"\n주공팀 총점: {president_team_points}점")
    if president_team_points >= game.current_bid.score:
        print("주공팀 승리!")
    else:
        print("야당팀 승리!")

    print("\n=== 누적 점수 ===")
    for i, player in enumerate(game.players):
        print(f"Player {i}: {player.total_score}점")

    print("\n다음 게임을 시작하려면 Enter를 누르세요...")
    input()


def test_game():
    global current_game

    # 첫 게임이거나 게임이 없는 경우 새로 생성
    if current_game is None:
        current_game = MightyGame()
        # 플레이어 추가
        for i in range(5):
            current_game.add_player(f"Player {i}")
    else:
        # 게임 상태만 초기화
        current_game.reset_game()

    game = current_game  # 현재 게임 객체 사용

    # 덱 초기화 및 카드 분배
    game.initialize_deck()
    game.deal_cards()

    print_game_status(game)

    # 비딩 페이즈 테스트
    while game.phase == "bidding":
        print(f"\nPlayer {game.current_player_idx}의 차례")

        # 이미 패스한 플레이어면 자동으로 패스
        if game.current_player_idx in game.passed_players:
            print(
                f"Player {game.current_player_idx}는 이미 패스했습니다. 자동으로 패스합니다."
            )
            game.submit_bid(game.current_player_idx, None, None)
            continue

        print("공약을 입력하세요 (13-20, 엔터는 패스):")
        print("예시: '13s' (13점 스페이드), '14h' (14점 하트)")
        print("s:스페이드 d:다이아 h:하트 c:클로버")

        bid_input = input().strip().lower()

        if not bid_input:  # 엔터만 입력한 경우 패���
            game.submit_bid(game.current_player_idx, None, None)
            print("패스")
        else:
            try:
                score = int(bid_input[:-1])
                suit_char = bid_input[-1]
                suit_map = {
                    "s": Suit.SPADE,
                    "d": Suit.DIAMOND,
                    "h": Suit.HEART,
                    "c": Suit.CLOVER,
                }

                if suit_char not in suit_map:
                    print("잘못된 무늬입니다")
                    continue

                suit = suit_map[suit_char]

                if game.submit_bid(game.current_player_idx, score, suit):
                    print(f"공약 제시 성공: {score} {suit.value}")
                else:
                    print("잘못된 공약입니다")
            except (ValueError, IndexError):
                print("잘못된 입력 형식입니다")
                continue

        print_game_status(game)

    # 비딩 페이즈 이후 카드 버리기 페이즈 추가
    while game.phase == "discarding":
        print(f"\n=== 카드 버리기 페이즈 ===")
        print(f"주공(Player {game.president_idx})의 차례")

        # 키티 카드와 현재 패를 합쳐서 보여주기
        player = game.players[game.president_idx]
        kitty = game.give_kitty_to_president()
        all_cards = sort_cards(player.cards + kitty, game.giruda)  # 기루다 전달

        print("\n전체 카드:")
        print(print_cards(all_cards, game.giruda))  # 기루다 전달

        print("\n카드 번호:")
        for i, card in enumerate(all_cards):
            print(f"{i}: {format_card(card)}")

        print("\n버릴 카드 3장을 선택하세요 (예: 1 4 7):")
        try:
            indices = list(map(int, input().split()))
            if len(indices) != 3:
                print("정확히 3장의 드를 선택해야 합니다")
                continue

            cards_to_discard = [all_cards[i] for i in indices]
            print(cards_to_discard)
            if game.discard_cards(game.president_idx, cards_to_discard):
                print("카드를 버렸습니다")
            else:
                print("잘못된 선택입니다")
        except (ValueError, IndexError):
            print("잘못된 입력입니다")
            continue

        print_game_status(game)

    # 카드 버리기 페이즈 이후 공약 수정 페이즈 추가
    while game.phase == "modify_bid":
        print(f"\n=== 공약 수정 페이즈 ===")
        print(f"주공(Player {game.president_idx})의 차례")
        print(f"현재 공약: {game.current_bid.score} {game.current_bid.suit.value}")
        print("\n공약을 수정하시겠습니까? (엔터는 수정하지 않음)")
        print("수정하려면 새로운 공약 입력 (예: '15s')")
        print("s:스페이드 d:다이아 h:하트 c:클로버")

        bid_input = input().strip().lower()

        if not bid_input:  # 엔터만 입력한 경우 수정하지 않음
            if game.modify_final_bid(game.president_idx, None, None):
                print("공약 수정 없이 진행합니다")
            else:
                print("오류가 발생했습니다")
        else:
            try:
                score = int(bid_input[:-1])
                suit_char = bid_input[-1]
                suit_map = {
                    "s": Suit.SPADE,
                    "d": Suit.DIAMOND,
                    "h": Suit.HEART,
                    "c": Suit.CLOVER,
                }

                if suit_char not in suit_map:
                    print("잘못된 무늬입니다")
                    continue

                suit = suit_map[suit_char]

                if game.modify_final_bid(game.president_idx, score, suit):
                    print(f"공약 수정 성공: {score} {suit.value}")
                else:
                    print("잘못된 공약입니��� (2점 이상 올리거나 20점이어야 합니다)")
            except (ValueError, IndexError):
                print("잘못된 입력 형식입니다")
                continue

        print_game_status(game)

    # 카드 버리기 페이즈 이후 프렌드 선택 페이즈 추가
    while game.phase == "friend_selection":
        print(f"\n=== 프렌드 선택 페이즈 ===")
        print(f"주공(Player {game.president_idx})의 차례")
        print("\n프렌드 카드를 선택하세요:")
        print("예시: 'sa' (스페이드A), 'h10' (하트10), 'jk' (조커)")
        print("s:스페이드 d:다이아 h:하트 c:클로버 jk:조커")
        print("숫자: 2-10, j, q, k, a")
        print("엔터: 노프렌드")

        friend_input = input().strip().lower()

        if not friend_input:  # 엔터만 입력한 경우 노프렌드
            if game.select_friend(game.president_idx):
                print("노프렌드를 선택했습니다")
            continue

        try:
            if friend_input == "jk":  # 조커를 프렌드로 선택
                if game.select_friend(game.president_idx, Suit.JOKER, 0):
                    print("프렌드 카드 선택 성공: 조커")
                else:
                    print("잘못된 프렌드 카드입니다")
                continue

            suit_char = friend_input[0]
            rank_str = friend_input[1:]

            suit_map = {
                "s": Suit.SPADE,
                "d": Suit.DIAMOND,
                "h": Suit.HEART,
                "c": Suit.CLOVER,
            }
            rank_map = {"j": 11, "q": 12, "k": 13, "a": 14}

            if suit_char not in suit_map:
                print("잘못된 무늬입니다")
                continue

            suit = suit_map[suit_char]
            rank = rank_map.get(rank_str, rank_str)
            if not isinstance(rank, int):
                rank = int(rank)

            if game.select_friend(game.president_idx, suit, rank):
                print(f"프렌드 카드 선택 성공: {suit.value}{rank_str.upper()}")
            else:
                print("잘못된 프렌드 카드입니다")
        except (ValueError, IndexError):
            print("잘못된 입력 형식입니다")
            continue

        print_game_status(game)

    # 플레이 페이즈 테스트
    print_game_status(game)
    while game.phase == "playing":
        print(f"\nPlayer {game.current_player_idx}의 차례")
        player = game.players[game.current_player_idx]

        print("가능한 카드:")
        valid_cards = sort_cards(player.cards, game.giruda)
        for i, card in enumerate(valid_cards):
            print(f"{i}: {format_card(card)}")

        card_idx = int(input("카드 선택: "))
        selected_card = valid_cards[card_idx]

        # 클로버3을 낼 때 조커콜 여부 선택
        call_joker = False
        if (
            not game.current_trick
            and selected_card.suit == Suit.CLOVER
            and selected_card.rank == 3
        ):
            print("\n조커를 콜하시겠습니까? (y/n)")
            call_joker = input().strip().lower() == "y"

        # 첫 카드가 조커인 경우 무늬 선택
        joker_suit = None
        if not game.current_trick and selected_card.is_joker():
            print("\n조커의 무늬를 선택하세요:")
            print("s:스페이드 d:다이아 h:하트 c:클로버")
            suit_input = input().strip().lower()
            suit_map = {
                "s": Suit.SPADE,
                "d": Suit.DIAMOND,
                "h": Suit.HEART,
                "c": Suit.CLOVER,
            }
            if suit_input in suit_map:
                joker_suit = suit_map[suit_input]
            else:
                print("잘못된 무늬입니다")
                continue

        if game.play_card(
            game.current_player_idx, selected_card, joker_suit, call_joker
        ):
            print("카드 플레이 성공")
            if call_joker:
                print("조커콜!")
            if joker_suit:
                print(f"조커 무늬: {joker_suit.value}")
        else:
            print("잘못된 카드입니다")

        print_game_status(game)

        # 트릭이 끝났는지 확인
        if len(game.current_trick) == 0:
            print("\n=== 트릭 종료 ===")
            for i, player in enumerate(game.players):
                print(f"Player {i}의 획득 점수: {player.points}점")
            input("계속하려면 Enter를 누르세요...")

    if game.phase == "game_over":
        print_game_result(game)
        return


if __name__ == "__main__":
    # 게임이 끝나면 자동으로 새게임 시작하도록
    while True:
        test_game()
