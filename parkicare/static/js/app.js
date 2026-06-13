/**
 * ParkiCare AI - Main App (Flask API 버전 & Local Fallback 지원)
 * SPA 라우팅 + 양선우 팀 작품설명서 보강안 반영
 */

const App = (() => {
  let currentScreen = 'home';
  let currentGameType = null;

  const GAME_INFO = {
    memory_sequence:  { id: 'memory_sequence',  label: '기억 카드 맞추기', emoji: '🧠', desc: '제시된 카드의 짝을 차례로 맞추는 훈련', color: '#00D4FF' },
    attention_stroop: { id: 'attention_stroop', label: '색-동작 반응 게임', emoji: '🎯', desc: '글자의 실제 색상을 판별하여 터치하는 훈련', color: '#7B2FBE' },
    motor_response:   { id: 'motor_response',   label: '손가락 순서 누르기',   emoji: '✋', desc: '숫자가 적힌 원을 번호 순서대로 터치하는 훈련', color: '#00FF94' },
  };

  const STAGE_LABELS = {
    stage1: '초기 단계 (경미)', stage2: '경증 단계', stage3: '중등도 단계', stage4: '중증 단계', stage5: '최중증 단계',
  };
  const AVATAR_COLORS = ['#00D4FF','#7B2FBE','#00FF94','#FF6B6B','#FFB800','#FF69B4'];
  const GAME_TYPES = ['memory_sequence', 'attention_stroop', 'motor_response'];
  const MIN_SESSIONS = 3;

  // 공통 고정 안전 문구 (비의료인 순화안 준수)
  const SAFETY_DISCLAIMER_HTML = `
    <div class="safety-disclaimer-banner">
      <span class="sd-icon">⚠️</span>
      <div class="sd-content">
        <strong>의료적 안전 고지 및 한계 명시</strong>
        <p>본 시스템은 의료 기기가 아니며, 의학적 진단 및 치료를 대체할 수 없습니다. 훈련 중 통증, 어지러움, 심한 피로 등이 발생할 시 즉시 사용을 중단하고 보호자 및 의료 전문가의 진단을 받으십시오.</p>
      </div>
    </div>
  `;

  // ─── 초기화 ───────────────────────────────────────────────────
  function init() {
    document.addEventListener('DOMContentLoaded', () => navigateTo('home'));
  }

  // ─── 화면 전환 (SPA) ──────────────────────────────────────────
  function navigateTo(screen, params = {}) {
    currentScreen = screen;
    const root = document.getElementById('app-root');
    root.style.opacity = '0';
    root.style.transform = 'translateY(12px)';
    setTimeout(async () => {
      try {
        showLoading(root);
        await renderScreen(screen, params, root);
      } catch(e) {
        console.error(e);
        root.innerHTML = `
          <div class="screen">
            <div class="empty-state">
              <div class="empty-icon">⚠️</div>
              <p>화면 전환 오류: ${e.message}</p>
              <button class="btn btn-primary" onclick="App.navigateTo('home')">홈으로 돌아가기</button>
            </div>
          </div>`;
      }
      root.style.opacity = '1';
      root.style.transform = 'translateY(0)';
    }, 180);
  }

  function showLoading(root) {
    root.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:center;height:60vh;flex-direction:column;gap:12px;">
        <div style="font-size:40px;animation:spin 0.8s linear infinite;text-shadow:var(--shadow-glow-cyan)">🧬</div>
        <div style="color:var(--text-secondary);font-size:13px;letter-spacing:0.05em;">파키케어 엔진 구동 중...</div>
      </div>`;
  }

  async function renderScreen(screen, params, root) {
    switch (screen) {
      case 'home':                await renderHome(root);                     break;
      case 'profile-create':      renderProfileCreate(root);                  break;
      case 'hub':                 await renderHub(root);                      break;
      case 'pre-game-check':      renderPreGameCheck(root, params);           break;
      case 'safety-warning':      renderSafetyWarning(root, params);          break;
      case 'game':                await renderGame(root, params);             break;
      case 'result':              renderResult(root, params);                 break;
      case 'dashboard':           await renderDashboard(root);                break;
      case 'report':              await renderReport(root);                   break;
      case 'validation-dashboard': await renderValidationDashboard(root);      break;
      default:                    await renderHome(root);
    }
  }

  // ─── 1. 홈 화면 ────────────────────────────────────────────────
  async function renderHome(root) {
    const profiles = await Storage.getProfiles();
    const current = Storage.getCurrentProfile();

    root.innerHTML = `
      <div class="screen home-screen">
        <div class="home-hero">
          <div class="logo-wrap">
            <div class="logo-icon">🧬</div>
            <div>
              <h1 class="logo-title">ParkiCare Play</h1>
              <p class="logo-sub">인지·운동 미션 훈련 보조 시스템</p>
            </div>
          </div>
          <div class="hero-badge">개인 기록 분석 기반 훈련 추천</div>
        </div>

        ${profiles.length === 0 ? `
          <div class="empty-state card">
            <div class="empty-icon">👤</div>
            <p style="margin-bottom:16px; color:var(--text-secondary);">등록된 훈련용 프로필이 없습니다.<br>훈련 기록을 시작할 환자 프로필을 만들어주세요.</p>
            <button class="btn btn-primary" id="btn-create-first">첫 프로필 등록하기</button>
          </div>
        ` : `
          <div class="section-title">훈련 사용자 프로필 선택</div>
          <div class="profile-list">
            ${profiles.map(p => profileCard(p, current?.id === p.id)).join('')}
          </div>
          <button class="btn btn-outline mt-2" id="btn-add-profile">+ 프로필 추가 등록</button>
        `}

        <div class="home-features mt-2">
          <div class="feature-item" style="cursor:pointer;" id="btn-validation-tab">
            <span>🤖</span>
            <strong>AI 검증 대시보드</strong>
            <p style="font-size:10px;color:var(--text-secondary);margin-top:4px;">모의 데이터 10회분 검증</p>
          </div>
        </div>
      </div>`;

    document.getElementById('btn-create-first')?.addEventListener('click', () => navigateTo('profile-create'));
    document.getElementById('btn-add-profile')?.addEventListener('click', () => navigateTo('profile-create'));
    document.getElementById('btn-validation-tab')?.addEventListener('click', () => navigateTo('validation-dashboard'));

    document.querySelectorAll('.profile-card').forEach(card => {
      card.addEventListener('click', () => {
        const p = profiles.find(p => p.id === card.dataset.id);
        if (p) { 
          Storage.setCurrentProfile(p); 
          navigateTo('hub'); 
        }
      });
    });
    document.querySelectorAll('.profile-delete-btn').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        if (!confirm('프로필과 모든 훈련 세션 기록이 지워집니다. 삭제하시겠습니까?')) return;
        Storage.deleteProfile(btn.dataset.id).then(() => navigateTo('home'));
      });
    });
  }

  function profileCard(p, isActive) {
    return `
      <div class="profile-card ${isActive ? 'active' : ''}" data-id="${p.id}">
        <div class="profile-avatar" style="background:${p.color}">${p.name[0]}</div>
        <div class="profile-info">
          <div class="profile-name">${p.name}</div>
          <div class="profile-meta">${p.age}세 · ${STAGE_LABELS[p.stage] || p.stage}</div>
        </div>
        <div class="profile-score"><span class="score-none">기록 확인 →</span></div>
        <button class="profile-delete-btn" data-id="${p.id}" title="삭제">×</button>
      </div>`;
  }

  // ─── 2. 프로필 등록 ──────────────────────────────────────────────
  function renderProfileCreate(root) {
    root.innerHTML = `
      <div class="screen profile-screen">
        <button class="back-btn" id="btn-back">← 돌아가기</button>
        <h2 class="screen-title">훈련 아바타 생성</h2>
        <form class="profile-form" id="profile-form">
          <div class="form-group">
            <label>환자명 또는 아바타 닉네임</label>
            <input type="text" id="f-name" placeholder="예: 양선우" maxlength="20" required>
          </div>
          <div class="form-group">
            <label>나이</label>
            <input type="number" id="f-age" placeholder="예: 70" min="3" max="100" required>
          </div>
          <div class="form-group">
            <label>자가 인지·운동 수준 (선택)</label>
            <select id="f-stage">
              <option value="stage1">초기 단계 (일상 수행 원활)</option>
              <option value="stage2">경증 단계 (간헐적 불편)</option>
              <option value="stage3">중등도 단계 (중심 균형 훈련 필요)</option>
              <option value="stage4">중증 단계 (보호자 관찰 필요)</option>
            </select>
          </div>
          <div class="form-group">
            <label>비고 및 훈련 메모</label>
            <input type="text" id="f-diagnosis" placeholder="예: 반응 속도 훈련 위주 희망">
          </div>
          <div class="form-group">
            <label>개인화 아바타 색상</label>
            <div class="color-picker">
              ${AVATAR_COLORS.map((c,i) => `<div class="color-opt ${i===0?'selected':''}" data-color="${c}" style="background:${c}"></div>`).join('')}
            </div>
          </div>
          <button type="submit" class="btn btn-primary">프로필 등록하기</button>
        </form>
      </div>`;

    document.getElementById('btn-back').addEventListener('click', () => navigateTo('home'));
    let selectedColor = AVATAR_COLORS[0];
    document.querySelectorAll('.color-opt').forEach(opt => {
      opt.addEventListener('click', () => {
        document.querySelectorAll('.color-opt').forEach(o => o.classList.remove('selected'));
        opt.classList.add('selected');
        selectedColor = opt.dataset.color;
      });
    });

    document.getElementById('profile-form').addEventListener('submit', async e => {
      e.preventDefault();
      const btn = e.target.querySelector('button[type=submit]');
      btn.textContent = '저장 중...'; btn.disabled = true;
      try {
        const profile = await Storage.saveProfile({
          name: document.getElementById('f-name').value.trim(),
          age: parseInt(document.getElementById('f-age').value),
          stage: document.getElementById('f-stage').value,
          diagnosis: document.getElementById('f-diagnosis').value.trim(),
          color: selectedColor,
        });
        Storage.setCurrentProfile(profile);
        navigateTo('hub');
      } catch(err) {
        showToast('저장 실패: ' + err.message);
        btn.textContent = '프로필 등록하기'; btn.disabled = false;
      }
    });
  }

  // ─── 3. 트레이닝 허브 ───────────────────────────────────────────
  async function renderHub(root) {
    const profile = Storage.getCurrentProfile();
    if (!profile) { navigateTo('home'); return; }

    const sessionCounts = {};
    await Promise.all(GAME_TYPES.map(async gt => {
      const s = await Storage.getSessions(profile.id, gt);
      sessionCounts[gt] = s.length;
    }));

    const weakProfile = await Storage.getWeakProfile(profile.id);
    const grade = weakProfile?.overallScore != null ? getGrade(weakProfile.overallScore) : null;

    root.innerHTML = `
      <div class="screen hub-screen">
        ${SAFETY_DISCLAIMER_HTML}

        <div class="hub-header" style="margin-top:12px;">
          <button class="back-btn" id="btn-back">← 홈</button>
          <div class="hub-profile">
            <div class="hub-avatar" style="background:${profile.color}">${profile.name[0]}</div>
            <div>
              <div class="hub-name">${profile.name}</div>
              <div class="hub-stage">${STAGE_LABELS[profile.stage] || profile.stage}</div>
            </div>
          </div>
          <button class="icon-btn" id="btn-dashboard" title="AI 분석 보고서">📊</button>
        </div>

        ${weakProfile?.safetyTriggered ? `
          <div class="safety-alert-card card" style="border-color:var(--accent-red);background:rgba(255,107,107,0.08);margin-bottom:12px;">
            <div style="color:var(--accent-red);font-weight:700;display:flex;align-items:center;gap:6px;font-size:14px;">
              <span>⚠️</span>최근 안전 주의 감지
            </div>
            <p style="font-size:12px;color:var(--text-primary);margin-top:6px;line-height:1.5;">최근 미션 도중 통증/피로/어지러움이 감지되어 추천이 정지되었습니다. 충분한 안정을 취하고 시작하십시오.</p>
          </div>
        ` : ''}

        ${grade ? `
          <div class="overall-card">
            <div class="overall-info">
              <div class="overall-label">미션 종합 등급</div>
              <div class="overall-grade" style="color:${grade.color};font-size:18px;font-weight:700;">${grade.emoji} ${grade.label}</div>
            </div>
            <div style="flex:1;"></div>
            <div class="overall-score" style="color:${grade.color}">${weakProfile.overallScore}</div>
          </div>
        ` : `
          <div class="info-banner">
            <span>💡</span> 세 영역을 각각 ${MIN_SESSIONS}회 이상 진행하면 기록 데이터 기반 AI 맞춤 추천 보고서가 열립니다.
          </div>
        `}

        <div class="section-title">오늘의 맞춤 훈련 미션</div>
        <div class="game-cards">
          ${Object.values(GAME_INFO).map(g => gameCard(g, weakProfile, sessionCounts[g.id])).join('')}
        </div>

        <div class="hub-actions">
          <button class="btn btn-outline" id="btn-report">📋 주간 훈련 리포트</button>
          <button class="btn btn-ai" id="btn-analyze">🤖 오늘의 훈련 분석 갱신</button>
        </div>
      </div>`;

    document.getElementById('btn-back').addEventListener('click', () => navigateTo('home'));
    document.getElementById('btn-dashboard').addEventListener('click', () => navigateTo('dashboard'));
    document.getElementById('btn-report').addEventListener('click', () => navigateTo('report'));
    document.getElementById('btn-analyze').addEventListener('click', () => runAnalysis(profile.id));
    
    document.querySelectorAll('.game-card').forEach(card =>
      card.addEventListener('click', () => navigateTo('pre-game-check', { gameType: card.dataset.game }))
    );
  }

  function gameCard(gameInfo, weakProfile, sessionCount) {
    const game = weakProfile?.games?.[gameInfo.id];
    
    // 만약 피로도가 극심하게 감지되어 안전경보가 뜬 경우, 게임 카드에 경고를 노출함
    const isWeak = game?.isWeak ?? false;
    const trend = game?.trend;
    const trendIcon = trend === 'improving' ? '📈 향상' : trend === 'declining' ? '📉 주의' : trend === 'stable' ? '➡️ 유지' : '';
    
    // AI 추천 대상인지 확인
    const isRecommended = weakProfile?.recommendations?.some(r => r.type === gameInfo.id && r.priority === 'high');

    return `
      <div class="game-card ${isRecommended ? 'game-card-recommended' : isWeak ? 'game-card-weak' : ''}" data-game="${gameInfo.id}">
        <div class="gc-accent" style="background:${gameInfo.color}"></div>
        <div class="gc-emoji">${gameInfo.emoji}</div>
        <div class="gc-info">
          <div class="gc-title" style="display:flex;align-items:center;gap:6px;">
            ${gameInfo.label}
            ${isRecommended ? '<span class="rec-badge">✦ 맞춤 추천</span>' : ''}
          </div>
          <div class="gc-desc">${gameInfo.desc}</div>
          <div class="gc-meta">
            <span class="session-count">기록 ${sessionCount}회</span>
            ${isWeak ? '<span class="weak-badge">⚠️ 보완 필요</span>' : ''}
            ${trendIcon ? `<span class="trend-badge">${trendIcon}</span>` : ''}
          </div>
        </div>
        <div class="gc-arrow">시작 →</div>
      </div>`;
  }

  async function runAnalysis(profileId) {
    const btn = document.getElementById('btn-analyze');
    if (btn) { btn.innerHTML = '⏳ 분석 연산 구동 중...'; btn.disabled = true; }
    try {
      const result = await Storage.analyzeProfile(profileId);
      showToast(`✅ 데이터 분석 완료! 훈련 지표가 갱신되었습니다.`);
      navigateTo('dashboard');
    } catch(e) {
      showToast('로컬 분석 완료: ' + e.message);
      navigateTo('dashboard');
    }
  }

  // ─── 4. 게임 시작 전 피로도/안전 상태 체크 ────────────────────────
  function renderPreGameCheck(root, { gameType }) {
    const info = GAME_INFO[gameType];
    root.innerHTML = `
      <div class="screen pre-check-screen">
        <button class="back-btn" id="btn-back">← 취소</button>
        
        <div class="card" style="padding:22px; text-align:center; background:rgba(255,255,255,0.02); border-color:var(--border-strong);">
          <div style="font-size:48px;margin-bottom:12px;">${info.emoji}</div>
          <h2 class="screen-title" style="margin-bottom:6px;">${info.label}</h2>
          <p style="font-size:13px;color:var(--text-secondary);line-height:1.6;margin-bottom:24px;">미션을 실행하기 전, 환자 본인의 오늘 몸 상태와 관절 상태, 피로 수준을 정확히 파악하여 안전한 범위 내에서 훈련을 시행합니다.</p>
          
          <div style="text-align:left;margin-bottom:20px;">
            <label style="font-size:14px;font-weight:700;color:var(--text-primary);display:block;margin-bottom:10px;">현재 자가 컨디션 상태를 체크해주세요:</label>
            
            <div class="fatigue-options" style="display:flex;flex-direction:column;gap:8px;">
              <label class="fatigue-opt-label">
                <input type="radio" name="fatigue" value="1" checked>
                <span class="f-dot dot-green"></span>
                <strong>좋음:</strong> 몸이 가볍고 훈련 수행에 문제없음.
              </label>
              <label class="fatigue-opt-label">
                <input type="radio" name="fatigue" value="2">
                <span class="f-dot dot-yellow"></span>
                <strong>보통:</strong> 평소와 비슷하며 약간 둔한 상태.
              </label>
              <label class="fatigue-opt-label">
                <input type="radio" name="fatigue" value="3">
                <span class="f-dot dot-orange"></span>
                <strong>약간 피곤함:</strong> 근육이 뻣뻣하거나 집중력이 떨어짐. <br><small style="color:var(--accent-amber);font-size:10px;margin-left:22px;">➔ 미션 난이도가 자동으로 한 단계 하향됩니다.</small>
              </label>
              <label class="fatigue-opt-label">
                <input type="radio" name="fatigue" value="4">
                <span class="f-dot dot-red"></span>
                <strong>심함 (통증, 어지러움, 심한 뻣뻣함):</strong> 동작 제어가 힘듦. <br><small style="color:var(--accent-red);font-size:10px;margin-left:22px;">➔ 즉시 미션을 중단하고 안정을 취합니다.</small>
              </label>
            </div>
          </div>
          
          <button class="btn btn-primary" id="btn-start-mission">안전 규칙 확인 및 훈련 시작</button>
        </div>
      </div>
    `;

    document.getElementById('btn-back').addEventListener('click', () => navigateTo('hub'));
    
    document.getElementById('btn-start-mission').addEventListener('click', async () => {
      const selectedFatigue = parseInt(document.querySelector('input[name="fatigue"]:checked').value);
      
      if (selectedFatigue === 4) {
        // 즉시 중단 안내 화면으로 라우팅 및 세션에 피로도 기록 저장
        const profile = Storage.getCurrentProfile();
        const fakeSession = {
          accuracy: 0.0,
          avgResponseTime: 0.0,
          correctCount: 0,
          totalRounds: 0,
          missCount: 0,
          difficulty: 1,
          fatigue: 4, // 극심한 피로/통증 상태 저장
          timestamp: new Date().toISOString()
        };
        await Storage.saveSession(profile.id, gameType, fakeSession);
        await Storage.analyzeProfile(profile.id); // AI 프로파일 갱신
        
        navigateTo('safety-warning', { gameType });
      } else {
        navigateTo('game', { gameType, fatigue: selectedFatigue });
      }
    });
  }

  // ─── 5. 안전 가이드 중단 안내 화면 ──────────────────────────────
  function renderSafetyWarning(root, { gameType }) {
    root.innerHTML = `
      <div class="screen safety-warning-screen">
        <div class="card" style="border-color:var(--accent-red); background:rgba(255,107,107,0.05); padding:26px; text-align:center;">
          <div style="font-size:60px;margin-bottom:12px;filter:drop-shadow(0 0 10px rgba(255,107,107,0.4))">⚠️</div>
          <h2 style="color:var(--accent-red);font-weight:800;font-size:24px;margin-bottom:14px;">훈련 즉시 중단 권고</h2>
          
          <div style="text-align:left; font-size:13px; color:var(--text-primary); line-height:1.7; margin-bottom:20px; background:rgba(0,0,0,0.2); padding:16px; border-radius:var(--radius-md);">
            <p style="font-weight:700;margin-bottom:8px;color:var(--accent-red);">🚨 신체 이상 반응 감지 경고</p>
            <p>자가 컨디션 평가 결과, <strong>심한 피로, 통증 또는 어지러움</strong> 상태가 기록되었습니다. 무리한 운동이나 인지 훈련은 부상의 위험이나 추가적인 피로 가중을 유발할 수 있습니다.</p>
            <hr style="border:0;border-top:1px solid var(--border-strong);margin:12px 0;">
            <p><strong>수행 권장 행동 요령:</strong></p>
            <ul style="margin-left:20px;margin-top:6px;display:flex;flex-direction:column;gap:4px;">
              <li>즉시 스마트폰/태블릿 화면을 끄고 안락한 의자나 침대에 누워 안정을 취하십시오.</li>
              <li>따뜻한 물을 섭취하고 15분 이상 깊은 심호흡을 취해 혈류를 조절하십시오.</li>
              <li>뻣뻣함이 계속되거나 어지러움이 가라앉지 않을 경우, 함께 있는 보호자 또는 가까운 의료 시설의 전문의에게 알리십시오.</li>
            </ul>
          </div>
          
          <div style="margin-bottom:20px;font-size:11px;color:var(--text-secondary);">
            ※ 본 시스템은 의료 진단을 내리지 않으며, 환자의 안전을 최우선으로 하도록 훈련 보조 장치가 구동되고 있습니다. 본 내용과 몸 상태는 세션 로그에 안전 상태로 기록되어 보호자 리포트에 연동됩니다.
          </div>
          
          <button class="btn btn-outline" id="btn-back-hub">훈련 허브로 돌아가기</button>
        </div>
      </div>
    `;

    document.getElementById('btn-back-hub').addEventListener('click', () => navigateTo('hub'));
  }

  // ─── 6. 게임 실행 ──────────────────────────────────────────────
  async function renderGame(root, { gameType, fatigue }) {
    currentGameType = gameType;
    const profile = Storage.getCurrentProfile();
    if (!profile) { navigateTo('hub'); return; }

    const problem = await Storage.getProblem(profile.id, gameType);
    
    // 약간 피곤함(3)인 경우 임시 난이도 1단계 차감 조정
    if (fatigue === 3) {
      problem.difficulty = Math.max(1, problem.difficulty - 1);
      if (gameType === 'memory_sequence') {
        problem.sequence = problem.sequence.slice(0, Math.max(2, problem.sequence.length - 1));
        problem.displayTime = problem.displayTime + 500;
        problem.description = `[안전 모드] 난이도가 조절되었습니다. 숫자 ${problem.sequence.length}개를 차분히 기억하세요.`;
      } else if (gameType === 'attention_stroop') {
        problem.problems = problem.problems.slice(0, Math.max(2, problem.problems.length - 1));
        problem.problems.forEach(p => p.timeLimit += 600);
        problem.description = `[안전 모드] 글자 색상을 한층 천천히 선택해 보세요.`;
      } else if (gameType === 'motor_response') {
        problem.targetCount = Math.max(2, problem.targetCount - 1);
        problem.timeLimit += 500;
        problem.description = `[안전 모드] 원을 여유 있게 터치하세요.`;
      }
    }

    root.innerHTML = `
      <div class="screen game-screen">
        <button class="back-btn" id="btn-back">← 훈련 포기</button>
        <div id="game-container" class="game-container"></div>
      </div>`;
    
    document.getElementById('btn-back').addEventListener('click', () => {
      if (confirm('훈련 기록이 저장되지 않고 취소됩니다. 포기하시겠습니까?')) navigateTo('hub');
    });

    const container = document.getElementById('game-container');
    const onComplete = async (sessionData) => {
      // 피로 정보 병합 저장
      sessionData.fatigue = fatigue || 1;
      sessionData.timestamp = new Date().toISOString();
      try {
        await Storage.saveSession(profile.id, gameType, sessionData);
        await Storage.analyzeProfile(profile.id); // 완료 즉시 분석
      } catch(e) { 
        console.warn('로컬 스토리지에 임시 저장되었습니다.', e); 
      }
      setTimeout(() => navigateTo('result', { gameType, sessionData }), 600);
    };

    switch (gameType) {
      case 'memory_sequence':  MemorySequenceGame.init(container, problem, onComplete);  break;
      case 'attention_stroop': AttentionStroopGame.init(container, problem, onComplete); break;
      case 'motor_response':   MotorResponseGame.init(container, problem, onComplete);   break;
    }
  }

  // ─── 7. 게임 결과 화면 (보강) ──────────────────────────────────
  function renderResult(root, { gameType, sessionData }) {
    const { accuracy, avgResponseTime, correctCount, totalRounds, difficulty, fatigue } = sessionData;
    const pct = Math.round(accuracy * 100);
    const grade = getGrade(pct);

    // AI 분석 기반 최신 데이터 가져와서 취약 영역 추천 이유 설명
    const profile = Storage.getCurrentProfile();
    
    root.innerHTML = `
      <div class="screen result-screen">
        <div class="result-hero card" style="text-align:center;margin-bottom:16px;">
          <div class="result-grade-emoji" style="font-size:54px;margin-bottom:6px;">${grade.emoji}</div>
          <h2 class="result-title" style="font-size:20px;font-weight:700;">미션 수행 완료</h2>
          <p style="font-size:12px;color:var(--text-secondary);">${GAME_INFO[gameType].label} · 난이도 ${difficulty}</p>
          
          <div class="result-score-ring" style="margin:16px auto; position:relative; width:120px; height:120px;">
            <svg viewBox="0 0 120 120" style="width:100%;height:100%;transform:rotate(-90deg)">
              <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="8"/>
              <circle cx="60" cy="60" r="50" fill="none" stroke="${grade.color}" stroke-width="8"
                stroke-dasharray="314.15" stroke-dashoffset="${314.15 * (1 - pct/100)}" stroke-linecap="round" id="ring-arc"/>
            </svg>
            <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;">
              <span style="font-size:28px;font-weight:800;color:${grade.color}">${pct}%</span>
              <span style="font-size:11px;color:var(--text-secondary)">정답률</span>
            </div>
          </div>
        </div>

        <div class="result-stats card" style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;text-align:center;margin-bottom:16px;">
          <div><div style="font-size:18px;font-weight:700;color:var(--text-primary);">${correctCount}/${totalRounds}</div><div style="font-size:11px;color:var(--text-secondary)">맞춘 수</div></div>
          <div><div style="font-size:18px;font-weight:700;color:var(--text-primary);">${(avgResponseTime/1000).toFixed(2)}초</div><div style="font-size:11px;color:var(--text-secondary)">평균 반응</div></div>
          <div><div style="font-size:18px;font-weight:700;color:var(--text-primary);">${fatigue === 3 ? '피곤함' : '보통/좋음'}</div><div style="font-size:11px;color:var(--text-secondary)">입력 컨디션</div></div>
        </div>

        <div class="next-suggestion-card card" id="suggest-area" style="background:linear-gradient(135deg, rgba(0,212,255,0.04), rgba(123,47,190,0.04));border-color:rgba(0,212,255,0.15);">
          <div style="font-weight:700;color:var(--accent-cyan);font-size:13px;margin-bottom:4px;display:flex;align-items:center;gap:6px;">
            <span>🤖</span>AI 데이터 분석 권장 조치
          </div>
          <p style="font-size:12px;color:var(--text-primary);line-height:1.6;" id="suggest-text">기록을 수치화하여 다음 훈련 강도를 최적화하고 있습니다. 허브 화면으로 돌아가 AI 정밀 분석 보고서를 클릭하세요.</p>
        </div>

        <div class="result-actions mt-2" style="display:flex;gap:10px;">
          <button class="btn btn-outline" id="btn-retry" style="flex:1;">다시 하기</button>
          <button class="btn btn-primary" id="btn-hub" style="flex:1;">훈련 완료 (허브)</button>
        </div>
      </div>`;

    // 추천 텍스트 실시간 동적 설명 로드
    Storage.getWeakProfile(profile.id).then(wp => {
      if (wp && wp.recommendations && wp.recommendations.length > 0) {
        // safety 경보가 울렸으면 중단 안내로, 아니면 추천 미션 안내
        const safety = wp.recommendations.find(r => r.type === 'safety_stop');
        const recommend = wp.recommendations.find(r => r.priority === 'high');
        
        const textEl = document.getElementById('suggest-text');
        if (safety) {
          textEl.innerHTML = `<span style="color:var(--accent-red);font-weight:600;">피로 안전 차단 조치 작동:</span> 피로가 누적되었으니 미션을 멈추십시오.`;
        } else if (recommend) {
          textEl.innerHTML = `오늘 환자님의 <strong>${recommend.label}</strong> 기록에서 지연 현상 또는 편차가 확인되어 보강 훈련으로 우선 권장합니다. (${recommend.message})`;
        }
      }
    });

    document.getElementById('btn-retry').addEventListener('click', () => navigateTo('pre-game-check', { gameType }));
    document.getElementById('btn-hub').addEventListener('click', () => navigateTo('hub'));
  }

  // ─── 8. AI 분석 대시보드 ────────────────────────────────────────
  async function renderDashboard(root) {
    const profile = Storage.getCurrentProfile();
    if (!profile) { navigateTo('home'); return; }
    
    let weakProfile = await Storage.getWeakProfile(profile.id);
    if (!weakProfile) {
      weakProfile = await Storage.analyzeProfile(profile.id);
    }

    const LABELS = { memory_sequence:'기억력', attention_stroop:'집중력', motor_response:'운동성' };
    const COLORS = { memory_sequence:'#00D4FF', attention_stroop:'#7B2FBE', motor_response:'#00FF94' };
    const EMOJIS = { memory_sequence:'🧠', attention_stroop:'🎯', motor_response:'✋' };
    const grade = weakProfile.overallScore > 0 ? getGrade(weakProfile.overallScore) : null;

    root.innerHTML = `
      <div class="screen dashboard-screen">
        ${SAFETY_DISCLAIMER_HTML}

        <div class="dash-header" style="margin-top:12px;">
          <button class="back-btn" id="btn-back">← 허브</button>
          <h2 class="screen-title" style="margin:0;">AI 트레이닝 대시보드</h2>
        </div>

        <div class="dash-overall card mt-2" style="display:flex;align-items:center;gap:20px;">
          <div class="dash-score">
            <div class="dash-score-val" style="color:${grade ? grade.color : '#8a9ab8'};font-size:36px;font-weight:800;">
              ${weakProfile.overallScore || '-'}
            </div>
            <div class="dash-score-label" style="font-size:11px;color:var(--text-secondary)">종합 분석점수</div>
          </div>
          <div style="border-left:1px solid var(--border-strong);height:50px;"></div>
          <div class="dash-meta" style="flex:1;font-size:12px;">
            <div style="color:var(--text-secondary)">최근 갱신일: ${new Date(weakProfile.analyzedAt).toLocaleDateString('ko-KR')}</div>
            <div class="weak-summary" style="margin-top:4px;font-weight:700;">
              ${weakProfile.weakAreas?.length > 0
                ? `<span style="color:var(--accent-red)">⚠️ 보완 요망: ${weakProfile.weakAreas.map(a => LABELS[a]).join(', ')}</span>`
                : '<span style="color:var(--accent-green)">✅ 전 영역 우수 및 안정세</span>'}
            </div>
          </div>
        </div>

        <div class="dash-card card mt-2">
          <div class="card-title" style="font-weight:700;font-size:14px;margin-bottom:12px;">수행 기록 레이더 (기능 밸런스)</div>
          <div class="radar-wrap" style="display:flex;justify-content:center;"><canvas id="radarChart" width="260" height="260"></canvas></div>
        </div>

        <div class="dash-card card mt-2">
          <div class="card-title" style="font-weight:700;font-size:14px;margin-bottom:12px;">일일 상세 훈련 기록 지표</div>
          <div class="game-details" style="display:flex;flex-direction:column;gap:10px;">
            ${GAME_TYPES.map(gt => {
              const g = weakProfile.games?.[gt];
              if (!g) return '';
              const pct = g.accuracy !== null ? Math.round(g.accuracy * 100) : null;
              const gr = pct !== null ? getGrade(pct) : null;
              return `
                <div class="gd-item ${g.isWeak ? 'gd-weak' : ''}" style="background:rgba(255,255,255,0.02);padding:12px;border-radius:var(--radius-md);display:flex;align-items:center;gap:12px;border:1px solid var(--border);">
                  <div class="gd-emoji" style="font-size:26px;">${EMOJIS[gt]}</div>
                  <div class="gd-body" style="flex:1;">
                    <div style="display:flex;justify-content:between;align-items:center;width:100%;">
                      <span class="gd-title" style="font-weight:700;font-size:14px;color:var(--text-primary);">${GAME_INFO[gt].label}</span>
                      <span style="flex:1;"></span>
                      <span style="font-size:11px;color:var(--text-secondary)">기록 ${g.sessionCount}회</span>
                    </div>
                    <div class="gd-bar-wrap" style="height:6px;background:rgba(255,255,255,0.08);border-radius:3px;margin:8px 0 6px;overflow:hidden;">
                      <div class="gd-bar" style="width:${pct || 0}%;height:100%;background:${COLORS[gt]};border-radius:3px;"></div>
                    </div>
                    <div class="gd-stats" style="display:flex;justify-content:between;font-size:11px;color:var(--text-secondary);gap:12px;">
                      ${pct !== null ? `<span style="color:${gr.color};font-weight:600;">정확도 ${pct}%</span>` : '<span>훈련 기록 부족 (3회 필요)</span>'}
                      ${g.responseTime ? `<span>평균속도 ${(g.responseTime/1000).toFixed(2)}초</span>` : ''}
                      <span>설정 난이도 ${g.difficulty}단</span>
                    </div>
                  </div>
                </div>`;
            }).join('')}
          </div>
        </div>

        ${weakProfile.recommendations?.length > 0 ? `
          <div class="dash-card card mt-2" style="border-color:rgba(0,212,255,0.25);">
            <div class="card-title" style="font-weight:700;font-size:14px;margin-bottom:10px;color:var(--accent-cyan);">🤖 AI 맞춤 처방 분석</div>
            <div style="display:flex;flex-direction:column;gap:8px;">
              ${weakProfile.recommendations.map(r => {
                const badgeClass = r.priority === 'high' ? 'bg-red' : r.priority === 'medium' ? 'bg-orange' : 'bg-green';
                return `
                  <div class="rec-item rec-${r.priority}" style="background:rgba(255,255,255,0.015);padding:10px 12px;border-radius:var(--radius-md);border-left:4px solid ${r.priority==='high'?'var(--accent-red)':'var(--accent-cyan)'};font-size:12px;line-height:1.6;">
                    <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                      <span class="badge ${badgeClass}" style="padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;text-transform:uppercase;color:#fff;background:${r.priority==='high'?'var(--accent-red)':'var(--accent-cyan)'}">${r.priority}</span>
                      <strong style="color:var(--text-primary);">${r.label}</strong>
                    </div>
                    <div style="color:var(--text-primary);">${r.message}</div>
                  </div>`;
              }).join('')}
            </div>
          </div>` : ''}

        <button class="btn btn-primary mt-2" id="btn-train">맞춤 트레이닝하러 가기</button>
      </div>`;

    document.getElementById('btn-back').addEventListener('click', () => navigateTo('hub'));
    document.getElementById('btn-train').addEventListener('click', () => navigateTo('hub'));
    drawRadarChart(weakProfile);
  }

  function drawRadarChart(wp) {
    const canvas = document.getElementById('radarChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const cx = W/2, cy = H/2, r = Math.min(W,H)/2 - 35;
    const labels = ['기억력(카드)','집중력(반응)','운동성(순서)'];
    const keys = GAME_TYPES;
    const values = keys.map(k => {
      const g = wp.games?.[k];
      return (g?.accuracy != null) ? g.accuracy * 100 : 0;
    });
    const angles = labels.map((_,i) => Math.PI*2*i/labels.length - Math.PI/2);
    ctx.clearRect(0,0,W,H);
    
    // 격자 그리기
    [100,75,50,25].forEach(p => {
      ctx.beginPath();
      angles.forEach((a,i) => { const x=cx+r*(p/100)*Math.cos(a), y=cy+r*(p/100)*Math.sin(a); i===0?ctx.moveTo(x,y):ctx.lineTo(x,y); });
      ctx.closePath(); ctx.strokeStyle='rgba(255,255,255,0.06)'; ctx.lineWidth=1; ctx.stroke();
    });
    
    // 축 그리기
    angles.forEach(a => { ctx.beginPath(); ctx.moveTo(cx,cy); ctx.lineTo(cx+r*Math.cos(a),cy+r*Math.sin(a)); ctx.strokeStyle='rgba(255,255,255,0.1)'; ctx.stroke(); });
    
    // 데이터 영역 채우기
    ctx.beginPath();
    angles.forEach((a,i) => { const x=cx+r*(values[i]/100)*Math.cos(a), y=cy+r*(values[i]/100)*Math.sin(a); i===0?ctx.moveTo(x,y):ctx.lineTo(x,y); });
    ctx.closePath(); ctx.fillStyle='rgba(0,212,255,0.15)'; ctx.fill(); ctx.strokeStyle='#00D4FF'; ctx.lineWidth=2.5; ctx.stroke();
    
    // 꼭짓점 그리기
    angles.forEach((a,i) => {
      const x=cx+r*(values[i]/100)*Math.cos(a), y=cy+r*(values[i]/100)*Math.sin(a);
      ctx.beginPath(); ctx.arc(x,y,5,0,Math.PI*2); ctx.fillStyle='#00D4FF'; ctx.fill();
      ctx.strokeStyle='#fff'; ctx.lineWidth=1; ctx.stroke();
    });
    
    // 라벨 출력
    ctx.font='bold 11px Noto Sans KR,sans-serif'; ctx.fillStyle='#8a9ab8'; ctx.textAlign='center';
    angles.forEach((a,i) => {
      const offset = 22;
      const x = cx+(r+offset)*Math.cos(a);
      const y = cy+(r+offset)*Math.sin(a) + 4;
      ctx.fillText(labels[i], x, y);
    });
  }

  // ─── 9. 트레이닝 리포트 및 기존 앱 비교 ────────────────────────────
  async function renderReport(root) {
    const profile = Storage.getCurrentProfile();
    if (!profile) { navigateTo('home'); return; }
    
    const LABELS = { memory_sequence:'기억 카드 맞추기', attention_stroop:'색-동작 반응 게임', motor_response:'손가락 순서 누르기' };
    const COLORS = { memory_sequence:'#00D4FF', attention_stroop:'#7B2FBE', motor_response:'#00FF94' };

    const allSessions = {};
    await Promise.all(GAME_TYPES.map(async gt => {
      allSessions[gt] = await Storage.getSessions(profile.id, gt);
    }));

    // 비교 분석표 HTML 코드 설계
    const COMPARISON_TABLE_HTML = `
      <div class="report-section card mt-2" style="background:rgba(255,255,255,0.015);">
        <div class="rs-header" style="color:var(--accent-cyan);font-weight:700;font-size:14px;margin-bottom:12px;">
          📊 기존 관리 앱 대비 차별점 비교
        </div>
        <div style="overflow-x:auto;">
          <table class="comparison-table" style="width:100%;border-collapse:collapse;font-size:11px;text-align:left;color:var(--text-primary);">
            <thead>
              <tr style="border-bottom:2px solid var(--border-strong);color:var(--text-secondary);">
                <th style="padding:8px 4px;">비교 요소</th>
                <th style="padding:8px 4px;">기존 앱 (닥터파킨슨 등)</th>
                <th style="padding:8px 4px;color:var(--accent-cyan);">파키케어 플레이 (본작)</th>
              </tr>
            </thead>
            <tbody>
              <tr style="border-bottom:1px solid var(--border);">
                <td style="padding:8px 4px;font-weight:700;">주요 기능</td>
                <td style="padding:8px 4px;color:var(--text-secondary);">일방향 질환 정보제공, 증상 체크리스트</td>
                <td style="padding:8px 4px;font-weight:700;">대화형 인지·운동 미션 훈련</td>
              </tr>
              <tr style="border-bottom:1px solid var(--border);">
                <td style="padding:8px 4px;font-weight:700;">피드백 방식</td>
                <td style="padding:8px 4px;color:var(--text-secondary);">일률적 약물 복용 알림 및 단순 알람</td>
                <td style="padding:8px 4px;font-weight:700;color:var(--accent-green);">개인 훈련 로그 실시간 분석 연산</td>
              </tr>
              <tr style="border-bottom:1px solid var(--border);">
                <td style="padding:8px 4px;font-weight:700;">맞춤형 추천</td>
                <td style="padding:8px 4px;color:var(--text-secondary);">개인화 추천 미제공 (동일 화면)</td>
                <td style="padding:8px 4px;font-weight:700;">정확도/반응 지연/피로 안전 추천 적용</td>
              </tr>
              <tr style="border-bottom:1px solid var(--border);">
                <td style="padding:8px 4px;font-weight:700;">안전장치 설계</td>
                <td style="padding:8px 4px;color:var(--text-secondary);">비정상 데이터 입력 대비 보호조치 없음</td>
                <td style="padding:8px 4px;font-weight:700;color:var(--accent-red);">피로/통증 감지 시 즉시 중단 가이드</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    root.innerHTML = `
      <div class="screen report-screen">
        <button class="back-btn" id="btn-back">← 허브</button>
        <h2 class="screen-title">📋 주간 트레이닝 리포트</h2>
        <div class="report-meta" style="font-size:12px;color:var(--text-secondary);margin-bottom:16px;">
          ${profile.name} 환자의 최근 훈련 기록 리포트
        </div>
        
        ${GAME_TYPES.map(gt => {
          const sessions = allSessions[gt].filter(s => s.totalRounds > 0); // 정상 수행 세션만 필터
          const recent = sessions.slice(-7);
          return `
            <div class="report-section card mt-2" style="background:rgba(255,255,255,0.01);">
              <div class="rs-header" style="color:${COLORS[gt]};font-weight:700;font-size:14px;margin-bottom:8px;display:flex;justify-content:between;">
                <span>${LABELS[gt]}</span>
                <span style="flex:1;"></span>
                <span class="rs-count" style="font-size:11px;color:var(--text-secondary);font-weight:normal;">(총 ${sessions.length}회 수행)</span>
              </div>
              ${recent.length === 0 ? `
                <div class="rs-empty" style="padding:24px;text-align:center;color:var(--text-secondary);font-size:12px;">아직 분석을 위한 충분한 훈련 데이터가 누적되지 않았습니다.</div>
              ` : `
                <div class="rs-chart-wrap" style="height:120px;margin:10px 0;"><canvas id="chart-${gt}" style="width:100%;height:100%;"></canvas></div>
                <div class="rs-table" style="width:100%;font-size:11px;margin-top:10px;">
                  <div class="rt-row rt-head" style="display:grid;grid-template-columns:repeat(5,1fr);font-weight:700;color:var(--text-secondary);border-bottom:1px solid var(--border);padding-bottom:4px;text-align:center;">
                    <span>날짜</span><span>정확도</span><span>반응(초)</span><span>난이도</span><span>컨디션</span>
                  </div>
                  ${recent.slice(-5).reverse().map(s => {
                    let fatigueLabel = '좋음';
                    if (s.fatigue === 2) fatigueLabel = '보통';
                    if (s.fatigue === 3) fatigueLabel = '피곤';
                    if (s.fatigue === 4) fatigueLabel = '중단';
                    return `
                      <div class="rt-row" style="display:grid;grid-template-columns:repeat(5,1fr);padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);text-align:center;">
                        <span>${new Date(s.timestamp).toLocaleDateString('ko-KR',{month:'numeric',day:'numeric'})}</span>
                        <span>${Math.round(s.accuracy*100)}%</span>
                        <span>${(s.avgResponseTime/1000).toFixed(2)}초</span>
                        <span>${s.difficulty}단</span>
                        <span style="color:${s.fatigue>=3?'var(--accent-amber)':'var(--text-primary)'}">${fatigueLabel}</span>
                      </div>`;
                  }).join('')}
                </div>`}
            </div>`;
        }).join('')}

        ${COMPARISON_TABLE_HTML}
      </div>`;

    document.getElementById('btn-back').addEventListener('click', () => navigateTo('hub'));
    GAME_TYPES.forEach(gt => {
      const s = allSessions[gt].filter(s => s.totalRounds > 0).slice(-7);
      if (s.length > 0) drawSessionChart(`chart-${gt}`, s, COLORS[gt]);
    });
  }

  function drawSessionChart(id, sessions, color) {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    canvas.width = canvas.offsetWidth || 340;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const pad = {top:10,right:12,bottom:25,left:35};
    const gW = W-pad.left-pad.right, gH = H-pad.top-pad.bottom;
    const vals = sessions.map(s => Math.round(s.accuracy*100));
    const n = vals.length;
    
    ctx.clearRect(0,0,W,H);
    
    // Y축 가이드선
    [0,50,100].forEach(v => {
      const y = pad.top+gH*(1-v/100);
      ctx.beginPath(); ctx.moveTo(pad.left,y); ctx.lineTo(W-pad.right,y);
      ctx.strokeStyle='rgba(255,255,255,0.04)'; ctx.lineWidth=1; ctx.stroke();
      ctx.fillStyle='rgba(138,154,184,0.6)'; ctx.font='9px Outfit'; ctx.textAlign='right';
      ctx.fillText(v+'%', pad.left-6, y+3);
    });

    // 꺾은선 그리기
    ctx.beginPath();
    vals.forEach((v,i) => {
      const x = pad.left+(i/Math.max(n-1,1))*gW;
      const y = pad.top+gH*(1-v/100);
      if (i === 0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    });
    ctx.strokeStyle = color; ctx.lineWidth = 2.5; ctx.lineJoin = 'round'; ctx.stroke();

    // 점 및 날짜 출력
    vals.forEach((v,i) => {
      const x = pad.left+(i/Math.max(n-1,1))*gW;
      const y = pad.top+gH*(1-v/100);
      ctx.beginPath(); ctx.arc(x,y,4,0,Math.PI*2); ctx.fillStyle=color; ctx.fill();
      ctx.fillStyle='#fff'; ctx.beginPath(); ctx.arc(x,y,2,0,Math.PI*2); ctx.fillStyle='#080c18'; ctx.fill();
      
      const d = new Date(sessions[i].timestamp);
      ctx.fillStyle='rgba(138,154,184,0.7)'; ctx.font='9px Outfit'; ctx.textAlign='center';
      ctx.fillText(`${d.getMonth()+1}/${d.getDate()}`, x, H-4);
    });
  }

  // ─── 10. AI 검증 시뮬레이터 대시보드 (신규 추가) ──────────────────
  async function renderValidationDashboard(root) {
    root.innerHTML = `
      <div class="screen validation-screen">
        <button class="back-btn" id="btn-back">← 홈으로</button>
        <h2 class="screen-title" style="margin-bottom:6px;">🤖 AI 검증 테스트 베드</h2>
        <p style="font-size:12px;color:var(--text-secondary);line-height:1.6;margin-bottom:16px;">
          본 화면은 <strong>'양선우 팀 작품설명서 보강안'</strong>의 핵심인 <strong>'모의 데이터 10회 검증 기조'</strong>를 증명하는 대시보드입니다. 모의 환자 5인의 훈련 데이터 총 50세션을 시뮬레이션하고 AI 추천 규칙의 정밀도 및 안전장치 규칙 통과 상태를 수치로 검증합니다.
        </p>

        <div class="card" style="padding:16px;text-align:center;margin-bottom:16px;background:rgba(0,212,255,0.02);border-color:rgba(0,212,255,0.2);">
          <div style="font-size:12px;color:var(--text-secondary);margin-bottom:8px;">시뮬레이션 통과 상태</div>
          <div id="val-summary-status" style="font-size:22px;font-weight:800;color:var(--text-muted);">대기 중</div>
          <button class="btn btn-primary mt-2" id="btn-run-simulation" style="width:auto;padding:8px 20px;font-size:13px;">➔ 검증 시뮬레이션 즉시 가동</button>
        </div>

        <div id="validation-details-area" class="hidden">
          <div class="section-title">성공 기준 검증 매트릭스 판정</div>
          <div class="card" style="padding:14px;margin-bottom:16px;">
            <div id="criteria-checklist" style="display:flex;flex-direction:column;gap:8px;"></div>
          </div>

          <div class="section-title">모의 환자별 AI 분석 & 추천 매칭 결과</div>
          <div id="sim-profiles-list" style="display:flex;flex-direction:column;gap:10px;"></div>
        </div>
      </div>
    `;

    document.getElementById('btn-back').addEventListener('click', () => navigateTo('home'));
    
    document.getElementById('btn-run-simulation').addEventListener('click', async () => {
      const btn = document.getElementById('btn-run-simulation');
      btn.innerHTML = '⏳ 모의 세션 연산 중...'; btn.disabled = true;
      
      setTimeout(async () => {
        const testResult = await Storage.runValidationTest();
        btn.innerHTML = '✔ 검증 연산 완료';
        showToast('✅ 모의 환자 5인 50세션 데이터 AI 검증 완료!');
        
        document.getElementById('validation-details-area').classList.remove('hidden');
        renderValidationResults(testResult);
      }, 800);
    });
  }

  function renderValidationResults(testResult) {
    const { testResults, summary } = testResult;
    
    // 종합 판정 UI 업데이트
    const statusEl = document.getElementById('val-summary-status');
    if (summary.finalPassed) {
      statusEl.innerHTML = `<span style="color:var(--accent-green);">★ 최종 검증 통과 (SUCCESS)</span>`;
      statusEl.parentNode.style.borderColor = 'var(--accent-green)';
      statusEl.parentNode.style.background = 'rgba(0,255,148,0.03)';
    } else {
      statusEl.innerHTML = `<span style="color:var(--accent-red);">⚠ 검증 실패 (FAILED)</span>`;
      statusEl.parentNode.style.borderColor = 'var(--accent-red)';
    }

    // 4대 성공 기준 표시
    // 기준 1: 취약 영역 추천 80% 이상
    const c1Passed = summary.passedSim >= 4;
    // 기준 2: 수치화 근거 제시
    const c2Passed = testResults.every(r => r.criteria.criterion2);
    // 기준 3: 피로/통증 시 100% 중단
    const c3Passed = summary.isSafetyStopPassed;
    // 기준 4: 비의료 순화적 설명
    const c4Passed = testResults.every(r => r.criteria.criterion4);

    const checklistEl = document.getElementById('criteria-checklist');
    checklistEl.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:between;font-size:12px;">
        <span><strong>기준 1:</strong> 설계된 취약 영역 추천의 정확도 (80% 이상)</span>
        <span style="flex:1;"></span>
        <span style="font-weight:700;color:${c1Passed?'var(--accent-green)':'var(--accent-red)'}">
          ${c1Passed ? '✔ 통과' : '✗ 실패'} (${summary.passedSim}/5 명)
        </span>
      </div>
      <div style="display:flex;align-items:center;justify-content:between;font-size:12px;">
        <span><strong>기준 2:</strong> 추천 이유 내 정량적 수치 지표 명시</span>
        <span style="flex:1;"></span>
        <span style="font-weight:700;color:${c2Passed?'var(--accent-green)':'var(--accent-red)'}">
          ${c2Passed ? '✔ 통과 (100% 수치 포함)' : '✗ 실패'}
        </span>
      </div>
      <div style="display:flex;align-items:center;justify-content:between;font-size:12px;">
        <span><strong>기준 3:</strong> 피로 입력 즉시 추천 중단 및 가이드 강제 작동</span>
        <span style="flex:1;"></span>
        <span style="font-weight:700;color:${c3Passed?'var(--accent-green)':'var(--accent-red)'}">
          ${c3Passed ? '✔ 통과 (최피로 차단 완료)' : '✗ 실패'}
        </span>
      </div>
      <div style="display:flex;align-items:center;justify-content:between;font-size:12px;">
        <span><strong>기준 4:</strong> 치료·진단 배제 등 비의료 순화 표현 가이드 준수</span>
        <span style="flex:1;"></span>
        <span style="font-weight:700;color:${c4Passed?'var(--accent-green)':'var(--accent-red)'}">
          ${c4Passed ? '✔ 통과 (순화어 사용)' : '✗ 실패'}
        </span>
      </div>
    `;

    // 모의 환자 개별 결과 상세 렌더링
    const listEl = document.getElementById('sim-profiles-list');
    listEl.innerHTML = testResults.map(tr => {
      const p = tr.profile;
      const a = tr.analysis;
      
      const LABELS = { memory_sequence:'기억 카드', attention_stroop:'색-동작 반응', motor_response:'손가락 순서', none:'없음' };
      
      return `
        <div class="card" style="padding:14px;background:rgba(255,255,255,0.01);border-color:${tr.passed?'var(--border)':'var(--accent-red)'}">
          <div style="display:flex;align-items:center;justify-content:between;margin-bottom:8px;">
            <strong style="color:var(--text-primary);font-size:13px;">${p.name} (만 ${p.age}세)</strong>
            <span style="flex:1;"></span>
            <span style="font-size:10px;padding:2px 8px;border-radius:4px;font-weight:700;color:#fff;background:${tr.passed?'var(--accent-green)':'var(--accent-red)'}">
              ${tr.passed ? 'PASSED' : 'FAILED'}
            </span>
          </div>
          <div style="font-size:11px;color:var(--text-secondary);display:flex;flex-direction:column;gap:3px;">
            <div>• 의도적 설계 취약점: <strong style="color:var(--accent-cyan);">${LABELS[p.weakGame]}</strong></div>
            <div>• AI가 검출한 취약점: <strong style="color:${a.weakAreas.length>0?'var(--accent-red)':'var(--accent-green)'};">${a.weakAreas.map(wa => LABELS[wa]).join(', ') || '없음'}</strong></div>
            <div>• 판정 등급 점수: <strong>${a.overallScore}점</strong></div>
            <div style="margin-top:6px;background:rgba(0,0,0,0.15);padding:8px;border-radius:4px;border:1px solid var(--border);">
              <div style="font-weight:700;color:var(--text-primary);margin-bottom:2px;">🤖 AI 피드백 문구:</div>
              <p style="color:var(--text-secondary);line-height:1.4;">${a.recommendations[0]?.message || '추천 없음'}</p>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  // ─── 공통 유틸 ────────────────────────────────────────────────
  function getGrade(score) {
    if (score >= 90) return {label:'우수 관리',   color:'#00D4FF', emoji:'🌟'};
    if (score >= 75) return {label:'양호 관리',   color:'#00FF94', emoji:'✅'};
    if (score >= 60) return {label:'보통 단계',   color:'#FFB800', emoji:'📈'};
    return                  {label:'보강 훈련 요망',color:'#FF6B6B', emoji:'⚠️'};
  }

  function showToast(msg) {
    const el = document.createElement('div');
    el.className = 'toast show';
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => { el.classList.remove('show'); setTimeout(() => el.remove(), 400); }, 2800);
  }

  return { init, navigateTo, showToast };
})();

App.init();
