const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:3000/api' 
    : '/api'; // fallback for relative path

// DOM Elements
const screens = {
    home: document.getElementById('home-screen'),
    join: document.getElementById('join-screen'),
    waiting: document.getElementById('waiting-screen'),
    result: document.getElementById('result-screen')
};

// Home Screen Elements
const btnShowCreate = document.getElementById('btn-show-create');
const btnShowJoin = document.getElementById('btn-show-join');
const createRoomSection = document.getElementById('create-room-section');
const btnCreateRoom = document.getElementById('btn-create-room');
const roomCreatedSection = document.getElementById('room-created-section');
const displayRoomCode = document.getElementById('display-room-code');
const btnEnterMyRoom = document.getElementById('btn-enter-my-room');
const creatorError = document.getElementById('creator-error');
const btnsBackHome = document.querySelectorAll('.btn-back-home');

// Join Screen Elements
const joinRoomCodeInput = document.getElementById('join-room-code');
const btnSubmitPicks = document.getElementById('btn-submit-picks');
const joinError = document.getElementById('join-error');

// State
let currentRoomCode = null;
let currentStudentId = null;
let pollInterval = null;
let myPicks = [];

// Screen Navigation
function showScreen(screenName) {
    Object.values(screens).forEach(screen => {
        screen.classList.remove('active');
        setTimeout(() => {
            if (!screen.classList.contains('active')) {
                screen.classList.add('hidden');
            }
        }, 400); // match css transition
    });

    setTimeout(() => {
        screens[screenName].classList.remove('hidden');
        // trigger reflow
        void screens[screenName].offsetWidth;
        screens[screenName].classList.add('active');
    }, 10);
}

// Initial Load
window.addEventListener('DOMContentLoaded', () => {
    // No URL parsing needed anymore since we use manual room code entry
});

// Show create section
btnShowCreate.addEventListener('click', () => {
    btnShowCreate.classList.add('hidden');
    btnShowJoin.classList.add('hidden');
    createRoomSection.classList.remove('hidden');
});

// Show join section
btnShowJoin.addEventListener('click', () => {
    showScreen('join');
});

// Back to Home
btnsBackHome.forEach(btn => {
    btn.addEventListener('click', () => {
        // Reset home screen state
        createRoomSection.classList.add('hidden');
        roomCreatedSection.classList.add('hidden');
        btnShowCreate.classList.remove('hidden');
        btnShowJoin.classList.remove('hidden');
        showScreen('home');
    });
});

// Create Room
btnCreateRoom.addEventListener('click', async () => {
    const creatorCode = document.getElementById('creator-code').value.trim();
    const maxUsers = document.getElementById('max-users').value.trim();

    creatorError.textContent = '';

    if (!creatorCode) {
        creatorError.textContent = '제작자 코드를 입력해주세요.';
        return;
    }
    if (!maxUsers) {
        creatorError.textContent = '목표 인원수를 입력해주세요.';
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/create-room`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ creatorCode, maxUsers })
        });
        const data = await res.json();

        if (res.ok) {
            currentRoomCode = data.roomCode;
            displayRoomCode.textContent = currentRoomCode;
            
            createRoomSection.classList.add('hidden');
            roomCreatedSection.classList.remove('hidden');
        } else {
            creatorError.textContent = data.error || '방 생성에 실패했습니다.';
        }
    } catch (err) {
        creatorError.textContent = '서버 통신 오류가 발생했습니다.';
    }
});

// Enter my own room
btnEnterMyRoom.addEventListener('click', () => {
    joinRoomCodeInput.value = currentRoomCode;
    showScreen('join');
});

// Submit Picks
btnSubmitPicks.addEventListener('click', async () => {
    const roomCodeInputValue = joinRoomCodeInput.value.trim().toUpperCase();
    const name = document.getElementById('user-name').value.trim();
    const studentId = document.getElementById('user-student-id').value.trim();
    
    myPicks = [
        document.getElementById('pick-1').value.trim(),
        document.getElementById('pick-2').value.trim(),
        document.getElementById('pick-3').value.trim(),
        document.getElementById('pick-4').value.trim(),
        document.getElementById('pick-5').value.trim()
    ];

    joinError.textContent = '';

    if (!roomCodeInputValue) {
        joinError.textContent = '방 코드를 입력해주세요.';
        return;
    }

    if (!name || !studentId) {
        joinError.textContent = '이름과 출석번호를 모두 입력해주세요.';
        return;
    }

    if (myPicks.some(p => p === '')) {
        joinError.textContent = '1위부터 5위까지 모두 입력해주세요.';
        return;
    }

    currentStudentId = studentId;
    currentRoomCode = roomCodeInputValue;

    try {
        const res = await fetch(`${API_BASE}/join-room`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ roomCode: currentRoomCode, name, studentId, picks: myPicks })
        });
        const data = await res.json();

        if (res.ok) {
            showScreen('waiting');
            startPolling();
        } else {
            joinError.textContent = data.error || '참가에 실패했습니다.';
        }
    } catch (err) {
        joinError.textContent = '서버 통신 오류가 발생했습니다.';
    }
});

// Polling for Room Status
function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    
    const checkStatus = async () => {
        try {
            const res = await fetch(`${API_BASE}/room-status/${currentRoomCode}?studentId=${currentStudentId}`);
            const data = await res.json();
            
            if (res.ok) {
                if (data.isReady) {
                    clearInterval(pollInterval);
                    showResults(data.results);
                } else {
                    document.getElementById('wait-status').textContent = `현재 인원: ${data.currentUsers} / ${data.maxUsers}`;
                }
            }
        } catch (err) {
            console.error('Polling error', err);
        }
    };

    checkStatus(); // Initial check
    pollInterval = setInterval(checkStatus, 2000); // Check every 2 seconds
}

// Show Results
function showResults(resultsArray) {
    const resultsContainer = document.getElementById('results-list');
    resultsContainer.innerHTML = '';

    if (!resultsArray) {
        resultsContainer.innerHTML = '<p class="error-text">결과를 불러올 수 없습니다.</p>';
    } else {
        myPicks.forEach((pickId, index) => {
            const rank = resultsArray[index];
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item ' + (rank ? 'success' : 'fail');
            
            const targetHtml = `<span class="target">${index + 1}위로 뽑은 사람 (${pickId}번)</span>`;
            const rankHtml = rank 
                ? `<span class="rank" style="color: #ef4444;">${rank}위 ❤️</span>` 
                : `<span class="rank">순위를 가져올 수 없음</span>`;
            
            resultItem.innerHTML = `${targetHtml}${rankHtml}`;
            resultsContainer.appendChild(resultItem);
        });
    }

    showScreen('result');
}

// Go Home
document.getElementById('btn-go-home').addEventListener('click', () => {
    window.location.href = window.location.pathname; // Remove query params
});
