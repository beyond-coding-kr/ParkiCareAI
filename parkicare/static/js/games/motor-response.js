/**
 * ParkiCare AI - Finger Sequence Tap Game
 * 운동 기능 훈련: 손가락 번호 순서 누르기 미니게임
 */

const MotorResponseGame = (() => {
  let problem = null;
  let targetCount = 3;
  let currentTargetIndex = 1; // 1부터 시작하여 순서대로 터치
  
  let hitCount = 0;
  let missCount = 0;
  let responseTimes = [];
  let appearTime = null;
  let lastClickTime = null;
  let onComplete = null;
  let totalTrials = 3; // 총 3 라운드 시행
  let currentRound = 1;
  let isFinished = false;

  function init(container, problemData, completeCb) {
    problem = problemData;
    targetCount = problem.targetCount || 3;
    hitCount = 0;
    missCount = 0;
    responseTimes = [];
    currentRound = 1;
    isFinished = false;
    onComplete = completeCb;

    render(container);
    startRound(container);
  }

  function render(container) {
    container.innerHTML = `
      <div class="game-wrap motor-game">
        <div class="game-header">
          <div class="game-title">✋ 손가락 순서 누르기</div>
          <div class="game-meta">
            <span class="round-badge">라운드 <span id="mtr-round">1</span> / ${totalTrials}</span>
            <span class="diff-badge">난이도 ${problem.difficulty}단</span>
          </div>
        </div>
        <p class="game-desc">화면에 나타난 번호 원들을 <strong>1 ➔ 2 ➔ 3</strong> 순서대로 차례로 터치하세요.</p>

        <div class="motor-stage" id="mtr-stage" style="position:relative; width:100%; height:300px; border:2px dashed var(--border); border-radius:var(--radius-lg); background:rgba(0,0,0,0.15); overflow:hidden;">
          <div class="motor-overlay" id="mtr-overlay">
            <div class="motor-ready-icon">✋</div>
            <div class="motor-ready-text">준비하세요!</div>
          </div>
        </div>

        <div class="motor-stats" style="display:flex; justify-content:space-around; margin-top:16px; font-size:12px; color:var(--text-secondary);">
          <div>실수(잘못 누름): <strong id="mtr-miss" style="color:var(--accent-red)">0</strong>회</div>
          <div>평균 반응속도: <strong id="mtr-avg">-</strong>초</div>
        </div>
      </div>
    `;
  }

  function startRound(container) {
    const stage = document.getElementById('mtr-stage');
    const overlay = document.getElementById('mtr-overlay');
    if (overlay) overlay.remove();
    if (!stage) return;

    // 이전 원 삭제
    stage.innerHTML = '';
    currentTargetIndex = 1;
    document.getElementById('mtr-round').textContent = currentRound;

    const stageW = stage.offsetWidth || 340;
    const stageH = stage.offsetHeight || 300;
    const size = 56; // 원 크기 고정
    const pad = size + 10;

    // 타겟들이 겹치지 않게 무작위 좌표 생성
    const positions = [];
    for (let i = 1; i <= targetCount; i++) {
      let x, y, overlap;
      let attempts = 0;
      
      do {
        x = pad/2 + Math.random() * (stageW - pad);
        y = pad/2 + Math.random() * (stageH - pad);
        overlap = positions.some(p => {
          const dist = Math.hypot(p.x - x, p.y - y);
          return dist < size + 15; // 다른 원과 최소 거리 유지
        });
        attempts++;
      } while (overlap && attempts < 100);

      positions.push({ id: i, x, y });
    }

    // 화면에 번호 원 렌더링
    positions.forEach(p => {
      const circle = document.createElement('div');
      circle.className = 'motor-target';
      circle.id = `target-num-${p.id}`;
      circle.dataset.num = p.id;
      
      // 원 위치 셋팅
      circle.style.cssText = `
        width:${size}px; height:${size}px;
        left:${p.x - size/2}px; top:${p.y - size/2}px;
        border-radius:50%;
        background:linear-gradient(135deg, #00D4FF, #7B2FBE);
        border:3px solid #fff;
        display:flex; align-items:center; justify-content:center;
        font-size:24px; font-weight:800; color:#fff;
        position:absolute; cursor:pointer;
        box-shadow:0 0 15px rgba(0,212,255,0.4);
        transition:transform 0.2s ease, opacity 0.2s ease;
      `;
      circle.innerHTML = `<span>${p.id}</span>`;

      // 터치/클릭 바인딩
      const pressHandler = (e) => {
        e.preventDefault();
        handleCirclePress(p.id, container);
      };
      
      circle.addEventListener('mousedown', pressHandler);
      circle.addEventListener('touchstart', pressHandler, { passive: false });
      
      stage.appendChild(circle);
    });

    appearTime = Date.now();
    lastClickTime = Date.now();
  }

  function handleCirclePress(num, container) {
    if (isFinished) return;
    const now = Date.now();
    const elapsed = now - lastClickTime;

    if (num === currentTargetIndex) {
      // 올바른 번호 순서 클릭 성공
      responseTimes.push(elapsed);
      lastClickTime = now;
      hitCount++;

      const targetEl = document.getElementById(`target-num-${num}`);
      if (targetEl) {
        // 성공 피드백 (초록색 변화 및 스케일 아웃 효과)
        targetEl.style.background = 'linear-gradient(135deg, #00FF94, #00aa55)';
        targetEl.style.transform = 'scale(1.2)';
        targetEl.style.opacity = '0.5';
        targetEl.style.pointerEvents = 'none';
      }

      currentTargetIndex++;

      // 현재 라운드 번호 원 모두 누름 성공
      if (currentTargetIndex > targetCount) {
        setTimeout(() => {
          if (currentRound < totalTrials) {
            currentRound++;
            startRound(container);
          } else {
            finishGame();
          }
        }, 400);
      }
    } else {
      // 잘못된 번호 클릭 (실수)
      missCount++;
      document.getElementById('mtr-miss').textContent = missCount;
      
      const targetEl = document.getElementById(`target-num-${num}`);
      if (targetEl) {
        // 흔들림 실패 피드백 효과
        targetEl.style.transform = 'scale(0.9)';
        setTimeout(() => {
          targetEl.style.transform = 'scale(1)';
        }, 150);
      }
    }
    
    updateStats();
  }

  function updateStats() {
    const avgEl = document.getElementById('mtr-avg');
    if (avgEl && responseTimes.length > 0) {
      const avg = responseTimes.reduce((a,b)=>a+b,0) / responseTimes.length;
      avgEl.textContent = (avg / 1000).toFixed(2);
    }
  }

  function finishGame() {
    if (isFinished) return;
    isFinished = true;

    // 정확도: 맞춘 개수(라운드수 * 타겟수) / (맞춘 개수 + 실수횟수)
    const expectedHits = totalTrials * targetCount;
    const accuracy = expectedHits / (expectedHits + missCount);
    const avgResponseTime = responseTimes.reduce((a,b)=>a+b,0) / responseTimes.length;

    const sessionData = {
      accuracy: parseFloat(accuracy.toFixed(2)),
      avgResponseTime,
      correctCount: expectedHits,
      totalRounds: totalTrials,
      missCount,
      difficulty: problem.difficulty
    };

    if (onComplete) onComplete(sessionData);
  }

  return { init };
})();
