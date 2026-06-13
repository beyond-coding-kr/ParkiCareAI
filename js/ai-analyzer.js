/**
 * ParkiCare AI - AI Analyzer Module
 * 세션 데이터를 분석하여 취약 영역을 진단하는 AI 모듈
 */

const AIAnalyzer = (() => {
  const GAME_TYPES = ['memory_sequence', 'attention_stroop', 'motor_response'];
  const ACCURACY_THRESHOLD = 0.70;   // 정답률 70% 미만 → 취약
  const RESPONSE_TIME_RATIO = 1.30;  // 전체 평균 130% 초과 → 취약
  const MIN_SESSIONS = 3;             // 분석을 위한 최소 세션 수

  // ─── 평균 계산 ────────────────────────────────────────────────
  function avg(arr) {
    if (!arr || arr.length === 0) return 0;
    return arr.reduce((a, b) => a + b, 0) / arr.length;
  }

  // ─── 단일 게임 취약 여부 판단 ─────────────────────────────────
  function isWeakArea(sessions, gameType) {
    if (!sessions || sessions.length < MIN_SESSIONS) return false;
    const recent = sessions.slice(-MIN_SESSIONS);
    const avgAccuracy = avg(recent.map(s => s.accuracy));
    const avgResponseTime = avg(recent.map(s => s.avgResponseTime));
    const globalStats = Storage.getGlobalStats();
    const globalAvg = globalStats[gameType]?.avgResponseTime || 2000;
    return avgAccuracy < ACCURACY_THRESHOLD || avgResponseTime > globalAvg * RESPONSE_TIME_RATIO;
  }

  // ─── 난이도 계산 (1~5) ────────────────────────────────────────
  function calcDifficulty(sessions) {
    if (!sessions || sessions.length < MIN_SESSIONS) return 1;
    const recent = sessions.slice(-MIN_SESSIONS);
    const avgAccuracy = avg(recent.map(s => s.accuracy));
    // 정확도에 따른 난이도 결정
    if (avgAccuracy >= 0.95) return 5;
    if (avgAccuracy >= 0.85) return 4;
    if (avgAccuracy >= 0.75) return 3;
    if (avgAccuracy >= 0.60) return 2;
    return 1;
  }

  // ─── 트렌드 분석 (개선/악화/유지) ────────────────────────────
  function calcTrend(sessions) {
    if (!sessions || sessions.length < 2) return 'insufficient';
    const half = Math.floor(sessions.length / 2);
    const firstHalf = sessions.slice(0, half);
    const secondHalf = sessions.slice(-half);
    const firstAvg = avg(firstHalf.map(s => s.accuracy));
    const secondAvg = avg(secondHalf.map(s => s.accuracy));
    const diff = secondAvg - firstAvg;
    if (diff > 0.05) return 'improving';
    if (diff < -0.05) return 'declining';
    return 'stable';
  }

  // ─── 전체 분석 실행 ───────────────────────────────────────────
  function analyze(profileId) {
    const weakProfile = {
      profileId,
      analyzedAt: new Date().toISOString(),
      games: {},
      overallScore: 0,
      weakAreas: [],
      strongAreas: [],
      recommendations: [],
    };

    let totalScore = 0;
    let gameCount = 0;

    GAME_TYPES.forEach(gameType => {
      const sessions = Storage.getSessions(profileId, gameType);
      const hasEnoughData = sessions.length >= MIN_SESSIONS;
      const recent = sessions.slice(-MIN_SESSIONS);

      const accuracy = hasEnoughData ? avg(recent.map(s => s.accuracy)) : null;
      const responseTime = hasEnoughData ? avg(recent.map(s => s.avgResponseTime)) : null;
      const difficulty = calcDifficulty(sessions);
      const trend = calcTrend(sessions);
      const weak = isWeakArea(sessions, gameType);

      weakProfile.games[gameType] = {
        sessionCount: sessions.length,
        hasEnoughData,
        accuracy,
        responseTime,
        difficulty,
        trend,
        isWeak: weak,
        recommendedDifficulty: weak ? Math.max(1, difficulty - 1) : difficulty,
      };

      if (hasEnoughData) {
        const score = Math.round(accuracy * 100);
        totalScore += score;
        gameCount++;
        if (weak) weakProfile.weakAreas.push(gameType);
        else weakProfile.strongAreas.push(gameType);
      }
    });

    weakProfile.overallScore = gameCount > 0 ? Math.round(totalScore / gameCount) : 0;
    weakProfile.recommendations = generateRecommendations(weakProfile);

    Storage.saveWeakProfile(profileId, weakProfile);
    return weakProfile;
  }

  // ─── 추천 메시지 생성 ─────────────────────────────────────────
  function generateRecommendations(weakProfile) {
    const recs = [];
    const GAME_LABELS = {
      memory_sequence: '기억력 훈련',
      attention_stroop: '집중력 훈련',
      motor_response: '운동 훈련',
    };

    weakProfile.weakAreas.forEach(area => {
      const game = weakProfile.games[area];
      recs.push({
        type: area,
        priority: 'high',
        message: `${GAME_LABELS[area]}에서 취약점이 발견되었습니다. 난이도 ${game.recommendedDifficulty}로 집중 훈련을 권장합니다.`,
        label: GAME_LABELS[area],
      });
    });

    weakProfile.strongAreas.forEach(area => {
      const game = weakProfile.games[area];
      if (game.trend === 'improving') {
        recs.push({
          type: area,
          priority: 'low',
          message: `${GAME_LABELS[area]}이 꾸준히 향상되고 있습니다! 계속 유지하세요.`,
          label: GAME_LABELS[area],
        });
      }
    });

    if (weakProfile.weakAreas.length === 0 && weakProfile.overallScore > 0) {
      recs.push({
        type: 'general',
        priority: 'info',
        message: '모든 영역에서 양호한 수준입니다. 꾸준한 훈련을 유지하세요!',
        label: '전체',
      });
    }

    return recs;
  }

  // ─── 퍼포먼스 점수 등급 ───────────────────────────────────────
  function getGrade(score) {
    if (score >= 90) return { label: '우수', color: '#00D4FF', emoji: '🌟' };
    if (score >= 75) return { label: '양호', color: '#00FF94', emoji: '✅' };
    if (score >= 60) return { label: '보통', color: '#FFB800', emoji: '📈' };
    return { label: '집중 필요', color: '#FF6B6B', emoji: '⚠️' };
  }

  return { analyze, isWeakArea, calcDifficulty, calcTrend, getGrade, GAME_TYPES, MIN_SESSIONS };
})();
