const socket = io();
const token = sessionStorage.getItem('playerToken');
const roomId = getRoomId();

// 페이지 로드 시 토큰 확인
if (!token) {
    window.location.href = '/';
} else {
    // 토큰으로 재연결 요청
    socket.emit('reconnect_room', {
        room_id: roomId,
        token: token
    });
}

// 재연결 실패 시 로비로 이동
socket.on('reconnect_failed', () => {
    sessionStorage.removeItem('playerToken');
    window.location.href = '/';
});

// 플레이어 목록 업데이트
socket.on('update_player_list', (data) => {
    updatePlayerList(data.players, data.ready_players || []);
});

function updatePlayerList(players, readyPlayers) {
    const playersList = document.getElementById('players');
    playersList.innerHTML = '';
    
    players.forEach(playerName => {
        const playerElement = document.createElement('li');
        playerElement.className = 'player-item';
        playerElement.setAttribute('data-username', playerName);
        playerElement.textContent = playerName;
        
        if (readyPlayers.includes(playerName)) {
            const readyStatus = document.createElement('span');
            readyStatus.className = 'ready-status';
            readyStatus.textContent = ' (준비 완료)';
            readyStatus.style.color = '#2ecc71';
            playerElement.appendChild(readyStatus);
        }
        
        playersList.appendChild(playerElement);
    });
}

// 준비하기 버튼 클릭 시 토큰도 함께 전송
function toggleReady() {
    socket.emit('ready', {
        room_id: roomId,
        token: token
    });
}

function getRoomId() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1];
}

socket.on('player_ready', function(data) {
    const playerElement = document.querySelector(`li[data-username="${data.username}"]`);
    if (playerElement) {
        const existingStatus = playerElement.querySelector('.ready-status');
        if (existingStatus) {
            existingStatus.remove();
        }
        
        const readyStatus = document.createElement('span');
        readyStatus.className = 'ready-status';
        readyStatus.textContent = ' (준비 완료)';
        readyStatus.style.color = '#2ecc71';
        playerElement.appendChild(readyStatus);
    }
});

// game_start 이벤트 핸들러 추가
socket.on('game_start', function() {
    window.location.href = `/game/${roomId}`;
}); 