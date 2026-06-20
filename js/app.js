const App = (() => {
  let currentScreen = 'home';
  let currentGameType = null;

  const GAME_INFO = {
    memory_sequence: {
      id: 'memory_sequence', label: '기억력 훈련', desc: '숫자 배열을 기억하고 순서대로 입력',
      color: '#00D4FF',
    },
    attention_stroop: {
      id: 'attention_stroop', label: '집중력 훈련', desc: '글자 색상을 빠르게 판별',
      color: '#7B2FBE',
    },
    motor_response: {
      id: 'motor_response', label: '운동 훈련', desc: '나타나는 타겟을 신속하게 터치',
      color: '#00FF94',
    },
  };

  function init() {
    document.addEventListener('DOMContentLoaded', () => {
      navigateTo('home');
    });
  }

  function navigateTo(screen, params = {}) {
    currentScreen = screen;
    const root = document.getElementById('app-root');
    root.style.opacity = '0';
    root.style.transform = 'translateY(12px)';
    setTimeout(() => {
      renderScreen(screen, params, root);
      root.style.opacity = '1';
      root.style.transform = 'translateY(0)';
    }, 180);
  }

  function renderScreen(screen, params, root) {
    switch (screen) {
      case 'home':       renderHome(root); break;
      case 'profile-create': renderProfileCreate(root, params); break;
      case 'hub':        renderHub(root); break;
      case 'game':       renderGame(root, params); break;
      case 'result':     renderResult(root, params); break;
      case 'dashboard':  renderDashboard(root); break;
      case 'report':     renderReport(root); break;
      default:           renderHome(root);
    }
  }

  function renderHome(root) {
    const profiles = Storage.getProfiles();
    const current = Storage.getCurrentProfile();
    root.innerHTML = `
      <div class="screen home-screen">
        <div class="home-hero">
          <div class="logo-wrap">
            <div>
              <h1 class="logo-title">ParkiCare AI</h1>
              <p class="logo-sub">파킨슨병 맞춤형 인지·운동 케어 시스템</p>
            </div>
          </div>
          <div class="hero-badge">AI 기반 개인화 트레이닝</div>
        </div>
        ${profiles.length === 0 ? `
          <div class="empty-state">
            <p>등록된 환자 프로필이 없습니다</p>
            <button class="btn btn-primary" id="btn-create-first">새 프로필 만들기</button>
          </div>
        ` : `
          <div class="section-title">환자 프로필 선택</div>
          <div class="profile-list" id="profile-list">
            ${profiles.map(p => profileCard(p, current?.id === p.id)).join('')}
          </div>
          <button class="btn btn-outline mt-2" id="btn-add-profile">+ 프로필 추가</button>
        `}
        <div class="home-features">
          <div class="feature-item"><span>AI 취약 영역 분석</span></div>
          <div class="feature-item"><span>미니게임 형식 훈련</span></div>
          <div class="feature-item"><span>맞춤형 리포트</span></div>
        </div>
      </div>
    `;
    document.getElementById('btn-create-first')?.addEventListener('click', () => navigateTo('profile-create'));
    document.getElementById('btn-add-profile')?.addEventListener('click', () => navigateTo('profile-create'));
    document.querySelectorAll('.profile-card').forEach(card => {
      card.addEventListener('click', () => {
        const id = card.dataset.id;
        Storage.setCurrentProfile(id);
        navigateTo('hub');
      });
    });
    document.querySelectorAll('.profile-delete-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm('프로필을 삭제하시겠습니까?')) {
          Storage.deleteProfile(btn.dataset.id);
          navigateTo('home');
        }
      });
    });
  }

  function profileCard(p, isActive) {
    const weakProfile = Storage.getWeakProfile(p.id);
    const score = weakProfile?.overallScore ?? null;
    const grade = score !== null ? AIAnalyzer.getGrade(score) : null;
    return `
      <div class="profile-card ${isActive ? 'active' : ''}" data-id="${p.id}">
        <div class="profile-avatar" style="background:#4a90e2">${p.name[0]}</div>
        <div class="profile-info">
          <div class="profile-name">${p.name}</div>
          <div class="profile-meta">${p.age}세</div>
        </div>
        <div class="profile-score">
          ${score !== null ? `<span style="color:${grade.color}">${score}</span>` : '<span class="score-none">미분석</span>'}
        </div>
        <button class="profile-delete-btn" data-id="${p.id}" title="삭제">×</button>
      </div>
    `;
  }

  const AVATAR_COLORS = [
    '#00D4FF','#7B2FBE','#00FF94','#FF6B6B','#FFB800','#FF69B4',
  ];

  function renderProfileCreate(root, params) {
    root.innerHTML = `
      <div class="screen profile-screen">
        <button class="back-btn" id="btn-back">← 돌아가기</button>
        <h2 class="screen-title">새 프로필 만들기</h2>
        <form class="profile-form" id="profile-form">
          <div class="form-group">
            <label>이름</label>
            <input type="text" id="f-name" placeholder="환자 이름" maxlength="20" required>
          </div>
          <div class="form-group">
            <label>나이</label>
            <input type="number" id="f-age" placeholder="나이" min="3" max="100" required>
          </div>
          <button type="submit" class="btn btn-primary">프로필 생성</button>
        </form>
      </div>
    `;
    document.getElementById('btn-back').addEventListener('click', () => navigateTo('home'));
    document.getElementById('profile-form').addEventListener('submit', (e) => {
      e.preventDefault();
      const name = document.getElementById('f-name').value.trim();
      const age = parseInt(document.getElementById('f-age').value);
      if (!name || !age) return;
      const profile = {
        name,
        age
      };
      const response = Storage.saveProfile(profile);
      if (response && response.id) {
        Storage.setCurrentProfile(response.id);
        navigateTo('hub');
      } else {
        showToast('프로필 생성 실패');
      }
    });
  }

  function renderHub(root) {
    const profile = Storage.getCurrentProfile();
    if (!profile) { navigateTo('home'); return; }
    const weakProfile = Storage.getWeakProfile(profile.id);
    const grade = weakProfile?.overallScore != null ? AIAnalyzer.getGrade(weakProfile.overallScore) : null;
    root.innerHTML = `
      <div class="screen hub-screen">
        <div class="hub-header">
          <button class="back-btn" id="btn-back">← 홈</button>
          <div class="hub-profile">
            <div class="hub-avatar" style="background:#4a90e2">${profile.name[0]}</div>
            <div>
              <div class="hub-name">${profile.name}</div>
            </div>
          </div>
          <button class="icon-btn" id="btn-dashboard" title="AI 대시보드">대시보드</button>
        </div>
        ${grade ? `
          <div class="overall-card" style="--accent:${grade.color}">
            <div class="overall-label">종합 점수</div>
            <div class="overall-score" style="color:${grade.color}">${weakProfile.overallScore}</div>
            <div class="overall-grade">${grade.label}</div>
          </div>
        ` : `
          <div class="info-banner">
            각 훈련을 3회 이상 수행하면 AI 분석이 시작됩니다
          </div>
        `}
        <div class="section-title">오늘의 훈련</div>
        <div class="game-cards">
          ${Object.values(GAME_INFO).map(g => gameCard(g, weakProfile, profile.id)).join('')}
        </div>
        <div class="hub-actions">
          <button class="btn btn-outline" id="btn-report">리포트 보기</button>
          <button class="btn btn-ai" id="btn-analyze">AI 분석 실행</button>
        </div>
      </div>
    `;
    document.getElementById('btn-back').addEventListener('click', () => navigateTo('home'));
    document.getElementById('btn-dashboard').addEventListener('click', () => navigateTo('dashboard'));
    document.getElementById('btn-report').addEventListener('click', () => navigateTo('report'));
    document.getElementById('btn-analyze').addEventListener('click', () => runAnalysis(profile.id));
    document.querySelectorAll('.game-card').forEach(card => {
      card.addEventListener('click', () => {
        const gameType = card.dataset.game;
        navigateTo('game', { gameType });
      });
    });
  }

  function gameCard(gameInfo, weakProfile, profileId) {
    const game = weakProfile?.games?.[gameInfo.id];
    const isWeak = game?.isWeak ?? false;
    const sessionCount = Storage.getSessions(profileId, gameInfo.id).length;
    return `
      <div class="game-card ${isWeak ? 'game-card-weak' : ''}" data-game="${gameInfo.id}">
        <div class="gc-accent" style="background:${gameInfo.color}"></div>
        <div class="gc-info">
          <div class="gc-title">${gameInfo.label}</div>
          <div class="gc-desc">${gameInfo.desc}</div>
          <div class="gc-meta">
            <span class="session-count">${sessionCount}회 수행</span>
            ${isWeak ? '<span class="weak-badge">집중 필요</span>' : ''}
          </div>
        </div>
        <div class="gc-arrow">→</div>
      </div>
    `;
  }

  function runAnalysis(profileId) {
    const btn = document.getElementById('btn-analyze');
    if (btn) { btn.textContent = '⏳ 분석 중...'; btn.disabled = true; }
    setTimeout(() => {
      const result = AIAnalyzer.analyze(profileId);
      if (result) {
        showToast(`분석 완료! 종합 점수: ${result.overallScore}점`);
        navigateTo('dashboard');
      } else {
        showToast('분석 실패 (각 훈련을 최소 1회 이상 수행해야 합니다)');
        navigateTo('hub');
      }
    }, 1200);
  }

  function renderGame(root, { gameType }) {
    currentGameType = gameType;
    const profile = Storage.getCurrentProfile();
    if (!profile) { navigateTo('hub'); return; }
    root.innerHTML = `
      <div class="screen game-screen">
        <button class="back-btn" id="btn-back">← 허브</button>
        <div id="game-container" class="game-container"></div>
      </div>
    `;
    document.getElementById('btn-back').addEventListener('click', () => navigateTo('hub'));
    const weakProfile = Storage.getWeakProfile(profile.id);
    const problem = weakProfile
      ? ProblemGenerator.generateForProfile(weakProfile, gameType)
      : ProblemGenerator.generateDefault(gameType);
    const container = document.getElementById('game-container');
    const onComplete = (sessionData) => {
      setTimeout(() => navigateTo('result', { gameType, sessionData }), 600);
    };
    switch (gameType) {
      case 'memory_sequence':  MemorySequenceGame.init(container, problem, onComplete); break;
      case 'attention_stroop': AttentionStroopGame.init(container, problem, onComplete); break;
      case 'motor_response':   MotorResponseGame.init(container, problem, onComplete); break;
    }
  }

  function renderResult(root, { gameType, sessionData }) {
    const { accuracy, avgResponseTime, correctCount, totalRounds } = sessionData;
    const pct = Math.round(accuracy * 100);
    const grade = AIAnalyzer.getGrade(pct);
    const GAME_LABELS = { memory_sequence:'기억력 훈련', attention_stroop:'집중력 훈련', motor_response:'운동 훈련' };
    root.innerHTML = `
      <div class="screen result-screen">
        <div class="result-hero">
          <h2 class="result-title">${GAME_LABELS[gameType]} 완료!</h2>
          <div class="result-score-ring">
            <svg viewBox="0 0 120 120" class="ring-svg">
              <circle cx="60" cy="60" r="50" fill="none" stroke="#1a1f35" stroke-width="10"/>
              <circle cx="60" cy="60" r="50" fill="none" stroke="${grade.color}" stroke-width="10"
                stroke-dasharray="${2*Math.PI*50}" stroke-dashoffset="${2*Math.PI*50*(1-pct/100)}"
                stroke-linecap="round" transform="rotate(-90 60 60)" class="ring-progress"/>
            </svg>
            <div class="ring-inner">
              <div class="ring-pct" style="color:${grade.color}">${pct}%</div>
              <div class="ring-label">${grade.label}</div>
            </div>
          </div>
        </div>
        <div class="result-stats">
          <div class="rstat">
            <div class="rstat-val">${correctCount}/${totalRounds}</div>
            <div class="rstat-label">정답</div>
          </div>
          <div class="rstat">
            <div class="rstat-val">${Math.round(avgResponseTime)}ms</div>
            <div class="rstat-label">평균 반응</div>
          </div>
          <div class="rstat">
            <div class="rstat-val">${sessionData.difficulty}</div>
            <div class="rstat-label">난이도</div>
          </div>
        </div>
        <div class="result-message ${pct >= 70 ? 'msg-good' : 'msg-warn'}">
          ${pct >= 90 ? '완벽합니다! 탁월한 수행 능력이에요.' :
            pct >= 70 ? '잘 하셨어요! 꾸준히 유지하세요.' :
            '조금 더 노력해봐요. AI가 맞춤 문제를 준비했어요!'}
        </div>
        <div class="result-actions">
          <button class="btn btn-outline" id="btn-retry">다시 하기</button>
          <button class="btn btn-primary" id="btn-hub">허브로 돌아가기</button>
        </div>
      </div>
    `;
    setTimeout(() => {
      document.querySelector('.ring-progress')?.classList.add('animated');
    }, 100);
    document.getElementById('btn-retry').addEventListener('click', () => navigateTo('game', { gameType }));
    document.getElementById('btn-hub').addEventListener('click', () => navigateTo('hub'));
  }

  function renderDashboard(root) {
    const profile = Storage.getCurrentProfile();
    if (!profile) { navigateTo('home'); return; }
    const weakProfile = Storage.getWeakProfile(profile.id) || AIAnalyzer.analyze(profile.id);
    const GAME_LABELS = { memory_sequence:'기억력', attention_stroop:'집중력', motor_response:'운동' };
    const GAME_COLORS = { memory_sequence:'#00D4FF', attention_stroop:'#7B2FBE', motor_response:'#00FF94' };
    root.innerHTML = `
      <div class="screen dashboard-screen">
        <div class="dash-header">
          <button class="back-btn" id="btn-back">← 허브</button>
          <h2 class="screen-title">AI 분석 대시보드</h2>
        </div>
        <div class="dash-overall">
          <div class="dash-score">
            <div class="dash-score-val" style="color:${weakProfile.overallScore > 0 ? AIAnalyzer.getGrade(weakProfile.overallScore).color : '#888'}">${weakProfile.overallScore || '-'}</div>
            <div class="dash-score-label">종합 점수</div>
          </div>
          <div class="dash-meta">
            <div>분석: ${new Date(weakProfile.analyzedAt||Date.now()).toLocaleDateString('ko-KR')}</div>
            <div class="weak-summary">
              ${weakProfile.weakAreas?.length > 0
                ? `집중 훈련 필요: ${weakProfile.weakAreas.map(a=>GAME_LABELS[a]).join(', ')}`
                : '모든 영역 양호'}
            </div>
          </div>
        </div>
        <div class="dash-card">
          <div class="card-title">영역별 수행 능력</div>
          <div class="radar-wrap">
            <canvas id="radarChart" width="280" height="280"></canvas>
          </div>
        </div>
        <div class="dash-card">
          <div class="card-title">게임별 상세 분석</div>
          <div class="game-details">
            ${AIAnalyzer.GAME_TYPES.map(gameType => {
              const g = weakProfile.games?.[gameType];
              if (!g) return '';
              const pct = g.accuracy !== null ? Math.round(g.accuracy * 100) : null;
              const grade = pct !== null ? AIAnalyzer.getGrade(pct) : null;
              return `
                <div class="gd-item ${g.isWeak ? 'gd-weak' : ''}">
                  <div class="gd-body">
                    <div class="gd-title">${GAME_LABELS[gameType]}</div>
                    <div class="gd-bar-wrap">
                      <div class="gd-bar" style="width:${pct || 0}%; background:${GAME_COLORS[gameType]}"></div>
                    </div>
                    <div class="gd-stats">
                      ${pct !== null ? `<span style="color:${grade.color}">${pct}%</span>` : '<span>데이터 부족</span>'}
                      <span>${g.sessionCount}회 수행</span>
                      <span>난이도 ${g.difficulty}</span>
                    </div>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
        ${weakProfile.recommendations?.length > 0 ? `
          <div class="dash-card">
            <div class="card-title">AI 추천</div>
            ${weakProfile.recommendations.map(r => `
              <div class="rec-item rec-${r.priority}">
                <div class="rec-dot"></div>
                <div>${r.message}</div>
              </div>
            `).join('')}
          </div>
        ` : ''}
        <button class="btn btn-primary mt-2" id="btn-train">맞춤 훈련 시작</button>
      </div>
    `;
    document.getElementById('btn-back').addEventListener('click', () => navigateTo('hub'));
    document.getElementById('btn-train').addEventListener('click', () => {
      let targetGame = 'memory_sequence';
      if (weakProfile.weakAreas && weakProfile.weakAreas.length > 0) {
        targetGame = weakProfile.weakAreas[0];
      }
      navigateTo('game', { gameType: targetGame });
    });
    drawRadarChart(weakProfile);
  }

  function drawRadarChart(weakProfile) {
    const canvas = document.getElementById('radarChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const cx = W / 2, cy = H / 2, r = Math.min(W, H) / 2 - 30;
    const labels = ['기억력', '집중력', '운동'];
    const keys = ['memory_sequence', 'attention_stroop', 'motor_response'];
    const values = keys.map(k => {
      const g = weakProfile.games?.[k];
      return g?.accuracy !== null && g?.accuracy != null ? g.accuracy * 100 : 0;
    });
    const angles = labels.map((_, i) => (Math.PI * 2 * i / labels.length) - Math.PI / 2);
    ctx.clearRect(0, 0, W, H);
    [100, 75, 50, 25].forEach(pct => {
      ctx.beginPath();
      angles.forEach((a, i) => {
        const x = cx + r * (pct/100) * Math.cos(a);
        const y = cy + r * (pct/100) * Math.sin(a);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.strokeStyle = 'rgba(255,255,255,0.08)';
      ctx.lineWidth = 1;
      ctx.stroke();
      const yLabel = cy - r * (pct / 100);
      ctx.fillStyle = 'rgba(200,214,240,0.5)';
      ctx.font = '10px Outfit';
      ctx.textAlign = 'right';
      ctx.fillText(pct + '%', cx - 6, yLabel + 4);
    });
    angles.forEach(a => {
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + r * Math.cos(a), cy + r * Math.sin(a));
      ctx.strokeStyle = 'rgba(255,255,255,0.12)';
      ctx.stroke();
    });
    ctx.beginPath();
    angles.forEach((a, i) => {
      const x = cx + r * (values[i]/100) * Math.cos(a);
      const y = cy + r * (values[i]/100) * Math.sin(a);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.fillStyle = 'rgba(0,212,255,0.20)';
    ctx.fill();
    ctx.strokeStyle = '#00D4FF';
    ctx.lineWidth = 2;
    ctx.stroke();
    angles.forEach((a, i) => {
      const x = cx + r * (values[i]/100) * Math.cos(a);
      const y = cy + r * (values[i]/100) * Math.sin(a);
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, Math.PI*2);
      ctx.fillStyle = '#00D4FF';
      ctx.fill();
    });
    ctx.font = 'bold 13px Outfit, sans-serif';
    ctx.fillStyle = '#c8d6f0';
    ctx.textAlign = 'center';
    angles.forEach((a, i) => {
      const labelR = r + 22;
      const x = cx + labelR * Math.cos(a);
      const y = cy + labelR * Math.sin(a) + 5;
      ctx.fillText(labels[i], x, y);
    });
  }

  function renderReport(root) {
    const profile = Storage.getCurrentProfile();
    if (!profile) { navigateTo('home'); return; }
    const GAME_LABELS = { memory_sequence:'기억력 훈련', attention_stroop:'집중력 훈련', motor_response:'운동 훈련' };
    const GAME_COLORS = { memory_sequence:'#00D4FF', attention_stroop:'#7B2FBE', motor_response:'#00FF94' };
    root.innerHTML = `
      <div class="screen report-screen">
        <button class="back-btn" id="btn-back">← 허브</button>
        <h2 class="screen-title">트레이닝 리포트</h2>
        <div class="report-meta">${profile.name} · ${new Date().toLocaleDateString('ko-KR')} 기준</div>
        ${AIAnalyzer.GAME_TYPES.map(gameType => {
          const sessions = Storage.getSessions(profile.id, gameType);
          const recent = sessions.slice(-7);
          return `
            <div class="report-section">
              <div class="rs-header" style="color:${GAME_COLORS[gameType]}">
                ${GAME_LABELS[gameType]} <span class="rs-count">(총 ${sessions.length}회)</span>
              </div>
              ${recent.length === 0 ? '<div class="rs-empty">아직 수행 기록이 없습니다</div>' : `
                <div class="rs-chart-wrap">
                  <canvas id="chart-${gameType}" height="120"></canvas>
                </div>
                <div class="rs-table">
                  <div class="rt-row rt-head">
                    <span>날짜</span><span>정답률</span><span>반응(ms)</span><span>난이도</span>
                  </div>
                  ${recent.slice(-5).reverse().map(s => `
                    <div class="rt-row">
                      <span>${new Date(s.timestamp).toLocaleDateString('ko-KR', {month:'numeric',day:'numeric'})}</span>
                      <span>${Math.round(s.accuracy*100)}%</span>
                      <span>${Math.round(s.avgResponseTime)}</span>
                      <span>${s.difficulty}</span>
                    </div>
                  `).join('')}
                </div>
              `}
            </div>
          `;
        }).join('')}
      </div>
    `;
    document.getElementById('btn-back').addEventListener('click', () => navigateTo('hub'));
    AIAnalyzer.GAME_TYPES.forEach(gameType => {
      const sessions = Storage.getSessions(profile.id, gameType).slice(-7);
      if (sessions.length === 0) return;
      drawSessionChart(`chart-${gameType}`, sessions, GAME_COLORS[gameType]);
    });
  }

  function drawSessionChart(canvasId, sessions, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    canvas.width = canvas.offsetWidth || 320;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const pad = { top:10, right:10, bottom:30, left:35 };
    const gW = W - pad.left - pad.right;
    const gH = H - pad.top - pad.bottom;
    const values = sessions.map(s => Math.round(s.accuracy * 100));
    const n = values.length;
    ctx.clearRect(0, 0, W, H);
    [0,25,50,75,100].forEach(v => {
      const y = pad.top + gH * (1 - v/100);
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(W - pad.right, y);
      ctx.strokeStyle = 'rgba(255,255,255,0.06)';
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.fillStyle = 'rgba(200,214,240,0.5)';
      ctx.font = '10px Outfit';
      ctx.textAlign = 'right';
      ctx.fillText(v + '%', pad.left - 4, y + 4);
    });
    ctx.beginPath();
    values.forEach((v, i) => {
      const x = pad.left + (i / Math.max(n-1,1)) * gW;
      const y = pad.top + gH * (1 - v/100);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.lineJoin = 'round';
    ctx.stroke();
    values.forEach((v, i) => {
      const x = pad.left + (i / Math.max(n-1,1)) * gW;
      const y = pad.top + gH * (1 - v/100);
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI*2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.fillStyle = 'rgba(200,214,240,0.6)';
      ctx.font = '9px Outfit';
      ctx.textAlign = 'center';
      const d = new Date(sessions[i].timestamp);
      ctx.fillText(`${d.getMonth()+1}/${d.getDate()}`, x, H - 5);
    });
  }

  function showToast(msg) {
    const el = document.createElement('div');
    el.className = 'toast show';
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => { el.classList.remove('show'); setTimeout(() => el.remove(), 400); }, 2500);
  }

  return { init, navigateTo, showToast };
})();

App.init();