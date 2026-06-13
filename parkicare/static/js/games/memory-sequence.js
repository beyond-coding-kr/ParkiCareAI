/**
 * ParkiCare AI - Memory Card Match Game
 * 인지력 훈련: 기억 카드 맞추기 미니게임
 */

const MemorySequenceGame = (() => {
  let problem = null;
  let cards = [];
  let flippedCards = [];
  let matchedPairs = 0;
  let totalFlips = 0;
  let clickCount = 0;
  
  let startTime = null;
  let lastClickTime = null;
  let responseTimes = [];
  let onComplete = null;
  let isChecking = false;

  const EMOJIS = ['🧠', '🍏', '🎯', '✋', '🌟', '🍇', '🍒', '🍋', '🥝', '🍉'];

  function init(container, problemData, completeCb) {
    problem = problemData;
    cards = [];
    flippedCards = [];
    matchedPairs = 0;
    totalFlips = 0;
    clickCount = 0;
    responseTimes = [];
    onComplete = completeCb;
    isChecking = false;

    // 카드 목록 구성 (난이도별 카드 개수: 1->4장, 2~3->6장, 4~5->8장)
    const diff = problem.difficulty || 2;
    const numPairs = diff === 1 ? 2 : (diff <= 3 ? 3 : 4);
    const selectedEmojis = EMOJIS.slice(0, numPairs);
    
    // 짝을 지어서 섞음
    const cardPool = [...selectedEmojis, ...selectedEmojis];
    cardPool.sort(() => Math.random() - 0.5);

    cards = cardPool.map((emoji, index) => ({
      id: index,
      emoji: emoji,
      isFlipped: false,
      isMatched: false
    }));

    render(container);
    startDisplayPhase(container);
  }

  function render(container) {
    container.innerHTML = `
      <div class="game-wrap memory-game">
        <div class="game-header">
          <div class="game-title">🧠 기억 카드 맞추기</div>
          <div class="game-meta">
            <span class="diff-badge">난이도 ${problem.difficulty}단</span>
          </div>
        </div>
        <p class="game-desc">제시된 카드들의 위치를 기억하고, 똑같은 카드 짝을 맞춰 뒤집으세요.</p>

        <div class="memory-stage">
          <!-- 대기 및 안내 화면 -->
          <div id="mg-ready" class="mg-ready">
            <div class="ready-icon">🧠</div>
            <div class="ready-text">기억하세요!</div>
            <div class="ready-sub">카드가 곧 앞면으로 공개됩니다.</div>
          </div>

          <!-- 카드 게임판 영역 -->
          <div id="mg-board" class="mg-board hidden" style="display:grid; grid-template-columns: repeat(${cards.length <= 4 ? 2 : 3}, 1fr); gap:12px; width:100%; max-width:320px; margin:0 auto;">
            ${cards.map(c => `
              <div class="card-item" data-id="${c.id}" id="card-${c.id}" style="aspect-ratio:1; background:var(--bg-card); border:2px solid var(--border); border-radius:var(--radius-md); display:flex; align-items:center; justify-content:center; font-size:32px; cursor:pointer; position:relative; transform-style:preserve-3d; transition:transform 0.4s cubic-bezier(0.4, 0, 0.2, 1); user-select:none;">
                <div class="card-face card-back" style="position:absolute; width:100%; height:100%; backface-visibility:hidden; display:flex; align-items:center; justify-content:center; border-radius:inherit; background:linear-gradient(135deg, #0d162d, #1a2f5a); color:var(--accent-cyan);">❓</div>
                <div class="card-face card-front" style="position:absolute; width:100%; height:100%; backface-visibility:hidden; display:flex; align-items:center; justify-content:center; border-radius:inherit; transform:rotateY(180deg); background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12)">${c.emoji}</div>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="progress-row" style="margin-top:20px;font-size:12px;color:var(--text-secondary);justify-content:center;display:flex;gap:16px;">
          <span>시도 횟수: <strong id="flip-count-display" style="color:var(--accent-cyan)">0</strong></span>
          <span>맞춘 쌍: <strong id="match-count-display" style="color:var(--accent-green)">0</strong> / ${cards.length / 2}</span>
        </div>
      </div>
    `;

    // 카드 뒤집기 클릭 바인딩
    container.querySelectorAll('.card-item').forEach(el => {
      el.addEventListener('click', () => handleCardClick(parseInt(el.dataset.id), container));
    });
  }

  // 카드 앞면 미리보기 단계 (암기 단계)
  function startDisplayPhase(container) {
    const readyEl = document.getElementById('mg-ready');
    const boardEl = document.getElementById('mg-board');
    
    // 카드가 곧 공개된다는 신호 후 앞면 공개
    setTimeout(() => {
      readyEl.classList.add('hidden');
      boardEl.classList.remove('hidden');

      // 모든 카드 앞면 노출
      cards.forEach(c => {
        const el = document.getElementById(`card-${c.id}`);
        if (el) el.style.transform = 'rotateY(180deg)';
      });

      // 암기 시간 (난이도 높을수록 짧음: 난이도 1->4초, 5->1.8초)
      const memorizeTime = Math.max(1800, 4500 - (problem.difficulty * 600));

      setTimeout(() => {
        // 다시 뒷면으로 뒤집고 실제 입력 훈련 시작
        cards.forEach(c => {
          const el = document.getElementById(`card-${c.id}`);
          if (el) el.style.transform = 'rotateY(0deg)';
        });
        
        startTime = Date.now();
        lastClickTime = Date.now();
      }, memorizeTime);
    }, 1200);
  }

  function handleCardClick(id, container) {
    if (isChecking) return;
    const card = cards.find(c => c.id === id);
    if (card.isFlipped || card.isMatched) return;

    // 시간 측정
    const now = Date.now();
    const elapsed = now - lastClickTime;
    responseTimes.push(elapsed);
    lastClickTime = now;

    // 카드 뒤집기 효과
    const cardEl = document.getElementById(`card-${id}`);
    cardEl.style.transform = 'rotateY(180deg)';
    card.isFlipped = true;
    flippedCards.push(card);

    if (flippedCards.length === 2) {
      isChecking = true;
      totalFlips++;
      document.getElementById('flip-count-display').textContent = totalFlips;
      
      const [card1, card2] = flippedCards;
      
      if (card1.emoji === card2.emoji) {
        // 카드 일치 성공
        card1.isMatched = true;
        card2.isMatched = true;
        matchedPairs++;
        document.getElementById('match-count-display').textContent = matchedPairs;
        
        // 성공 이펙트
        const el1 = document.getElementById(`card-${card1.id}`);
        const el2 = document.getElementById(`card-${card2.id}`);
        setTimeout(() => {
          el1.style.borderColor = 'var(--accent-green)';
          el2.style.borderColor = 'var(--accent-green)';
          flippedCards = [];
          isChecking = false;
          
          // 모든 카드를 다 맞춘 경우 종료
          if (matchedPairs === cards.length / 2) {
            finishGame();
          }
        }, 300);
      } else {
        // 카드 불일치 실패
        setTimeout(() => {
          const el1 = document.getElementById(`card-${card1.id}`);
          const el2 = document.getElementById(`card-${card2.id}`);
          el1.style.transform = 'rotateY(0deg)';
          el2.style.transform = 'rotateY(0deg)';
          card1.isFlipped = false;
          card2.isFlipped = false;
          flippedCards = [];
          isChecking = false;
        }, 900);
      }
    }
  }

  function finishGame() {
    // 최종 정확도 = 짝 개수 / 총 시도 횟수 (최대 1.0)
    // 최소 시도 횟수는 짝 개수와 같으므로, 정확도 = 짝개수 / totalFlips
    const pairs = cards.length / 2;
    const accuracy = parseFloat((pairs / totalFlips).toFixed(2));
    
    // 평균 반응 속도 연산
    const avgResponseTime = responseTimes.reduce((a,b) => a+b, 0) / responseTimes.length;

    const sessionData = {
      accuracy: accuracy > 1 ? 1.0 : accuracy,
      avgResponseTime,
      correctCount: pairs,
      totalRounds: totalFlips, // 총 플립한 시도 수
      difficulty: problem.difficulty,
      missCount: totalFlips - pairs // 틀린 시도 횟수
    };

    if (onComplete) onComplete(sessionData);
  }

  return { init };
})();
