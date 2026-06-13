"""
ParkiCare AI - 데이터베이스 초기화
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """앱과 DB를 초기화하고 기본 GlobalStats 레코드를 생성한다."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        _seed_global_stats()


def _seed_global_stats():
    """GlobalStats 초기 레코드가 없으면 기본값으로 생성."""
    from models import GlobalStats
    defaults = {
        'memory_sequence':  2000.0,
        'attention_stroop': 5000.0,
        'motor_response':   800.0,
    }
    for game_type, avg_rt in defaults.items():
        if not GlobalStats.query.get(game_type):
            db.session.add(GlobalStats(
                game_type=game_type,
                avg_response_time=avg_rt,
                count=0,
            ))
    db.session.commit()
