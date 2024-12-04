from flask import render_template, request, redirect, url_for, jsonify
from flask_socketio import emit, join_room, leave_room
from app import app, socketio
from app.game_manager import GameManager
import random
import string
from app.model.mighty import MightyGame, Suit
from app.utils import print_game_status
from app.model.card import Card


game_manager = GameManager()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/room/<room_id>")
def room(room_id):
    room = game_manager.get_room(room_id)
    if not room:
        return redirect(url_for("index"))
    player_names = [player.name for player in room.players]
    return render_template(
        "room.html",
        room_id=room.room_id,
        players=player_names,
        ready_players=room.ready_players,
    )


@app.route("/game/<room_id>")
def game(room_id):
    room = game_manager.get_room(room_id)
    if not room or not room.game:
        return redirect(url_for("index"))
    return render_template("game.html", room=room)


@socketio.on("create_room")
def handle_create_room(data):
    room_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    room = game_manager.create_room(room_id, data["username"], request.sid)
    token = room.player_tokens[data["username"]]
    emit("room_created", {"room_id": room_id, "token": token})


@socketio.on("join_room")
def handle_join_room(data):
    room = game_manager.get_room(data["room_id"])
    if not room:
        emit("join_error", {"message": "존재하지 않는 방입니다."})
        return

    success, token = room.add_player(data["username"], request.sid)
    if success:
        join_room(data["room_id"])

        emit(
            "player_joined",
            {"username": data["username"], "room_id": data["room_id"], "token": token},
            to=request.sid,
        )

        player_list = [player.name for player in room.players]
        emit(
            "update_player_list",
            {"players": player_list, "ready_players": list(room.ready_players)},
            room=data["room_id"],
        )
    else:
        emit("join_error", {"message": "방에 입장할 수 없습니다."})


@socketio.on("ready")
def handle_ready(data):
    print(f"[Ready] 준비 요청 수신. room_id: {data['room_id']}, token: {data['token']}")
    room = game_manager.get_room(data["room_id"])
    print(room)
    if room:
        player = next(
            (p for p in room.players if room.player_tokens[p.name] == data["token"]),
            None,
        )
        if player:
            print(f"[Ready] {player.name} 플레이어가 준비 완료")
            room.ready_players.add(player.name)
            emit("player_ready", {"username": player.name}, room=data["room_id"])

            if room.is_ready_to_start():
                print(
                    f"[Ready] 방 {data['room_id']}의 모든 플레이어가 준비 완료. 게임 시작"
                )
                room.game = MightyGame()
                for player in room.players:
                    room.game.add_player(player.name)
                room.game.initialize_deck()
                room.game.deal_cards()
                emit("game_start", room=data["room_id"])


@socketio.on("update_room_list")
def handle_update_room_list():
    rooms_data = game_manager.get_all_rooms()
    emit("update_room_list", {"rooms": rooms_data}, broadcast=True)


@socketio.on("request_room_list")
def handle_room_list_request():
    rooms_data = game_manager.get_all_rooms()
    emit("update_room_list", {"rooms": rooms_data})


@socketio.on("reconnect_room")
def handle_reconnect(data):
    room = game_manager.get_room(data["room_id"])
    if room:
        player = next(
            (p for p in room.players if room.player_tokens[p.name] == data["token"]),
            None,
        )
        if player:
            player.sid = request.sid
            join_room(data["room_id"])
            emit(
                "update_player_list",
                {
                    "players": [p.name for p in room.players],
                    "ready_players": list(room.ready_players),
                },
                room=data["room_id"],
            )
            return

    emit("reconnect_failed")


@socketio.on("init_game")
def handle_init_game(data):
    print("\n=== init_game 이벤트 ===")
    print("받은 데이터:", data)

    room_id = data.get("room_id")
    token = data.get("token")

    room = game_manager.get_room(room_id)
    if not room or not room.game:
        return

    # 현재 요청한 플레이어 찾기
    current_player = None
    if token:
        current_player = next(
            (p for p in room.players if room.player_tokens[p.name] == token), None
        )
    if current_player:
        # 플레이어 순서 정보 생성
        player_list = list(room.players)
        current_idx = player_list.index(current_player)
        players = []

        for i in range(len(player_list)):
            idx = (current_idx + i) % len(player_list)
            player = player_list[idx]
            players.append(
                {
                    "id": player.sid,
                    "name": player.name,
                    "token": room.player_tokens[player.name],
                }
            )

        # 현재 플레이어의 카드 정보 가져오기
        player_cards = room.game.get_player_cards(current_player.name)
        print("현재 플레이어의 카드 정보:", player_cards)
        sorted_cards = room.game.sort_cards(player_cards)  # 카드 정렬
        cards_data = [
            {"suit": card.suit.value, "rank": card.rank} for card in sorted_cards
        ]

        # 선 플레이어인 경우 추가 정보 전송
        is_first_player = room.game.current_player_idx == room.players.index(
            current_player
        )

        emit(
            "init_game",
            {
                "players": players,
                "cards": cards_data,
                "is_first_player": is_first_player,
                "phase": "bidding",  # 게임 페이즈 추가
            },
            to=request.sid,
        )
    else:
        # 관전자 등 토큰이 없는 경우는 플레이어 정보만 전송
        players = [
            {
                "id": player.sid,
                "name": player.name,
                "token": room.player_tokens[player.name],
            }
            for player in room.players
        ]

        emit("init_game", {"players": players}, room=room_id)


@socketio.on("join_game_room")
def handle_join_game_room(data):
    room_id = data.get("room_id")
    token = data.get("token")

    if not room_id:
        return

    room = game_manager.get_room(room_id)
    if room:
        if token:
            player = next(
                (p for p in room.players if room.player_tokens[p.name] == token), None
            )
            if player:
                player.sid = request.sid
        join_room(room_id)
        handle_init_game({"room_id": room_id, "token": token})


@socketio.on("submit_bid")
def handle_submit_bid(data):
    room_id = data.get("room_id")
    token = data.get("token")
    suit = data.get("suit")
    score = data.get("score")

    room = game_manager.get_room(room_id)
    if not room or not room.game:
        emit("error_message", {"message": "게임을 찾을 수 없습니다"})
        return

    # 토큰으로 현재 플레이어 확인
    current_player = next(
        (p for p in room.game.players if room.player_tokens[p.name] == token), None
    )
    if not current_player:
        emit("error_message", {"message": "플레이어를 찾을 수 없습니다"})
        return

    player_idx = room.game.players.index(current_player)

    # 비딩 제출
    print(
        f"[Submit Bid] 공약 제출 시도 - player: {current_player.name}, suit: {suit}, score: {score}"
    )
    try:
        suit_obj = getattr(Suit, suit.upper())
    except:
        suit_obj = None
    success = room.game.submit_bid(player_idx, score, suit_obj)
    if not success:
        emit("error_message", {"message": "잘못된 공약입니다"})
        return

    print(f"[Submit Bid] {current_player.name}님이 {suit} {score}을(를) 공약했습니다.")

    # 비딩 결과 브로드캐스트
    if score is None:  # 패스한 경우
        socketio.emit(
            "bid_passed",
            {
                "player_name": current_player.name,
            },
            room=room_id,
        )
    else:  # 공약 제시한 경우
        print(
            f"[Submit Bid] bid_updated 이벤트 emit - player: {current_player.name}, suit: {suit}, score: {score}"
        )
        socketio.emit(
            "bid_updated",
            {
                "player_name": current_player.name,
                "suit": suit,
                "score": score,
            },
            room=room_id,
        )

    # 비딩 페이즈가 끝났는지 확인
    if room.game.phase == "bidding":  # 다음 플레이어 턴
        print(f"[Submit Bid] 다음 플레이어 턴: {player_idx}")
        next_player_idx = (player_idx + 1) % len(room.game.players)
        while next_player_idx in room.game.passed_players:
            next_player_idx = (next_player_idx + 1) % len(room.game.players)
        next_player = room.game.players[next_player_idx]
        socketio.emit(
            "your_turn",
            {"phase": "bidding", "next_player": next_player.name},
            room=room_id,
        )
    else:  # 비딩이 끝난 경우
        print(f"[Submit Bid] 비딩이 끝났습니다. 대통령: {room.game.president_idx}")
        game_president = room.game.players[room.game.president_idx]
        # room.players에서 실제 sid를 가진 플레이어 객체를 찾음
        president = next(p for p in room.players if p.name == game_president.name)

        socketio.emit(
            "bidding_complete",
            {
                "president": president.name,
                "suit": room.game.giruda.value,
                "score": room.game.current_bid.score,
            },
            room=room_id,
        )

        # 주공에게 원래 카드와 kitty 같이 정렬해서 카드 전송
        player_cards = room.game.get_player_cards(president.name)
        kitty = room.game.give_kitty_to_president()
        sorted_cards = room.game.sort_cards(
            player_cards + kitty
        )  # 기루다 기준으로 정렬
        print(
            f"[Submit Bid] Kitty 전송 - president: {president.name}, sid: {president.sid}"
        )
        socketio.emit(
            "discard_and_update_bid",
            {
                "cards": [
                    {"suit": card.suit.value, "rank": card.rank}
                    for card in sorted_cards
                ],
                "current_bid": room.game.current_bid.score,
                "current_bid_suit": room.game.current_bid.suit.value,
            },
            room=president.sid,
        )


@socketio.on("discard_cards_and_update_bid")
def handle_discard_cards_and_update_bid(data):
    print(
        f"[Discard Cards and Update Bid] 버리기 및 공약 수정 요청 수신 - data: {data}"
    )
    room_id = data.get("room_id")
    token = data.get("token")
    cards = data.get("cards")
    updated_bid = data.get("updated_bid")

    room = game_manager.get_room(room_id)
    current_player = next(
        (p for p in room.players if room.player_tokens[p.name] == token), None
    )

    if not room or not room.game:
        emit("error_message", {"message": "게임을 찾을 수 없습니다"})
        return

    if room.game.phase != "discarding":
        emit(
            "error_message",
            {"message": "현재 페이즈에서는 버리기 작업을 할 수 없습니다"},
        )
        return

    if room.game.president_idx != room.players.index(current_player):
        emit("error_message", {"message": "현재 플레이어가 주공이 아닙니다"})
        return

    if room.game.discard_cards(room.game.president_idx, cards):
        socketio.emit("discard_complete", {}, room=room_id)
    else:
        emit("error_message", {"message": "잘못된 버리기 작업입니다"})

    suit_map = {
        "♠": Suit.SPADE,
        "♦": Suit.DIAMOND,
        "♥": Suit.HEART,
        "♣": Suit.CLOVER,
        "🃏": Suit.JOKER,
        "spade": Suit.SPADE,
        "diamond": Suit.DIAMOND,
        "heart": Suit.HEART,
        "club": Suit.CLOVER,
        "joker": Suit.JOKER,
    }
    if room.game.phase == "modify_bid":
        print(f"[Discard Cards and Update Bid] 공약 수정 페이즈로 변경")
        if room.game.modify_final_bid(
            room.game.president_idx, updated_bid["score"], suit_map[updated_bid["suit"]]
        ):
            socketio.emit(
                "bid_updated",
                {
                    "player_name": current_player.name,
                    "suit": updated_bid["suit"],
                    "score": updated_bid["score"],
                },
                room=room_id,
            )
        else:
            emit("error_message", {"message": "잘못된 공약입니다"})

    emit("end_discard_and_update_bid", {}, room=current_player.sid)


@socketio.on("submit_friend")
def handle_submit_friend(data):
    print(f"[Submit Friend] 프렌드 선택 요청 수신 - data: {data}")
    room_id = data.get("room_id")
    token = data.get("token")
    suit = data.get("suit")
    rank = data.get("rank")

    suit_map = {
        "spade": Suit.SPADE,
        "diamond": Suit.DIAMOND,
        "heart": Suit.HEART,
        "club": Suit.CLOVER,
        "joker": Suit.JOKER,
    }
    suit = suit_map.get(suit, None)
    if not suit:
        emit("error_message", {"message": "잘못된 무늬입니다"})
        return
    room = game_manager.get_room(room_id)
    current_player = next(
        (p for p in room.players if room.player_tokens[p.name] == token), None
    )
    if not room or not room.game:
        emit("error_message", {"message": "게임을 찾을 수 없습니다"})
        return

    if not current_player:
        emit("error_message", {"message": "플레이어를 찾을 수 없습니다"})
        return

    if room.game.phase != "friend_selection":
        emit(
            "error_message",
            {"message": "현재 페이즈에서는 프렌드 선택을 할 수 없습니다"},
        )
        return

    if room.game.president_idx != room.players.index(current_player):
        emit("error_message", {"message": "현재 플레이어가 주공이 아닙니다"})
        return

    if not isinstance(rank, int):
        rank = int(rank)

    if room.game.select_friend(room.game.president_idx, suit, rank):
        print(f"프렌드 카드 선택 성공: {suit.value}{rank}")
        emit(
            "end_friend_selection",
            {"suit": suit.value, "rank": rank, "president_name": current_player.name},
            room=room_id,
        )
        # 각 유저에게 카드덱 전송하면서 게임 시작
        for player in room.players:
            player_cards = room.game.get_player_cards(player.name)
            sorted_cards = room.game.sort_cards(player_cards)
            emit(
                "game_start",
                {
                    "cards": [
                        {"suit": card.suit.value, "rank": card.rank}
                        for card in sorted_cards
                    ]
                },
                room=player.sid,
            )

    else:
        emit(
            "error_message_friend_selection",
            {"message": "프렌드로 선택할 수 없는 카드입니다"},
        )

    print_game_status(room.game)


@socketio.on("submit_card")
def handle_submit_card(data):
    print(f"[Submit Card] 카드 제출 요청 수신 - data: {data}")
    room_id = data.get("room_id")
    token = data.get("token")
    suit = data.get("suit")
    rank = data.get("rank")

    room = game_manager.get_room(room_id)
    if not room or not room.game:
        emit("error_message", {"message": "게임을 찾을 수 없습니다"})
        return

    suit_map = {
        "♠": Suit.SPADE,
        "♦": Suit.DIAMOND,
        "♥": Suit.HEART,
        "♣": Suit.CLOVER,
        "🃏": Suit.JOKER,
        "spade": Suit.SPADE,
        "diamond": Suit.DIAMOND,
        "heart": Suit.HEART,
        "club": Suit.CLOVER,
        "joker": Suit.JOKER,
    }
    current_player = next(
        (p for p in room.players if room.player_tokens[p.name] == token), None
    )
    if not current_player:
        emit("error_message", {"message": "플레이어를 찾을 수 없습니다"})
        return

    if room.game.phase != "playing":
        emit(
            "error_message", {"message": "현재 페이즈에서는 카드를 제출할 수 없습니다"}
        )
        return

    if room.game.current_player_idx != room.players.index(current_player):
        emit("error_message", {"message": "현재 플레이어가 아닙니다"})
        return

    if room.game.play_card(
        room.players.index(current_player), Card(suit_map[suit], rank), None, False
    ):
        emit(
            "card_submitted",
            {"player_name": current_player.name, "suit": suit, "rank": rank},
            room=room_id,
        )
    else:
        emit("error_message", {"message": "잘못된 카드입니다"})

    # 트릭이 끝났는지 확인
    if len(room.game.current_trick) == 0:
        print("\n=== 트릭 종료 ===")
        socketio.emit(
            "clear_trick", 
            {"winner_name": room.game.players[room.game.current_player_idx].name}, 
            room=room_id
        )