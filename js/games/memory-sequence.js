/**
 * ParkiCare AI - Memory Sequence Game
 * 기억력 훈련: 숫자 순서 기억 미니게임
 */

const MemorySequenceGame = (() => {
  let problem = null;
  let userInput = [];
  let startTime = null;
  let responseTimes = [];
  let correctCount = 0;
  let totalRounds = 3;
  let currentRound = 0;
  let onComplete = null;
  let showPhase = false; // true: 숫자 표시 중

  function init(container, problemData, completeCb) {
    problem = problemData;
    userInput = [];
    responseTimes = [];
    correctCount = 0;
    currentRound = 0;
    onComplete = completeCb;
    render(container);
    startRound(container);
  }

  function render(container) {
    container.innerHTML = `
      <div class="game-wrap memory-game">
        <div class="game-header">
          <div class="game-title">🧠 기억력 훈련</div>
          <div class="game-meta">
            <span class="round-badge">라운드 <span id="mg-round">1</span> / ${totalRounds}</span>
            <span class="diff-badge">난이도 ${problem.difficulty}</span>
          </div>
        </div>
        <p class="game-desc">${problem.description}</p>

        <div class="memory-stage">
          <!-- 숫자 표시 영역 -->
          <div id="mg-display" class="mg-display hidden">
            <div class="mg-nums" id="mg-nums"></div>
            <div class="mg-timer-bar-wrap"><div class="mg-timer-bar" id="mg-timer-bar"></div></div>
          </div>

          <!-- 입력 영역 -->
          <div id="mg-input-area" class="mg-input-area hidden">
            <p class="input-hint">기억한 숫자를 순서대로 입력하세요</p>
            <div class="mg-entered" id="mg-entered"></div>
            <div class="mg-keypad">
              ${[1,2,3,4,5,6,7,8,9,'←',0,'✓'].map(k => `
                <button class="keypad-btn ${typeof k==='string'&&k!=='✓'?'keypad-del':typeof k==='string'?'keypad-ok':''}"
                  data-key="${k}" id="kp-${k}">${k}</button>
              `).join('')}
            </div>
          </div>

          <!-- 결과 표시 -->
          <div id="mg-result" class="mg-result hidden"></div>

          <!-- 대기 화면 -->
          <div id="mg-ready" class="mg-ready">
            <div class="ready-icon">🧠</div>
            <div class="ready-text">준비하세요!</div>
            <div class="ready-sub">숫자가 곧 표시됩니다</div>
          </div>
        </div>

        <div class="progress-row">
          ${Array.from({length: totalRounds}, (_,i) => `
            <div class="prog-dot" id="prog-${i}"></div>
          `).join('')}
        </div>
      </div>
    `;

    // 키패드 이벤트
    container.querySelectorAll('.keypad-btn').forEach(btn => {
      btn.addEventListener('click', () => handleKeypad(btn.dataset.key, container));
    });
  }

  function startRound(container) {
    currentRound++;
    userInput = [];
    showPhase = true;
    document.getElementById('mg-round').textContent = currentRound;

    // 새 문제 생성 (라운드마다 새 숫자)
    const len = problem.sequence.length;
    problem.sequence = Array.from({length: len}, () => Math.floor(Math.random()*9)+1);

    // 준비 화면 → 숫자 표시
    showEl('mg-ready'); hideEl('mg-display'); hideEl('mg-input-area'); hideEl('mg-result');
    setTimeout(() => {
      hideEl('mg-ready'); showEl('mg-display');
      const numsEl = document.getElementById('mg-nums');
      numsEl.innerHTML = problem.sequence.map(n =>
        `<span class="mg-num">${n}</span>`
      ).join('');

      // 타이머 바 애니메이션
      const bar = document.getElementById('mg-timer-bar');
      bar.style.transition = 'none';
      bar.style.width = '100%';
      requestAnimationFrame(() => {
        bar.style.transition = `width ${problem.displayTime}ms linear`;
        bar.style.width = '0%';
      });

      // 표시 시간 후 입력 화면으로
      setTimeout(() => {
        showPhase = false;
        hideEl('mg-display');
        showEl('mg-input-area');
        updateEntered();
        startTime = Date.now();
      }, problem.displayTime);
    }, 900);
  }

  function handleKeypad(key, container) {
    if (showPhase) return;
    if (key === '←') {
      userInput.pop();
    } else if (key === '✓') {
      submitAnswer(container);
      return;
    } else if (userInput.length < problem.sequence.length) {
      userInput.push(parseInt(key));
      if (userInput.length === problem.sequence.length) submitAnswer(container);
    }
    updateEntered();
  }

  function updateEntered() {
    const el = document.getElementById('mg-entered');
    if (!el) return;
    const len = problem.sequence.length;
    let html = '';
    for (let i = 0; i < len; i++) {
      html += `<div class="entered-slot ${i < userInput.length ? 'filled' : ''}">
        ${i < userInput.length ? userInput[i] : ''}
      </div>`;
    }
    el.innerHTML = html;
  }

  function submitAnswer(container) {
    const elapsed = Date.now() - startTime;
    responseTimes.push(elapsed);
    const isCorrect = userInput.length === problem.sequence.length &&
      userInput.every((v, i) => v === problem.sequence[i]);
    if (isCorrect) correctCount++;

    // 결과 표시
    hideEl('mg-input-area');
    showEl('mg-result');
    const resultEl = document.getElementById('mg-result');
    resultEl.innerHTML = `
      <div class="result-icon ${isCorrect ? 'correct' : 'wrong'}">${isCorrect ? '✓' : '✗'}</div>
      <div class="result-text">${isCorrect ? '정답!' : '오답'}</div>
      <div class="result-answer">
        정답: <strong>${problem.sequence.join(' → ')}</strong><br>
        입력: <strong>${userInput.join(' → ') || '-'}</strong>
      </div>
    `;
    resultEl.classList.add('show');

    // 진행 점 업데이트
    const dot = document.getElementById(`prog-${currentRound-1}`);
    if (dot) dot.className = `prog-dot ${isCorrect ? 'correct' : 'wrong'}`;

    // 다음 라운드 or 완료
    setTimeout(() => {
      if (currentRound < totalRounds) {
        resultEl.classList.remove('show');
        startRound(container);
      } else {
        finishGame();
      }
    }, 1800);
  }

  function finishGame() {
    const accuracy = correctCount / totalRounds;
    const avgResponseTime = responseTimes.reduce((a,b)=>a+b,0) / responseTimes.length;
    Storage.updateGlobalStats('memory_sequence', avgResponseTime);
    const sessionData = {
      accuracy, avgResponseTime,
      correctCount, totalRounds,
      difficulty: problem.difficulty,
    };
    const profile = Storage.getCurrentProfile();
    if (profile) Storage.saveSession(profile.id, 'memory_sequence', sessionData);
    if (onComplete) onComplete(sessionData);
  }

  function showEl(id) { const e = document.getElementById(id); if(e) e.classList.remove('hidden'); }
  function hideEl(id) { const e = document.getElementById(id); if(e) e.classList.add('hidden'); }

  return { init };
})();
