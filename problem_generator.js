const COLORS = [
  { name: '빨강', hex: '#C62828' },
  { name: '파랑', hex: '#1565C0' },
  { name: '초록', hex: '#2E7D32' },
  { name: '노랑', hex: '#FFEA00' },
  { name: '보라', hex: '#6A1B9A' },
  { name: '검정', hex: '#212121' }
];

function generate_memory_sequence(difficulty = 1, is_accessible = true) {
  let length = Math.max(2, 2 + parseInt(difficulty, 10));
  let display_time = 3500 - parseInt(difficulty, 10) * 400;
  
  if (is_accessible) {
      display_time = Math.max(2000, display_time);
  }
      
  let sequence = Array.from({ length }, () => Math.floor(Math.random() * 9) + 1);
  let final_time = Math.max(1200, display_time);
  
  return {
      type: 'memory_sequence',
      difficulty: difficulty,
      sequence: sequence,
      displayTime: final_time,
      inputTime: 15000,
      description: `숫자 ${length}개를 ${(final_time/1000).toFixed(1)}초 동안 기억하세요`
  };
}

function generate_attention_stroop(difficulty = 1, is_accessible = true) {
  let time_limit = Math.max(800, 2500 - parseInt(difficulty, 10) * 250);
  let stimulus_count = Math.max(2, 3 + parseInt(difficulty, 10));
  let option_count = Math.max(2, Math.min(4, 2 + parseInt(difficulty, 10)));
  
  if (is_accessible) {
      time_limit = Math.max(1500, time_limit);
      stimulus_count = Math.min(6, stimulus_count);
  }
      
  let problems = [];
  for (let i = 0; i < stimulus_count; i++) {
      let text_color_idx = Math.floor(Math.random() * COLORS.length);
      let display_color_idx = text_color_idx;
      while (display_color_idx === text_color_idx) {
          display_color_idx = Math.floor(Math.random() * COLORS.length);
      }
          
      let wrong_options = [];
      let used_idx = new Set([text_color_idx, display_color_idx]);
      while (wrong_options.length < option_count - 1) {
          let idx = Math.floor(Math.random() * COLORS.length);
          if (!used_idx.has(idx)) {
              wrong_options.push(COLORS[idx]);
              used_idx.add(idx);
          }
      }
              
      let options = [COLORS[text_color_idx], ...wrong_options];
      options.sort(() => Math.random() - 0.5); // shuffle
      
      problems.push({
          text: COLORS[display_color_idx].name,
          textColor: COLORS[text_color_idx].hex,
          correctAnswer: COLORS[text_color_idx].name,
          options: options,
          timeLimit: time_limit
      });
  }
      
  return {
      type: 'attention_stroop',
      difficulty: difficulty,
      problems: problems,
      description: `글자의 '색상'을 선택하세요 (${stimulus_count}문제, ${(time_limit/1000).toFixed(1)}초 제한)`
  };
}

function generate_motor_response(difficulty = 1, is_accessible = true) {
  let target_count = Math.max(2, 3 + parseInt(difficulty, 10));
  let target_size = Math.max(40, 90 - parseInt(difficulty, 10) * 8);
  let time_limit = Math.max(500, 2000 - parseInt(difficulty, 10) * 200);
  
  if (is_accessible) {
      target_count = Math.min(8, target_count);
      target_size = Math.max(60, target_size);
      time_limit = Math.max(1500, time_limit);
  }
      
  return {
      type: 'motor_response',
      difficulty: difficulty,
      targetCount: target_count,
      targetSize: target_size,
      timeLimit: time_limit,
      description: `나타나는 원을 빠르게 터치하세요 (${target_count}개, ${(time_limit/1000).toFixed(1)}초 제한)`
  };
}

function generate_for_profile(weak_profile, game_type, is_accessible = true) {
  let game_data = weak_profile?.games?.[game_type] || {};
  let difficulty = game_data.recommendedDifficulty !== undefined ? game_data.recommendedDifficulty : 2;
  
  if (game_type === 'memory_sequence') {
      return generate_memory_sequence(difficulty, is_accessible);
  } else if (game_type === 'attention_stroop') {
      return generate_attention_stroop(difficulty, is_accessible);
  } else if (game_type === 'motor_response') {
      return generate_motor_response(difficulty, is_accessible);
  }
  return null;
}

function generate_default(game_type, is_accessible = true) {
  if (game_type === 'memory_sequence') {
      return generate_memory_sequence(2, is_accessible);
  } else if (game_type === 'attention_stroop') {
      return generate_attention_stroop(2, is_accessible);
  } else if (game_type === 'motor_response') {
      return generate_motor_response(2, is_accessible);
  }
  return null;
}

module.exports = {
  generate_for_profile,
  generate_default
};
