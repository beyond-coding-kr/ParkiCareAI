from datetime import datetime
from database import GlobalStats

GAME_TYPES = ['memory_sequence', 'attention_stroop', 'motor_response']
ACCURACY_THRESHOLD = 0.70
RESPONSE_TIME_RATIO = 1.30

def avg(arr):
    if not arr:
        return 0.0
    return sum(arr) / len(arr)

def get_global_stats():
    rows = GlobalStats.query.all()
    return {r.game_type: r.avg_response_time for r in rows}

def is_weak_area(sessions, game_type):
    if not sessions:
        return False
    recent = sessions[-3:]
    
    avg_accuracy = avg([s['accuracy'] for s in recent])
    avg_response_time = avg([s['avgResponseTime'] for s in recent])
    
    global_stats = get_global_stats()
    global_avg = global_stats.get(game_type, 2000.0)

    is_acc_weak = avg_accuracy < ACCURACY_THRESHOLD
    is_time_weak = avg_response_time > (global_avg * RESPONSE_TIME_RATIO)

    return is_acc_weak or is_time_weak

def calc_difficulty(sessions):
    if not sessions:
        return 2
    last_session = sessions[-1]
    prev_diff = last_session.get('difficulty', 2)
    avg_accuracy = last_session.get('accuracy', 0.0)
    
    next_diff = prev_diff
    if avg_accuracy >= 0.80:
        next_diff += 1
    elif avg_accuracy < 0.60:
        next_diff -= 1

    return max(1, min(5, next_diff))

def calc_trend(sessions):
    if not sessions or len(sessions) < 2:
        return 'stable'
    recent = sessions[-3:]
    if len(recent) < 2:
        return 'stable'
    
    first_acc = recent[0]['accuracy']
    last_acc = recent[-1]['accuracy']
    diff = last_acc - first_acc

    if diff > 0.1:
        return 'improving'
    if diff < -0.1:
        return 'declining'
    return 'stable'

def generate_recommendations(weak_profile):
    recs = []
    GAME_LABELS = {
        'memory_sequence': '기억력 훈련',
        'attention_stroop': '집중력 훈련',
        'motor_response': '운동 훈련',
    }

    for area in weak_profile['weakAreas']:
        game = weak_profile['games'][area]
        recs.append({
            'type': area,
            'priority': 'high',
            'message': f"{GAME_LABELS[area]}에서 취약점이 발견되었습니다. 난이도 {game['recommendedDifficulty']} 단계 집중 훈련을 권장합니다.",
            'label': GAME_LABELS[area],
        })

    for area in weak_profile['strongAreas']:
        game = weak_profile['games'][area]
        if game['trend'] == 'improving':
            recs.append({
                'type': area,
                'priority': 'low',
                'message': f"{GAME_LABELS[area]}이 꾸준히 향상되고 있습니다! 계속 유지하세요.",
                'label': GAME_LABELS[area],
            })

    if not weak_profile['weakAreas'] and weak_profile['overallScore'] > 0:
        recs.append({
            'type': 'general',
            'priority': 'info',
            'message': '모든 영역에서 양호한 수준입니다. 꾸준한 훈련을 유지하세요!',
            'label': '전체',
        })

    return recs

def analyze(profile_id, get_sessions_fn):
    weak_profile = {
        'profileId': profile_id,
        'analyzedAt': datetime.utcnow().isoformat() + "Z",
        'games': {},
        'overallScore': 0,
        'weakAreas': [],
        'strongAreas': [],
        'recommendations': [],
    }

    total_score = 0
    game_count = 0

    for game_type in GAME_TYPES:
        sessions = get_sessions_fn(profile_id, game_type)
        has_enough_data = len(sessions) >= 1
        recent = sessions[-3:]

        accuracy = avg([s['accuracy'] for s in recent]) if has_enough_data else None
        response_time = avg([s['avgResponseTime'] for s in recent]) if has_enough_data else None
        difficulty = calc_difficulty(sessions)
        trend = calc_trend(sessions)
        weak = is_weak_area(sessions, game_type)

        weak_profile['games'][game_type] = {
            'sessionCount': len(sessions),
            'hasEnoughData': has_enough_data,
            'accuracy': accuracy,
            'responseTime': response_time,
            'difficulty': difficulty,
            'trend': trend,
            'isWeak': weak,
            'recommendedDifficulty': difficulty,
        }

        if has_enough_data:
            score = round(accuracy * 100)
            total_score += score
            game_count += 1
            if weak:
                weak_profile['weakAreas'].append(game_type)
            else:
                weak_profile['strongAreas'].append(game_type)

    weak_profile['overallScore'] = round(total_score / game_count) if game_count > 0 else 0
    weak_profile['recommendations'] = generate_recommendations(weak_profile)

    return weak_profile
