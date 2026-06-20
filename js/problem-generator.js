const ProblemGenerator = (() => {
  function generateForProfile(weakProfile, gameType, isAccessible = true) {
    const profile = Storage.getCurrentProfile();
    const profileId = profile ? profile.id : null;
    return Storage.getProblem(gameType, profileId, isAccessible);
  }

  function generateDefault(gameType, isAccessible = true) {
    return Storage.getProblem(gameType, null, isAccessible);
  }

  return { generateForProfile, generateDefault };
})();