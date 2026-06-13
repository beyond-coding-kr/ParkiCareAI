/**
 * ParkiCare AI - Storage Module
 * LocalStorage 기반 데이터 영속 저장 레이어
 */

const Storage = (() => {
  const KEYS = {
    PROFILES: 'parkicare_profiles',
    CURRENT_PROFILE: 'parkicare_current_profile',
    SESSIONS: 'parkicare_sessions',
    WEAK_PROFILES: 'parkicare_weak_profiles',
    GLOBAL_STATS: 'parkicare_global_stats',
  };

  // ─── 기본 유틸 ───────────────────────────────────────────────
  function get(key) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  }

  function set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch { return false; }
  }

  // ─── 프로필 ───────────────────────────────────────────────────
  function getProfiles() {
    return get(KEYS.PROFILES) || [];
  }

  function saveProfile(profile) {
    const profiles = getProfiles();
    const idx = profiles.findIndex(p => p.id === profile.id);
    if (idx >= 0) profiles[idx] = profile;
    else profiles.push(profile);
    set(KEYS.PROFILES, profiles);
    return profile;
  }

  function deleteProfile(id) {
    const profiles = getProfiles().filter(p => p.id !== id);
    set(KEYS.PROFILES, profiles);
    // 해당 프로필 세션도 삭제
    const sessions = getAllSessions();
    const filtered = {};
    Object.keys(sessions).forEach(k => {
      if (!k.startsWith(id + '_')) filtered[k] = sessions[k];
    });
    set(KEYS.SESSIONS, filtered);
  }

  function getCurrentProfile() {
    const id = get(KEYS.CURRENT_PROFILE);
    if (!id) return null;
    return getProfiles().find(p => p.id === id) || null;
  }

  function setCurrentProfile(id) {
    set(KEYS.CURRENT_PROFILE, id);
  }

  // ─── 세션 ─────────────────────────────────────────────────────
  function getAllSessions() {
    return get(KEYS.SESSIONS) || {};
  }

  function getSessionKey(profileId, gameType) {
    return `${profileId}_${gameType}`;
  }

  function getSessions(profileId, gameType) {
    const all = getAllSessions();
    return all[getSessionKey(profileId, gameType)] || [];
  }

  function saveSession(profileId, gameType, sessionData) {
    const all = getAllSessions();
    const key = getSessionKey(profileId, gameType);
    if (!all[key]) all[key] = [];
    const session = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      gameType,
      ...sessionData,
    };
    all[key].push(session);
    // 최대 50세션만 유지
    if (all[key].length > 50) all[key] = all[key].slice(-50);
    set(KEYS.SESSIONS, all);
    return session;
  }

  // ─── 취약 프로파일 ────────────────────────────────────────────
  function getWeakProfile(profileId) {
    const all = get(KEYS.WEAK_PROFILES) || {};
    return all[profileId] || null;
  }

  function saveWeakProfile(profileId, weakProfile) {
    const all = get(KEYS.WEAK_PROFILES) || {};
    all[profileId] = { ...weakProfile, updatedAt: new Date().toISOString() };
    set(KEYS.WEAK_PROFILES, all);
  }

  // ─── 전역 통계 (전체 사용자 평균 계산용) ──────────────────────
  function getGlobalStats() {
    return get(KEYS.GLOBAL_STATS) || {
      memory_sequence: { avgResponseTime: 5000, count: 0 },
      attention_stroop: { avgResponseTime: 2000, count: 0 },
      motor_response: { avgResponseTime: 800, count: 0 },
    };
  }

  function updateGlobalStats(gameType, responseTime) {
    const stats = getGlobalStats();
    if (!stats[gameType]) stats[gameType] = { avgResponseTime: responseTime, count: 1 };
    else {
      const { avgResponseTime, count } = stats[gameType];
      stats[gameType] = {
        avgResponseTime: (avgResponseTime * count + responseTime) / (count + 1),
        count: count + 1,
      };
    }
    set(KEYS.GLOBAL_STATS, stats);
  }

  // ─── 초기화 ───────────────────────────────────────────────────
  function clearAll() {
    Object.values(KEYS).forEach(k => localStorage.removeItem(k));
  }

  return {
    getProfiles, saveProfile, deleteProfile,
    getCurrentProfile, setCurrentProfile,
    getSessions, saveSession,
    getWeakProfile, saveWeakProfile,
    getGlobalStats, updateGlobalStats,
    clearAll,
  };
})();
