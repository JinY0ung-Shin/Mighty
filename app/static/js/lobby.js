const socket = io();
let nickname = '';

function showNicknameModal() {
    document.getElementById('nickname-modal').style.display = 'block';
}

function showCreateRoomModal() {
    if (!nickname) {
        alert('닉네임을 먼저 설정해주세요.');
        showNicknameModal();
        return;
    }
    document.getElementById('create-room-modal').style.display = 'block';
}

function setNickname() {
    const usernameInput = document.getElementById('username');
    nickname = usernameInput.value.trim();
    
    if (nickname) {
        document.getElementById('nickname-modal').style.display = 'none';
        // 서버에 닉네임 설정 알림
        socket.emit('set_nickname', { username: nickname });
    } else {
        alert('닉네임을 입력해주세요.');
    }
}

function createRoom() {
    const roomNameInput = document.getElementById('room-name');
    const roomName = roomNameInput.value.trim();
    
    if (roomName) {
        document.getElementById('create-room-modal').style.display = 'none';
        // 서버에 방 생성 요청
        socket.emit('create_room', { username: nickname });
    } else {
        alert('방 이름을 입력해주세요.');
    }
}

socket.on('room_created', (data) => {
    sessionStorage.setItem('playerToken', data.token);
    window.location.href = `/room/${data.room_id}`;
});

// 방 목록 업데이트 (초기 로딩 및 실시간 업데이트에 모두 사용)
socket.on('update_room_list', (data) => {
    const roomList = document.getElementById('room-list');
    roomList.innerHTML = '';
    
    data.rooms.forEach(room => {
        const roomElement = document.createElement('div');
        roomElement.className = 'room-item';
        roomElement.innerHTML = `
            <div class="room-name">${room.name}</div>
            <div class="room-players">${room.current_players}/${room.max_players}</div>
            <button onclick="joinRoom('${room.id}')">입장</button>
        `;
        roomList.appendChild(roomElement);
    });
});

function generateRandomNickname() {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < 8; i++) {
        result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return result;
}

function joinRoom(roomId) {
    if (!nickname) {
        nickname = generateRandomNickname();
    }
    socket.emit('join_room', { room_id: roomId, username: nickname });
}

// ESC 키로 모달 닫기
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.getElementById('nickname-modal').style.display = 'none';
        document.getElementById('create-room-modal').style.display = 'none';
    }
});

// 페이지 로드 시 방 목록 요청
document.addEventListener('DOMContentLoaded', () => {
    socket.emit('request_room_list');
});

// 방 입장 성공 시 토큰 저장
socket.on('player_joined', (data) => {
    sessionStorage.setItem('playerToken', data.token);
    window.location.href = `/room/${data.room_id}`;
});

// 방 입장 실패 시 에러 메시지 표시
socket.on('join_error', (data) => {
    alert(data.message);
});
  