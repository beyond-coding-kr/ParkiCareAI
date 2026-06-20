const Storage = (() => {
  const BASE_URL = '/api';

  function requestSync(endpoint, method = 'GET', body = null) {
    const xhr = new XMLHttpRequest();
    xhr.open(method, BASE_URL + endpoint, false); // false makes it synchronous
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

  return {
    getProfiles, saveProfile, deleteProfile,
    getCurrentProfile, setCurrentProfile,
    getSessions, saveSession,
    getWeakProfile, runAnalysis,
    getProblem
  };
})();