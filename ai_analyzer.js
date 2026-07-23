const GAME_TYPES = ['memory_sequence', 'attention_stroop', 'motor_response'];
const ACCURACY_THRESHOLD = 0.70;
const RESPONSE_TIME_RATIO = 1.30;

function avg(arr) {
  if (!arr || arr.length === 0) return 0.0;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

async function get_global_stats(GlobalStats) {
  const rows = await GlobalStats.findAll();
  let stats = {};
  for (let r of rows) {
    stats[r.game_type] = r.avg_response_time;
  }
  return stats;
}

async function is_weak_area(sessions, game_type, GlobalStats) {
  if (!sessions || sessions.length === 0) return false;
  const recent = sessions.slice(-3);
  
  const avg_accuracy = avg(recent.map(s => s.accuracy));
  const avg_response_time = avg(recent.map(s => s.avgResponseTime || s.avg_response_time));
  
  const global_stats = await get_global_stats(GlobalStats);
  const global_avg = global_stats[game_type] || 2000.0;
  
  const is_acc_weak = avg_accuracy < ACCURACY_THRESHOLD;
  const is_time_weak = avg_response_time > (global_avg * RESPONSE_TIME_RATIO);
  
  return is_acc_weak || is_time_weak;
}

function calc_difficulty(sessions) {
  if (!sessions || sessions.length === 0) return 2;
  const last_session = sessions[sessions.length - 1];
  const prev_diff = last_session.difficulty !== undefined ? last_session.difficulty : 2;
  const avg_accuracy = last_session.accuracy !== undefined ? last_session.accuracy : 0.0;
  
  let next_diff = prev_diff;
  if (avg_accuracy >= 0.80) {
    next_diff += 1;
  } else if (avg_accuracy < 0.60) {
    next_diff -= 1;
  }
  
  return Math.max(0, Math.min(5, next_diff));
}

function calc_trend(sessions) {
  if (!sessions || sessions.length < 2) return 'stable';
  const recent = sessions.slice(-3);
  if (recent.length < 2) return 'stable';
  
  const first_acc = recent[0].accuracy;
  const last_acc = recent[recent.length - 1].accuracy;
  const diff = last_acc - first_acc;
  
  if (diff > 0.1) return 'improving';
  if (diff < -0.1) return 'declining';
  return 'stable';
}

function generate_recommendations(weak_profile) {
  const recs = [];
  const GAME_LABELS = {
    'memory_sequence': '기억력 훈련',
    'attention_stroop': '집중력 훈련',
    'motor_response': '운동 훈련',
  };
  
  for (let area of weak_profile.weakAreas) {
    let game = weak_profile.games[area];
    recs.push({
      type: area,
      priority: 'high',
      message: `${GAME_LABELS[area]}에서 취약점이 발견되었습니다. 난이도 ${game.recommendedDifficulty} 단계 집중 훈련을 권장합니다.`,
      label: GAME_LABELS[area]
    });
  }
  
  for (let area of weak_profile.strongAreas) {
    let game = weak_profile.games[area];
    if (game.trend === 'improving') {
      recs.push({
        type: area,
        priority: 'low',
        message: `${GAME_LABELS[area]}이 꾸준히 향상되고 있습니다! 계속 유지하세요.`,
        label: GAME_LABELS[area]
      });
    }
  }
  
  if (weak_profile.weakAreas.length === 0 && weak_profile.overallScore > 0) {
    recs.push({
      type: 'general',
      priority: 'info',
      message: '모든 영역에서 양호한 수준입니다. 꾸준한 훈련을 유지하세요!',
      label: '전체'
    });
  }
  
  return recs;
}

async function analyze(profile_id, get_sessions_fn, GlobalStats) {
  const weak_profile = {
    profileId: profile_id,
    analyzedAt: new Date().toISOString(),
    games: {},
    overallScore: 0,
    weakAreas: [],
    strongAreas: [],
    recommendations: []
  };
  
  let total_score = 0;
  let game_count = 0;
  
  for (let game_type of GAME_TYPES) {
    const sessions = await get_sessions_fn(profile_id, game_type);
    const has_enough_data = sessions.length >= 1;
    const recent = sessions.slice(-3);
    
    let accuracy = null;
    let response_time = null;
    if (has_enough_data) {
      accuracy = avg(recent.map(s => s.accuracy));
      response_time = avg(recent.map(s => s.avgResponseTime || s.avg_response_time));
    }
    const difficulty = calc_difficulty(sessions);
    const trend = calc_trend(sessions);
    const weak = await is_weak_area(sessions, game_type, GlobalStats);
    
    weak_profile.games[game_type] = {
      sessionCount: sessions.length,
      hasEnoughData: has_enough_data,
      accuracy: accuracy,
      responseTime: response_time,
      difficulty: difficulty,
      trend: trend,
      isWeak: weak,
      recommendedDifficulty: difficulty
    };
    
    if (has_enough_data) {
      const score = Math.round(accuracy * 100);
      total_score += score;
      game_count += 1;
      if (weak) {
        weak_profile.weakAreas.push(game_type);
      } else {
        weak_profile.strongAreas.push(game_type);
      }
    }
  }
  
  weak_profile.overallScore = game_count > 0 ? Math.round(total_score / game_count) : 0;
  weak_profile.recommendations = generate_recommendations(weak_profile);
  
  return weak_profile;
}

module.exports = { analyze };
