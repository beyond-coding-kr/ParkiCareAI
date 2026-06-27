from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username
        }

class Profile(db.Model):
    __tablename__ = 'profiles'
    
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'userId': self.user_id,
            'createdAt': self.created_at.isoformat()
        }

class GameSession(db.Model):
    __tablename__ = 'game_sessions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.String(64), db.ForeignKey('profiles.id'), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    avg_response_time = db.Column(db.Float, nullable=False)
    correct_count = db.Column(db.Integer, nullable=False)
    total_rounds = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.Integer, nullable=False, default=2)
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
            'difficulty': self.difficulty,
            'timestamp': self.timestamp.isoformat()
        }

class GlobalStats(db.Model):
    __tablename__ = 'global_stats'
    
    game_type = db.Column(db.String(50), primary_key=True)
    avg_response_time = db.Column(db.Float, nullable=False, default=2000.0)
    count = db.Column(db.Integer, nullable=False, default=0)

class WeakProfile(db.Model):
    __tablename__ = 'weak_profiles'
    
    profile_id = db.Column(db.String(64), db.ForeignKey('profiles.id'), primary_key=True)
    data_json = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
