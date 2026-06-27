import json
import uuid
from datetime import datetime
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from database import db, User, Profile, GameSession, GlobalStats, WeakProfile
import ai_analyzer
import problem_generator

app = Flask(__name__, static_folder='.', static_url_path='/')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parkicare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'parkicare_session_secret_key_2026'

CORS(app)
db.init_app(app)

def ok(data=None, **kwargs):
    return jsonify({'ok': True, 'data': data, **kwargs})

def err(msg, status=400):
    return jsonify({'ok': False, 'error': msg}), status

@app.before_request
def create_tables():
    if not hasattr(app, 'tables_created'):
        db.create_all()
        # Dynamic migration to add user_id column to profiles if it doesn't exist
        try:
            db.session.execute(db.text('ALTER TABLE profiles ADD COLUMN user_id INTEGER REFERENCES users(id)'))
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        if GlobalStats.query.count() == 0:
            db.session.add(GlobalStats(game_type='memory_sequence', avg_response_time=2200.0, count=50))
            db.session.add(GlobalStats(game_type='attention_stroop', avg_response_time=1400.0, count=50))
            db.session.add(GlobalStats(game_type='motor_response', avg_response_time=1800.0, count=50))
            db.session.commit()
        app.tables_created = True

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

@app.route('/')
def index():
    return app.send_static_file('index.html')

# --- Helper: Profile Ownership Verification ---
def _verify_profile_ownership(profile_id):
    user_id = session.get('user_id')
    if not user_id:
        return False
    profile = Profile.query.filter_by(id=profile_id, user_id=user_id).first()
    return profile is not None

# --- Authentication APIs ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    body = request.get_json(force=True)
    username = body.get('username', '').strip()
    password = body.get('password', '').strip()
    if not username or not password:
        return err('아이디와 비밀번호를 입력해주세요.')
    
    if User.query.filter_by(username=username).first():
        return err('이미 존재하는 아이디입니다.')
        
    user = User(
        username=username,
        password_hash=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    return ok(user.to_dict()), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    body = request.get_json(force=True)
    username = body.get('username', '').strip()
    password = body.get('password', '').strip()
    if not username or not password:
        return err('아이디와 비밀번호를 입력해주세요.')
        
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return err('아이디 또는 비밀번호가 틀렸습니다.', 401)
        
    session['user_id'] = user.id
    return ok(user.to_dict())

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return ok()

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    user_id = session.get('user_id')
    if not user_id:
        return err('로그인이 필요합니다.', 401)
    user = User.query.get(user_id)
    if not user:
        session.pop('user_id', None)
        return err('로그인이 필요합니다.', 401)
    return ok(user.to_dict())

# --- Profiles APIs ---
@app.route('/api/profiles', methods=['GET'])
def get_profiles():
    user_id = session.get('user_id')
    if not user_id:
        return err('로그인이 필요합니다.', 401)
    profiles = Profile.query.filter_by(user_id=user_id).order_by(Profile.created_at.asc()).all()
    return ok([p.to_dict() for p in profiles])

@app.route('/api/profiles', methods=['POST'])
def create_profile():
    user_id = session.get('user_id')
    if not user_id:
        return err('로그인이 필요합니다.', 401)
    body = request.get_json(force=True)
    if 'name' not in body or 'age' not in body:
        return err('name and age are required')

    profile = Profile(
        id=f'p_{uuid.uuid4().hex[:12]}',
        name=body['name'].strip(),
        age=int(body['age']),
        user_id=user_id
    )
    db.session.add(profile)
    db.session.commit()
    return ok(profile.to_dict()), 201

@app.route('/api/profiles/<profile_id>', methods=['DELETE'])
def delete_profile(profile_id):
    user_id = session.get('user_id')
    if not user_id:
        return err('로그인이 필요합니다.', 401)
    profile = Profile.query.filter_by(id=profile_id, user_id=user_id).first()
    if profile:
        # Also clean up child rows to maintain database integrity
        GameSession.query.filter_by(profile_id=profile_id).delete()
        WeakProfile.query.filter_by(profile_id=profile_id).delete()
        db.session.delete(profile)
        db.session.commit()
    return ok({'deleted': profile_id})

def _get_sessions_dict(profile_id, game_type):
    sessions = GameSession.query.filter_by(
        profile_id=profile_id, 
        game_type=game_type
    ).order_by(GameSession.timestamp.asc()).all()
    return [s.to_dict() for s in sessions]

@app.route('/api/sessions/<profile_id>/<game_type>', methods=['GET'])
def get_sessions(profile_id, game_type):
    if not _verify_profile_ownership(profile_id):
        return err('접근 권한이 없습니다.', 403)
    return ok(_get_sessions_dict(profile_id, game_type))

@app.route('/api/sessions/<profile_id>/<game_type>', methods=['POST'])
def save_session(profile_id, game_type):
    if not _verify_profile_ownership(profile_id):
        return err('접근 권한이 없습니다.', 403)
        
    body = request.get_json(force=True)
    
    gs_session = GameSession(
        profile_id=profile_id,
        game_type=game_type,
        accuracy=body.get('accuracy', 0.0),
        avg_response_time=body.get('avgResponseTime', 0.0),
        correct_count=body.get('correctCount', 0),
        total_rounds=body.get('totalRounds', 0),
        difficulty=body.get('difficulty', 2)
    )
    db.session.add(gs_session)
    
    gstat = GlobalStats.query.get(game_type)
    if gstat:
        total_time = gstat.avg_response_time * gstat.count
        gstat.count += 1
        gstat.avg_response_time = (total_time + gs_session.avg_response_time) / gstat.count
    
    db.session.commit()

    weak_profile = ai_analyzer.analyze(profile_id, _get_sessions_dict)
    
    wp_record = WeakProfile.query.get(profile_id)
    if not wp_record:
        wp_record = WeakProfile(profile_id=profile_id)
        db.session.add(wp_record)
    wp_record.data_json = json.dumps(weak_profile, ensure_ascii=False)
    wp_record.updated_at = datetime.utcnow()
    
    db.session.commit()
    return ok(gs_session.to_dict()), 201

@app.route('/api/analysis/<profile_id>', methods=['GET'])
def get_weak_profile(profile_id):
    if not _verify_profile_ownership(profile_id):
        return err('접근 권한이 없습니다.', 403)
    wp = WeakProfile.query.get(profile_id)
    if not wp:
        return ok(None)
    return ok(json.loads(wp.data_json))

@app.route('/api/analysis/<profile_id>', methods=['POST'])
def run_analysis(profile_id):
    if not _verify_profile_ownership(profile_id):
        return err('접근 권한이 없습니다.', 403)
    weak_profile = ai_analyzer.analyze(profile_id, _get_sessions_dict)
    
    wp_record = WeakProfile.query.get(profile_id)
    if not wp_record:
        wp_record = WeakProfile(profile_id=profile_id)
        db.session.add(wp_record)
    wp_record.data_json = json.dumps(weak_profile, ensure_ascii=False)
    wp_record.updated_at = datetime.utcnow()
    db.session.commit()
    
    return ok(weak_profile)

@app.route('/api/problems/<game_type>', methods=['GET'])
def generate_problems(game_type):
    profile_id = request.args.get('profileId')
    if profile_id == 'null':
        profile_id = None
    is_accessible = request.args.get('accessible', 'true').lower() == 'true'
    
    if profile_id:
        if not _verify_profile_ownership(profile_id):
            return err('접근 권한이 없습니다.', 403)
        wp = WeakProfile.query.get(profile_id)
        if wp:
            weak_profile = json.loads(wp.data_json)
            prob = problem_generator.generate_for_profile(weak_profile, game_type, is_accessible)
            return ok(prob)
            
    prob = problem_generator.generate_default(game_type, is_accessible)
    return ok(prob)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
