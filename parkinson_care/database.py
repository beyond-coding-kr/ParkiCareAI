"""
파킨슨병 환자 관리 앱 - SQLite 데이터베이스 관리
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from config import DB_PATH, DEFAULT_REHAB_TYPES


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.conn = None
        self.init_db()

    def get_conn(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA foreign_keys=ON")
        return self.conn

    def init_db(self):
        conn = self.get_conn()
        c = conn.cursor()

        # 사용자 테이블
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'patient',
                phone TEXT,
                guardian_name TEXT,
                guardian_phone TEXT,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)

        # 증상 기록
        c.execute("""
            CREATE TABLE IF NOT EXISTS symptoms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT NOT NULL,
                severity INTEGER DEFAULT 5,
                description TEXT,
                media_path TEXT,
                media_type TEXT,
                recorded_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 재활 치료 종류
        c.execute("""
            CREATE TABLE IF NOT EXISTS rehab_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                icon TEXT,
                category TEXT,
                description TEXT,
                difficulty INTEGER DEFAULT 1,
                is_custom INTEGER DEFAULT 0,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # 재활 치료 세션 기록
        c.execute("""
            CREATE TABLE IF NOT EXISTS rehab_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                rehab_type_id INTEGER,
                completed INTEGER DEFAULT 0,
                rating INTEGER,
                notes TEXT,
                scheduled_date TEXT,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (rehab_type_id) REFERENCES rehab_types(id)
            )
        """)

        # AI 분석 결과
        c.execute("""
            CREATE TABLE IF NOT EXISTS ai_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                analysis_type TEXT,
                input_data TEXT,
                result TEXT,
                recommendations TEXT,
                analyzed_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 음성 분석 결과
        c.execute("""
            CREATE TABLE IF NOT EXISTS voice_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                audio_path TEXT,
                jitter REAL,
                shimmer REAL,
                hnr REAL,
                mfcc_data TEXT,
                ai_interpretation TEXT,
                risk_level TEXT,
                analyzed_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 설정
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # 긴급 연락 기록
        c.execute("""
            CREATE TABLE IF NOT EXISTS emergency_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                emergency_type TEXT,
                contacted_number TEXT,
                logged_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()

        # 기본 데이터 삽입
        self._insert_defaults()

    def _insert_defaults(self):
        conn = self.get_conn()
        c = conn.cursor()

        # 기본 재활 치료 종류가 없으면 삽입
        c.execute("SELECT COUNT(*) FROM rehab_types WHERE is_custom=0")
        if c.fetchone()[0] == 0:
            for rt in DEFAULT_REHAB_TYPES:
                c.execute(
                    "INSERT INTO rehab_types (name, icon, category, description, difficulty, is_custom) VALUES (?,?,?,?,?,0)",
                    (rt["name"], rt["icon"], rt["category"], rt["desc"], rt["difficulty"]),
                )

        # 기본 사용자가 없으면 생성
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            c.execute(
                "INSERT INTO users (name, role, guardian_name, guardian_phone) VALUES (?, ?, ?, ?)",
                ("환자", "patient", "보호자", "010-0000-0000"),
            )

        conn.commit()

    # ── 사용자 관련 ──
    def get_user(self, user_id=1):
        c = self.get_conn().cursor()
        c.execute("SELECT * FROM users WHERE id=?", (user_id,))
        return c.fetchone()

    def update_user(self, user_id, **kwargs):
        conn = self.get_conn()
        fields = ", ".join(f"{k}=?" for k in kwargs)
        values = list(kwargs.values()) + [user_id]
        conn.execute(f"UPDATE users SET {fields} WHERE id=?", values)
        conn.commit()

    # ── 증상 관련 ──
    def add_symptom(self, user_id, category, severity, description="", media_path="", media_type=""):
        conn = self.get_conn()
        conn.execute(
            "INSERT INTO symptoms (user_id, category, severity, description, media_path, media_type) VALUES (?,?,?,?,?,?)",
            (user_id, category, severity, description, media_path, media_type),
        )
        conn.commit()

    def get_symptoms(self, user_id=1, limit=50, days=None):
        conn = self.get_conn()
        query = "SELECT * FROM symptoms WHERE user_id=?"
        params = [user_id]
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            query += " AND recorded_at >= ?"
            params.append(cutoff)
        query += " ORDER BY recorded_at DESC LIMIT ?"
        params.append(limit)
        return conn.execute(query, params).fetchall()

    def get_symptom_stats(self, user_id=1, days=30):
        conn = self.get_conn()
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return conn.execute(
            "SELECT category, COUNT(*) as cnt, AVG(severity) as avg_sev FROM symptoms WHERE user_id=? AND recorded_at>=? GROUP BY category ORDER BY cnt DESC",
            (user_id, cutoff),
        ).fetchall()

    # ── 재활 치료 관련 ──
    def get_rehab_types(self):
        return self.get_conn().execute("SELECT * FROM rehab_types ORDER BY category, name").fetchall()

    def add_custom_rehab(self, name, icon, category, description, difficulty, created_by):
        conn = self.get_conn()
        conn.execute(
            "INSERT INTO rehab_types (name, icon, category, description, difficulty, is_custom, created_by) VALUES (?,?,?,?,?,1,?)",
            (name, icon, category, description, difficulty, created_by),
        )
        conn.commit()

    def get_today_rehab_sessions(self, user_id=1):
        today = datetime.now().strftime("%Y-%m-%d")
        return self.get_conn().execute(
            """SELECT rs.*, rt.name as rehab_name, rt.icon, rt.category 
               FROM rehab_sessions rs 
               JOIN rehab_types rt ON rs.rehab_type_id = rt.id 
               WHERE rs.user_id=? AND rs.scheduled_date=?
               ORDER BY rs.id""",
            (user_id, today),
        ).fetchall()

    def schedule_rehab(self, user_id, rehab_type_id, date=None):
        conn = self.get_conn()
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO rehab_sessions (user_id, rehab_type_id, scheduled_date) VALUES (?,?,?)",
            (user_id, rehab_type_id, date),
        )
        conn.commit()

    def complete_rehab(self, session_id, rating=3, notes=""):
        conn = self.get_conn()
        conn.execute(
            "UPDATE rehab_sessions SET completed=1, rating=?, notes=?, completed_at=datetime('now','localtime') WHERE id=?",
            (rating, notes, session_id),
        )
        conn.commit()

    def get_rehab_stats(self, user_id=1, days=30):
        conn = self.get_conn()
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return conn.execute(
            """SELECT rt.name, rt.category, COUNT(*) as total, SUM(rs.completed) as done, AVG(rs.rating) as avg_rating
               FROM rehab_sessions rs JOIN rehab_types rt ON rs.rehab_type_id=rt.id
               WHERE rs.user_id=? AND rs.scheduled_date>=?
               GROUP BY rt.name ORDER BY total DESC""",
            (user_id, cutoff),
        ).fetchall()

    def get_streak(self, user_id=1):
        """연속 재활 수행 일수 계산"""
        conn = self.get_conn()
        rows = conn.execute(
            """SELECT DISTINCT scheduled_date FROM rehab_sessions
               WHERE user_id=? AND completed=1
               ORDER BY scheduled_date DESC""",
            (user_id,),
        ).fetchall()
        if not rows:
            return 0
        streak = 0
        today = datetime.now().date()
        for row in rows:
            d = datetime.strptime(row["scheduled_date"], "%Y-%m-%d").date()
            expected = today - timedelta(days=streak)
            if d == expected:
                streak += 1
            else:
                break
        return streak

    # ── AI 분석 관련 ──
    def add_ai_analysis(self, user_id, analysis_type, input_data, result, recommendations=""):
        conn = self.get_conn()
        conn.execute(
            "INSERT INTO ai_analyses (user_id, analysis_type, input_data, result, recommendations) VALUES (?,?,?,?,?)",
            (user_id, analysis_type, input_data, result, recommendations),
        )
        conn.commit()

    def get_ai_analyses(self, user_id=1, limit=20):
        return self.get_conn().execute(
            "SELECT * FROM ai_analyses WHERE user_id=? ORDER BY analyzed_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()

    # ── 음성 분석 관련 ──
    def add_voice_analysis(self, user_id, audio_path, jitter, shimmer, hnr, mfcc_data, ai_interpretation, risk_level):
        conn = self.get_conn()
        conn.execute(
            "INSERT INTO voice_analyses (user_id, audio_path, jitter, shimmer, hnr, mfcc_data, ai_interpretation, risk_level) VALUES (?,?,?,?,?,?,?,?)",
            (user_id, audio_path, jitter, shimmer, hnr, json.dumps(mfcc_data), ai_interpretation, risk_level),
        )
        conn.commit()

    def get_voice_analyses(self, user_id=1, limit=20):
        return self.get_conn().execute(
            "SELECT * FROM voice_analyses WHERE user_id=? ORDER BY analyzed_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()

    # ── 긴급 연락 기록 ──
    def log_emergency(self, user_id, emergency_type, contacted_number):
        conn = self.get_conn()
        conn.execute(
            "INSERT INTO emergency_logs (user_id, emergency_type, contacted_number) VALUES (?,?,?)",
            (user_id, emergency_type, contacted_number),
        )
        conn.commit()

    def get_emergency_logs(self, user_id=1, limit=10):
        return self.get_conn().execute(
            "SELECT * FROM emergency_logs WHERE user_id=? ORDER BY logged_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()

    # ── 설정 관련 ──
    def get_setting(self, key, default=None):
        row = self.get_conn().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        conn = self.get_conn()
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, str(value)))
        conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
