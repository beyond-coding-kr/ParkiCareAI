"""
ParkiCare AI - Python AI 분석 모듈
세션 데이터를 분석하여 취약 영역을 진단한다.
"""

import json
from datetime import datetime

GAME_TYPES = ['memory_sequence', 'attention_stroop', 'motor_response']
ACCURACY_THRESHOLD = 0.70    # 정답률 70% 미만 → 취약
RESPONSE_TIME_RATIO = 1.30   # 전체 평균 130% 초과 → 취약
MIN_SESSIONS = 3              # 분석 최소 세션 수

GAME_LABELS = {
    'memory_sequence':  '기억력 훈련',
    'attention_stroop': '집중력 훈련',
    'motor_response':   '운동 훈련',
}


# ─── 유틸 ──────────────────────────────────────────────────────────────────
def _avg(values: list) -> float:
    return sum(values) / len(values) if values else 0.0


def _is_weak(sessions: list, game_type: str, global_avg_rt: float) -> bool:
    """최근 MIN_SESSIONS 세션 기준으로 취약 여부 반환."""
    if len(sessions) < MIN_SESSIONS:
        return False
    recent = sessions[-MIN_SESSIONS:]
    avg_accuracy = _avg([s['accuracy'] for s in recent])
    avg_rt = _avg([s['avgResponseTime'] for s in recent])
    return avg_accuracy < ACCURACY_THRESHOLD or avg_rt > global_avg_rt * RESPONSE_TIME_RATIO


def _calc_difficulty(sessions: list) -> int:
    """정확도 기반 난이도(1~5) 계산."""
    if len(sessions) < MIN_SESSIONS:
        return 1
    recent = sessions[-MIN_SESSIONS:]
    avg_acc = _avg([s['accuracy'] for s in recent])
    if avg_acc >= 0.95: return 5
    if avg_acc >= 0.85: return 4
    if avg_acc >= 0.75: return 3
    if avg_acc >= 0.60: return 2
    return 1


def _calc_trend(sessions: list) -> str:
    """개선/악화/유지 추세 반환."""
    if len(sessions) < 2:
        return 'insufficient'
    half = max(len(sessions) // 2, 1)
    first_avg = _avg([s['accuracy'] for s in sessions[:half]])
    second_avg = _avg([s['accuracy'] for s in sessions[-half:]])
    diff = second_avg - first_avg
    if diff > 0.05:  return 'improving'
    if diff < -0.05: return 'declining'
    return 'stable'


def _generate_recommendations(weak_areas: list, strong_areas: list,
                               games: dict, overall_score: int) -> list:
    recs = []
    for area in weak_areas:
        g = games.get(area, {})
        recs.append({
            'type': area,
            'priority': 'high',
            'message': (f"{GAME_LABELS.get(area, area)}에서 취약점이 발견되었습니다. "
                        f"난이도 {g.get('recommendedDifficulty', 1)}로 집중 훈련을 권장합니다."),
            'label': GAME_LABELS.get(area, area),
        })
    for area in strong_areas:
        g = games.get(area, {})
        if g.get('trend') == 'improving':
            recs.append({
                'type': area,
                'priority': 'low',
                'message': f"{GAME_LABELS.get(area, area)}이 꾸준히 향상되고 있습니다! 계속 유지하세요.",
                'label': GAME_LABELS.get(area, area),
            })
    if not weak_areas and overall_score > 0:
        recs.append({
            'type': 'general',
            'priority': 'info',
            'message': '모든 영역에서 양호한 수준입니다. 꾸준한 훈련을 유지하세요!',
            'label': '전체',
        })
    return recs


# ─── 핵심 분석 함수 ────────────────────────────────────────────────────────
def analyze(profile_id: str, sessions_by_type: dict, global_stats: dict) -> dict:
    """
    profile_id     : 환자 ID
    sessions_by_type : { game_type: [session_dict, ...] }
    global_stats   : { game_type: { avgResponseTime, count } }
    반환값: weak_profile dict (DB 저장용)
    """
    games = {}
    total_score = 0
    game_count = 0
    weak_areas = []
    strong_areas = []

    for game_type in GAME_TYPES:
        sessions = sessions_by_type.get(game_type, [])
        has_data = len(sessions) >= MIN_SESSIONS
        recent = sessions[-MIN_SESSIONS:] if has_data else []

        accuracy = _avg([s['accuracy'] for s in recent]) if has_data else None
        rt = _avg([s['avgResponseTime'] for s in recent]) if has_data else None
        global_avg_rt = global_stats.get(game_type, {}).get('avgResponseTime', 2000.0)
        difficulty = _calc_difficulty(sessions)
        trend = _calc_trend(sessions)
        weak = _is_weak(sessions, game_type, global_avg_rt)

        games[game_type] = {
            'sessionCount': len(sessions),
            'hasEnoughData': has_data,
            'accuracy': accuracy,
            'responseTime': rt,
            'difficulty': difficulty,
            'trend': trend,
            'isWeak': weak,
            'recommendedDifficulty': max(1, difficulty - 1) if weak else difficulty,
        }

        if has_data:
            score = round(accuracy * 100)
            total_score += score
            game_count += 1
            (weak_areas if weak else strong_areas).append(game_type)

    overall_score = round(total_score / game_count) if game_count > 0 else 0
    recommendations = _generate_recommendations(weak_areas, strong_areas, games, overall_score)

    return {
        'profileId': profile_id,
        'overallScore': overall_score,
        'games': games,
        'weakAreas': weak_areas,
        'strongAreas': strong_areas,
        'recommendations': recommendations,
        'analyzedAt': datetime.utcnow().isoformat(),
    }


def get_grade(score: int) -> dict:
    """점수 등급 반환."""
    if score >= 90: return {'label': '우수',      'color': '#00D4FF', 'emoji': '🌟'}
    if score >= 75: return {'label': '양호',      'color': '#00FF94', 'emoji': '✅'}
    if score >= 60: return {'label': '보통',      'color': '#FFB800', 'emoji': '📈'}
    return              {'label': '집중 필요',  'color': '#FF6B6B', 'emoji': '⚠️'}
