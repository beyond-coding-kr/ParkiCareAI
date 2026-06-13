/**
 * ParkiCare AI - Storage & AI Engine Simulator Module
 * REST API 서버와의 연동을 기본으로 하되, 오프라인/서버 미구동 시 LocalStorage로 자동 Fallback.
 * 양선우 팀의 검증계획(모의 사용자 5명 * 10회 데이터)을 즉시 실행하고 판정할 수 있는 시뮬레이터를 포함합니다.
 */

const Storage = (() => {
  const BASE = '/api';
  const SESSION_KEY = 'parkicare_current_profile';

  // 로컬 폴백용 스토리지 키
  const LOCAL_KEYS = {
    PROFILES: 'parkicare_local_profiles',
    SESSIONS: 'parkicare_local_sessions_', // suffix: profileId
    WEAK_PROFILES: 'parkicare_local_weak_profiles_', // suffix: profileId
    GLOBAL_STATS: 'parkicare_local_global_stats'
  };

  // 기본 전역 통계 (초기값)
  const DEFAULT_GLOBAL_STATS = {
    memory_sequence: { avgResponseTime: 2200.0, count: 50 },
    attention_stroop: { avgResponseTime: 1400.0, count: 50 },
    motor_response: { avgResponseTime: 1800.0, count: 50 }
  };

  // 게임 라벨 매핑 (의료적 진단 표현 배제, 훈련/보조 표현 사용)
  const GAME_LABELS = {
    memory_sequence: '기억 카드 맞추기 훈련',
    attention_stroop: '색-동작 반응 훈련',
    motor_response: '손가락 순서 누르기 훈련'
  };

  // ─── 헬퍼: API 통신 및 폴백 제어 ──────────────────────────────────
  let isOfflineMode = false;

  async function _fetch(url, options = {}) {
    if (isOfflineMode) {
      throw new Error('Offline Mode Active');
    }
    try {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), 1500); // 1.5초 타임아웃

      const res = await fetch(BASE + url, {
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        ...options,
      });
      clearTimeout(id);
      
      const json = await res.json();
      if (!json.ok) throw new Error(json.error || 'API 오류');
      return json.data;
    } catch (e) {
      console.warn(`REST API 호출 실패 [${url}], 로컬 스토리지 모드로 자동 전환합니다. 사유: ${e.message}`);
      isOfflineMode = true; // 이후 자동 로컬 모드
      throw e;
    }
  }

  // ─── 로컬 스토리지 접근 헬퍼 ──────────────────────────────────────────
  function _getLocal(key, def = null) {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : def;
  }

  function _setLocal(key, val) {
    localStorage.setItem(key, JSON.stringify(val));
  }

  // ─── 프로필 ──────────────────────────────────────────────────────────
  async function getProfiles() {
    try {
      return await _fetch('/profiles');
    } catch (e) {
      return _getLocal(LOCAL_KEYS.PROFILES, []);
    }
  }

  async function saveProfile(profile) {
    try {
      return await _fetch('/profiles', {
        method: 'POST',
        body: JSON.stringify(profile),
      });
    } catch (e) {
      const list = _getLocal(LOCAL_KEYS.PROFILES, []);
      const newProfile = {
        id: profile.id || `p_local_${Math.random().toString(36).substr(2, 9)}`,
        name: profile.name,
        age: parseInt(profile.age),
        stage: profile.stage || 'stage1',
        diagnosis: profile.diagnosis || '',
        color: profile.color || '#00D4FF',
        createdAt: new Date().toISOString()
      };
      list.push(newProfile);
      _setLocal(LOCAL_KEYS.PROFILES, list);
      return newProfile;
    }
  }

  async function deleteProfile(id) {
    try {
      return await _fetch(`/profiles/${id}`, { method: 'DELETE' });
    } catch (e) {
      let list = _getLocal(LOCAL_KEYS.PROFILES, []);
      list = list.filter(p => p.id !== id);
      _setLocal(LOCAL_KEYS.PROFILES, list);
      localStorage.removeItem(LOCAL_KEYS.SESSIONS + id);
      localStorage.removeItem(LOCAL_KEYS.WEAK_PROFILES + id);
      return { deleted: id };
    }
  }

  function getCurrentProfile() {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  }

  function setCurrentProfile(profileData) {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(profileData));
  }

  function clearCurrentProfile() {
    sessionStorage.removeItem(SESSION_KEY);
  }

  // ─── 세션 기록 ────────────────────────────────────────────────────────
  async function getSessions(profileId, gameType) {
    try {
      return await _fetch(`/sessions/${profileId}/${gameType}`);
    } catch (e) {
      const all = _getLocal(LOCAL_KEYS.SESSIONS + profileId, []);
      return all.filter(s => s.gameType === gameType);
    }
  }

  async function saveSession(profileId, gameType, sessionData) {
    const payload = {
      profileId,
      gameType,
      accuracy: parseFloat(sessionData.accuracy),
      avgResponseTime: parseFloat(sessionData.avgResponseTime),
      correctCount: parseInt(sessionData.correctCount),
      totalRounds: parseInt(sessionData.totalRounds),
      missCount: parseInt(sessionData.missCount || 0),
      difficulty: parseInt(sessionData.difficulty),
      fatigue: parseInt(sessionData.fatigue || 1), // 피로도 (1: 좋음 ~ 4: 심함)
      timestamp: sessionData.timestamp || new Date().toISOString()
    };

    try {
      const saved = await _fetch('/sessions', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      // 전역 통계 자동 업데이트 유도
      await updateGlobalStats(gameType, payload.avgResponseTime);
      return saved;
    } catch (e) {
      const key = LOCAL_KEYS.SESSIONS + profileId;
      const list = _getLocal(key, []);
      const newSession = {
        id: list.length + 1,
        ...payload
      };
      list.push(newSession);
      _setLocal(key, list);

      // 전역 통계 업데이트
      await updateGlobalStats(gameType, payload.avgResponseTime);
      return newSession;
    }
  }

  // ─── 전역 통계 관리 ───────────────────────────────────────────────────
  async function getGlobalStats() {
    try {
      return await _fetch('/global-stats');
    } catch (e) {
      return _getLocal(LOCAL_KEYS.GLOBAL_STATS, DEFAULT_GLOBAL_STATS);
    }
  }

  async function updateGlobalStats(gameType, responseTime) {
    try {
      // 서버에서 세션 저장 시 처리하지만 오프라인 시를 위해 호출만 해둠
      await _fetch('/global-stats');
    } catch (e) {
      const stats = _getLocal(LOCAL_KEYS.GLOBAL_STATS, DEFAULT_GLOBAL_STATS);
      if (stats[gameType]) {
        const s = stats[gameType];
        s.avgResponseTime = (s.avgResponseTime * s.count + responseTime) / (s.count + 1);
        s.count += 1;
        _setLocal(LOCAL_KEYS.GLOBAL_STATS, stats);
      }
    }
  }

  // ─── 규칙 기반 AI 분석 엔진 (JS 구현체) ──────────────────────────────
  // 파킨슨 환자 기록에 따른 정교한 분석 규칙 적용
  function runLocalAnalysisRule(profileId, sessionsByType, globalStats) {
    const games = {};
    let totalScore = 0;
    let gameCount = 0;
    const weakAreas = [];
    const strongAreas = [];
    const gameTypes = ['memory_sequence', 'attention_stroop', 'motor_response'];

    // 분석에 필요한 최소 세션 수
    const MIN_SESSIONS = 3; 

    // 안전 확인 규칙: 가장 최근 수행 중 심한 피로/통증/어지러움이 입력되었는지 확인
    let safetyTriggered = false;
    let safetyMessage = '';

    for (const gt of gameTypes) {
      const sessions = sessionsByType[gt] || [];
      const hasData = sessions.length >= MIN_SESSIONS;
      const recent = sessions.slice(-MIN_SESSIONS);

      // 피로도 안전장치 점검 (최근 1회 세션 기준 fatigue 가 4(심한 피로/통증/어지러움) 인 경우)
      if (sessions.length > 0) {
        const lastSession = sessions[sessions.length - 1];
        if (lastSession.fatigue >= 4) {
          safetyTriggered = true;
          safetyMessage = `⚠️ [안전 주의] 최근 ${GAME_LABELS[lastSession.gameType]} 훈련 도중 극심한 피로, 통증 또는 어지러움이 기록되었습니다. 훈련을 즉시 중단하고 충분한 휴식을 취하시거나 보호자/전문가의 상담을 받으시기 바랍니다.`;
        }
      }

      let accuracy = null;
      let rt = null;
      let isWeak = false;
      let difficulty = 1;
      let trend = 'stable';

      if (hasData) {
        accuracy = recent.reduce((sum, s) => sum + s.accuracy, 0) / MIN_SESSIONS;
        rt = recent.reduce((sum, s) => sum + s.avgResponseTime, 0) / MIN_SESSIONS;
        
        // 해당 게임 전체 세션에 대한 평균과 최근 3회 평균 비교
        const allAvgRt = sessions.reduce((sum, s) => sum + s.avgResponseTime, 0) / sessions.length;
        const globalAvgRt = globalStats[gt]?.avgResponseTime || DEFAULT_GLOBAL_STATS[gt].avgResponseTime;

        // 취약 판정 규칙: 
        // 1) 최근 3회 평균 정답률이 70% 미만이거나
        // 2) 최근 3회 평균 반응 속도가 전역 기준치의 1.3배를 초과하거나
        // 3) 본인의 이전 세션 평균보다 최근 3회 응답 속도가 25% 이상 늘어난 경우 (지연 현상)
        const isAccuracyWeak = accuracy < 0.70;
        const isRtWeak = rt > globalAvgRt * 1.30;
        const isSelfDeclining = sessions.length > MIN_SESSIONS && (rt > allAvgRt * 1.25);

        isWeak = isAccuracyWeak || isRtWeak || isSelfDeclining;

        // 난이도 결정 (정답률이 높고 피로 입력이 없을 때만 단계 상승)
        const hasFatigueInRecent = recent.some(s => s.fatigue >= 3);
        const lastSession = recent[recent.length - 1];
        
        if (lastSession.accuracy >= 0.85 && !hasFatigueInRecent) {
          difficulty = Math.min(5, lastSession.difficulty + 1); // 1단계 상승
        } else if (isWeak || hasFatigueInRecent || lastSession.fatigue >= 4) {
          difficulty = Math.max(1, lastSession.difficulty - 1); // 1단계 하향
        } else {
          difficulty = lastSession.difficulty; // 유지
        }

        // 트렌드 분석
        const half = Math.max(1, Math.floor(sessions.length / 2));
        const firstHalfAcc = sessions.slice(0, half).reduce((sum, s) => sum + s.accuracy, 0) / half;
        const secondHalfAcc = sessions.slice(-half).reduce((sum, s) => sum + s.accuracy, 0) / half;
        const diff = secondHalfAcc - firstHalfAcc;
        if (diff > 0.05) trend = 'improving';
        else if (diff < -0.05) trend = 'declining';
        else trend = 'stable';
      }

      games[gt] = {
        sessionCount: sessions.length,
        hasEnoughData: hasData,
        accuracy: accuracy,
        responseTime: rt,
        difficulty: difficulty,
        trend: trend,
        isWeak: isWeak,
        recommendedDifficulty: isWeak ? Math.max(1, difficulty) : difficulty
      };

      if (hasData) {
        totalScore += Math.round(accuracy * 100);
        gameCount++;
        if (isWeak) weakAreas.push(gt);
        else strongAreas.push(gt);
      }
    }

    const overallScore = gameCount > 0 ? Math.round(totalScore / gameCount) : 0;
    
    // 추천 리스트 생성 (의료 진단 표현 절대 금지, 숫자로 이유 명시)
    const recommendations = [];

    // 안전 확인 경고가 켜진 경우 최우선 배치
    if (safetyTriggered) {
      recommendations.push({
        type: 'safety_stop',
        priority: 'high',
        message: safetyMessage,
        label: '안전 보조 경고'
      });
    }

    weakAreas.forEach(area => {
      const g = games[area];
      const globalAvg = globalStats[area]?.avgResponseTime || DEFAULT_GLOBAL_STATS[area].avgResponseTime;
      const ratio = g.responseTime ? (g.responseTime / globalAvg).toFixed(1) : '1.3';
      
      let reason = '';
      if (g.accuracy < 0.70) {
        reason = `최근 3회 평균 정답률이 ${(g.accuracy * 100).toFixed(0)}%로 훈련 통과 기준(70%)보다 낮습니다.`;
      } else {
        reason = `최근 3회 평균 응답 시간이 ${(g.responseTime / 1000).toFixed(2)}초로 기준치(${(globalAvg / 1000).toFixed(2)}초) 대비 약 ${ratio}배 지연되었습니다.`;
      }

      recommendations.push({
        type: area,
        priority: safetyTriggered ? 'medium' : 'high',
        message: `📋 [추천] ${GAME_LABELS[area]}을 보강 훈련으로 추천합니다. (이유: ${reason} 맞춤형 난이도 ${g.recommendedDifficulty}로 설정을 조절합니다.)`,
        label: GAME_LABELS[area]
      });
    });

    strongAreas.forEach(area => {
      const g = games[area];
      if (g.trend === 'improving') {
        recommendations.push({
          type: area,
          priority: 'low',
          message: `✨ [유지] ${GAME_LABELS[area]} 훈련의 정확도가 점진적으로 우수해지고 있습니다! 이 페이스를 지속하여 일일 훈련 기록으로 유지하세요.`,
          label: GAME_LABELS[area]
        });
      }
    });

    if (weakAreas.length === 0 && gameCount > 0) {
      recommendations.push({
        type: 'general',
        priority: 'info',
        message: `👍 모든 훈련 영역이 관리 기준 범위 내에 원활하게 유지되고 있습니다. 꾸준한 반복 플레이를 통해 기능 유지 및 기록 관리를 하시기 바랍니다.`,
        label: '종합'
      });
    }

    return {
      profileId,
      overallScore,
      games,
      weakAreas,
      strongAreas,
      recommendations,
      safetyTriggered,
      analyzedAt: new Date().toISOString()
    };
  }

  // ─── 취약 프로파일 가져오기 및 분석 실행 ────────────────────────────
  async function getWeakProfile(profileId) {
    try {
      return await _fetch(`/weak-profile/${profileId}`);
    } catch (e) {
      return _getLocal(LOCAL_KEYS.WEAK_PROFILES + profileId, null);
    }
  }

  async function analyzeProfile(profileId) {
    try {
      // 서버 분석 호출
      const result = await _fetch(`/analyze/${profileId}`);
      return result;
    } catch (e) {
      // 로컬 분석 수행 및 저장
      const sessionsByType = {};
      const gameTypes = ['memory_sequence', 'attention_stroop', 'motor_response'];
      for (const gt of gameTypes) {
        sessionsByType[gt] = await getSessions(profileId, gt);
      }
      const globalStats = await getGlobalStats();
      const analysis = runLocalAnalysisRule(profileId, sessionsByType, globalStats);

      _setLocal(LOCAL_KEYS.WEAK_PROFILES + profileId, analysis);
      return analysis;
    }
  }

  // ─── 문제 생성 (로컬/서버) ──────────────────────────────────────────
  async function getProblem(profileId, gameType) {
    try {
      return await _fetch(`/problem/${profileId}/${gameType}`);
    } catch (e) {
      // 로컬 문제 생성
      const wp = _getLocal(LOCAL_KEYS.WEAK_PROFILES + profileId, null);
      const diff = wp?.games?.[gameType]?.recommendedDifficulty || 2;
      return generateLocalProblem(gameType, diff);
    }
  }

  function generateLocalProblem(gameType, difficulty) {
    if (gameType === 'memory_sequence') {
      // 3~7개 카드 매칭용 수열 혹은 상태
      const numCards = 2 + difficulty; // 난이도 1: 3개, 5: 7개
      const sequence = Array.from({length: numCards}, () => Math.floor(Math.random()*9)+1);
      return {
        type: 'memory_sequence',
        difficulty,
        sequence,
        displayTime: Math.max(1200, 3800 - difficulty * 400),
        description: `제시되는 숫자 ${numCards}개를 순서대로 잘 기억하고 똑같이 입력해보세요.`
      };
    } else if (gameType === 'attention_stroop') {
      const colors = [
        {name: '빨강', hex: '#FF4444'},
        {name: '파랑', hex: '#4488FF'},
        {name: '초록', hex: '#44CC44'},
        {name: '노랑', hex: '#FFCC00'}
      ];
      const problems = Array.from({length: 3 + difficulty}, () => {
        const textOpt = colors[Math.floor(Math.random() * colors.length)];
        // 스트룹 간섭 효과를 극대화하기 위해 글자 텍스트와 실제 색상을 불일치 시킴
        const colorOpt = colors.filter(c => c.name !== textOpt.name)[Math.floor(Math.random() * (colors.length - 1))];
        return {
          text: textOpt.name, // 글자 내용 (예: "파랑")
          textColor: colorOpt.hex, // 글자 색상 (예: 초록색)
          correctAnswer: colorOpt.name, // 정답은 글자 색상인 "초록"
          options: [...colors].sort(() => Math.random() - 0.5),
          timeLimit: Math.max(800, 2600 - difficulty * 300)
        };
      });
      return {
        type: 'attention_stroop',
        difficulty,
        problems,
        description: `화면에 나타나는 글자의 <strong>글자 색상</strong>을 빠르게 고르세요. (예: 빨강 색상으로 적힌 '파랑' 글자면 정답은 '빨강')`
      };
    } else {
      // motor_response: 손가락 순서 누르기 (1,2,3,4 번호 순서대로 누르기)
      const targetCount = Math.min(6, 3 + difficulty);
      return {
        type: 'motor_response',
        difficulty,
        targetCount,
        timeLimit: Math.max(600, 2200 - difficulty * 250),
        description: `화면에 생기는 번호 원들을 반드시 <strong>1부터 순서대로(1 ➔ 2 ➔ 3)</strong> 빠르게 터치하세요.`
      };
    }
  }

  // ─── 양선우 팀 모의 데이터 10회분 AI 검증 시뮬레이터 ─────────────────
  async function runValidationTest() {
    const simProfiles = [
      { id: 'p_sim_1', name: '김기억 (기억력 취약 유형)', age: 68, stage: 'stage2', diagnosis: '2024년 2월', color: '#00D4FF', weakGame: 'memory_sequence' },
      { id: 'p_sim_2', name: '이반응 (반응 지연 유형)', age: 72, stage: 'stage3', diagnosis: '2023년 5월', color: '#7B2FBE', weakGame: 'attention_stroop' },
      { id: 'p_sim_3', name: '박운동 (동작 조절 취약 유형)', age: 65, stage: 'stage2', diagnosis: '2025년 1월', color: '#00FF94', weakGame: 'motor_response' },
      { id: 'p_sim_4', name: '최피로 (피로안전 중단 유형)', age: 74, stage: 'stage4', diagnosis: '2022년 8월', color: '#FF6B6B', weakGame: 'none', testFatigue: true },
      { id: 'p_sim_5', name: '정안전 (안전 튜닝 유형)', age: 70, stage: 'stage2', diagnosis: '2024년 9월', color: '#FFB800', weakGame: 'none', testFatigueTuning: true }
    ];

    const testResults = [];
    const globalStats = DEFAULT_GLOBAL_STATS;

    for (const p of simProfiles) {
      const sessions = [];
      const gameTypes = ['memory_sequence', 'attention_stroop', 'motor_response'];

      // 10회분 (총 10 세션 / 각 게임별 고루 분산)의 모의 데이터 생성
      for (let i = 1; i <= 10; i++) {
        for (const gt of gameTypes) {
          let accuracy = 0.85 + Math.random() * 0.15; // 기본 85~100%
          let avgResponseTime = 1200 + Math.random() * 400; // 기본 1.2~1.6초
          let missCount = 0;
          let fatigue = 1; // 좋음

          // 피로 조건 환자인 최피로의 경우 9회, 10회 플레이 시 피로 상태(4)로 기록
          if (p.testFatigue && i >= 9) {
            fatigue = 4; // 심한 피로/통증/어지러움
          }

          // 피로 튜닝 환자 정안전의 경우 5회차에 피로도 3(보통/피곤) 기록하여 난이도 하향 튜닝 테스트
          if (p.testFatigueTuning && i === 5) {
            fatigue = 3;
          }

          // 취약 영역 설계
          if (gt === p.weakGame) {
            if (gt === 'memory_sequence') {
              accuracy = 0.45 + Math.random() * 0.15; // 45~60%의 낮은 정확도
              avgResponseTime = 2500 + Math.random() * 500;
            } else if (gt === 'attention_stroop') {
              accuracy = 0.88;
              avgResponseTime = 3000 + Math.random() * 400; // 3초 이상의 매우 느린 반응 시간
            } else if (gt === 'motor_response') {
              accuracy = 0.60;
              missCount = 5 + Math.floor(Math.random()*4); // 놓친 탭 수가 의도적으로 많음
              avgResponseTime = 2600 + Math.random() * 300;
            }
          }

          sessions.push({
            profileId: p.id,
            gameType: gt,
            accuracy,
            avgResponseTime,
            correctCount: Math.round(accuracy * 5),
            totalRounds: 5,
            missCount,
            difficulty: 2,
            fatigue,
            timestamp: new Date(Date.now() - (11 - i) * 24 * 60 * 60 * 1000).toISOString() // 일 단위 이전 기록으로 설정
          });
        }
      }

      // ── AI 추천 규칙 엔진 구동 ──
      const sessionsByType = {
        memory_sequence: sessions.filter(s => s.gameType === 'memory_sequence'),
        attention_stroop: sessions.filter(s => s.gameType === 'attention_stroop'),
        motor_response: sessions.filter(s => s.gameType === 'motor_response')
      };

      const analysis = runLocalAnalysisRule(p.id, sessionsByType, globalStats);

      // ── 검증 성공 항목 판정 ──
      let criterion1 = false; // 취약 영역 추천 일치 여부
      let criterion2 = false; // 수치 근거 제시 여부
      let criterion3 = false; // 피로 감지 시 중단 우선 여부
      let criterion4 = true;  // 비의료적 순화 표현 만족도

      // 성공 기준 1 판정: 취약 설계한 영역이 추천되었는가?
      if (p.weakGame !== 'none') {
        criterion1 = analysis.weakAreas.includes(p.weakGame);
      } else {
        criterion1 = analysis.weakAreas.length === 0; // 취약 없어야 정상
      }

      // 성공 기준 2 판정: 추천 메시지에 수치(%, 초 등)가 들어가 있는가?
      const weakRecs = analysis.recommendations.filter(r => r.type === p.weakGame);
      if (p.weakGame !== 'none' && weakRecs.length > 0) {
        const msg = weakRecs[0].message;
        criterion2 = /초|%|배/.test(msg); // 숫자나 지표 단위 검증
      } else {
        criterion2 = true; // 취약이 없는 경우 패스
      }

      // 성공 기준 3 판정: 피로 감지 시 중단 안내 최우선 출력 여부
      if (p.testFatigue) {
        const hasSafety = analysis.recommendations.some(r => r.type === 'safety_stop');
        criterion3 = hasSafety && (analysis.recommendations[0]?.type === 'safety_stop');
      } else {
        criterion3 = true; // 일반 환자는 패스
      }

      // 성공 기준 4 판정: "치료", "완치", "개선한다", "진단" 등의 비의료적 표현 순화 검출
      const allText = JSON.stringify(analysis);
      const bannedWords = ['치료한다', '완치', '치료법', '진단합니다', '의사 대행', '병을 고친다', '증상개선'];
      bannedWords.forEach(w => {
        if (allText.includes(w)) criterion4 = false;
      });

      testResults.push({
        profile: p,
        sessionsCount: sessions.length,
        analysis,
        criteria: { criterion1, criterion2, criterion3, criterion4 },
        passed: criterion1 && criterion2 && criterion3 && criterion4
      });
    }

    // 통과 요약 연산
    const totalSim = simProfiles.length;
    const passedSim = testResults.filter(r => r.passed).length;
    
    // 최종 검증 통과 조건: 5명 중 4명 이상 통과 && 최피로(피로 100% 중단) 반드시 통과
    const isSafetyStopPassed = testResults.find(r => r.profile.id === 'p_sim_4')?.criteria.criterion3 === true;
    const finalPassed = passedSim >= 4 && isSafetyStopPassed;

    return {
      testResults,
      summary: {
        totalSim,
        passedSim,
        finalPassed,
        isSafetyStopPassed
      }
    };
  }

  return {
    getProfiles, saveProfile, deleteProfile,
    getCurrentProfile, setCurrentProfile, clearCurrentProfile,
    getSessions, saveSession, updateGlobalStats,
    getWeakProfile, analyzeProfile,
    getProblem,
    getGlobalStats,
    runValidationTest
  };
})();
