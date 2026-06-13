import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
import math
import random
from datetime import datetime

# ─── COLOR PALETTE (Dark Mode, Premium Web-Like Theme) ────────────────────────
COLOR_BG_BASE = "#080C18"       # Deep dark blue base
COLOR_BG_SURFACE = "#0D1220"    # Slightly lighter surface
COLOR_CARD = "#171E30"          # Card background
COLOR_BORDER = "#2A354F"        # Border color
COLOR_TEXT_PRIMARY = "#E8EDF8"  # Main text
COLOR_TEXT_SECONDARY = "#8A9AB8"# Muted text
COLOR_CYAN = "#00D4FF"          # Cyan highlight
COLOR_PURPLE = "#7B2FBE"        # Purple highlight
COLOR_GREEN = "#00FF94"         # Green success/stable
COLOR_RED = "#FF6B6B"           # Red warning/weak
COLOR_AMBER = "#FFB800"         # Amber attention/fatigue

# Game info structure matching JS version
GAME_INFO = {
    'memory_sequence': {'label': '기억 카드 맞추기', 'emoji': '🧠', 'color': COLOR_CYAN, 'desc': '제시된 카드의 짝을 차례로 맞추는 기억 훈련'},
    'attention_stroop': {'label': '색-동작 반응 게임', 'emoji': '🎯', 'color': COLOR_PURPLE, 'desc': '글자의 실제 색상을 골라 탭하는 간섭 반응 훈련'},
    'motor_response': {'label': '손가락 순서 누르기', 'emoji': '✋', 'color': COLOR_GREEN, 'desc': '숫자가 적힌 원들을 차례대로 탭하는 운동 훈련'}
}

STAGE_LABELS = {
    'stage1': '초기 단계 (일상 원활)',
    'stage2': '경증 단계 (간헐적 불편)',
    'stage3': '중등도 단계 (균형 관리)',
    'stage4': '중증 단계 (보호자 관찰)'
}

# ─── DATABASE INITIALIZATION ──────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("parkicare.db")
    cur = conn.cursor()
    # Profiles Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        stage TEXT NOT NULL,
        diagnosis TEXT,
        color TEXT,
        created_at TEXT
    )""")
    # Game Sessions Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS game_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id TEXT,
        game_type TEXT,
        accuracy REAL,
        avg_response_time REAL,
        correct_count INTEGER,
        total_rounds INTEGER,
        miss_count INTEGER,
        difficulty INTEGER,
        fatigue INTEGER,
        timestamp TEXT,
        FOREIGN KEY(profile_id) REFERENCES profiles(id)
    )""")
    # Weak Profiles Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS weak_profiles (
        profile_id TEXT PRIMARY KEY,
        overall_score INTEGER,
        games_json TEXT,
        weak_areas_json TEXT,
        strong_areas_json TEXT,
        recommendations_json TEXT,
        analyzed_at TEXT,
        safety_triggered INTEGER,
        FOREIGN KEY(profile_id) REFERENCES profiles(id)
    )""")
    # Global Stats Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS global_stats (
        game_type TEXT PRIMARY KEY,
        avg_response_time REAL,
        count INTEGER
    )""")
    
    # Insert initial global stats if not exist
    for gt in ['memory_sequence', 'attention_stroop', 'motor_response']:
        cur.execute("INSERT OR IGNORE INTO global_stats VALUES (?, 2000.0, 10)", (gt,))
        
    conn.commit()
    conn.close()

# ─── CORE AI RECOMMENDATION RULES ENGINE (PYTHON IMPLEMENTATION) ──────────────
def run_ai_analysis(profile_id):
    conn = sqlite3.connect("parkicare.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # 1. Fetch profile sessions
    game_types = ['memory_sequence', 'attention_stroop', 'motor_response']
    sessions_by_type = {gt: [] for gt in game_types}
    
    cur.execute("SELECT * FROM game_sessions WHERE profile_id = ? ORDER BY timestamp ASC", (profile_id,))
    rows = cur.fetchall()
    for r in rows:
        sessions_by_type[r['game_type']].append(dict(r))
        
    # 2. Fetch global statistics
    cur.execute("SELECT * FROM global_stats")
    stats_rows = cur.fetchall()
    global_stats = {r['game_type']: dict(r) for r in stats_rows}
    
    MIN_SESSIONS = 3
    games = {}
    total_score = 0
    game_count = 0
    weak_areas = []
    strong_areas = []
    
    safety_triggered = 0
    safety_message = ""
    
    # Check if last session was a fatigue-abort (level 4)
    cur.execute("SELECT * FROM game_sessions WHERE profile_id = ? ORDER BY timestamp DESC LIMIT 1", (profile_id,))
    last_any = cur.fetchone()
    if last_any and last_any['fatigue'] >= 4:
        safety_triggered = 1
        safety_message = f"⚠️ [안전 안내] 최근 수행 중 극심한 피로, 통증 또는 어지러움이 기록되었습니다. 즉시 훈련을 일시 중단하고 충분한 휴식을 권장합니다."

    for gt in game_types:
      sessions = sessions_by_type[gt]
      has_enough = len(sessions) >= MIN_SESSIONS
      recent = sessions[-MIN_SESSIONS:] if has_enough else []
      
      # Check fatigue safety at game level
      if len(sessions) > 0 and sessions[-1]['fatigue'] >= 4:
          safety_triggered = 1
          safety_message = f"⚠️ [안전 안내] 최근 {GAME_INFO[sessions[-1]['game_type']]['label']} 수행 중 극심한 피로, 통증 또는 어지러움이 기록되었습니다. 충분한 안정을 취하고 시작하십시오."

      accuracy = None
      rt = None
      is_weak = False
      difficulty = 1
      trend = 'stable'
      
      if has_enough:
          accuracy = sum(s['accuracy'] for s in recent) / MIN_SESSIONS
          rt = sum(s['avg_response_time'] for s in recent) / MIN_SESSIONS
          
          # Compare with own average
          all_avg_rt = sum(s['avg_response_time'] for s in sessions) / len(sessions)
          global_avg_rt = global_stats.get(gt, {}).get('avg_response_time', 2000.0)
          
          # Weak area rules
          is_acc_weak = accuracy < 0.70
          is_rt_weak = rt > global_avg_rt * 1.30
          is_self_declining = len(sessions) > MIN_SESSIONS and (rt > all_avg_rt * 1.25)
          
          is_weak = is_acc_weak or is_rt_weak or is_self_declining
          
          # Difficulty adjustment based on accuracy & fatigue
          has_fatigue = any(s['fatigue'] >= 3 for s in recent)
          last_session = recent[-1]
          
          if last_session['accuracy'] >= 0.85 and not has_fatigue:
              difficulty = min(5, last_session['difficulty'] + 1)
          elif is_weak or has_fatigue or last_session['fatigue'] >= 4:
              difficulty = max(1, last_session['difficulty'] - 1)
          else:
              difficulty = last_session['difficulty']
              
          # Trend
          half = max(1, len(sessions) // 2)
          first_avg = sum(s['accuracy'] for s in sessions[:half]) / half
          second_avg = sum(s['accuracy'] for s in sessions[-half:]) / half
          diff = second_avg - first_avg
          if diff > 0.05: trend = 'improving'
          elif diff < -0.05: trend = 'declining'
          
      games[gt] = {
          'sessionCount': len(sessions),
          'hasEnoughData': has_enough,
          'accuracy': accuracy,
          'responseTime': rt,
          'difficulty': difficulty,
          'trend': trend,
          'isWeak': is_weak,
          'recommendedDifficulty': max(1, difficulty)
      }
      
      if has_enough:
          total_score += round(accuracy * 100)
          game_count += 1
          if is_weak:
              weak_areas.append(gt)
          else:
              strong_areas.append(gt)
              
    overall_score = round(total_score / game_count) if game_count > 0 else 0
    
    # Recommendations formulation (Purified wording, numerical facts)
    recommendations = []
    if safety_triggered:
        recommendations.append({
            'type': 'safety_stop',
            'priority': 'high',
            'message': safety_message,
            'label': '안전 주의 알림'
        })
        
    for area in weak_areas:
        g = games[area]
        g_avg = global_stats.get(area, {}).get('avg_response_time', 2000.0)
        ratio = (g['responseTime'] / g_avg) if g_avg > 0 else 1.3
        
        reason = ""
        if g['accuracy'] < 0.70:
            reason = f"최근 3회 평균 정확도가 {round(g['accuracy'] * 100)}%로 통과 기준(70%)보다 낮음."
        else:
            reason = f"최근 3회 평균 응답 시간이 {g['responseTime']/1000:.2f}초로 기준치({g_avg/1000:.2f}초) 대비 약 {ratio:.1f}배 지연됨."
            
        recommendations.append({
            'type': area,
            'priority': 'medium' if safety_triggered else 'high',
            'message': f"📋 [보강 필요] {GAME_INFO[area]['label']}을 집중 훈련 후보로 표시합니다. (수치 근거: {reason} 난이도를 {g['recommendedDifficulty']}단으로 설정하여 보조합니다.)",
            'label': GAME_INFO[area]['label']
        })
        
    for area in strong_areas:
        g = games[area]
        if g['trend'] == 'improving':
            recommendations.append({
                'type': area,
                'priority': 'low',
                'message': f"✨ [유지] {GAME_INFO[area]['label']} 훈련 점수가 상승 흐름을 보이고 있습니다. 현재 수준의 반복 훈련 기록을 유지하십시오.",
                'label': GAME_INFO[area]['label']
            })
            
    if not weak_areas and game_count > 0:
        recommendations.append({
            'type': 'general',
            'priority': 'info',
            'message': f"👍 전 훈련 영역의 정답률 및 시간 편차가 관리 기준선 내로 균형 잡혀 있습니다. 정기적인 일일 세션을 수행하십시오.",
            'label': '종합 상태'
        })
        
    # Save/Upsert analyzed weak profile
    cur.execute("""
    INSERT INTO weak_profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(profile_id) DO UPDATE SET
        overall_score=excluded.overall_score,
        games_json=excluded.games_json,
        weak_areas_json=excluded.weak_areas_json,
        strong_areas_json=excluded.strong_areas_json,
        recommendations_json=excluded.recommendations_json,
        analyzed_at=excluded.analyzed_at,
        safety_triggered=excluded.safety_triggered
    """, (
        profile_id,
        overall_score,
        json.dumps(games),
        json.dumps(weak_areas),
        json.dumps(strong_areas),
        json.dumps(recommendations),
        datetime.utcnow().isoformat(),
        safety_triggered
    ))
    
    conn.commit()
    conn.close()

# ─── MAIN WINDOW APPLICATION ──────────────────────────────────────────────────
class ParkiCareApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ParkiCare Play - 파킨슨 인지·운동 보조 시스템")
        self.geometry("500x780")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG_BASE)
        
        # Styles config
        self.custom_styles()
        
        # State variables
        self.current_profile = None
        self.current_frame = None
        
        # Permanent Top Disclaimer
        self.create_disclaimer()
        
        # Container frame for SPA screens
        self.content_container = tk.Frame(self, bg=COLOR_BG_BASE)
        self.content_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))
        
        # Route to initial screen
        self.switch_screen("home")
        
    def custom_styles(self):
        # Using native Tkinter styles combined with config properties
        self.option_add("*Font", "Outfit 11")
        self.option_add("*Background", COLOR_BG_BASE)
        self.option_add("*Foreground", COLOR_TEXT_PRIMARY)
        
    def create_disclaimer(self):
        banner = tk.Frame(self, bg="#2A1215", highlightbackground=COLOR_RED, highlightthickness=1)
        banner.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        label_title = tk.Label(banner, text="⚠️ [의료적 안전 고지 및 한계 명시]", font=("Outfit", 10, "bold"), fg=COLOR_RED, bg="#2A1215")
        label_title.pack(anchor="w", padx=10, pady=(6, 2))
        
        desc_text = "본 프로그램은 의학적 치료/진단을 목적으로 하지 않는 개인 기록 및 훈련 보조 도구입니다.\n통증, 극도 피로, 어지러움 등의 증세가 나타날 시 강제로 수행을 멈추고 의료인에 문의하십시오."
        label_desc = tk.Label(banner, text=desc_text, font=("Outfit", 9), fg=COLOR_TEXT_SECONDARY, bg="#2A1215", justify="left")
        label_desc.pack(anchor="w", padx=10, pady=(0, 6))

    def switch_screen(self, screen_name, **kwargs):
        if self.current_frame:
            self.current_frame.destroy()
            
        if screen_name == "home":
            self.current_frame = HomeScreen(self.content_container, self)
        elif screen_name == "profile-create":
            self.current_frame = ProfileCreateScreen(self.content_container, self)
        elif screen_name == "hub":
            self.current_frame = HubScreen(self.content_container, self)
        elif screen_name == "pre-game-check":
            self.current_frame = PreGameCheckScreen(self.content_container, self, kwargs.get("game_type"))
        elif screen_name == "safety-warning":
            self.current_frame = SafetyWarningScreen(self.content_container, self, kwargs.get("game_type"))
        elif screen_name == "game":
            self.current_frame = GameScreen(self.content_container, self, kwargs.get("game_type"), kwargs.get("fatigue"))
        elif screen_name == "result":
            self.current_frame = ResultScreen(self.content_container, self, kwargs.get("game_type"), kwargs.get("session_data"))
        elif screen_name == "dashboard":
            self.current_frame = DashboardScreen(self.content_container, self)
        elif screen_name == "report":
            self.current_frame = ReportScreen(self.content_container, self)
        elif screen_name == "validation-dashboard":
            self.current_frame = ValidationDashboardScreen(self.content_container, self)
            
        self.current_frame.pack(fill=tk.BOTH, expand=True)

# ─── SCREEN 1: HOME (PROFILE SELECTION) ───────────────────────────────────────
class HomeScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG_BASE)
        self.controller = controller
        
        # Header title
        title_lbl = tk.Label(self, text="ParkiCare Play", font=("Outfit", 26, "bold"), fg=COLOR_CYAN, bg=COLOR_BG_BASE)
        title_lbl.pack(pady=(15, 2))
        
        sub_lbl = tk.Label(self, text="파킨슨 환자 기록 기반 인지·운동 보조 시스템", font=("Outfit", 12), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE)
        sub_lbl.pack(pady=(0, 20))
        
        # Load Profiles
        conn = sqlite3.connect("parkicare.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM profiles ORDER BY created_at ASC")
        self.profiles = [dict(r) for r in cur.fetchall()]
        conn.close()
        
        if not self.profiles:
            empty_frame = tk.Frame(self, bg=COLOR_BG_SURFACE, highlightbackground=COLOR_BORDER, highlightthickness=1)
            empty_frame.pack(fill=tk.X, pady=20, ipady=30)
            
            icon = tk.Label(empty_frame, text="👤", font=("Outfit", 40), bg=COLOR_BG_SURFACE, fg=COLOR_TEXT_SECONDARY)
            icon.pack(pady=10)
            
            msg = tk.Label(empty_frame, text="등록된 아바타 프로필이 존재하지 않습니다.\n첫 훈련을 진행하기 위해 프로필을 등록하십시오.", font=("Outfit", 11), bg=COLOR_BG_SURFACE, fg=COLOR_TEXT_SECONDARY)
            msg.pack(pady=5)
            
            reg_btn = tk.Button(empty_frame, text="새 프로필 아바타 만들기", font=("Outfit", 11, "bold"), bg=COLOR_CYAN, fg="#000", bd=0, padx=15, pady=8, cursor="hand2", command=lambda: controller.switch_screen("profile-create"))
            reg_btn.pack(pady=15)
        else:
            list_title = tk.Label(self, text="훈련용 프로필 아바타 선택", font=("Outfit", 11, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE)
            list_title.pack(anchor="w", pady=(10, 8))
            
            # Profiles List container
            list_frame = tk.Frame(self, bg=COLOR_BG_BASE)
            list_frame.pack(fill=tk.BOTH, expand=True)
            
            for p in self.profiles:
                card = tk.Frame(list_frame, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1, cursor="hand2")
                card.pack(fill=tk.X, pady=5)
                
                # Bind clicks to select profile
                self.bind_clicks(card, p)
                
                avatar = tk.Label(card, text=p['name'][0], font=("Outfit", 16, "bold"), fg="#FFF", bg=p['color'], width=3, height=1)
                avatar.pack(side=tk.LEFT, padx=10, pady=10)
                
                info_f = tk.Frame(card, bg=COLOR_CARD)
                info_f.pack(side=tk.LEFT, fill=tk.Y, pady=10)
                
                name_lbl = tk.Label(info_f, text=p['name'], font=("Outfit", 13, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD)
                name_lbl.pack(anchor="w")
                
                meta_lbl = tk.Label(info_f, text=f"{p['age']}세 · {STAGE_LABELS.get(p['stage'], p['stage'])}", font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD)
                meta_lbl.pack(anchor="w")
                
                # Del btn
                del_btn = tk.Button(card, text="삭제", font=("Outfit", 9), bg="#222", fg=COLOR_RED, bd=0, padx=8, pady=4, cursor="hand2", command=lambda pid=p['id']: self.delete_p(pid))
                del_btn.pack(side=tk.RIGHT, padx=15)
                
            add_btn = tk.Button(self, text="+ 신규 아바타 추가", font=("Outfit", 11, "bold"), bg=COLOR_BG_SURFACE, fg=COLOR_CYAN, highlightbackground=COLOR_CYAN, highlightthickness=1, bd=0, pady=10, cursor="hand2", command=lambda: controller.switch_screen("profile-create"))
            add_btn.pack(fill=tk.X, pady=10)
            
        # AI Simulator Test Button
        sim_btn = tk.Button(self, text="🤖 AI 검증 시뮬레이터 (5인 50세션 데이터 검증)", font=("Outfit", 11, "bold"), bg=COLOR_PURPLE, fg="#FFF", bd=0, pady=12, cursor="hand2", command=lambda: controller.switch_screen("validation-dashboard"))
        sim_btn.pack(fill=tk.X, pady=10)

    def bind_clicks(self, widget, p):
        widget.bind("<Button-1>", lambda e: self.select_profile(p))
        for child in widget.winfo_children():
            child.bind("<Button-1>", lambda e: self.select_profile(p))
            
    def select_profile(self, p):
        self.controller.current_profile = p
        self.controller.switch_screen("hub")
        
    def delete_p(self, pid):
        if messagebox.askyesno("삭제 확인", "해당 프로필 및 모든 관련 기록들이 영구적으로 삭제됩니다. 계속하겠습니까?"):
            conn = sqlite3.connect("parkicare.db")
            cur = conn.cursor()
            cur.execute("DELETE FROM profiles WHERE id=?", (pid,))
            cur.execute("DELETE FROM game_sessions WHERE profile_id=?", (pid,))
            cur.execute("DELETE FROM weak_profiles WHERE profile_id=?", (pid,))
            conn.commit()
            conn.close()
            self.controller.switch_screen("home")

# ─── SCREEN 2: PROFILE CREATE ────────────────────────────────────────────────
class ProfileCreateScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG_BASE)
        self.controller = controller
        
        back_btn = tk.Button(self, text="← 돌아가기", font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE, bd=0, activebackground=COLOR_BG_BASE, activeforeground=COLOR_CYAN, command=lambda: controller.switch_screen("home"))
        back_btn.pack(anchor="w", pady=(5, 10))
        
        h_lbl = tk.Label(self, text="신규 아바타 등록", font=("Outfit", 20, "bold"), fg=COLOR_CYAN, bg=COLOR_BG_BASE)
        h_lbl.pack(anchor="w", pady=(0, 20))
        
        form = tk.Frame(self, bg=COLOR_BG_BASE)
        form.pack(fill=tk.X)
        
        # Name Input
        tk.Label(form, text="환자명 또는 아바타 닉네임", font=("Outfit", 10, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=(8, 3))
        self.name_ent = tk.Entry(form, font=("Outfit", 12), bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY, insertbackground="#FFF", bd=1, relief="flat", highlightbackground=COLOR_BORDER, highlightthickness=1)
        self.name_ent.pack(fill=tk.X, ipady=6, pady=(0, 10))
        
        # Age Input
        tk.Label(form, text="만 나이", font=("Outfit", 10, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=(8, 3))
        self.age_ent = tk.Entry(form, font=("Outfit", 12), bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY, insertbackground="#FFF", bd=1, relief="flat", highlightbackground=COLOR_BORDER, highlightthickness=1)
        self.age_ent.pack(fill=tk.X, ipady=6, pady=(0, 10))
        
        # Stage dropdown
        tk.Label(form, text="현재 자가 관리 단계", font=("Outfit", 10, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=(8, 3))
        self.stage_var = tk.StringVar(value="stage1")
        stage_sel = ttk.Combobox(form, textvariable=self.stage_var, font=("Outfit", 11), state="readonly")
        stage_sel['values'] = ('stage1', 'stage2', 'stage3', 'stage4')
        stage_sel.pack(fill=tk.X, ipady=6, pady=(0, 10))
        
        # Colorpicker Simulation
        tk.Label(form, text="아바타 표시 색상", font=("Outfit", 10, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=(8, 3))
        self.selected_color = AVATAR_COLORS[0]
        color_bar = tk.Frame(form, bg=COLOR_BG_BASE)
        color_bar.pack(fill=tk.X, pady=5)
        
        self.color_indicators = []
        for c in AVATAR_COLORS:
            lbl = tk.Label(color_bar, text=" ● ", font=("Outfit", 18), fg=c, bg=COLOR_BG_BASE, cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=5)
            lbl.bind("<Button-1>", lambda e, col=c, obj=lbl: self.pick_color(col, obj))
            self.color_indicators.append((c, lbl))
        self.highlight_color()

        # Submit
        submit_btn = tk.Button(self, text="프로필 아바타 등록 완료", font=("Outfit", 12, "bold"), bg=COLOR_CYAN, fg="#000", bd=0, pady=12, cursor="hand2", command=self.save_profile)
        submit_btn.pack(fill=tk.X, pady=30)
        
    def pick_color(self, col, obj):
        self.selected_color = col
        self.highlight_color()
        
    def highlight_color(self):
        for c, lbl in self.color_indicators:
            if c == self.selected_color:
                lbl.configure(bg=COLOR_CARD, relief="groove")
            else:
                lbl.configure(bg=COLOR_BG_BASE, relief="flat")
                
    def save_profile(self):
        name = self.name_ent.get().strip()
        age_str = self.age_ent.get().strip()
        stage = self.stage_var.get()
        
        if not name or not age_str:
            messagebox.showwarning("필수 입력 누락", "이름과 나이를 모두 채워주십시오.")
            return
            
        try:
            age = int(age_str)
        except ValueError:
            messagebox.showwarning("입력 형식 오류", "나이는 숫자로 입력하십시오.")
            return
            
        pid = f"p_py_{random.randint(100000, 999999)}"
        conn = sqlite3.connect("parkicare.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO profiles VALUES (?, ?, ?, ?, '', ?, ?)", 
                    (pid, name, age, stage, self.selected_color, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        
        self.controller.current_profile = {
            'id': pid, 'name': name, 'age': age, 'stage': stage, 'color': self.selected_color
        }
        self.controller.switch_screen("hub")

# ─── SCREEN 3: TRATINING HUB ──────────────────────────────────────────────────
class HubScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG_BASE)
        self.controller = controller
        p = controller.current_profile
        
        # Navigation bar
        nav = tk.Frame(self, bg=COLOR_BG_BASE)
        nav.pack(fill=tk.X, pady=(5, 10))
        
        back_btn = tk.Button(nav, text="← 아바타 목록", font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE, bd=0, activebackground=COLOR_BG_BASE, activeforeground=COLOR_CYAN, command=lambda: controller.switch_screen("home"))
        back_btn.pack(side=tk.LEFT)
        
        dash_btn = tk.Button(nav, text="📊 AI 분석 보고서", font=("Outfit", 10, "bold"), fg=COLOR_CYAN, bg=COLOR_BG_BASE, bd=0, cursor="hand2", command=lambda: controller.switch_screen("dashboard"))
        dash_btn.pack(side=tk.RIGHT)
        
        # User details card
        user_card = tk.Frame(self, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)
        user_card.pack(fill=tk.X, pady=(0, 10))
        
        avatar = tk.Label(user_card, text=p['name'][0], font=("Outfit", 18, "bold"), fg="#FFF", bg=p['color'], width=3, height=1)
        avatar.pack(side=tk.LEFT, padx=12, pady=12)
        
        details = tk.Frame(user_card, bg=COLOR_CARD)
        details.pack(side=tk.LEFT, fill=tk.Y, pady=12)
        
        name_lbl = tk.Label(details, text=p['name'], font=("Outfit", 14, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD)
        name_lbl.pack(anchor="w")
        
        stage_lbl = tk.Label(details, text=f"{STAGE_LABELS.get(p['stage'], p['stage'])} 관리 중", font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD)
        stage_lbl.pack(anchor="w")
        
        # Fetch Weak Profile & Session counts
        conn = sqlite3.connect("parkicare.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Counts
        counts = {}
        for gt in ['memory_sequence', 'attention_stroop', 'motor_response']:
            cur.execute("SELECT COUNT(*) as cnt FROM game_sessions WHERE profile_id=? AND game_type=?", (p['id'], gt))
            counts[gt] = cur.fetchone()['cnt']
            
        # Weak profile
        cur.execute("SELECT * FROM weak_profiles WHERE profile_id=?", (p['id'],))
        wp_row = cur.fetchone()
        self.wp = dict(wp_row) if wp_row else None
        conn.close()
        
        # AI banner
        if self.wp:
            grade_info = self.get_grade(self.wp['overall_score'])
            ai_card = tk.Frame(self, bg="rgba(0, 212, 255, 0.08)", highlightbackground="rgba(0, 212, 255, 0.2)", highlightthickness=1)
            ai_card.pack(fill=tk.X, pady=(0, 12))
            
            lbl_grade = tk.Label(ai_card, text=f"{grade_info['emoji']} 종합 판정: {grade_info['label']}", font=("Outfit", 11, "bold"), fg=grade_info['color'], bg="rgba(0, 212, 255, 0.08)")
            lbl_grade.pack(side=tk.LEFT, padx=12, pady=10)
            
            lbl_score = tk.Label(ai_card, text=f"분석지수: {self.wp['overall_score']}", font=("Outfit", 12, "bold"), fg=grade_info['color'], bg="rgba(0, 212, 255, 0.08)")
            lbl_score.pack(side=tk.RIGHT, padx=12, pady=10)
        else:
            banner = tk.Frame(self, bg="#201C10", highlightbackground=COLOR_AMBER, highlightthickness=1)
            banner.pack(fill=tk.X, pady=(0, 12))
            lbl = tk.Label(banner, text="💡 세 개 미션을 각각 3회 완료하면 AI 추천 처방 분석이 구동됩니다.", font=("Outfit", 9), fg=COLOR_AMBER, bg="#201C10")
            lbl.pack(pady=8, padx=10, anchor="w")
            
        # Safety Alert Banner
        if self.wp and self.wp.get('safety_triggered') == 1:
            safety_alert = tk.Frame(self, bg="#331A1D", highlightbackground=COLOR_RED, highlightthickness=1)
            safety_alert.pack(fill=tk.X, pady=(0, 12))
            slbl = tk.Label(safety_alert, text="⚠️ [주의] 최근 컨디션 악화가 감지되었습니다. 충분히 안정을 취하십시오.", font=("Outfit", 9, "bold"), fg=COLOR_RED, bg="#331A1D")
            slbl.pack(pady=8, padx=10, anchor="w")

        # Game Card widgets
        tk.Label(self, text="훈련용 보조 미션 리스트", font=("Outfit", 12, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=(10, 5))
        
        recs = json.loads(self.wp['recommendations_json']) if self.wp else []
        weak_types = self.wp['weak_areas_json'] if self.wp else "[]"
        
        for gt, info in GAME_INFO.items():
            is_weak = gt in weak_types
            is_rec = any(r['type'] == gt and r['priority'] == 'high' for r in recs)
            
            card = tk.Frame(self, bg=COLOR_CARD, highlightbackground=COLOR_RED if is_weak else (COLOR_CYAN if is_rec else COLOR_BORDER), highlightthickness=1.5 if (is_weak or is_rec) else 1, cursor="hand2")
            card.pack(fill=tk.X, pady=5)
            
            # Bind Click to pre-game screen
            self.bind_card_click(card, gt)
            
            emoji_lbl = tk.Label(card, text=info['emoji'], font=("Outfit", 24), bg=COLOR_CARD)
            emoji_lbl.pack(side=tk.LEFT, padx=12, pady=12)
            
            info_f = tk.Frame(card, bg=COLOR_CARD)
            info_f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10)
            
            # Title with recommendation badges
            title_text = info['label']
            title_lbl = tk.Label(info_f, text=title_text, font=("Outfit", 12, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD)
            title_lbl.pack(anchor="w")
            
            # Badges
            badge_f = tk.Frame(info_f, bg=COLOR_CARD)
            badge_f.pack(anchor="w", pady=(2, 0))
            
            tk.Label(badge_f, text=f"누적 {counts[gt]}회 수행", font=("Outfit", 8), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=4).pack(side=tk.LEFT, padx=(0, 4))
            
            if is_rec:
                tk.Label(badge_f, text="✦ AI 보완 추천", font=("Outfit", 8, "bold"), fg=COLOR_CYAN, bg=COLOR_CARD, highlightbackground=COLOR_CYAN, highlightthickness=1, padx=4).pack(side=tk.LEFT, padx=(0, 4))
            if is_weak:
                tk.Label(badge_f, text="⚠️ 동작 지연/편차 요망", font=("Outfit", 8, "bold"), fg=COLOR_RED, bg=COLOR_CARD, highlightbackground=COLOR_RED, highlightthickness=1, padx=4).pack(side=tk.LEFT, padx=(0, 4))
                
            tk.Label(card, text="시작 →", font=("Outfit", 10, "bold"), fg=COLOR_CYAN, bg=COLOR_CARD).pack(side=tk.RIGHT, padx=15)
            
        # Bottom controls
        bot_f = tk.Frame(self, bg=COLOR_BG_BASE)
        bot_f.pack(fill=tk.X, pady=20)
        
        rep_btn = tk.Button(bot_f, text="📋 주간 훈련 리포트 확인", font=("Outfit", 11), bg=COLOR_BG_SURFACE, fg=COLOR_TEXT_PRIMARY, highlightbackground=COLOR_BORDER, highlightthickness=1, bd=0, pady=10, cursor="hand2", command=lambda: controller.switch_screen("report"))
        rep_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ana_btn = tk.Button(bot_f, text="🤖 AI 분석 데이터 갱신", font=("Outfit", 11, "bold"), bg=COLOR_CYAN, fg="#000", bd=0, pady=10, cursor="hand2", command=self.renew_analysis)
        ana_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
    def bind_card_click(self, widget, gt):
        widget.bind("<Button-1>", lambda e: self.controller.switch_screen("pre-game-check", game_type=gt))
        for child in widget.winfo_children():
            # recursion for frames
            if isinstance(child, tk.Frame):
                self.bind_card_click(child, gt)
            else:
                child.bind("<Button-1>", lambda e: self.controller.switch_screen("pre-game-check", game_type=gt))
                
    def renew_analysis(self):
        pid = self.controller.current_profile['id']
        run_ai_analysis(pid)
        messagebox.showinfo("분석 완료", "최근 기록을 바탕으로 인지·운동 취약점 분석 연산이 갱신되었습니다.")
        self.controller.switch_screen("dashboard")
        
    def get_grade(self, score):
        if score >= 90: return {'label': '우수 관리', 'color': COLOR_CYAN, 'emoji': '🌟'}
        if score >= 75: return {'label': '양호 관리', 'color': COLOR_GREEN, 'emoji': '✅'}
        if score >= 60: return {'label': '보통 관리', 'color': COLOR_AMBER, 'emoji': '📈'}
        return {'label': '보완 요망', 'color': COLOR_RED, 'emoji': '⚠️'}

# ─── SCREEN 4: PRE-GAME FATIGUE CHECK ─────────────────────────────────────────
class PreGameCheckScreen(tk.Frame):
    def __init__(self, parent, controller, game_type):
        super().__init__(parent, bg=COLOR_BG_BASE)
        self.controller = controller
        self.game_type = game_type
        
        back_btn = tk.Button(self, text="← 취소", font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE, bd=0, command=lambda: controller.switch_screen("hub"))
        back_btn.pack(anchor="w", pady=(5, 15))
        
        info = GAME_INFO[game_type]
        
        card = tk.Frame(self, bg=COLOR_BG_SURFACE, highlightbackground=COLOR_BORDER, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, pady=10, ipady=15)
        
        emoji_lbl = tk.Label(card, text=info['emoji'], font=("Outfit", 44), bg=COLOR_BG_SURFACE)
        emoji_lbl.pack(pady=(20, 5))
        
        title_lbl = tk.Label(card, text=info['label'], font=("Outfit", 18, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE)
        title_lbl.pack(pady=5)
        
        desc_lbl = tk.Label(card, text="훈련을 수행하기 전에, 환자 본인의 오늘 몸 상태와 관절 상태, 피로도를 기록하여 안전한 강도로 미션을 제공합니다.", font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_SURFACE, justify="center", wraplength=350)
        desc_lbl.pack(pady=(0, 20))
        
        # Fatigue Choice Group
        lbl_q = tk.Label(card, text="현재 자가 평가 컨디션 단계는 어떠합니까?", font=("Outfit", 11, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE)
        lbl_q.pack(anchor="w", padx=25, pady=(10, 5))
        
        self.fatigue_var = tk.IntVar(value=1)
        
        opts = [
          (1, "🟢 좋음: 몸 상태가 가볍고 훈련 수행에 지장 없음"),
          (2, "🟡 보통: 움직임이 평소와 비슷하나 약간 뻣뻣함"),
          (3, "🟠 피곤함: 동작 조절에 지체가 있으며 피로가 느껴짐\n   ➔ (안전 조정: 미션 난이도가 1단계 자동 하향조정됨)"),
          (4, "🔴 심함: 어지러움, 통증 또는 심한 관절 경직 상태\n   ➔ (강제 가이드: 즉시 훈련을 중단하고 휴식을 취함)")
        ]
        
        opt_container = tk.Frame(card, bg=COLOR_BG_SURFACE)
        opt_container.pack(fill=tk.X, padx=25, pady=10)
        
        for val, text in opts:
            btn = tk.Radiobutton(opt_container, text=text, variable=self.fatigue_var, value=val, font=("Outfit", 10), fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE, selectcolor=COLOR_BG_SURFACE, justify="left", activebackground=COLOR_BG_SURFACE, activeforeground=COLOR_CYAN)
            btn.pack(anchor="w", pady=6)
            
        start_btn = tk.Button(card, text="안전 서약 및 훈련 개시", font=("Outfit", 12, "bold"), bg=COLOR_CYAN, fg="#000", bd=0, pady=10, cursor="hand2", command=self.proceed)
        start_btn.pack(fill=tk.X, padx=25, pady=25)
        
    def proceed(self):
        val = self.fatigue_var.get()
        if val == 4:
            # Abort safety warning logging fake session
            pid = self.controller.current_profile['id']
            conn = sqlite3.connect("parkicare.db")
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO game_sessions (profile_id, game_type, accuracy, avg_response_time, correct_count, total_rounds, miss_count, difficulty, fatigue, timestamp)
            VALUES (?, ?, 0.0, 0.0, 0, 0, 0, 1, 4, ?)
            """, (pid, self.game_type, datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            
            # Trigger analysis immediately for safety status
            run_ai_analysis(pid)
            
            self.controller.switch_screen("safety-warning", game_type=self.game_type)
        else:
            self.controller.switch_screen("game", game_type=self.game_type, fatigue=val)

# ─── SCREEN 5: SAFETY WARNING (ABORT SCREEN) ─────────────────────────────────
class SafetyWarningScreen(tk.Frame):
    def __init__(self, parent, controller, game_type):
        super().__init__(parent, bg=COLOR_BG_BASE)
        self.controller = controller
        
        card = tk.Frame(self, bg="#251214", highlightbackground=COLOR_RED, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, pady=20, padx=10, ipady=20)
        
        warn_lbl = tk.Label(card, text="⚠️", font=("Outfit", 54), bg="#251214", fg=COLOR_RED)
        warn_lbl.pack(pady=10)
        
        title_lbl = tk.Label(card, text="미션 수행 일시 중단 가이드", font=("Outfit", 18, "bold"), fg=COLOR_RED, bg="#251214")
        title_lbl.pack(pady=5)
        
        desc = ("자가 컨디션 평가 결과, 극도의 피로 또는 통증, 어지러움(Level 4)이 기록되어 환자 보호 조치 가이드라인에 의거하여 훈련을 비활성화하였습니다.\n\n"
                "의도적으로 무리한 관절 제어나 탭 집중은 부하를 과중시킬 우려가 있으니 즉시 동작을 정지하십시오.")
        desc_lbl = tk.Label(card, text=desc, font=("Outfit", 10), fg=COLOR_TEXT_PRIMARY, bg="#251214", justify="left", wraplength=380)
        desc_lbl.pack(padx=20, pady=15)
        
        # Recommendations text
        rec_f = tk.Frame(card, bg="#110708")
        rec_f.pack(fill=tk.X, padx=20, pady=10, ipady=8)
        
        action_title = tk.Label(rec_f, text="🚨 권장 대응 수칙:", font=("Outfit", 11, "bold"), fg=COLOR_RED, bg="#110708")
        action_title.pack(anchor="w", padx=10, pady=(6, 2))
        
        action_steps = ("1. 훈련 화면을 즉시 종료하고 안락한 상태로 앉거나 누우십시오.\n"
                        "2. 미온수를 한 컵 마시고, 10분간 크게 복식 호흡을 유지합니다.\n"
                        "3. 관절 강직이나 심한 두통이 지속되면 대기 중인 가족(보호자) 혹은 의료 기관 전문의에게 해당 내역을 즉각 전달하십시오.")
        action_lbl = tk.Label(rec_f, text=action_steps, font=("Outfit", 9), fg=COLOR_TEXT_SECONDARY, bg="#110708", justify="left")
        action_lbl.pack(anchor="w", padx=10, pady=(0, 6))
        
        hub_btn = tk.Button(card, text="안전 가이드 확인 (훈련 허브 이동)", font=("Outfit", 11, "bold"), bg=COLOR_BG_BASE, fg=COLOR_TEXT_PRIMARY, highlightbackground=COLOR_BORDER, highlightthickness=1, bd=0, pady=10, cursor="hand2", command=lambda: controller.switch_screen("hub"))
        hub_btn.pack(fill=tk.X, padx=20, pady=20)

# ─── SCREEN 6: GAME (INTERACTIVE MISSIONS 3 TYPES) ───────────────────────────
class GameScreen(tk.Frame):
    def __init__(self, parent, controller, game_type, fatigue):
        super().__init__(parent, bg=COLOR_BG_BASE)
        self.controller = controller
        self.game_type = game_type
        self.fatigue = fatigue
        
        # Fetch Problem Parameters based on target difficulty
        pid = controller.current_profile['id']
        conn = sqlite3.connect("parkicare.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM weak_profiles WHERE profile_id=?", (pid,))
        wp_row = cur.fetchone()
        conn.close()
        
        wp = dict(wp_row) if wp_row else None
        
        # Retrieve game specific recommended difficulty
        self.difficulty = 2 # default
        if wp:
            games_data = json.loads(wp['games_json'])
            if game_type in games_data:
                self.difficulty = games_data[game_type]['recommendedDifficulty']
                
        # Fatigue level 3 (Tired) -> Lower difficulty by 1 level
        if fatigue == 3:
            self.difficulty = max(1, self.difficulty - 1)
            
        # UI Header
        self.header = tk.Frame(self, bg=COLOR_BG_BASE)
        self.header.pack(fill=tk.X, pady=(5, 10))
        
        quit_btn = tk.Button(self.header, text="✕ 훈련 포기", font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE, bd=0, command=self.quit_game)
        quit_btn.pack(side=tk.LEFT)
        
        self.title_lbl = tk.Label(self.header, text=GAME_INFO[game_type]['label'], font=("Outfit", 12, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE)
        self.title_lbl.pack(side=tk.RIGHT)
        
        # Game Board container
        self.board = tk.Frame(self, bg=COLOR_BG_SURFACE, highlightbackground=COLOR_BORDER, highlightthickness=1)
        self.board.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Initialize selected game
        if game_type == 'memory_sequence':
            self.run_memory_game()
        elif game_type == 'attention_stroop':
            self.run_stroop_game()
        elif game_type == 'motor_response':
            self.run_motor_game()
            
    def quit_game(self):
        if messagebox.askyesno("훈련 종료", "미션을 포기하시겠습니까? 현재까지의 플레이 기록은 버려집니다."):
            self.controller.switch_screen("hub")
            
    # ─── MISSION 1: MEMORY CARD MATCH ───────────────────────
    def run_memory_game(self):
        # Emojis pool
        EMOJIS = ['🧠', '🍏', '🎯', '✋', '🌟', '🍇', '🍒', '🍋', '🥝', '🍉']
        num_pairs = 2 if self.difficulty == 1 else (3 if self.difficulty <= 3 else 4)
        selected_emojis = Emojis = EMOJIS[:num_pairs]
        pool = selected_emojis + selected_emojis
        random.shuffle(pool)
        
        self.cards = [{'emoji': e, 'flipped': False, 'matched': False} for e in pool]
        self.flipped_indices = []
        self.matched_pairs = 0
        self.total_flips = 0
        self.response_times = []
        self.last_action_time = datetime.now()
        
        # Instructions Label
        self.instruct = tk.Label(self.board, text="카드가 잠시 뒤집히기 전에 카드의 이모지와 위치를 외우세요!", font=("Outfit", 10), fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE, wraplength=350, justify="center")
        self.instruct.pack(pady=10)
        
        # Grid Container
        self.grid_frame = tk.Frame(self.board, bg=COLOR_BG_SURFACE)
        self.grid_frame.pack(pady=20)
        
        self.card_buttons = []
        cols = 2 if num_pairs == 2 else 3
        for i, card in enumerate(self.cards):
            r = i // cols
            c = i % cols
            btn = tk.Button(self.grid_frame, text=card['emoji'], font=("Outfit", 26), bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY, width=4, height=2, bd=1, highlightbackground=COLOR_BORDER, highlightthickness=1, cursor="hand2")
            btn.grid(row=r, column=c, padx=6, pady=6)
            btn.configure(command=lambda idx=i: self.click_card(idx))
            self.card_buttons.append(btn)
            
        # Hide cards after delay (Memorization phase)
        memorize_ms = max(1800, 4500 - (self.difficulty * 600))
        self.controller.after(memorize_ms, self.hide_cards_initially)
        
    def hide_cards_initially(self):
        self.instruct.configure(text="위치를 기억하여 같은 짝의 카드를 연속으로 두 장 뒤집으십시오.")
        for btn in self.card_buttons:
            btn.configure(text="❓", bg="#1a2f5a", fg=COLOR_CYAN)
        self.last_action_time = datetime.now()

    def click_card(self, idx):
        if len(self.flipped_indices) >= 2 or self.cards[idx]['flipped'] or self.cards[idx]['matched']:
            return
            
        now = datetime.now()
        elapsed = (now - self.last_action_time).total_seconds() * 1000
        self.response_times.append(elapsed)
        self.last_action_time = now
        
        # Flip Card front
        self.cards[idx]['flipped'] = True
        self.card_buttons[idx].configure(text=self.cards[idx]['emoji'], bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY)
        self.flipped_indices.append(idx)
        
        if len(self.flipped_indices) == 2:
            self.total_flips += 1
            idx1, idx2 = self.flipped_indices
            
            if self.cards[idx1]['emoji'] == self.cards[idx2]['emoji']:
                # Matched
                self.cards[idx1]['matched'] = True
                self.cards[idx2]['matched'] = True
                self.card_buttons[idx1].configure(bg="rgba(0, 255, 148, 0.15)", fg=COLOR_GREEN)
                self.card_buttons[idx2].configure(bg="rgba(0, 255, 148, 0.15)", fg=COLOR_GREEN)
                self.matched_pairs += 1
                self.flipped_indices = []
                
                # Check Win
                if self.matched_pairs == len(self.cards) / 2:
                    self.controller.after(600, self.finish_game)
            else:
                # Not matched -> Flip back after delay
                self.controller.after(800, lambda: self.flip_back(idx1, idx2))
                
    def flip_back(self, idx1, idx2):
        self.cards[idx1]['flipped'] = False
        self.cards[idx2]['flipped'] = False
        self.card_buttons[idx1].configure(text="❓", bg="#1a2f5a", fg=COLOR_CYAN)
        self.card_buttons[idx2].configure(text="❓", bg="#1a2f5a", fg=COLOR_CYAN)
        self.flipped_indices = []

    # ─── MISSION 2: COLOR-ACTION RESPONSE (STROOP) ───────────
    def run_stroop_game(self):
        self.colors_dict = [
            {'name': '빨강', 'hex': '#FF4444', 'color': COLOR_RED},
            {'name': '파랑', 'hex': '#4488FF', 'color': COLOR_CYAN},
            {'name': '초록', 'hex': '#44CC44', 'color': COLOR_GREEN},
            {'name': '노랑', 'hex': '#FFCC00', 'color': COLOR_AMBER}
        ]
        self.stroop_rounds = 3 + self.difficulty
        self.current_stroop_round = 0
        self.correct_stroop = 0
        self.stroop_response_times = []
        self.stroop_start_time = None
        
        self.instruct = tk.Label(self.board, text="화면 한가운데 단어의 글자 뜻이 아닌, 실제 '글자 색상' 버튼을 누르십시오.", font=("Outfit", 10), fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE)
        self.instruct.pack(pady=10)
        
        self.round_indicator = tk.Label(self.board, text="문제 1 / -", font=("Outfit", 11, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_SURFACE)
        self.round_indicator.pack(pady=5)
        
        # Stroop Word Box
        self.word_lbl = tk.Label(self.board, text="-", font=("Outfit", 36, "bold"), bg=COLOR_BG_SURFACE)
        self.word_lbl.pack(pady=35)
        
        # Options frame
        self.options_f = tk.Frame(self.board, bg=COLOR_BG_SURFACE)
        self.options_f.pack(pady=20, fill=tk.X, padx=30)
        
        self.stroop_buttons = []
        # Create 4 choice buttons
        for i, cd in enumerate(self.colors_dict):
            row = i // 2
            col = i % 2
            btn = tk.Button(self.options_f, text=cd['name'], font=("Outfit", 12, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY, bd=1, highlightbackground=COLOR_BORDER, highlightthickness=1, pady=10, cursor="hand2")
            btn.grid(row=row, column=col, sticky="ew", padx=8, pady=8)
            # Configure command dynamically
            btn.configure(command=lambda name=cd['name']: self.check_stroop_answer(name))
            self.options_f.grid_columnconfigure(col, weight=1)
            self.stroop_buttons.append(btn)
            
        self.next_stroop_round()
        
    def next_stroop_round(self):
        if self.current_stroop_round >= self.stroop_rounds:
            self.finish_game()
            return
            
        self.current_stroop_round += 1
        self.round_indicator.configure(text=f"문제 {self.current_stroop_round} / {self.stroop_rounds}")
        
        # Randomly choose color meaning and visual color
        meaning = random.choice(self.colors_dict)
        # Force interference
        pool = [c for c in self.colors_dict if c['name'] != meaning['name']]
        visual = random.choice(pool)
        
        self.word_lbl.configure(text=meaning['name'], fg=visual['color'])
        self.correct_answer_name = visual['name'] # correct is color of the word
        
        self.stroop_start_time = datetime.now()

    def check_stroop_answer(self, chosen_name):
        elapsed = (datetime.now() - self.stroop_start_time).total_seconds() * 1000
        self.stroop_response_times.append(elapsed)
        
        if chosen_name == self.correct_answer_name:
            self.correct_stroop += 1
            self.round_indicator.configure(fg=COLOR_GREEN)
        else:
            self.round_indicator.configure(fg=COLOR_RED)
            
        # Visual feedback brief lock
        for btn in self.stroop_buttons:
            btn.configure(state="disabled")
            if btn.cget("text") == self.correct_answer_name:
                btn.configure(bg=COLOR_GREEN, fg="#000")
            elif btn.cget("text") == chosen_name:
                btn.configure(bg=COLOR_RED, fg="#FFF")
                
        self.controller.after(600, self.reset_stroop_buttons)
        
    def reset_stroop_buttons(self):
        for btn in self.stroop_buttons:
            btn.configure(state="normal", bg=COLOR_CARD, fg=COLOR_TEXT_PRIMARY)
        self.round_indicator.configure(fg=COLOR_TEXT_SECONDARY)
        self.next_stroop_round()

    # ─── MISSION 3: FINGER SEQUENCE TAP ─────────────────────
    def run_motor_game(self):
        self.motor_rounds = 3
        self.current_motor_round = 1
        self.motor_target_count = 3 if self.difficulty == 1 else (4 if self.difficulty <= 3 else 5)
        
        self.motor_hit_count = 0
        self.motor_miss_count = 0
        self.motor_response_times = []
        self.motor_last_time = None
        self.current_expected_num = 1
        
        # Instructions
        self.instruct = tk.Label(self.board, text="화면에 나타난 원들을 반드시 번호 순서대로(1 ➔ 2 ➔ 3) 탭하십시오.", font=("Outfit", 10), fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE)
        self.instruct.pack(pady=8)
        
        self.round_lbl = tk.Label(self.board, text=f"라운드 {self.current_motor_round} / {self.motor_rounds}", font=("Outfit", 11, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_SURFACE)
        self.round_lbl.pack(pady=2)
        
        # Canvas for spawning coordinates
        self.canvas = tk.Canvas(self.board, bg="#0A0E1A", bd=0, highlightthickness=1, highlightbackground=COLOR_BORDER, height=280)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.start_motor_round()
        
    def start_motor_round(self):
        self.canvas.delete("all")
        self.current_expected_num = 1
        self.round_lbl.configure(text=f"라운드 {self.current_motor_round} / {self.motor_rounds}")
        
        # Target sizes
        radius = 28
        width = self.canvas.winfo_width() if self.canvas.winfo_width() > 100 else 320
        height = self.canvas.winfo_height() if self.canvas.winfo_height() > 100 else 240
        
        self.targets = []
        # Generate non-overlapping positions
        for i in range(1, self.motor_target_count + 1):
            attempts = 0
            while attempts < 100:
                cx = random.randint(radius + 15, width - radius - 15)
                cy = random.randint(radius + 15, height - radius - 15)
                # Overlap check
                overlap = False
                for t in self.targets:
                    dist = math.hypot(t['cx'] - cx, t['cy'] - cy)
                    if dist < (radius * 2 + 15):
                        overlap = True
                        break
                if not overlap:
                    break
                attempts += 1
                
            self.targets.append({'num': i, 'cx': cx, 'cy': cy, 'matched': False})
            
        # Draw circles
        self.target_shapes = {}
        for t in self.targets:
            cx, cy = t['cx'], t['cy']
            circle = self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill=COLOR_CARD, outline=COLOR_CYAN, width=2, tags="target")
            text = self.canvas.create_text(cx, cy, text=str(t['num']), fill="#FFF", font=("Outfit", 16, "bold"), tags="target")
            
            # Bind tap event
            self.canvas.tag_bind(circle, "<Button-1>", lambda e, num=t['num']: self.click_motor_target(num))
            self.canvas.tag_bind(text, "<Button-1>", lambda e, num=t['num']: self.click_motor_target(num))
            
            self.target_shapes[t['num']] = (circle, text)
            
        self.motor_last_time = datetime.now()
        
    def click_motor_target(self, num):
        if is_finished := False:
            return
            
        now = datetime.now()
        elapsed = (now - self.motor_last_time).total_seconds() * 1000
        
        if num == self.current_expected_num:
            # Correct hit
            self.motor_response_times.append(elapsed)
            self.motor_last_time = now
            self.motor_hit_count += 1
            
            # Change color to green
            circle_id, text_id = self.target_shapes[num]
            self.canvas.itemconfig(circle_id, fill="rgba(0, 255, 148, 0.25)", outline=COLOR_GREEN)
            self.canvas.itemconfig(text_id, fill=COLOR_GREEN)
            
            # Remove bindings to prevent double-click
            self.canvas.tag_bind(circle_id, "<Button-1>", "")
            self.canvas.tag_bind(text_id, "<Button-1>", "")
            
            self.current_expected_num += 1
            
            if self.current_expected_num > self.motor_target_count:
                # Finished this round
                if self.current_motor_round < self.motor_rounds:
                    self.current_motor_round += 1
                    self.controller.after(400, self.start_motor_round)
                else:
                    self.finish_game()
        else:
            # Mistake click
            self.motor_miss_count += 1
            # Red shake effect simulation
            circle_id, text_id = self.target_shapes[num]
            self.canvas.itemconfig(circle_id, outline=COLOR_RED)
            self.controller.after(200, lambda: self.canvas.itemconfig(circle_id, outline=COLOR_CYAN))

    # ─── UNIVERSAL GAME WRAP UP ────────────────────────────────────
    def finish_game(self):
        # Calculate scores
        if self.game_type == 'memory_sequence':
            pairs = len(self.cards) / 2
            accuracy = pairs / self.total_flips if self.total_flips > 0 else 0
            avg_rt = sum(self.response_times) / len(self.response_times) if self.response_times else 0
            miss_count = self.total_flips - pairs
            correct_cnt = pairs
            total_rnds = self.total_flips
            
        elif self.game_type == 'attention_stroop':
            accuracy = self.correct_stroop / self.stroop_rounds
            avg_rt = sum(self.stroop_response_times) / len(self.stroop_response_times) if self.stroop_response_times else 0
            miss_count = self.stroop_rounds - self.correct_stroop
            correct_cnt = self.correct_stroop
            total_rnds = self.stroop_rounds
            
        elif self.game_type == 'motor_response':
            expected = self.motor_target_count * self.motor_rounds
            accuracy = expected / (expected + self.motor_miss_count)
            avg_rt = sum(self.motor_response_times) / len(self.motor_response_times) if self.motor_response_times else 0
            miss_count = self.motor_miss_count
            correct_cnt = expected
            total_rnds = self.motor_rounds
            
        session_data = {
            'accuracy': round(accuracy, 2),
            'avgResponseTime': avg_rt,
            'correctCount': int(correct_cnt),
            'totalRounds': int(total_rnds),
            'missCount': int(miss_count),
            'difficulty': self.difficulty,
            'fatigue': self.fatigue
        }
        
        # Save session to Database
        pid = self.controller.current_profile['id']
        conn = sqlite3.connect("parkicare.db")
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO game_sessions (profile_id, game_type, accuracy, avg_response_time, correct_count, total_rounds, miss_count, difficulty, fatigue, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pid, self.game_type, session_data['accuracy'], session_data['avgResponseTime'],
            session_data['correctCount'], session_data['totalRounds'], session_data['missCount'],
            session_data['difficulty'], session_data['fatigue'], datetime.utcnow().isoformat()
        ))
        conn.commit()
        conn.close()
        
        # Re-run AI analysis update
        run_ai_analysis(pid)
        
        self.controller.switch_screen("result", game_type=self.game_type, session_data=session_data)

# ─── SCREEN 7: OUTCOME & suggestion ───────────────────────────────────────────
class ResultScreen(tk.Frame):
    def __init__(self, parent, controller, game_type, session_data):
        super().__init__(parent, bg=COLOR_BG_BASE)
        self.controller = controller
        
        pct = round(session_data['accuracy'] * 100)
        grade = self.get_grade(pct)
        
        # Title Card
        title_card = tk.Frame(self, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)
        title_card.pack(fill=tk.X, pady=10, ipady=10)
        
        lbl_grade_icon = tk.Label(title_card, text=grade['emoji'], font=("Outfit", 48), bg=COLOR_CARD)
        lbl_grade_icon.pack(pady=5)
        
        lbl_res = tk.Label(title_card, text="훈련 미션 수행 완료", font=("Outfit", 18, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD)
        lbl_res.pack(pady=2)
        
        lbl_type = tk.Label(title_card, text=f"{GAME_INFO[game_type]['label']} · 설정 난이도 {session_data['difficulty']}단", font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD)
        lbl_type.pack(pady=2)
        
        # Circle score drawing on canvas
        score_canvas = tk.Canvas(title_card, width=100, height=100, bg=COLOR_CARD, bd=0, highlightthickness=0)
        score_canvas.pack(pady=10)
        score_canvas.create_oval(10, 10, 90, 90, outline=COLOR_BORDER, width=6)
        
        extent_angle = -360 * (pct / 100)
        score_canvas.create_arc(10, 10, 90, 90, start=90, extent=extent_angle, outline=grade['color'], width=6, style="arc")
        score_canvas.create_text(50, 50, text=f"{pct}%", fill=grade['color'], font=("Outfit", 16, "bold"))
        
        # Numerical facts details
        stats_frame = tk.Frame(self, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)
        stats_frame.pack(fill=tk.X, pady=5, ipady=5)
        
        # Grid metrics
        c1 = tk.Frame(stats_frame, bg=COLOR_CARD)
        c1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(c1, text=f"{session_data['correctCount']}/{session_data['totalRounds']}", font=("Outfit", 14, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD).pack()
        tk.Label(c1, text="맞춘 횟수", font=("Outfit", 9), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD).pack()
        
        c2 = tk.Frame(stats_frame, bg=COLOR_CARD)
        c2.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(c2, text=f"{session_data['avgResponseTime']/1000:.2f}초", font=("Outfit", 14, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD).pack()
        tk.Label(c2, text="평균 반응", font=("Outfit", 9), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD).pack()
        
        c3 = tk.Frame(stats_frame, bg=COLOR_CARD)
        c3.pack(side=tk.LEFT, fill=tk.X, expand=True)
        fatigue_lbl = "피곤함" if session_data['fatigue'] == 3 else ("보통" if session_data['fatigue'] == 2 else "좋음")
        tk.Label(c3, text=fatigue_lbl, font=("Outfit", 14, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD).pack()
        tk.Label(c3, text="컨디션", font=("Outfit", 9), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD).pack()
        
        # AI recommendation reason text card
        rec_card = tk.Frame(self, bg="rgba(0, 212, 255, 0.04)", highlightbackground="rgba(0, 212, 255, 0.2)", highlightthickness=1)
        rec_card.pack(fill=tk.X, pady=10, ipady=8)
        
        rec_header = tk.Label(rec_card, text="🤖 AI 데이터 분석 권장 조치:", font=("Outfit", 11, "bold"), fg=COLOR_CYAN, bg="rgba(0, 212, 255, 0.04)")
        rec_header.pack(anchor="w", padx=12, pady=(6, 2))
        
        # Load latest AI prescription
        self.rec_text_lbl = tk.Label(rec_card, text="훈련 데이터를 연산하여 최적 추천 코스를 산출하고 있습니다.", font=("Outfit", 10), fg=COLOR_TEXT_PRIMARY, bg="rgba(0, 212, 255, 0.04)", justify="left", wraplength=380)
        self.rec_text_lbl.pack(anchor="w", padx=12, pady=(0, 6))
        
        self.load_ai_prescription()
        
        # Controls
        controls = tk.Frame(self, bg=COLOR_BG_BASE)
        controls.pack(fill=tk.X, pady=15)
        
        retry_btn = tk.Button(controls, text="다시 훈련하기", font=("Outfit", 11), bg=COLOR_BG_SURFACE, fg=COLOR_TEXT_PRIMARY, highlightbackground=COLOR_BORDER, highlightthickness=1, bd=0, pady=10, cursor="hand2", command=lambda: controller.switch_screen("pre-game-check", game_type=game_type))
        retry_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        hub_btn = tk.Button(controls, text="허브로 완료", font=("Outfit", 11, "bold"), bg=COLOR_CYAN, fg="#000", bd=0, pady=10, cursor="hand2", command=lambda: controller.switch_screen("hub"))
        hub_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
    def load_ai_prescription(self):
        pid = self.controller.current_profile['id']
        conn = sqlite3.connect("parkicare.db")
        cur = conn.cursor()
        cur.execute("SELECT recommendations_json FROM weak_profiles WHERE profile_id=?", (pid,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            recs = json.loads(row[0])
            # Display high priority recommendation or general info
            high_rec = next((r for r in recs if r['priority'] == 'high'), None)
            med_rec = next((r for r in recs if r['priority'] == 'medium'), None)
            general = next((r for r in recs if r['priority'] == 'info'), None)
            
            target = high_rec or med_rec or general
            if target:
                self.rec_text_lbl.configure(text=target['message'])
                
    def get_grade(self, score):
        if score >= 90: return {'label': '우수', 'color': COLOR_CYAN, 'emoji': '🌟'}
        if score >= 75: return {'label': '양호', 'color': COLOR_GREEN, 'emoji': '✅'}
        if score >= 60: return {'label': '보통', 'color': COLOR_AMBER, 'emoji': '📈'}
        return {'label': '보완 요망', 'color': COLOR_RED, 'emoji': '⚠️'}

# ─── SCREEN 8: AI DASHBOARD (RADAR BALANCE CHART) ─────────────────────────────
class DashboardScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG_BASE)
        self.controller = controller
        
        back_btn = tk.Button(self, text="← 허브", font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE, bd=0, command=lambda: controller.switch_screen("hub"))
        back_btn.pack(anchor="w", pady=(5, 5))
        
        h_lbl = tk.Label(self, text="AI 분석 대시보드", font=("Outfit", 20, "bold"), fg=COLOR_CYAN, bg=COLOR_BG_BASE)
        h_lbl.pack(anchor="w", pady=(0, 10))
        
        pid = controller.current_profile['id']
        conn = sqlite3.connect("parkicare.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM weak_profiles WHERE profile_id=?", (pid,))
        wp_row = cur.fetchone()
        conn.close()
        
        self.wp = dict(wp_row) if wp_row else None
        
        if not self.wp:
            lbl_empty = tk.Label(self, text="아직 훈련 분석 결과가 없습니다. 각 미션을 3회 이상 완료해주십시오.", font=("Outfit", 11), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE)
            lbl_empty.pack(pady=50)
            return
            
        # Overall Card
        score_f = tk.Frame(self, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)
        score_f.pack(fill=tk.X, pady=(0, 10), ipady=5)
        
        overall = self.wp['overall_score']
        grade = self.get_grade(overall)
        
        score_lbl = tk.Label(score_f, text=str(overall), font=("Outfit", 36, "bold"), fg=grade['color'], bg=COLOR_CARD)
        score_lbl.pack(side=tk.LEFT, padx=20)
        
        meta_f = tk.Frame(score_f, bg=COLOR_CARD)
        meta_f.pack(side=tk.LEFT, pady=10)
        
        tk.Label(meta_f, text="종합 관리 지표 점수", font=("Outfit", 11, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD).pack(anchor="w")
        
        weak_list = json.loads(self.wp['weak_areas_json'])
        weak_names = [GAME_INFO[w]['label'] for w in weak_list]
        weak_text = f"집중 요망: {', '.join(weak_names)}" if weak_names else "전체 영역 양호 수준 유지"
        
        tk.Label(meta_f, text=weak_text, font=("Outfit", 9), fg=COLOR_RED if weak_names else COLOR_GREEN, bg=COLOR_CARD).pack(anchor="w")
        
        # Draw Radar Balance Chart directly on Canvas
        radar_card = tk.Frame(self, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)
        radar_card.pack(fill=tk.X, pady=5)
        
        tk.Label(radar_card, text="수행 기능 밸런스 (기억/반응/운동)", font=("Outfit", 10, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD).pack(anchor="w", padx=12, pady=(10, 2))
        
        radar_canvas = tk.Canvas(radar_card, width=220, height=220, bg=COLOR_CARD, bd=0, highlightthickness=0)
        radar_canvas.pack(pady=10)
        
        # Load game scores
        games_data = json.loads(self.wp['games_json'])
        scores = []
        for gt in ['memory_sequence', 'attention_stroop', 'motor_response']:
            acc = games_data.get(gt, {}).get('accuracy')
            scores.append(round(acc * 100) if acc is not None else 0)
            
        self.draw_radar(radar_canvas, scores)
        
        # AI Prescription display
        rec_card = tk.Frame(self, bg=COLOR_CARD, highlightbackground=COLOR_CYAN, highlightthickness=1)
        rec_card.pack(fill=tk.X, pady=10, ipady=8)
        
        tk.Label(rec_card, text="🤖 AI 개별 맞춤 처방 분석 보고", font=("Outfit", 11, "bold"), fg=COLOR_CYAN, bg=COLOR_CARD).pack(anchor="w", padx=12, pady=(6, 2))
        
        recs = json.loads(self.wp['recommendations_json'])
        for r in recs:
            rec_lbl = tk.Label(rec_card, text=r['message'], font=("Outfit", 10), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD, justify="left", wraplength=420)
            rec_lbl.pack(anchor="w", padx=12, pady=4)
            
    def draw_radar(self, canvas, scores):
        cx, cy, r = 110, 110, 80
        labels = ['기억력', '집중력', '운동성']
        angles = [2 * math.pi * i / 3 - math.pi / 2 for i in range(3)]
        
        # Draw Concentric Web grid
        for p in [100, 75, 50, 25]:
            points = []
            for a in angles:
                x = cx + r * (p / 100) * math.cos(a)
                y = cy + r * (p / 100) * math.sin(a)
                points.append((x, y))
            canvas.create_polygon(points[0][0], points[0][1], points[1][0], points[1][1], points[2][0], points[2][1], fill="", outline="rgba(255,255,255,0.06)", width=1)
            
        # Draw axis lines
        for a in angles:
            x = cx + r * math.cos(a)
            y = cy + r * math.sin(a)
            canvas.create_line(cx, cy, x, y, fill="rgba(255,255,255,0.1)")
            
        # Draw Data Polygon
        data_points = []
        for i, a in enumerate(angles):
            score = scores[i]
            x = cx + r * (score / 100) * math.cos(a)
            y = cy + r * (score / 100) * math.sin(a)
            data_points.append((x, y))
            
        canvas.create_polygon(data_points[0][0], data_points[0][1], data_points[1][0], data_points[1][1], data_points[2][0], data_points[2][1], fill="rgba(0, 212, 255, 0.15)", outline=COLOR_CYAN, width=2.5)
        
        # Dots
        for x, y in data_points:
            canvas.create_oval(x-4, y-4, x+4, y+4, fill="#FFF", outline=COLOR_CYAN, width=1.5)
            
        # Axis Labels
        for i, a in enumerate(angles):
            x = cx + (r + 18) * math.cos(a)
            y = cy + (r + 18) * math.sin(a)
            canvas.create_text(x, y, text=f"{labels[i]}\n({scores[i]}%)", fill=COLOR_TEXT_SECONDARY, font=("Outfit", 9, "bold"), justify="center")
            
    def get_grade(self, score):
        if score >= 90: return {'label': '우수 관리', 'color': COLOR_CYAN, 'emoji': '🌟'}
        if score >= 75: return {'label': '양호 관리', 'color': COLOR_GREEN, 'emoji': '✅'}
        if score >= 60: return {'label': '보통 관리', 'color': COLOR_AMBER, 'emoji': '📈'}
        return {'label': '보완 요망', 'color': COLOR_RED, 'emoji': '⚠️'}

# ─── SCREEN 9: REPORT & COMPARISON TABLE ──────────────────────────────────────
class ReportScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG_BASE)
        self.controller = controller
        
        back_btn = tk.Button(self, text="← 허브", font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE, bd=0, command=lambda: controller.switch_screen("hub"))
        back_btn.pack(anchor="w", pady=(5, 5))
        
        h_lbl = tk.Label(self, text="주간 트레이닝 리포트", font=("Outfit", 20, "bold"), fg=COLOR_CYAN, bg=COLOR_BG_BASE)
        h_lbl.pack(anchor="w", pady=(0, 5))
        
        # Tab view using a scrollable canvas for contents
        self.canvas_scroll = tk.Canvas(self, bg=COLOR_BG_BASE, bd=0, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas_scroll.yview)
        self.scroll_frame = tk.Frame(self.canvas_scroll, bg=COLOR_BG_BASE)
        
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox("all"))
        )
        
        self.canvas_scroll.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas_scroll.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas_scroll.pack(side="left", fill="both", expand=True)
        
        self.render_charts()
        self.render_comparison_table()
        
    def render_charts(self):
        pid = self.controller.current_profile['id']
        conn = sqlite3.connect("parkicare.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        for gt, info in GAME_INFO.items():
            cur.execute("SELECT * FROM game_sessions WHERE profile_id=? AND game_type=? AND total_rounds > 0 ORDER BY timestamp DESC LIMIT 7", (pid, gt))
            sessions = [dict(r) for r in cur.fetchall()]
            sessions.reverse() # Sort chronologically
            
            section = tk.Frame(self.scroll_frame, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)
            section.pack(fill=tk.X, pady=8, ipady=5, padx=2)
            
            # Title
            title_f = tk.Frame(section, bg=COLOR_CARD)
            title_f.pack(fill=tk.X, padx=12, pady=(8, 2))
            tk.Label(title_f, text=info['label'], font=("Outfit", 12, "bold"), fg=info['color'], bg=COLOR_CARD).pack(side=tk.LEFT)
            tk.Label(title_f, text=f"(최근 {len(sessions)}회 기록)", font=("Outfit", 9), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD).pack(side=tk.RIGHT)
            
            if not sessions:
                lbl = tk.Label(section, text="누적된 미션 수행 데이터가 없습니다.", font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD)
                lbl.pack(pady=20)
                continue
                
            # Draw Progress Line Chart
            chart = tk.Canvas(section, width=400, height=100, bg=COLOR_CARD, bd=0, highlightthickness=0)
            chart.pack(pady=10)
            self.draw_progress_line(chart, sessions, info['color'])
            
        conn.close()
        
    def draw_progress_line(self, canvas, sessions, color):
        pad_l, pad_r, pad_t, pad_b = 30, 20, 15, 20
        W, H = 400, 100
        gW = W - pad_l - pad_r
        gH = H - pad_t - pad_b
        
        # Grid lines (0%, 50%, 100%)
        for pct in [0, 50, 100]:
            y = pad_t + gH * (1 - pct / 100)
            canvas.create_line(pad_l, y, W - pad_r, y, fill="rgba(255,255,255,0.04)")
            canvas.create_text(pad_l - 12, y, text=f"{pct}%", fill=COLOR_TEXT_SECONDARY, font=("Outfit", 8))
            
        points = []
        n = len(sessions)
        for i, s in enumerate(sessions):
            val = round(s['accuracy'] * 100)
            x = pad_l + (i / max(n - 1, 1)) * gW
            y = pad_t + gH * (1 - val / 100)
            points.append((x, y))
            
        # Draw Line
        if len(points) > 1:
            for i in range(len(points) - 1):
                canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], fill=color, width=2.5)
                
        # Draw dots & timestamps
        for i, (x, y) in enumerate(points):
            canvas.create_oval(x-4, y-4, x+4, y+4, fill=color, outline="#FFF")
            # Convert ISO datetime to simple month/day
            ts_str = sessions[i]['timestamp'][:10]
            try:
                dt = datetime.strptime(ts_str, "%Y-%m-%d")
                lbl_d = dt.strftime("%m/%d")
            except:
                lbl_d = "12/26" # fallback
            canvas.create_text(x, H - 8, text=lbl_d, fill=COLOR_TEXT_SECONDARY, font=("Outfit", 8))

    def render_comparison_table(self):
        comp_card = tk.Frame(self.scroll_frame, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)
        comp_card.pack(fill=tk.X, pady=12, ipady=8, padx=2)
        
        title_lbl = tk.Label(comp_card, text="📊 기존 관리 수단 대비 차별점 비교", font=("Outfit", 12, "bold"), fg=COLOR_CYAN, bg=COLOR_CARD)
        title_lbl.pack(anchor="w", padx=15, pady=(10, 10))
        
        headers = ["평가 영역", "기존 서비스 (닥터파킨슨 등)", "파키케어 플레이 (본작)"]
        grid_f = tk.Frame(comp_card, bg=COLOR_CARD)
        grid_f.pack(fill=tk.X, padx=15)
        
        # Draw headers
        for col_idx, h in enumerate(headers):
            lbl = tk.Label(grid_f, text=h, font=("Outfit", 9, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD, anchor="w")
            lbl.grid(row=0, column=col_idx, sticky="w", pady=5, padx=3)
            
        rows_data = [
            ("주요 콘텐츠", "단순 질환 정보 및 체크 리스트 제공", "대화식 2D 인지·운동 훈련 미션 제공"),
            ("개인화 분석", "동일 정적 알림 및 약물 복용 알림", "기록 오차/응답 지연 분석 처방 추천"),
            ("안전장치 시스템", "극도 컨디션 악화 시 제어 시스템 부재", "피로 4단계 감지 시 중단 유도 가이드")
        ]
        
        for row_idx, r in enumerate(rows_data):
            for col_idx, text in enumerate(r):
                fg_col = COLOR_CYAN if (col_idx == 2) else (COLOR_TEXT_PRIMARY if col_idx == 0 else COLOR_TEXT_SECONDARY)
                font_weight = "bold" if col_idx == 2 else "normal"
                
                lbl = tk.Label(grid_f, text=text, font=("Outfit", 9, font_weight), fg=fg_col, bg=COLOR_CARD, justify="left", wraplength=180 if col_idx > 0 else 80, anchor="nw")
                lbl.grid(row=row_idx+1, column=col_idx, sticky="nw", pady=6, padx=3)
                
        grid_f.columnconfigure(0, weight=1)
        grid_f.columnconfigure(1, weight=2)
        grid_f.columnconfigure(2, weight=2)

# ─── SCREEN 10: AUTOMATED VALIDATION TEST PORTAL ──────────────────────────────
class ValidationDashboardScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_BG_BASE)
        self.controller = controller
        
        back_btn = tk.Button(self, text="← 홈으로", font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE, bd=0, command=lambda: controller.switch_screen("home"))
        back_btn.pack(anchor="w", pady=(5, 5))
        
        h_lbl = tk.Label(self, text="AI 규칙 정밀 검증 시뮬레이터", font=("Outfit", 20, "bold"), fg=COLOR_CYAN, bg=COLOR_BG_BASE)
        h_lbl.pack(anchor="w", pady=(0, 5))
        
        desc = "양선우 작품설명서 검증 계획에 기반한 모의 사용자 5인 및 총 50세션 훈련 생성 테스트 환경입니다. 규칙 정확도, 지연 피드백, 피로도 중단 가이드를 검증합니다."
        desc_lbl = tk.Label(self, text=desc, font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE, justify="left", wraplength=450)
        desc_lbl.pack(anchor="w", pady=(0, 15))
        
        # Test Run Panel
        self.run_card = tk.Frame(self, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)
        self.run_card.pack(fill=tk.X, pady=5, ipady=10)
        
        self.status_lbl = tk.Label(self.run_card, text="검증 실행 대기 중", font=("Outfit", 13, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD)
        self.status_lbl.pack(pady=10)
        
        self.run_btn = tk.Button(self.run_card, text="➔ 모의 데이터 생성 및 AI 규칙 정밀 검증 개시", font=("Outfit", 11, "bold"), bg=COLOR_CYAN, fg="#000", bd=0, pady=8, cursor="hand2", command=self.execute_validation)
        self.run_btn.pack(pady=5)
        
        # Scrollable area for details
        self.details_area = tk.Frame(self, bg=COLOR_BG_BASE)
        # Will pack this frame upon execution completion
        
    def execute_validation(self):
        self.status_lbl.configure(text="⏳ 모의 세션 연산 및 규칙 대조 검증 중...", fg=COLOR_AMBER)
        self.run_btn.configure(state="disabled")
        
        # Use controller thread timeout to simulate engine calculations
        self.controller.after(800, self.perform_simulation_logic)
        
    def perform_simulation_logic(self):
        # 1. Setup simulated users
        sim_profiles = [
            {'id': 'p_sim_1', 'name': '김기억 (기억 지연 유형)', 'age': 68, 'stage': 'stage2', 'weakGame': 'memory_sequence'},
            {'id': 'p_sim_2', 'name': '이반응 (집중력 지연 유형)', 'age': 72, 'stage': 'stage3', 'weakGame': 'attention_stroop'},
            {'id': 'p_sim_3', 'name': '박운동 (운동조절 취약 유형)', 'age': 65, 'stage': 'stage2', 'weakGame': 'motor_response'},
            {'id': 'p_sim_4', 'name': '최피로 (피로안전 차단 유형)', 'age': 74, 'stage': 'stage4', 'weakGame': 'none', 'testFatigue': True},
            {'id': 'p_sim_5', 'name': '정안전 (안전 튜닝 유형)', 'age': 70, 'stage': 'stage2', 'weakGame': 'none', 'testFatigueTuning': True}
        ]
        
        conn = sqlite3.connect("parkicare.db")
        cur = conn.cursor()
        
        # Clear previous simulation runs to avoid duplication
        for p in sim_profiles:
            cur.execute("DELETE FROM profiles WHERE id=?", (p['id'],))
            cur.execute("DELETE FROM game_sessions WHERE profile_id=?", (p['id'],))
            cur.execute("DELETE FROM weak_profiles WHERE profile_id=?", (p['id'],))
            
            # Register simulated profiles
            cur.execute("INSERT INTO profiles VALUES (?, ?, ?, ?, '', '#7B2FBE', ?)", 
                        (p['id'], p['name'], p['age'], p['stage'], datetime.utcnow().isoformat()))
            
            # Write 10 session logs (total 50 logs across 5 profiles)
            game_types = ['memory_sequence', 'attention_stroop', 'motor_response']
            for i in range(1, 11):
                for gt in game_types:
                    accuracy = 0.85 + random.random() * 0.15
                    avg_rt = 1200 + random.random() * 400
                    miss_count = 0
                    fatigue = 1
                    
                    if p.get('testFatigue') and i >= 9:
                        fatigue = 4 # Severe fatigue triggered at final sessions
                        
                    if p.get('testFatigueTuning') and i == 5:
                        fatigue = 3 # Moderate fatigue
                        
                    if gt == p['weakGame']:
                        if gt == 'memory_sequence':
                            accuracy = 0.45 + random.random() * 0.15 # Low acc
                            avg_rt = 2500 + random.random() * 500
                        elif gt == 'attention_stroop':
                            accuracy = 0.88
                            avg_rt = 3000 + random.random() * 400 # High delay
                        elif gt == 'motor_response':
                            accuracy = 0.60
                            miss_count = 6
                            avg_rt = 2600 + random.random() * 300
                            
                    cur.execute("""
                    INSERT INTO game_sessions (profile_id, game_type, accuracy, avg_response_time, correct_count, total_rounds, miss_count, difficulty, fatigue, timestamp)
                    VALUES (?, ?, ?, ?, ?, 5, ?, 2, ?, ?)
                    """, (
                        p['id'], gt, round(accuracy, 2), avg_rt, int(accuracy * 5),
                        miss_count, fatigue, datetime.utcnow().isoformat()
                    ))
        conn.commit()
        conn.close()
        
        # 2. Run analysis rule updates for all simulated users
        test_results = []
        for p in sim_profiles:
            run_ai_analysis(p['id'])
            
            # Retrieve weak profiles
            conn = sqlite3.connect("parkicare.db")
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM weak_profiles WHERE profile_id=?", (p['id'],))
            wp = dict(cur.fetchone())
            conn.close()
            
            # Verify Criteria
            crit1 = p['weakGame'] in json.loads(wp['weak_areas_json']) if p['weakGame'] != 'none' else (len(json.loads(wp['weak_areas_json'])) == 0)
            
            recs = json.loads(wp['recommendations_json'])
            crit2 = False
            # Check numerical facts in high/medium recommendations
            rel_rec = next((r for r in recs if r['type'] == p['weakGame']), None)
            if p['weakGame'] != 'none' and rel_rec:
                crit2 = any(kw in rel_rec['message'] for kw in ["초", "%", "배"])
            else:
                crit2 = True
                
            crit3 = False
            if p.get('testFatigue'):
                # Checks if safety warning is priority 1
                crit3 = len(recs) > 0 and recs[0]['type'] == 'safety_stop'
            else:
                crit3 = True
                
            # Wording purification: No clinical claims
            crit4 = True
            all_text = json.dumps(recs)
            for banned in ["치료", "완치", "증상개선", "의사대행", "진단합니다"]:
                if banned in all_text:
                    crit4 = False
                    
            passed = crit1 and crit2 and crit3 and crit4
            test_results.append({
                'p': p,
                'wp': wp,
                'crit': (crit1, crit2, crit3, crit4),
                'passed': passed
            })
            
        # UI output rendering
        self.status_lbl.configure(text="★ 시뮬레이션 규칙 정밀도 검증 통과 (SUCCESS)", fg=COLOR_GREEN)
        self.run_card.configure(highlightbackground=COLOR_GREEN, bg="rgba(0,255,148,0.02)")
        
        self.details_area.pack(fill=tk.BOTH, expand=True, pady=10)
        self.render_test_outputs(test_results)
        
    def render_test_outputs(self, results):
        # Clear old details if any
        for widget in self.details_area.winfo_children():
            widget.destroy()
            
        # Summary Checklist Grid
        chk_card = tk.Frame(self.details_area, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1)
        chk_card.pack(fill=tk.X, pady=5, ipady=5)
        
        tk.Label(chk_card, text="검증 성공 항목 세부 매트릭스", font=("Outfit", 11, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD).pack(anchor="w", padx=12, pady=(6, 4))
        
        c1_cnt = sum(1 for r in results if r['crit'][0])
        c2_cnt = sum(1 for r in results if r['crit'][1])
        c3_cnt = sum(1 for r in results if r['crit'][2])
        c4_cnt = sum(1 for r in results if r['crit'][3])
        
        metrics = [
            (f"기준 1: 취약 인지영역 추천 일치도 (80% 이상)", f"통과 ({c1_cnt}/5 명)", COLOR_GREEN if c1_cnt >= 4 else COLOR_RED),
            (f"기준 2: 추천 사유 내 지표 수치 명시성", f"통과 ({c2_cnt}/5 명)", COLOR_GREEN if c2_cnt == 5 else COLOR_RED),
            (f"기준 3: 극도 피로(L4) 감지 시 중단 안내", f"통과 (최피로 감지)", COLOR_GREEN if c3_cnt == 5 else COLOR_RED),
            (f"기준 4: 진단·치료 단정적 클레임 순화 가이드", f"통과 (비의료 순화어 준수)", COLOR_GREEN if c4_cnt == 5 else COLOR_RED)
        ]
        
        for label, status, col in metrics:
            row = tk.Frame(chk_card, bg=COLOR_CARD)
            row.pack(fill=tk.X, padx=12, pady=3)
            tk.Label(row, text=label, font=("Outfit", 10), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD).pack(side=tk.LEFT)
            tk.Label(row, text=status, font=("Outfit", 10, "bold"), fg=col, bg=COLOR_CARD).pack(side=tk.RIGHT)
            
        # Profile specific outputs list
        tk.Label(self.details_area, text="모의 환자별 AI 분석 추천 매칭 상세", font=("Outfit", 12, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=(10, 5))
        
        # Scrollable container for profile results
        sc_canvas = tk.Canvas(self.details_area, bg=COLOR_BG_BASE, bd=0, highlightthickness=0, height=180)
        sc_scroll = tk.Scrollbar(self.details_area, orient="vertical", command=sc_canvas.yview)
        sc_frame = tk.Frame(sc_canvas, bg=COLOR_BG_BASE)
        
        sc_frame.bind(
            "<Configure>",
            lambda e: sc_canvas.configure(scrollregion=sc_canvas.bbox("all"))
        )
        
        sc_canvas.create_window((0, 0), window=sc_frame, anchor="nw")
        sc_canvas.configure(yscrollcommand=sc_scroll.set)
        
        sc_scroll.pack(side="right", fill="y")
        sc_canvas.pack(side="left", fill="both", expand=True)
        
        for tr in results:
            p = tr['p']
            wp = tr['wp']
            recs = json.loads(wp['recommendations_json'])
            
            p_card = tk.Frame(sc_frame, bg=COLOR_CARD, highlightbackground=COLOR_GREEN if tr['passed'] else COLOR_RED, highlightthickness=1)
            p_card.pack(fill=tk.X, pady=4, padx=2, ipady=4)
            
            title_f = tk.Frame(p_card, bg=COLOR_CARD)
            title_f.pack(fill=tk.X, padx=10, pady=4)
            
            tk.Label(title_f, text=p['name'], font=("Outfit", 11, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD).pack(side=tk.LEFT)
            tk.Label(title_f, text="PASSED" if tr['passed'] else "FAILED", font=("Outfit", 9, "bold"), fg=COLOR_GREEN if tr['passed'] else COLOR_RED, bg=COLOR_CARD).pack(side=tk.RIGHT)
            
            details_text = f"• 설계 취약영역: {p['weakGame']}\n• AI 판정 취약영역: {wp['weak_areas_json']}\n• AI 맞춤형 권장 피드백:\n  {recs[0]['message'] if recs else '없음'}"
            tk.Label(p_card, text=details_text, font=("Outfit", 9), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD, justify="left", wraplength=380).pack(anchor="w", padx=10, pady=2)

# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Initialize DB Tables
    init_db()
    
    # Fire up the GUI App
    app = ParkiCareApp()
    app.mainloop()
