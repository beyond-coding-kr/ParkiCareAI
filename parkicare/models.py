"""
ParkiCare AI - SQLAlchemy 데이터베이스 모델
"""

from datetime import datetime
from database import db


class Profile(db.Model):
    """환자 프로필"""
    __tablename__ = 'profiles'

    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    stage = db.Column(db.String(20), nullable=False, default='stage1')
    diagnosis = db.Column(db.String(200), nullable=True)
    color = db.Column(db.String(20), nullable=False, default='#00D4FF')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sessions = db.relationship('GameSession', backref='profile',
                               lazy=True, cascade='all, delete-orphan')
    weak_profiles = db.relationship('WeakProfile', backref='profile',
                                    lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'stage': self.stage,
            'diagnosis': self.diagnosis,
            'color': self.color,
            'createdAt': self.created_at.isoformat(),
        }


class GameSession(db.Model):
    """게임 세션 기록"""
    __tablename__ = 'game_sessions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.String(64), db.ForeignKey('profiles.id'), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)
    accuracy = db.Column(db.Float, nullable=False)            # 0.0 ~ 1.0
    avg_response_time = db.Column(db.Float, nullable=False)   # 밀리초
    correct_count = db.Column(db.Integer, nullable=False)
    total_rounds = db.Column(db.Integer, nullable=False)
    miss_count = db.Column(db.Integer, nullable=True, default=0)
    difficulty = db.Column(db.Integer, nullable=False, default=1)
    fatigue = db.Column(db.Integer, nullable=True, default=1)    # 피로도 (1: 좋음 ~ 4: 심함)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'profileId': self.profile_id,
            'gameType': self.game_type,
            'accuracy': self.accuracy,
            'avgResponseTime': self.avg_response_time,
            'correctCount': self.correct_count,
            'totalRounds': self.total_rounds,
            'missCount': self.miss_count or 0,
            'difficulty': self.difficulty,
            'fatigue': self.fatigue or 1,
            'timestamp': self.timestamp.isoformat(),
        }


class WeakProfile(db.Model):
    """AI 분석 결과 - 취약 프로파일"""
    __tablename__ = 'weak_profiles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.String(64), db.ForeignKey('profiles.id'), nullable=False, unique=True)
    overall_score = db.Column(db.Integer, nullable=False, default=0)
    games_json = db.Column(db.Text, nullable=False, default='{}')     # JSON 문자열
    weak_areas_json = db.Column(db.Text, nullable=False, default='[]')
    strong_areas_json = db.Column(db.Text, nullable=False, default='[]')
    recommendations_json = db.Column(db.Text, nullable=False, default='[]')
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            'profileId': self.profile_id,
            'overallScore': self.overall_score,
            'games': json.loads(self.games_json),
            'weakAreas': json.loads(self.weak_areas_json),
            'strongAreas': json.loads(self.strong_areas_json),
            'recommendations': json.loads(self.recommendations_json),
            'analyzedAt': self.analyzed_at.isoformat(),
        }


class GlobalStats(db.Model):
    """전체 사용자 평균 통계 (응답 시간 기준)"""
    __tablename__ = 'global_stats'

    game_type = db.Column(db.String(50), primary_key=True)
    avg_response_time = db.Column(db.Float, nullable=False, default=2000.0)
    count = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            'gameType': self.game_type,
            'avgResponseTime': self.avg_response_time,
            'count': self.count,
        }
