import json
import uuid
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

from database import db, Profile, GameSession, GlobalStats, WeakProfile
import ai_analyzer
import problem_generator

app = Flask(__name__, static_folder='.', static_url_path='/')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parkicare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

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

@app.route('/api/profiles', methods=['GET'])
def get_profiles():
    profiles = Profile.query.order_by(Profile.created_at.asc()).all()
    return ok([p.to_dict() for p in profiles])

@app.route('/api/profiles', methods=['POST'])
def create_profile():
    body = request.get_json(force=True)
    if 'name' not in body or 'age' not in body:
        return err('name and age are required')

    profile = Profile(
        id=f'p_{uuid.uuid4().hex[:12]}',
        name=body['name'].strip(),
        age=int(body['age'])
    )
    db.session.add(profile)
    db.session.commit()
    return ok(profile.to_dict()), 201

@app.route('/api/profiles/<profile_id>', methods=['DELETE'])
def delete_profile(profile_id):
    profile = Profile.query.get(profile_id)
    if profile:
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
    return ok(_get_sessions_dict(profile_id, game_type))

@app.route('/api/sessions/<profile_id>/<game_type>', methods=['POST'])
def save_session(profile_id, game_type):
    body = request.get_json(force=True)
    
    session = GameSession(
        profile_id=profile_id,
        game_type=game_type,
        accuracy=body.get('accuracy', 0.0),
        avg_response_time=body.get('avgResponseTime', 0.0),
        correct_count=body.get('correctCount', 0),
        total_rounds=body.get('totalRounds', 0),
        difficulty=body.get('difficulty', 2)
    )
    db.session.add(session)
    
    gstat = GlobalStats.query.get(game_type)
    if gstat:
        total_time = gstat.avg_response_time * gstat.count
        gstat.count += 1
        gstat.avg_response_time = (total_time + session.avg_response_time) / gstat.count
    
    db.session.commit()

    weak_profile = ai_analyzer.analyze(profile_id, _get_sessions_dict)
    
    wp_record = WeakProfile.query.get(profile_id)
    if not wp_record:
        wp_record = WeakProfile(profile_id=profile_id)
        db.session.add(wp_record)
    wp_record.data_json = json.dumps(weak_profile, ensure_ascii=False)
    wp_record.updated_at = datetime.utcnow()
    
    db.session.commit()
    return ok(session.to_dict()), 201

@app.route('/api/analysis/<profile_id>', methods=['GET'])
def get_weak_profile(profile_id):
    wp = WeakProfile.query.get(profile_id)
    if not wp:
        return ok(None)
    return ok(json.loads(wp.data_json))

@app.route('/api/analysis/<profile_id>', methods=['POST'])
def run_analysis(profile_id):
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
        wp = WeakProfile.query.get(profile_id)
        if wp:
            weak_profile = json.loads(wp.data_json)
            prob = problem_generator.generate_for_profile(weak_profile, game_type, is_accessible)
            return ok(prob)
            
    prob = problem_generator.generate_default(game_type, is_accessible)
    return ok(prob)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
