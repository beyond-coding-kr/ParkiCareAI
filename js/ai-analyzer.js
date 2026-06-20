const AIAnalyzer = (() => {
  const GAME_TYPES = ['memory_sequence', 'attention_stroop', 'motor_response'];

  function getGrade(score) {
    if (score >= 90) return { letter: 'A', color: '#51CF66', label: '최우수', message: '최우수' };
    if (score >= 75) return { letter: 'B', color: '#4DABF7', label: '우수', message: '우수' };
    if (score >= 60) return { letter: 'C', color: '#FCC419', label: '보통', message: '보통' };
    if (score >= 40) return { letter: 'D', color: '#FF922B', label: '주의', message: '주의' };
    return { letter: 'F', color: '#FF6B6B', label: '취약', message: '취약' };
  }

  function analyze(profileId) {
    return Storage.runAnalysis(profileId);
  }

  return { GAME_TYPES, getGrade, analyze };
})();