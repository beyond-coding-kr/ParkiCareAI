const Storage = (() => {
  const BASE_URL = '/api';
  function requestSync(endpoint, method = 'GET', body = null) {
    const xhr = new XMLHttpRequest();
    xhr.open(method, BASE_URL + endpoint, false); 
    xhr.setRequestHeader('Content-Type', 'application/json');
    try {
      if (body) {
        xhr.send(JSON.stringify(body));
      } else {
        xhr.send(null);
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        const json = JSON.parse(xhr.responseText);
        return json.ok ? json.data : null;
      }
    } catch (e) {
      console.error("XHR Error:", e);
    }
    return null;
  }
  function getProfiles() {
    return requestSync('/profiles') || [];
  }
  function saveProfile(profile) {
    return requestSync('/profiles', 'POST', profile);
  }
  function deleteProfile(id) {
    return requestSync(`/profiles/${id}`, 'DELETE');
  }
  function getCurrentProfile() {
    const id = localStorage.getItem('parkicare_current_profile');
    if (!id) return null;
    const profiles = getProfiles();
    return profiles.find(p => p.id === id) || null;
  }
  function setCurrentProfile(id) {
    localStorage.setItem('parkicare_current_profile', id);
  }
  function getSessions(profileId, gameType) {
    return requestSync(`/sessions/${profileId}/${gameType}`) || [];
  }
  function saveSession(profileId, gameType, sessionData) {
    return requestSync(`/sessions/${profileId}/${gameType}`, 'POST', sessionData);
  }
  function getWeakProfile(profileId) {
    return requestSync(`/analysis/${profileId}`);
  }
  function runAnalysis(profileId) {
    return requestSync(`/analysis/${profileId}`, 'POST');
  }
  function getProblem(gameType, profileId = null, accessible = true) {
    let url = `/problems/${gameType}?accessible=${accessible}`;
    if (profileId) url += `&profileId=${profileId}`;
    return requestSync(url);
  }
  function login(username, password) {
    const res = requestSync('/auth/login', 'POST', { username, password });
    if (res) {
      localStorage.setItem('parkicare_user', JSON.stringify(res));
      return res;
    }
    return null;
  }
  function register(username, password) {
    const res = requestSync('/auth/register', 'POST', { username, password });
    if (res) {
      localStorage.setItem('parkicare_user', JSON.stringify(res));
      return res;
    }
    return null;
  }
  function logout() {
    requestSync('/auth/logout', 'POST');
    localStorage.removeItem('parkicare_user');
    localStorage.removeItem('parkicare_current_profile');
  }
  function getCurrentUser() {
    const userStr = localStorage.getItem('parkicare_user');
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch (e) {
      return null;
    }
  }
  function checkSession() {
    const res = requestSync('/auth/me');
    if (res) {
      localStorage.setItem('parkicare_user', JSON.stringify(res));
      return res;
    } else {
      localStorage.removeItem('parkicare_user');
      return null;
    }
  }
  return {
    getProfiles, saveProfile, deleteProfile,
    getCurrentProfile, setCurrentProfile,
    getSessions, saveSession,
    getWeakProfile, runAnalysis,
    getProblem,
    login, register, logout, getCurrentUser, checkSession
  };
})();