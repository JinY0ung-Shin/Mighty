from typing import Dict, Optional, List
from app.model.mighty import MightyGame, Card
from app.model.player import Player
import secrets  # 안전한 토큰 생성을 위해


class GameRoom:
    def __init__(self, room_id: str, host_name: str, host_sid: str):
        self.room_id = room_id
        self.host_name = host_name
        self.players: List[Player] = []
        self.player_tokens = {}  # {player_name: token} 매핑으로 변경
        self.game: Optional[MightyGame] = None
        self.ready_players = set()
        # 호스트 추가 및 토큰 생성
        self.add_player(host_name, host_sid)

    def add_player(self, player_name: str, sid: str) -> tuple[bool, str | None]:
        if len(self.players) >= 5:
            return False, None
        if any(player.name == player_name for player in self.players):
            return False, None

        # 유저별 고유 토큰 생성
        token = secrets.token_urlsafe(16)
        self.player_tokens[player_name] = token  # player_name을 키로 사용
        self.players.append(Player(player_name, sid))
        return True, token

    def get_player_token(self, player_name: str) -> Optional[str]:
        return self.player_tokens.get(player_name)

    def get_player_by_token(self, token: str) -> Optional[Player]:
        if token not in self.player_tokens:
            return None
        player_name = self.player_tokens[token]
        return next((p for p in self.players if p.name == player_name), None)

    def remove_player(self, player_name: str) -> None:
        self.players = [player for player in self.players if player.name != player_name]
        self.ready_players.discard(player_name)

    def is_ready_to_start(self) -> bool:
        return len(self.players) == 5 and len(self.ready_players) == 5

    def get_player_list(self) -> List[Player]:
        return self.players


class GameManager:
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}

    def create_room(
        self, room_id: str, host_name: str, host_sid: str
    ) -> Optional[GameRoom]:
        if room_id in self.rooms:
            return None
        room = GameRoom(room_id, host_name, host_sid)
        self.rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        return self.rooms.get(room_id)

    def remove_room(self, room_id: str) -> None:
        if room_id in self.rooms:
            del self.rooms[room_id]

    def get_all_rooms(self):
        rooms_data = []
        for room_id, room in self.rooms.items():
            player_list = [player.name for player in room.players]
            rooms_data.append(
                {
                    "id": room_id,
                    "name": f"Room {room_id}",
                    "current_players": len(room.players),
                    "max_players": 5,  # 마이티 게임은 5명이 최대
                    "players": player_list,
                }
            )
        return rooms_data
