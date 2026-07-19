const MotorResponseGame = (() => {
  let problem = null;
  let hitCount = 0;
  let missCount = 0;
  let responseTimes = [];
  let currentTarget = null;
  let targetTimeout = null;
  let appearTime = null;
  let onComplete = null;
  let remainingTargets = 0;
  let isFinished = false;

  function init(container, problemData, completeCb) {
    problem = problemData;
    hitCount = 0;
    missCount = 0;
    responseTimes = [];
    currentTarget = null;
    isFinished = false;
    remainingTargets = problem.targetCount;
    onComplete = completeCb;
    render(container);
    setTimeout(() => spawnTarget(container), 800);
  }

  function render(container) {
    container.innerHTML = `
      <div class="game-wrap motor-game">
        <div class="game-header">
          <div class="game-title">운동 훈련</div>
          <div class="game-meta">
            <span class="round-badge">남은 타겟 <span id="mtr-remain">${problem.targetCount}</span></span>
            <span class="diff-badge">난이도 ${problem.difficulty}</span>
          </div>
        </div>
        <p class="game-desc">${problem.description}</p>
        <div class="motor-stage" id="mtr-stage">
          <div class="motor-overlay" id="mtr-overlay">
            <div class="motor-ready-text">준비!</div>
          </div>
        </div>
        <div class="motor-stats">
          <div class="mstat">
            <span class="mstat-val" id="mtr-hit">0</span>
            <span class="mstat-label">적중</span>
          </div>
          <div class="mstat mstat-miss">
            <span class="mstat-val" id="mtr-miss">0</span>
            <span class="mstat-label">실패</span>
          </div>
        </div>
      </div>
    `;
  }

  function spawnTarget(container) {
    if (isFinished) return;
    const stage = document.getElementById('mtr-stage');
    const overlay = document.getElementById('mtr-overlay');
    if (overlay) overlay.remove();
    if (!stage) return;
    const old = document.getElementById('mtr-target');
    if (old) old.remove();
    const stageW = stage.offsetWidth  || 340;
    const stageH = stage.offsetHeight || 300;
    const size = problem.targetSize;
    const pad = size / 2 + 10;
    const x = pad + Math.random() * (stageW - pad * 2);
    const y = pad + Math.random() * (stageH - pad * 2);
    const target = document.createElement('div');
    target.id = 'mtr-target';
    target.className = 'motor-target';
    target.style.cssText = `
      width:${size}px; height:${size}px;
      left:${x - size/2}px; top:${y - size/2}px;
    `;
    target.innerHTML = '';
    stage.appendChild(target);
    currentTarget = target;
    appearTime = Date.now();
    target.addEventListener('click', () => handleHit(container));
    target.addEventListener('touchstart', (e) => { e.preventDefault(); handleHit(container); }, {passive:false});
    clearTimeout(targetTimeout);
    targetTimeout = setTimeout(() => {
      if (!isFinished) handleMiss(container);
    }, problem.timeLimit);
  }

  function handleHit(container) {
    if (isFinished || !currentTarget) return;
    const target = currentTarget;
    currentTarget = null;
    clearTimeout(targetTimeout);
    const elapsed = Date.now() - appearTime;
    responseTimes.push(elapsed);
    hitCount++;
    remainingTargets--;
    updateStats();
    target.remove();
    nextOrFinish(container);
  }

  function handleMiss(container) {
    if (isFinished || !currentTarget) return;
    const target = currentTarget;
    currentTarget = null;
    clearTimeout(targetTimeout);
    missCount++;
    remainingTargets--;
    responseTimes.push(problem.timeLimit); 
    updateStats();
    target.remove();
    nextOrFinish(container);
  }

  function nextOrFinish(container) {
    const old = document.getElementById('mtr-target');
    if (old) old.remove();
    if (remainingTargets <= 0) { finishGame(); return; }
    document.getElementById('mtr-remain').textContent = remainingTargets;
    setTimeout(() => spawnTarget(container), 300);
  }

  function updateStats() {
    const hitEl = document.getElementById('mtr-hit');
    const missEl = document.getElementById('mtr-miss');
    if (hitEl) hitEl.textContent = hitCount;
    if (missEl) missEl.textContent = missCount;
  }

  function finishGame() {
    if (isFinished) return;
    isFinished = true;
    clearTimeout(targetTimeout);
    const total = problem.targetCount;
    const accuracy = hitCount / total;
    const avgResponseTime = responseTimes.length > 0
      ? responseTimes.reduce((a,b)=>a+b,0) / responseTimes.length
      : problem.timeLimit;
    const sessionData = {
      accuracy, avgResponseTime,
      correctCount: hitCount,
      totalRounds: total,
      missCount,
      difficulty: problem.difficulty,
    };
    const profile = Storage.getCurrentProfile();
    if (profile) Storage.saveSession(profile.id, 'motor_response', sessionData);
    if (onComplete) onComplete(sessionData);
  }

  return { init };
})();