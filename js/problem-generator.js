/**
 * ParkiCare AI - Problem Generator Module
 * 취약 프로파일을 기반으로 다음 세션 문제를 자동 생성
 */

const ProblemGenerator = (() => {

  // ─── 기억력 훈련 문제 생성 ────────────────────────────────────
  function generateMemorySequence(difficulty = 1) {
    const length = 2 + difficulty;             // 난이도 1→3개, 5→7개
    const displayTime = 3500 - difficulty * 400; // 난이도 1→3100ms, 5→1500ms
    const sequence = [];
    for (let i = 0; i < length; i++) {
      sequence.push(Math.floor(Math.random() * 9) + 1); // 1~9
    }
    return {
      type: 'memory_sequence',
      difficulty,
      sequence,
      displayTime: Math.max(1200, displayTime),
      inputTime: 15000, // 입력 제한 시간
      description: `숫자 ${length}개를 ${(Math.max(1200, displayTime)/1000).toFixed(1)}초 동안 기억하세요`,
    };
  }

  // ─── 집중력 훈련 문제 생성 ────────────────────────────────────
  const COLORS = [
    { name: '빨강', hex: '#FF4444' },
    { name: '파랑', hex: '#4488FF' },
    { name: '초록', hex: '#44CC44' },
    { name: '노랑', hex: '#FFCC00' },
    { name: '보라', hex: '#AA44FF' },
    { name: '주황', hex: '#FF8800' },
  ];

  function generateAttentionStroop(difficulty = 1) {
    const timeLimit = Math.max(800, 2500 - difficulty * 250); // 응답 제한 시간(ms)
    const stimulusCount = 3 + difficulty;       // 문제 수
    const optionCount = Math.min(4, 2 + difficulty); // 선택지 수

    const problems = [];
    for (let i = 0; i < stimulusCount; i++) {
      const textColorIdx = Math.floor(Math.random() * COLORS.length);
      let displayColorIdx;
      do { displayColorIdx = Math.floor(Math.random() * COLORS.length); }
      while (displayColorIdx === textColorIdx);

      // 틀린 선택지 생성
      const wrongOptions = [];
      const usedIdx = new Set([textColorIdx, displayColorIdx]);
      while (wrongOptions.length < optionCount - 1) {
        const idx = Math.floor(Math.random() * COLORS.length);
        if (!usedIdx.has(idx)) { wrongOptions.push(COLORS[idx]); usedIdx.add(idx); }
      }

      // 선택지 섞기
      const options = [COLORS[textColorIdx], ...wrongOptions].sort(() => Math.random() - 0.5);

      problems.push({
        text: COLORS[displayColorIdx].name,    // 화면에 표시되는 텍스트
        textColor: COLORS[textColorIdx].hex,   // 텍스트의 실제 색상
        correctAnswer: COLORS[textColorIdx].name, // 정답 = 텍스트 색상 이름
        options,
        timeLimit,
      });
    }

    return {
      type: 'attention_stroop',
      difficulty,
      problems,
      description: `글자의 '색상'을 선택하세요 (${stimulusCount}문제, ${(timeLimit/1000).toFixed(1)}초 제한)`,
    };
  }

  // ─── 운동 훈련 문제 생성 ──────────────────────────────────────
  function generateMotorResponse(difficulty = 1) {
    const targetCount = 3 + difficulty;                     // 타겟 수
    const targetSize = Math.max(40, 90 - difficulty * 8);   // 타겟 크기(px)
    const timeLimit = Math.max(500, 2000 - difficulty * 200); // 각 타겟 응답 제한

    return {
      type: 'motor_response',
      difficulty,
      targetCount,
      targetSize,
      timeLimit,
      description: `나타나는 원을 빠르게 터치하세요 (${targetCount}개, ${(timeLimit/1000).toFixed(1)}초 제한)`,
    };
  }

  // ─── 통합 문제 생성 (취약 프로파일 적용) ─────────────────────
  function generateForProfile(weakProfile, gameType) {
    const gameData = weakProfile?.games?.[gameType];
    const difficulty = gameData?.recommendedDifficulty || 2;
    switch (gameType) {
      case 'memory_sequence':  return generateMemorySequence(difficulty);
      case 'attention_stroop': return generateAttentionStroop(difficulty);
      case 'motor_response':   return generateMotorResponse(difficulty);
      default: return null;
    }
  }

  // ─── 기본 문제 생성 (신규 환자) ───────────────────────────────
  function generateDefault(gameType) {
    switch (gameType) {
      case 'memory_sequence':  return generateMemorySequence(2);
      case 'attention_stroop': return generateAttentionStroop(2);
      case 'motor_response':   return generateMotorResponse(2);
      default: return null;
    }
  }

  return {
    generateMemorySequence,
    generateAttentionStroop,
    generateMotorResponse,
    generateForProfile,
    generateDefault,
    COLORS,
  };
})();
