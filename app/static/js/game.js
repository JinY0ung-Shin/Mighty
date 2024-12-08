class GameUI {
    constructor() {
        this.socket = io();
        this.positions = ['player-bottom', 'player-right', 'player-top-right', 'player-top-left', 'player-left'];
        this.token = sessionStorage.getItem('playerToken');
        console.log('[GameUI 생성] 저장된 토큰:', this.token);
        this.initializeSocketEvents();
        this.currentPhase = null;
    }

    initializeSocketEvents() {
        // 소켓 연결 후 방에 join
        this.socket.on('connect', () => {
            this.joinRoom(ROOM_ID);
            this.socket.emit('init_game', {
                room_id: ROOM_ID,
                token: this.token
            });
        });

        this.socket.on('init_game', (data) => this.handleInitGame(data));

        // 공약 관련 이벤트
        this.socket.on('error_message', (data) => {
            alert(data.message);
        });
        
        this.socket.on('bid_updated', (data) => {
            this.updateBidInfo(data);
        });
        
        this.socket.on('bid_passed', (data) => {
            this.handleBidPassed(data);
        });
        
        this.socket.on('bidding_complete', (data) => {
            this.handleBiddingComplete(data);
        });

        this.socket.on('your_turn', (data) => {
            const nextPlayerName = data.next_player;
            if (data.phase === 'bidding' && nextPlayerName === this.name) {
                this.showBiddingUI();
            }
        });

        this.socket.on('discard_and_update_bid', (data) => {
            this.handleDiscardAndUpdateBid(data);
        });

        this.socket.on('end_discard_and_update_bid', (data) => {
            this.handleEndDiscardAndUpdateBid(data);
        });

        this.socket.on('end_friend_selection', (data) => {
            this.endFriendSelection(data);
        });

        this.socket.on('error_message_friend_selection', (data) => {
            alert(data.message);
        });

        this.socket.on('game_start', (data) => {
            this.handleGameStart(data);
        });

        this.socket.on('card_submitted', (data) => {
            this.handleCardSubmitted(data);
        });

        this.socket.on('clear_trick', (data) => {
            console.log('clear trick');
            this.handleClearTrick(data);
        });
    }

    joinRoom(roomId) {
        this.socket.emit('join_game_room', {
            room_id: roomId,
            token: this.token
        });
    }

    handleInitGame(data) {
        const players = data.players;
        const myCards = data.cards;  // 서버에서 받은 카드 정보
        const myIndex = players.findIndex(p => p.token === this.token);
        this.name = players[myIndex].name;
        console.log("카드 정보:", myCards);
        
        if (myIndex === -1) {
            console.error('플레이어를 찾을 수 없습니다');
            return;
        }
        
        this.initializePlayerNames(players);
        this.updatePlayerPositions(players, myIndex);
        
        // 모든 플레이어의 카드 생성
        this.createAllPlayersCards(players.length, myCards);
        
        if (data.is_first_player && data.phase === 'bidding') {
            this.showBiddingUI();
        }
    }

    initializePlayerNames(players) {
        document.querySelectorAll('.player-name').forEach(el => {
            el.textContent = '빈 자리';
        });
    }

    updatePlayerPositions(players, myIndex) {
        for (let i = 0; i < players.length; i++) {
            const relativePos = (i - myIndex + players.length) % players.length;
            const playerArea = document.querySelector(`.${this.positions[relativePos]} .player-name`);
            
            if (playerArea) {
                const player = players[i];
                if (i === myIndex) {
                    console.log(`${player.name}는 나! position: ${this.positions[relativePos]}`);
                    playerArea.textContent = `${player.name} (나)`;
                } else {
                    console.log(`${player.name}는 상대방, position: ${this.positions[relativePos]}`);
                    playerArea.textContent = player.name;
                }
            }
        }
    }

    createAllPlayersCards(playerCount, myCards) {
        this.positions.forEach((position, index) => {
            if (index < playerCount) {
                const isBottom = position === 'player-bottom';
                const container = document.querySelector(`.${position} .cards-container`);
                container.innerHTML = '';
                
                // 내 카드는 실제 카드를, 다른 플레이어 면을 보여줌
                if (isBottom && myCards) {
                    myCards.forEach(card => {
                        const cardElement = document.createElement('div');
                        cardElement.className = 'card';
                        const fileName = this.getCardFileName(card);
                        cardElement.style.backgroundImage = `url('/static/svg-cards/${fileName}')`;
                        cardElement.style.backgroundSize = 'cover';
                        cardElement.style.backgroundPosition = 'center';
                        container.appendChild(cardElement);
                    });
                } else {
                    // 다른 플레이어의 카드는 10장의 뒷면 카드를 보여줌
                    for (let i = 0; i < 10; i++) {
                        const cardElement = document.createElement('div');
                        cardElement.className = 'card opponent-card';
                        container.appendChild(cardElement);
                    }
                }
            }
        });
    }

    getCardFileName(card) {
        if (card.suit === "") {
            return "joker.svg";
        }
        
        const suitMap = {
            "♠": "spades",
            "♥": "hearts",
            "♦": "diamonds",
            "♣": "clubs"
        };
        
        const rankMap = {
            11: "jack",
            12: "queen",
            13: "king",
            14: "ace"
        };
        
        const suit = suitMap[card.suit];
        const rank = rankMap[card.rank] || card.rank;
        
        return `${rank}_of_${suit}.svg`;
    }

    showBiddingUI() {
        // 이미 bidding UI가 있다면 중복 생성하지 않음
        if (document.querySelector('.bidding-ui')) {
            return;
        }

        const biddingUI = document.createElement('div');
        biddingUI.className = 'bidding-ui';
        biddingUI.innerHTML = `
            <div class="bidding-box">
                <div class="bidding-title">공약 선택</div>
                <div class="suit-selection">
                    <div class="suit spade" data-suit="spade">♠</div>
                    <div class="suit diamond" data-suit="diamond">♦</div>
                    <div class="suit heart" data-suit="heart">♥</div>
                    <div class="suit club" data-suit="clover">♣</div>
                    <div class="suit none" data-suit="none">X</div>
                </div>
                <div class="score-selection">
                    <button class="score-btn" data-score="13">13</button>
                    <button class="score-btn" data-score="14">14</button>
                    <button class="score-btn" data-score="15">15</button>
                    <button class="score-btn" data-score="16">16</button>
                    <button class="score-btn" data-score="17">17</button>
                    <button class="score-btn" data-score="18">18</button>
                    <button class="score-btn" data-score="19">19</button>
                    <button class="score-btn" data-score="20">20</button>
                </div>
                <div class="bidding-buttons">
                    <button class="bid-btn" onclick="gameUI.submitBid('bid-btn')">출마</button>
                    <button class="pass-btn" onclick="gameUI.submitBid('pass-btn')">패스</button>
                </div>
            </div>
        `;
        document.querySelector('.game-table').appendChild(biddingUI);
        
        // 문양 선택 이벤트
        biddingUI.querySelectorAll('.suit').forEach(suit => {
            suit.addEventListener('click', () => {
                biddingUI.querySelectorAll('.suit').forEach(s => s.classList.remove('selected'));
                suit.classList.add('selected');
            });
        });

        // 점수 선택 이벤트
        biddingUI.querySelectorAll('.score-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                biddingUI.querySelectorAll('.score-btn').forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
            });
        });
    }

    submitBid(buttonClass) {
        const selectedSuit = document.querySelector('.suit.selected')?.dataset.suit;
        const selectedScore = document.querySelector('.score-btn.selected')?.dataset.score;
        
        // 패스하는 경우나 선택이 안된 경우
        if (buttonClass === 'pass-btn' ) {
            this.socket.emit('submit_bid', {
                room_id: ROOM_ID,
                token: this.token,
                suit: null,
                score: null
            });
            return;
        }

        // 공약 제시하는 경우
        this.socket.emit('submit_bid', {
            room_id: ROOM_ID,
            token: this.token,
            suit: selectedSuit,
            score: parseInt(selectedScore)
        });
    }

    addBidInfoText(text) {
        let bidInfo = document.querySelector('.bid-info');
        if (!bidInfo) {
            bidInfo = document.createElement('div');
            bidInfo.className = 'bid-info';
            document.querySelector('.center-area').appendChild(bidInfo);
        }
        bidInfo.innerHTML += (bidInfo.innerHTML ? '<br>' : '') + text;
    }

    updateBidInfo(data) {
        console.log('[updateBidInfo] 현재 플레이어:', this.name);
        console.log('[updateBidInfo] 공약 제출한 플이어:', data.player_name);
        console.log('[updateBidInfo] 공약:', data.suit, data.score);
        const biddingUI = document.querySelector('.bidding-ui');
        
        // 공약 패널 업데이트 로직 추가
        const suitEmoji = {
            'spade': '♠️',
            'diamond': '<span style="color: red;">♦️</span>',
            'heart': '<span style="color: red;">♥️</span>',
            'clover': '♣️', 
            'none': '노프',
            '♠': '♠️',
            '♦': '<span style="color: red;">♦️</span>',
            '♥': '<span style="color: red;">♥️</span>',
            '♣': '♣️',
        };

        // 기존 패널이 있다면 업데이트하고, 없으면 새로 생성
        let bidInfoPanel = document.querySelector('.bid-info-panel');
        if (!bidInfoPanel) {
            bidInfoPanel = document.createElement('div');
            bidInfoPanel.className = 'bid-info-panel';
            document.querySelector('.player-top-right').insertAdjacentElement('beforebegin', bidInfoPanel);
        }

        // 패널 내용 업데이트 (패스가 아닌 경우에만)
        if (data.score !== null) {
            bidInfoPanel.innerHTML = `현재 공약: ${suitEmoji[data.suit]} ${data.score}`;
        }
        
        // 기존 텍스트 출력 로직
        let newBidText = '';
        if (data.score === null) {
            newBidText = `${data.player_name}님이 패스했습니다.`;
        } else {
            newBidText = `${data.player_name}님이 ${data.suit} ${data.score}을(를) 공약했습니다.`;
        }
        
        this.addBidInfoText(newBidText);
        
        if (biddingUI && data.player_name === this.name) {
            biddingUI.remove();
        }
    }

    handleBidPassed(data) {
        this.updateBidInfo({
            player_name: data.player_name,
            score: null
        });
    }

    handleBiddingComplete(data) {
        // 기존 공약 UI 제거
        const biddingUI = document.querySelector('.bidding-ui');
        if (biddingUI) {
            biddingUI.remove();
        }
        
        // 최종 공약 정보 표시
        this.addBidInfoText(`주공 ${data.president}님이 ${data.suit} ${data.score}을(를) 선언했습니다.`);
        this.addBidInfoText(`${data.president}님이 버릴 카드를 고르고 있습니다.`);
    }

    isCurrentPlayer(playerName) {
        return document.querySelector('.player-bottom .player-name').textContent.includes(playerName);
    }

    handleDiscardAndUpdateBid(data) {
        // 기존 confirm 버튼이 있다면 제거
        const existingConfirmButton = document.querySelector('.confirm-button');
        if (existingConfirmButton) {
            existingConfirmButton.remove();
        }

        // 기존 카드 제거
        const cardsContainer = document.querySelector('.player-bottom .cards-container');
        if (!cardsContainer) {
            console.error('카드 컨테이너를 찾을 수 없습니다');
            return;
        }
        cardsContainer.innerHTML = '';

        // 새로운 카드 추가 
        this.card_to_discard = [];
        data.cards.forEach(card => {
            const cardElement = document.createElement('div');
            cardElement.className = 'card selectable-card';
            cardElement.style.backgroundImage = `url('/static/svg-cards/${this.getCardFileName(card)}')`;
            cardElement.style.backgroundSize = 'cover';
            cardElement.style.backgroundPosition = 'center';
            
            cardElement.addEventListener('click', () => {
                // 이미 선택된 카드가 3개이고 현재 카드가 선택되지 않은 상태면 클릭 무시
                if (this.card_to_discard.length >= 3 && !cardElement.classList.contains('selected-card')) {
                    return;
                }
                
                cardElement.classList.toggle('selected-card');
                if (cardElement.classList.contains('selected-card')) {
                    this.card_to_discard.push(card);
                } else {
                    this.card_to_discard = this.card_to_discard.filter(c => c !== card);
                }
            });
            cardsContainer.appendChild(cardElement);
        });
        console.log('카드 추가 완료:', data.cards.length);

        // Update Bid
        this.current_bid = data.current_bid;
        this.current_bid_suit = data.current_bid_suit;
        
        // 현재 bid보다 2이상 늘리거나 20으로 bid 할 수 있도록 UI 생성
        this.showBidUI();
        
        // 확인 버튼 추가
        const confirmButton = document.createElement('button');
        confirmButton.textContent = '확인';
        confirmButton.className = 'confirm-button';
        confirmButton.addEventListener('click', () => this.confirmDiscardAndUpdateBid());
        document.querySelector('.game-table').appendChild(confirmButton);
    }

    confirmDiscardAndUpdateBid() {
        // 선택된 카드가 3장인지 확인
        if (this.card_to_discard.length !== 3) {
            alert('카드를 정확히 3장 선택해주세요.');
            return;
        }

        // 선택된 카드 3장과 공약 수정 결과를 emit
        console.log('선택된 카드:', this.card_to_discard);
        console.log('공약 수정 결과:', {
            suit: document.querySelector('.suit.selected').dataset.suit,
            score: parseInt(document.querySelector('.score-btn.selected').textContent)
        });
        this.socket.emit('discard_cards_and_update_bid', {
            room_id: ROOM_ID,
            token: this.token,
            cards: this.card_to_discard,
            updated_bid: {
                suit: this.current_bid_suit,
                score: this.current_bid
            }
        });
    }

    showBidUI() {
        // 현재 bid보다 2이상 늘리거나 20으로 bid 할 수 있도록 UI 생성
        // 기존 UI가 있다면 제거
        const existingUI = document.querySelector('.bidding-ui');
        if (existingUI) {
            existingUI.remove();
        }

        // UI 컨테이너 생성
        const biddingUI = document.createElement('div');
        biddingUI.className = 'bidding-ui';

        const biddingBox = document.createElement('div');
        biddingBox.className = 'bidding-box';

        // 제목 추가
        const title = document.createElement('div');
        title.className = 'bidding-title';
        title.textContent = '공약 수정하기';
        biddingBox.appendChild(title);

        // 기루다 선택 UI
        const suitSelection = document.createElement('div');
        suitSelection.className = 'suit-selection';
        
        const suits = ['spade', 'diamond', 'heart', 'club'];
        const suitSymbols = {'spade': '♠', 'diamond': '♦', 'heart': '♥', 'club': '♣'};
        const suitSymbols_inverse = {'♠': 'spade', '♦': 'diamond', '♥': 'heart', '♣': 'club'};
        
        suits.forEach(suit => {
            const suitElement = document.createElement('div');
            suitElement.className = `suit ${suit}`;
            if (suit === suitSymbols_inverse[this.current_bid_suit]) {
                suitElement.classList.add('selected');
            }
            suitElement.textContent = suitSymbols[suit];
            suitElement.onclick = () => {
                document.querySelectorAll('.suit').forEach(el => el.classList.remove('selected'));
                suitElement.classList.add('selected');
                this.current_bid_suit = suit;
            };
            suitSelection.appendChild(suitElement);
        });
        biddingBox.appendChild(suitSelection);

        // 점수 선택 UI
        const scoreSelection = document.createElement('div');
        scoreSelection.className = 'score-selection';
        
        // 현재 bid부터 20까지 모든 버튼 생성
        for (let i = this.current_bid; i <= 20; i++) {
            const scoreBtn = document.createElement('button');
            scoreBtn.className = 'score-btn';
            
            // 현재 선택된 점수와 같다면 selected 클래스 추가
            if (i === this.current_bid) {
                scoreBtn.classList.add('selected');
            }
            
            // 현재 bid보다 2 이상 높지 않은 버튼은 비활성화 (20은 제외)
            if (i < this.current_bid + 2 && i !== 20 && i !== this.current_bid) {
                scoreBtn.classList.add('disabled');
                scoreBtn.disabled = true;
            }
            
            scoreBtn.textContent = i;
            scoreBtn.onclick = () => {
                // 다른 점수 버튼들의 selected 클래스 제거
                document.querySelectorAll('.score-btn').forEach(btn => btn.classList.remove('selected'));
                // 클릭된 버튼에 selected 클래스 추가
                scoreBtn.classList.add('selected');
                this.current_bid = i;   
            };
            scoreSelection.appendChild(scoreBtn);
        }
        
        biddingBox.appendChild(scoreSelection);

        biddingUI.appendChild(biddingBox);
        document.body.appendChild(biddingUI);
    }
    handleEndDiscardAndUpdateBid(data) {
        console.log('[handleEndDiscardAndUpdateBid] 공약 수정 완료');
        // card selectable-card selected-card 클래스 제거
        document.querySelectorAll('.selectable-card.selected-card').forEach(card => {
            card.classList.remove('selected-card');
        });
        // 확인 버튼 제거
        const confirmButton = document.querySelector('.confirm-button');
        if (confirmButton) {
            confirmButton.remove();
        }
        // 공약 수정 UI 제거
        const biddingUI = document.querySelector('.bidding-ui');
        if (biddingUI) {
            biddingUI.remove();
        }

        // 프렌드 선택 UI 표시
        this.showFriendSelectionUI();
    }

    showFriendSelectionUI() {
        const existingUI = document.querySelector('.friend-selection-ui');
        if (existingUI) {
            existingUI.remove();
        }

        const friendSelectionUI = document.createElement('div');
        friendSelectionUI.className = 'friend-selection-ui';
        
        const container = document.createElement('div');
        container.className = 'friend-selection-container';
        
        // 제목 추가
        const title = document.createElement('div');
        title.className = 'friend-selection-title';
        title.textContent = '프렌드를 선택합니다';
        container.appendChild(title);

        // 빠른 선택 버튼들 (마이티, 조커, 노프렌드)
        const quickButtons = document.createElement('div');
        quickButtons.className = 'quick-buttons';

        const mightyBtn = document.createElement('button');
        mightyBtn.className = 'quick-button mighty';
        mightyBtn.textContent = '마이티';
        mightyBtn.onclick = () => this.submitFriend('spade', 14); // 스페이드 A
        quickButtons.appendChild(mightyBtn);

        const jokerBtn = document.createElement('button');
        jokerBtn.className = 'quick-button joker';
        jokerBtn.textContent = '조커';
        jokerBtn.onclick = () => this.submitFriend('joker', 0);
        quickButtons.appendChild(jokerBtn);

        const noFriendBtn = document.createElement('button');
        noFriendBtn.className = 'quick-button no-friend';
        noFriendBtn.textContent = '노프렌드';
        noFriendBtn.onclick = () => this.submitFriend(null, null);
        quickButtons.appendChild(noFriendBtn);

        container.appendChild(quickButtons);

        // 무늬 선택 (라디오 버튼)
        const suitSelection = document.createElement('div');
        suitSelection.className = 'suit-selection';
        
        const suits = [
            { name: 'spade', symbol: '♠', color: 'black' },
            { name: 'diamond', symbol: '♦', color: 'red' },
            { name: 'heart', symbol: '♥', color: 'red' },
            { name: 'club', symbol: '♣', color: 'black' }
        ];

        suits.forEach(suit => {
            const radioInput = document.createElement('input');
            radioInput.type = 'radio';
            radioInput.id = `suit-${suit.name}`;
            radioInput.name = 'suit';
            radioInput.className = 'suit-radio';
            radioInput.value = suit.name;
            
            const label = document.createElement('label');
            label.htmlFor = `suit-${suit.name}`;
            label.className = `suit-label ${suit.name}`;
            label.textContent = suit.symbol;

            suitSelection.appendChild(radioInput);
            suitSelection.appendChild(label);
        });

        container.appendChild(suitSelection);

        // 숫자 선택
        const rankSelection = document.createElement('div');
        rankSelection.className = 'rank-selection';

        const ranks = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
        const rankValues = {A: 14, K: 13, Q: 12, J: 11};

        ranks.forEach(rank => {
            const rankBtn = document.createElement('button');
            rankBtn.className = 'rank-button';
            rankBtn.textContent = rank;
            rankBtn.onclick = () => {
                const selectedSuit = document.querySelector('input[name="suit"]:checked')?.value;
                if (!selectedSuit) {
                    alert('무늬를 먼저 선택해주세요');
                    return;
                }
                const rankValue = rankValues[rank] || parseInt(rank);
                this.submitFriend(selectedSuit, rankValue);
            };
            rankSelection.appendChild(rankBtn);
        });

        container.appendChild(rankSelection);
        friendSelectionUI.appendChild(container);
        document.querySelector('.game-table').appendChild(friendSelectionUI);
    }

    submitFriend(suit, rank) {
        this.socket.emit('submit_friend', {
            room_id: ROOM_ID,
            token: this.token,
            suit: suit,
            rank: rank
        });
    }

    endFriendSelection(data) {
        console.log('[endFriendSelection] 프렌드 선택 완료');
        // 프렌드 선택 UI 제거
        const friendSelectionUI = document.querySelector('.friend-selection-ui');
        if (friendSelectionUI) {
            friendSelectionUI.remove();
        }
        // 현재 공약과 프렌드 정보 함께 표시
        const bidInfoPanel = document.querySelector('.bid-info-panel');
        const currentBid = bidInfoPanel.innerHTML; // 기존 공약 정보 저장
        bidInfoPanel.innerHTML = `${currentBid}<br>현재 프렌드: ${data.suit} ${data.rank}`;

        // 주공 플레이어 이름 파란색으로 표시
        const presidentName = data.president_name;
        // 모든 플레이어 영역에서 주공 찾기
        document.querySelectorAll('.player-name').forEach(nameElement => {
            // "(나)" 텍스트를 제외하고 비교하기 위해 정규식 사용
            const playerName = nameElement.textContent.replace(' (나)', '');
            if (playerName === presidentName) {
                nameElement.style.color = 'blue';
            }
        });
    }

    handleGameStart(data) {
        console.log('[handleGameStart] 게임 시작');
        // bid-info 에 적은 text 제거
        const bidInfo = document.querySelector('.bid-info');
        if (bidInfo) {
            bidInfo.innerHTML = '';
        }

        // 이전에 있던 카드 덱 제거 
        const cardsContainer = document.querySelector('.player-bottom .cards-container');
        if (cardsContainer) {
            cardsContainer.innerHTML = '';
        }

        // 새로운 카드 생성
        if (data.cards && Array.isArray(data.cards)) {
            data.cards.forEach(card => {
                const cardElement = document.createElement('div');
                cardElement.className = 'card';
                const fileName = this.getCardFileName(card);
                cardElement.style.backgroundImage = `url('/static/svg-cards/${fileName}')`;
                cardElement.style.backgroundSize = 'cover';
                cardElement.style.backgroundPosition = 'center';
                
                // data-suit와 data-rank 속성 추가
                cardElement.dataset.suit = card.suit;
                cardElement.dataset.rank = card.rank;
                
                // 카드 클릭 이벤트 추가
                cardElement.addEventListener('click', () => {
                    // 서버에 카드 제출 이벤트 전송
                    this.socket.emit('submit_card', {
                        room_id: ROOM_ID,
                        token: this.token,
                        suit: card.suit,
                        rank: card.rank
                    });
                });
                
                cardsContainer.appendChild(cardElement);
            });
        }
    }

    handleCardSubmitted(data) {
        const playerName = data.player_name;
        const suit = data.suit;
        const rank = data.rank;
        console.log(`[handleCardSubmitted] ${playerName} 카드 제출 완료 - ${suit} ${rank}`);

        // 카드를 낸 플레이어가 본인인 경우에만 카드 덱에서 제거
        if (playerName === this.name) {
            const cardElement = document.querySelector(`.player-bottom .card[data-suit="${suit}"][data-rank="${rank}"]`);
            if (cardElement) {
                //카드가 가운데로 이동
                const centerArea = document.querySelector('.center-area');  
                const cardCopy = cardElement.cloneNode(true);
                centerArea.appendChild(cardCopy);
                cardElement.remove();
            }
        }
        else {
            // 플레이어 이름으로 해당 플레이어의 위치 찾기
            const playerNameElements = document.querySelectorAll('.player-name');
            let playerPosition = null;
            playerNameElements.forEach(nameElement => {
                const elementName = nameElement.textContent.replace(' (나)', '');
                if (elementName === playerName) {
                    playerPosition = nameElement.closest('.player-bottom, .player-right, .player-top-right, .player-top-left, .player-left').className;
                }
            });

            if (playerPosition) {
                console.log("[handleCardSubmitted] 플레이어 위치 찾음:", playerPosition);
                // player-top-left 클래스만 사용하도록 수정
                const positionClass = playerPosition.includes('player-top-left') ? 'player-top-left' :
                                     playerPosition.includes('player-top-right') ? 'player-top-right' :
                                     playerPosition.includes('player-right') ? 'player-right' :
                                     playerPosition.includes('player-left') ? 'player-left' : 'player-bottom';
                                     
                const playerCardContainer = document.querySelector(`.${positionClass} .cards-container`);
                console.log("[handleCardSubmitted] 카드 컨테이너:", playerCardContainer);
                if (playerCardContainer && playerCardContainer.firstChild) {
                    const cardToRemove = playerCardContainer.firstChild;
                    const centerArea = document.querySelector('.center-area');
                    console.log("[handleCardSubmitted] 중앙 영역:", centerArea);
                    const cardCopy = document.createElement('div');
                    cardCopy.className = 'card';
                    cardCopy.dataset.suit = suit;
                    cardCopy.dataset.rank = rank;
                    const cardFileName = this.getCardFileName({suit, rank});
                    console.log("[handleCardSubmitted] 카드 파일명:", cardFileName);
                    cardCopy.style.backgroundImage = `url('/static/svg-cards/${cardFileName}')`;
                    cardCopy.style.backgroundSize = 'cover';
                    cardCopy.style.backgroundPosition = 'center';
                    centerArea.appendChild(cardCopy);
                    cardToRemove.remove();
                    console.log("[handleCardSubmitted] 카드 이동 완료");
                } else {
                    console.log("[handleCardSubmitted] 카드 컨테이너가 비어있거나 존재하지 않음");
                }
            } else {
                console.log("[handleCardSubmitted] 플레이어 위치를 찾을 수 없음");
            }
        }
    }
    handleClearTrick(data) {
        console.log("[handleClearTrick] 플레이어의 카드 제거 완료");
        const winnerName = data.winner_name;
        console.log("[handleClearTrick] 승리 플레이어:", winnerName);

        const centerArea = document.querySelector('.center-area');
        const centerAreaCards = centerArea.querySelectorAll('.card');
        
        const winnerElement = Array.from(document.querySelectorAll('.player-area .player-name')).find(el => el.innerHTML.trim().startsWith(winnerName));
        const obtainedCardsElement = winnerElement.closest('.player-area').querySelector('[class^="obtained-cards"]');


        if (obtainedCardsElement) {
            // centerAreaCards 중 data-rank가 10 이상인 카드를 obainedCardsElement에 추가
            centerAreaCards.forEach(card => {
                console.log(card);
                const rank = parseInt(card.dataset.rank) || 0;
                if (rank >= 10) {
                    const cardClone = card.cloneNode(true);
                    obtainedCardsElement.appendChild(cardClone);
                }
                card.remove();
             });
        }
    }
}