"""
ParkiCare AI - Flask 메인 앱
REST API 서버 + 정적 파일 서빙
"""

import json
import time
import uuid
from datetime import datetime

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS

from database import db, init_db
from models import Profile, GameSession, WeakProfile, GlobalStats
import ai_analyzer
import problem_generator

# ─── 앱 설정 ─────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parkicare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False   # 한글 JSON 인코딩

CORS(app)
init_db(app)


# ─── 헬퍼 ────────────────────────────────────────────────────────────────
def ok(data=None, **kwargs):
    return jsonify({'ok': True, 'data': data, **kwargs})

def err(msg, status=400):
    return jsonify({'ok': False, 'error': msg}), status

def _sessions_for_analysis(profile_id: str) -> dict:
    """AI 분석용 게임 타입별 세션 dict 반환."""
    result = {}
    for game_type in ai_analyzer.GAME_TYPES:
        rows = (GameSession.query
                .filter_by(profile_id=profile_id, game_type=game_type)
                .order_by(GameSession.timestamp.asc())
                .all())
        result[game_type] = [r.to_dict() for r in rows]
    return result

def _global_stats_dict() -> dict:
    rows = GlobalStats.query.all()
    return {r.game_type: {'avgResponseTime': r.avg_response_time, 'count': r.count}
            for r in rows}


# ─── 메인 페이지 ──────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


# ─── 프로필 API ──────────────────────────────────────────────────────────
@app.route('/api/profiles', methods=['GET'])
def get_profiles():
    profiles = Profile.query.order_by(Profile.created_at.asc()).all()
    return ok([p.to_dict() for p in profiles])


@app.route('/api/profiles', methods=['POST'])
def create_profile():
    body = request.get_json(force=True)
    required = ('name', 'age', 'stage')
    if not all(body.get(f) for f in required):
        return err('name, age, stage 는 필수 항목입니다')

    profile = Profile(
        id=f'p_{uuid.uuid4().hex[:12]}',
        name=body['name'].strip(),
        age=int(body['age']),
        stage=body.get('stage', 'stage1'),
        diagnosis=body.get('diagnosis', ''),
        color=body.get('color', '#00D4FF'),
    )
    db.session.add(profile)
    db.session.commit()
    return ok(profile.to_dict()), 201


@app.route('/api/profiles/<profile_id>', methods=['DELETE'])
def delete_profile(profile_id):
    profile = Profile.query.get(profile_id)
    if not profile:
        return err('프로필을 찾을 수 없습니다', 404)
    db.session.delete(profile)
    db.session.commit()
    return ok({'deleted': profile_id})


# ─── 세션 API ────────────────────────────────────────────────────────────
@app.route('/api/sessions/<profile_id>/<game_type>', methods=['GET'])
def get_sessions(profile_id, game_type):
    sessions = (GameSession.query
                .filter_by(profile_id=profile_id, game_type=game_type)
                .order_by(GameSession.timestamp.asc())
                .all())
    return ok([s.to_dict() for s in sessions])


@app.route('/api/sessions', methods=['POST'])
def save_session():
    body = request.get_json(force=True)
    required = ('profileId', 'gameType', 'accuracy', 'avgResponseTime',
                 'correctCount', 'totalRounds', 'difficulty')
    if not all(k in body for k in required):
        return err(f'필수 필드 누락: {required}')

    profile = Profile.query.get(body['profileId'])
    if not profile:
        return err('프로필을 찾을 수 없습니다', 404)

    session = GameSession(
        profile_id=body['profileId'],
        game_type=body['gameType'],
        accuracy=float(body['accuracy']),
        avg_response_time=float(body['avgResponseTime']),
        correct_count=int(body['correctCount']),
        total_rounds=int(body['totalRounds']),
        miss_count=int(body.get('missCount', 0)),
        difficulty=int(body['difficulty']),
        fatigue=int(body.get('fatigue', 1)),
    )
    db.session.add(session)

    # 전역 통계 업데이트 (이동 평균)
    stats = GlobalStats.query.get(body['gameType'])
    if stats:
        rt = float(body['avgResponseTime'])
        new_avg = (stats.avg_response_time * stats.count + rt) / (stats.count + 1)
        stats.avg_response_time = new_avg
        stats.count += 1

    db.session.commit()
    return ok(session.to_dict()), 201


# ─── AI 분석 API ─────────────────────────────────────────────────────────
@app.route('/api/analyze/<profile_id>', methods=['GET'])
def run_analysis(profile_id):
    """AI 분석을 실행하고 취약 프로파일을 DB에 저장 후 반환."""
    profile = Profile.query.get(profile_id)
    if not profile:
        return err('프로필을 찾을 수 없습니다', 404)

    t_start = time.perf_counter()
    sessions_by_type = _sessions_for_analysis(profile_id)
    global_stats = _global_stats_dict()
    result = ai_analyzer.analyze(profile_id, sessions_by_type, global_stats)
    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)

    # DB 저장 (upsert)
    wp = WeakProfile.query.filter_by(profile_id=profile_id).first()
    if not wp:
        wp = WeakProfile(profile_id=profile_id)
        db.session.add(wp)

    wp.overall_score = result['overallScore']
    wp.games_json = json.dumps(result['games'], ensure_ascii=False)
    wp.weak_areas_json = json.dumps(result['weakAreas'], ensure_ascii=False)
    wp.strong_areas_json = json.dumps(result['strongAreas'], ensure_ascii=False)
    wp.recommendations_json = json.dumps(result['recommendations'], ensure_ascii=False)
    wp.analyzed_at = datetime.utcnow()
    db.session.commit()

    return ok({**result, 'elapsedMs': elapsed_ms})


@app.route('/api/weak-profile/<profile_id>', methods=['GET'])
def get_weak_profile(profile_id):
    wp = WeakProfile.query.filter_by(profile_id=profile_id).first()
    if not wp:
        return ok(None)
    return ok(wp.to_dict())


# ─── 문제 생성 API ───────────────────────────────────────────────────────
@app.route('/api/problem/<profile_id>/<game_type>', methods=['GET'])
def get_problem(profile_id, game_type):
    """취약 프로파일 기반으로 다음 세션 문제를 생성하여 반환."""
    wp = WeakProfile.query.filter_by(profile_id=profile_id).first()
    weak_profile_dict = wp.to_dict() if wp else None
    problem = (problem_generator.generate_for_profile(weak_profile_dict, game_type)
               if weak_profile_dict
               else problem_generator.generate_default(game_type))
    return ok(problem)


# ─── 전역 통계 API ───────────────────────────────────────────────────────
@app.route('/api/global-stats', methods=['GET'])
def get_global_stats():
    return ok(_global_stats_dict())


# ─── 헬스체크 ─────────────────────────────────────────────────────────────
@app.route('/api/health', methods=['GET'])
def health():
    return ok({'status': 'ok', 'time': datetime.utcnow().isoformat()})


# ─── 실행 ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 55)
    print("  ParkiCare AI - Flask Server Starting")
    print("  Access: http://127.0.0.1:5000")
    print("=" * 55)
    app.run(debug=True, host='127.0.0.1', port=5000)
