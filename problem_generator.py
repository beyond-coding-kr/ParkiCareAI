import random

COLORS = [
    {'name': '빨강', 'hex': '#C62828'},
    {'name': '파랑', 'hex': '#1565C0'},
    {'name': '초록', 'hex': '#2E7D32'},
    {'name': '노랑', 'hex': '#FFEA00'},
    {'name': '보라', 'hex': '#6A1B9A'},
    {'name': '주황', 'hex': '#FF6D00'}
]

def generate_memory_sequence(difficulty=1, is_accessible=True):
    length = 2 + difficulty
    display_time = 3500 - difficulty * 400
    
    if is_accessible:
        display_time = max(2000, display_time)
        
    sequence = [random.randint(1, 9) for _ in range(length)]
    final_time = max(1200, display_time)
    
    return {
        'type': 'memory_sequence',
        'difficulty': difficulty,
        'sequence': sequence,
        'displayTime': final_time,
        'inputTime': 15000,
        'description': f"숫자 {length}개를 {(final_time/1000):.1f}초 동안 기억하세요"
    }

def generate_attention_stroop(difficulty=1, is_accessible=True):
    time_limit = max(800, 2500 - difficulty * 250)
    stimulus_count = 3 + difficulty
    option_count = min(4, 2 + difficulty)
    
    if is_accessible:
        time_limit = max(1500, time_limit)
        stimulus_count = min(6, stimulus_count)
        
    problems = []
    for _ in range(stimulus_count):
        text_color_idx = random.randint(0, len(COLORS) - 1)
        display_color_idx = text_color_idx
        while display_color_idx == text_color_idx:
            display_color_idx = random.randint(0, len(COLORS) - 1)
            
        wrong_options = []
        used_idx = {text_color_idx, display_color_idx}
        while len(wrong_options) < option_count - 1:
            idx = random.randint(0, len(COLORS) - 1)
            if idx not in used_idx:
                wrong_options.append(COLORS[idx])
                used_idx.add(idx)
                
        options = [COLORS[text_color_idx]] + wrong_options
        random.shuffle(options)
        
        problems.append({
            'text': COLORS[display_color_idx]['name'],
            'textColor': COLORS[text_color_idx]['hex'],
            'correctAnswer': COLORS[text_color_idx]['name'],
            'options': options,
            'timeLimit': time_limit
        })
        
    return {
        'type': 'attention_stroop',
        'difficulty': difficulty,
        'problems': problems,
        'description': f"글자의 '색상'을 선택하세요 ({stimulus_count}문제, {(time_limit/1000):.1f}초 제한)"
    }

def generate_motor_response(difficulty=1, is_accessible=True):
    target_count = 3 + difficulty
    target_size = max(40, 90 - difficulty * 8)
    time_limit = max(500, 2000 - difficulty * 200)
    
    if is_accessible:
        target_count = min(8, target_count)
        target_size = max(60, target_size)
        time_limit = max(1500, time_limit)
        
    return {
        'type': 'motor_response',
        'difficulty': difficulty,
        'targetCount': target_count,
        'targetSize': target_size,
        'timeLimit': time_limit,
        'description': f"나타나는 원을 빠르게 터치하세요 ({target_count}개, {(time_limit/1000):.1f}초 제한)"
    }

def generate_for_profile(weak_profile, game_type, is_accessible=True):
    game_data = weak_profile.get('games', {}).get(game_type, {})
    difficulty = game_data.get('recommendedDifficulty', 2)
    
    if game_type == 'memory_sequence':
        return generate_memory_sequence(difficulty, is_accessible)
    elif game_type == 'attention_stroop':
        return generate_attention_stroop(difficulty, is_accessible)
    elif game_type == 'motor_response':
        return generate_motor_response(difficulty, is_accessible)
    return None

def generate_default(game_type, is_accessible=True):
    if game_type == 'memory_sequence':
        return generate_memory_sequence(2, is_accessible)
    elif game_type == 'attention_stroop':
        return generate_attention_stroop(2, is_accessible)
    elif game_type == 'motor_response':
        return generate_motor_response(2, is_accessible)
    return None
