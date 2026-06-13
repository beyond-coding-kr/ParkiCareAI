/**
 * ParkiCare AI - Attention Stroop Game
 * 집중력 훈련: 색상-텍스트 불일치 스트룹 과제
 */

const AttentionStroopGame = (() => {
  let problem = null;
  let currentProblemIdx = 0;
  let correctCount = 0;
  let responseTimes = [];
  let startTime = null;
  let timerInterval = null;
  let onComplete = null;

  function init(container, problemData, completeCb) {
    problem = problemData;
    currentProblemIdx = 0;
    correctCount = 0;
    responseTimes = [];
    onComplete = completeCb;
    render(container);
    showProblem(container);
  }

  function render(container) {
    container.innerHTML = `
      <div class="game-wrap stroop-game">
        <div class="game-header">
          <div class="game-title">🎯 집중력 훈련</div>
          <div class="game-meta">
            <span class="round-badge">문제 <span id="sg-round">1</span> / ${problem.problems.length}</span>
            <span class="diff-badge">난이도 ${problem.difficulty}</span>
          </div>
        </div>
        <p class="game-desc">글자의 <strong>색상</strong>을 선택하세요 (글자 내용이 아닙니다)</p>

        <div class="stroop-stage" id="sg-stage">
          <div class="stroop-time-bar-wrap">
            <div class="stroop-time-bar" id="sg-time-bar"></div>
          </div>
          <div class="stroop-word-wrap">
            <div class="stroop-word" id="sg-word"></div>
            <div class="stroop-hint">이 글자의 <em>색상</em>은?</div>
          </div>
          <div class="stroop-options" id="sg-options"></div>
        </div>

        <div class="progress-row" id="sg-progress"></div>
      </div>
    `;
    renderProgress(container);
  }

  function renderProgress(container) {
    const prog = document.getElementById('sg-progress');
    if (!prog) return;
    prog.innerHTML = Array.from({length: problem.problems.length}, (_,i) =>
      `<div class="prog-dot" id="sg-prog-${i}"></div>`
    ).join('');
  }

  function showProblem(container) {
    if (currentProblemIdx >= problem.problems.length) { finishGame(); return; }
    const p = problem.problems[currentProblemIdx];
    document.getElementById('sg-round').textContent = currentProblemIdx + 1;

    // 단어 표시
    const wordEl = document.getElementById('sg-word');
    wordEl.textContent = p.text;
    wordEl.style.color = p.textColor;
    wordEl.classList.remove('pop');
    requestAnimationFrame(() => wordEl.classList.add('pop'));

    // 선택지
    const optEl = document.getElementById('sg-options');
    optEl.innerHTML = '';
    p.options.forEach(opt => {
      const btn = document.createElement('button');
      btn.className = 'stroop-opt-btn';
      btn.innerHTML = `
        <span class="color-dot" style="background:${opt.hex}"></span>
        <span>${opt.name}</span>
      `;
      btn.addEventListener('click', () => handleAnswer(opt.name, p, container));
      optEl.appendChild(btn);
    });

    // 타이머
    clearInterval(timerInterval);
    startTime = Date.now();
    const bar = document.getElementById('sg-time-bar');
    bar.style.transition = 'none';
    bar.style.width = '100%';
    bar.style.background = 'linear-gradient(90deg, #00D4FF, #7B2FBE)';
    requestAnimationFrame(() => {
      bar.style.transition = `width ${p.timeLimit}ms linear`;
      bar.style.width = '0%';
    });

    timerInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      if (elapsed >= p.timeLimit) {
        clearInterval(timerInterval);
        handleAnswer(null, p, container); // 시간 초과 → 오답
      }
    }, 100);
  }

  function handleAnswer(selected, p, container) {
    clearInterval(timerInterval);
    const elapsed = Date.now() - startTime;
    responseTimes.push(Math.min(elapsed, p.timeLimit));
    const isCorrect = selected === p.correctAnswer;
    if (isCorrect) correctCount++;

    // 버튼 피드백
    const optEls = document.querySelectorAll('.stroop-opt-btn');
    optEls.forEach(btn => {
      btn.disabled = true;
      const name = btn.querySelector('span:last-child').textContent;
      if (name === p.correctAnswer) btn.classList.add('opt-correct');
      else if (name === selected && !isCorrect) btn.classList.add('opt-wrong');
    });

    // 진행 점 업데이트
    const dot = document.getElementById(`sg-prog-${currentProblemIdx}`);
    if (dot) dot.className = `prog-dot ${isCorrect ? 'correct' : 'wrong'}`;

    currentProblemIdx++;
    setTimeout(() => showProblem(container), 900);
  }

  function finishGame() {
    const accuracy = correctCount / problem.problems.length;
    const avgResponseTime = responseTimes.reduce((a,b)=>a+b,0) / responseTimes.length;
    Storage.updateGlobalStats('attention_stroop', avgResponseTime);
    const sessionData = {
      accuracy, avgResponseTime,
      correctCount,
      totalRounds: problem.problems.length,
      difficulty: problem.difficulty,
    };
    const profile = Storage.getCurrentProfile();
    if (profile) Storage.saveSession(profile.id, 'attention_stroop', sessionData);
    if (onComplete) onComplete(sessionData);
  }

  return { init };
})();
