const express = require('express');
const session = require('express-session');
const bcrypt = require('bcryptjs');
const path = require('path');
const crypto = require('crypto');
const { sequelize, User, Profile, GameSession, GlobalStats, WeakProfile } = require('./database');
const { analyze } = require('./ai_analyzer');
const { generate_for_profile, generate_default } = require('./problem_generator');

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, '.')));

app.use(session({
  secret: 'parkicare_session_secret_key_2026',
  resave: false,
  saveUninitialized: false,
  cookie: { secure: false } // Change to true if HTTPS
}));

// Initialize tables
sequelize.sync().then(async () => {
  const count = await GlobalStats.count();
  if (count === 0) {
    await GlobalStats.bulkCreate([
      { game_type: 'memory_sequence', avg_response_time: 2200.0, count: 50 },
      { game_type: 'attention_stroop', avg_response_time: 1400.0, count: 50 },
      { game_type: 'motor_response', avg_response_time: 1800.0, count: 50 }
    ]);
  }
});

app.use((req, res, next) => {
  res.set('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.set('Pragma', 'no-cache');
  res.set('Expires', '0');
  next();
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Helper
const err = (res, msg, status = 400) => res.status(status).json({ ok: false, error: msg });
const ok = (res, data = null, extra = {}) => res.json({ ok: true, data, ...extra });

async function verifyProfileOwnership(req, profile_id) {
  const user_id = req.session.user_id;
  if (!user_id) return false;
  const profile = await Profile.findOne({ where: { id: profile_id, user_id } });
  return profile !== null;
}

// Auth APIs
app.post('/api/auth/register', async (req, res) => {
  let { username, password } = req.body;
  username = (username || '').trim();
  password = (password || '').trim();
  if (!username || !password) return err(res, '아이디와 비밀번호를 입력해주세요.');
  
  const existing = await User.findOne({ where: { username } });
  if (existing) return err(res, '이미 존재하는 아이디입니다.');
  
  const hash = await bcrypt.hash(password, 10);
  const user = await User.create({ username, password_hash: hash });
  
  req.session.user_id = user.id;
  ok(res, { id: user.id, username: user.username });
});

app.post('/api/auth/login', async (req, res) => {
  let { username, password } = req.body;
  username = (username || '').trim();
  password = (password || '').trim();
  if (!username || !password) return err(res, '아이디와 비밀번호를 입력해주세요.');
  
  const user = await User.findOne({ where: { username } });
  if (!user || !(await bcrypt.compare(password, user.password_hash))) {
    return err(res, '아이디 또는 비밀번호가 틀렸습니다.', 401);
  }
  
  req.session.user_id = user.id;
  ok(res, { id: user.id, username: user.username });
});

app.post('/api/auth/logout', (req, res) => {
  req.session.destroy();
  ok(res);
});

app.get('/api/auth/me', async (req, res) => {
  if (!req.session.user_id) return err(res, 'Not logged in', 401);
  const user = await User.findByPk(req.session.user_id);
  if (!user) return err(res, 'User not found', 404);
  ok(res, { id: user.id, username: user.username });
});

// Profile APIs
app.get('/api/profiles', async (req, res) => {
  const user_id = req.session.user_id;
  if (!user_id) return err(res, '로그인이 필요합니다.', 401);
  
  const profiles = await Profile.findAll({ where: { user_id }, order: [['created_at', 'DESC']] });
  ok(res, profiles.map(p => ({ id: p.id, name: p.name, age: p.age, userId: p.user_id, createdAt: p.created_at })));
});

app.post('/api/profiles', async (req, res) => {
  const user_id = req.session.user_id;
  if (!user_id) return err(res, '로그인이 필요합니다.', 401);
  
  const { name, age } = req.body;
  if (!name || !age) return err(res, '이름과 나이는 필수입니다.');
  
  const profile = await Profile.create({
    id: crypto.randomUUID(),
    name,
    age,
    user_id
  });
  ok(res, { id: profile.id, name: profile.name, age: profile.age, userId: profile.user_id, createdAt: profile.created_at });
});

app.get('/api/profiles/:id', async (req, res) => {
  if (!(await verifyProfileOwnership(req, req.params.id))) return err(res, '접근 권한이 없습니다.', 403);
  
  const profile = await Profile.findByPk(req.params.id);
  if (!profile) return err(res, 'Profile not found', 404);
  ok(res, { id: profile.id, name: profile.name, age: profile.age, userId: profile.user_id, createdAt: profile.created_at });
});

// Session APIs
app.post('/api/sessions', async (req, res) => {
  const data = req.body;
  const profile_id = data.profileId;
  
  if (!(await verifyProfileOwnership(req, profile_id))) return err(res, '접근 권한이 없습니다.', 403);
  
  const sess = await GameSession.create({
    profile_id,
    game_type: data.gameType,
    accuracy: data.accuracy,
    avg_response_time: data.avgResponseTime,
    correct_count: data.correctCount,
    total_rounds: data.totalRounds,
    difficulty: data.difficulty
  });

  // Re-analyze profile and update WeakProfile immediately
  try {
    const get_sessions_fn = async (pid, gtype) => {
      return await GameSession.findAll({ where: { profile_id: pid, game_type: gtype }, order: [['timestamp', 'ASC']] });
    };
    const latest_analysis = await analyze(profile_id, get_sessions_fn, GlobalStats);
    let weakProfile = await WeakProfile.findOne({ where: { profile_id } });
    if (weakProfile) {
      weakProfile.data_json = JSON.stringify(latest_analysis);
      await weakProfile.save();
    } else {
      await WeakProfile.create({ profile_id, data_json: JSON.stringify(latest_analysis) });
    }
  } catch (e) {
    console.error("Error updating weak profile on session save:", e);
  }
  
  ok(res, { id: sess.id });
});

app.get('/api/sessions/profile/:profile_id', async (req, res) => {
  if (!(await verifyProfileOwnership(req, req.params.profile_id))) return err(res, '접근 권한이 없습니다.', 403);
  
  const sessions = await GameSession.findAll({ where: { profile_id: req.params.profile_id }, order: [['timestamp', 'ASC']] });
  const result = sessions.map(s => ({
    id: s.id, profileId: s.profile_id, gameType: s.game_type, accuracy: s.accuracy,
    avgResponseTime: s.avg_response_time, correctCount: s.correct_count, totalRounds: s.total_rounds,
    difficulty: s.difficulty, timestamp: s.timestamp
  }));
  ok(res, result);
});

// Analysis
app.get('/api/analysis/:profile_id', async (req, res) => {
  const profile_id = req.params.profile_id;
  if (!(await verifyProfileOwnership(req, profile_id))) return err(res, '접근 권한이 없습니다.', 403);
  
  let weakProfile = await WeakProfile.findOne({ where: { profile_id } });
  
  const get_sessions_fn = async (pid, gtype) => {
    return await GameSession.findAll({ where: { profile_id: pid, game_type: gtype }, order: [['timestamp', 'ASC']] });
  };
  
  const latest_analysis = await analyze(profile_id, get_sessions_fn, GlobalStats);
  
  if (weakProfile) {
    weakProfile.data_json = JSON.stringify(latest_analysis);
    await weakProfile.save();
  } else {
    await WeakProfile.create({ profile_id, data_json: JSON.stringify(latest_analysis) });
  }
  
  ok(res, latest_analysis);
});

// Problem Generator
app.get('/api/generate_problem', async (req, res) => {
  const profile_id = req.query.profileId;
  const game_type = req.query.gameType;
  
  if (!game_type) return err(res, 'gameType is required');
  
  let is_accessible = true;
  let problem = null;
  
  if (profile_id) {
    if (!(await verifyProfileOwnership(req, profile_id))) return err(res, '접근 권한이 없습니다.', 403);
    
    let weakProfileRow = await WeakProfile.findOne({ where: { profile_id } });
    if (!weakProfileRow) {
      const get_sessions_fn = async (pid, gtype) => {
        return await GameSession.findAll({ where: { profile_id: pid, game_type: gtype }, order: [['timestamp', 'ASC']] });
      };
      const latest_analysis = await analyze(profile_id, get_sessions_fn, GlobalStats);
      weakProfileRow = await WeakProfile.create({ profile_id, data_json: JSON.stringify(latest_analysis) });
    }
    
    if (weakProfileRow) {
      const wp = JSON.parse(weakProfileRow.data_json);
      problem = generate_for_profile(wp, game_type, is_accessible);
    }
  }
  
  if (!problem) {
    problem = generate_default(game_type, is_accessible);
  }
  
  if (!problem) return err(res, 'Invalid game type', 400);
  ok(res, problem);
});

const PORT = 5000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on http://0.0.0.0:${PORT}`);
});
