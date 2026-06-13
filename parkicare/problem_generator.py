"""
ParkiCare AI - Python 문제 자동 생성 모듈
취약 프로파일 기반으로 다음 세션 문제를 생성한다.
"""

import random

COLORS = [
    {'name': '빨강', 'hex': '#FF4444'},
    {'name': '파랑', 'hex': '#4488FF'},
    {'name': '초록', 'hex': '#44CC44'},
    {'name': '노랑', 'hex': '#FFCC00'},
    {'name': '보라', 'hex': '#AA44FF'},
    {'name': '주황', 'hex': '#FF8800'},
]


# ─── 기억력 훈련 ─────────────────────────────────────────────────────────
def generate_memory_sequence(difficulty: int = 1) -> dict:
    length = 2 + difficulty                              # 1→3개, 5→7개
    display_time = max(1200, 3500 - difficulty * 400)   # 1→3100ms, 5→1500ms
    sequence = [random.randint(1, 9) for _ in range(length)]
    return {
        'type': 'memory_sequence',
        'difficulty': difficulty,
        'sequence': sequence,
        'displayTime': display_time,
        'inputTime': 15000,
        'description': f'숫자 {length}개를 {display_time/1000:.1f}초 동안 기억하세요',
    }


# ─── 집중력 훈련 ─────────────────────────────────────────────────────────
def generate_attention_stroop(difficulty: int = 1) -> dict:
    time_limit = max(800, 2500 - difficulty * 250)
    stimulus_count = 3 + difficulty
    option_count = min(4, 2 + difficulty)

    problems = []
    for _ in range(stimulus_count):
        text_color = random.choice(COLORS)
        display_color = random.choice([c for c in COLORS if c['name'] != text_color['name']])

        used = {text_color['name'], display_color['name']}
        wrong_opts = []
        pool = [c for c in COLORS if c['name'] not in used]
        random.shuffle(pool)
        wrong_opts = pool[:option_count - 1]

        options = [text_color] + wrong_opts
        random.shuffle(options)

        problems.append({
            'text': display_color['name'],
            'textColor': text_color['hex'],
            'correctAnswer': text_color['name'],
            'options': options,
            'timeLimit': time_limit,
        })

    return {
        'type': 'attention_stroop',
        'difficulty': difficulty,
        'problems': problems,
        'description': f"글자의 '색상'을 선택하세요 ({stimulus_count}문제, {time_limit/1000:.1f}초 제한)",
    }


# ─── 운동 훈련 ───────────────────────────────────────────────────────────
def generate_motor_response(difficulty: int = 1) -> dict:
    target_count = 3 + difficulty
    target_size = max(40, 90 - difficulty * 8)
    time_limit = max(500, 2000 - difficulty * 200)
    return {
        'type': 'motor_response',
        'difficulty': difficulty,
        'targetCount': target_count,
        'targetSize': target_size,
        'timeLimit': time_limit,
        'description': f'나타나는 원을 빠르게 터치하세요 ({target_count}개, {time_limit/1000:.1f}초 제한)',
    }


# ─── 통합 생성 ───────────────────────────────────────────────────────────
def generate_for_profile(weak_profile: dict, game_type: str) -> dict:
    """취약 프로파일 기반 문제 생성."""
    game_data = (weak_profile or {}).get('games', {}).get(game_type, {})
    difficulty = game_data.get('recommendedDifficulty', 2)
    return _dispatch(game_type, difficulty)


def generate_default(game_type: str) -> dict:
    """신규 환자용 기본 문제 생성."""
    return _dispatch(game_type, 2)


def _dispatch(game_type: str, difficulty: int) -> dict:
    if game_type == 'memory_sequence':
        return generate_memory_sequence(difficulty)
    if game_type == 'attention_stroop':
        return generate_attention_stroop(difficulty)
    if game_type == 'motor_response':
        return generate_motor_response(difficulty)
    return {}
