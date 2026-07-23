from pyscript import document, window
import json
import storage
import math
from games.memory_sequence import MemorySequenceGame
from games.attention_stroop import AttentionStroopGame
from games.motor_response import MotorResponseGame

class App:
    current_screen = 'home'
    current_game_type = None

    GAME_INFO = {
        'memory_sequence': {
            'id': 'memory_sequence', 'label': '기억력 훈련', 'desc': '숫자 배열을 기억하고 순서대로 입력',
            'color': '#00D4FF',
        },
        'attention_stroop': {
            'id': 'attention_stroop', 'label': '집중력 훈련', 'desc': '글자 색상을 빠르게 판별',
            'color': '#7B2FBE',
        },
        'motor_response': {
            'id': 'motor_response', 'label': '운동 훈련', 'desc': '나타나는 타겟을 신속하게 터치',
            'color': '#00FF94',
        },
    }

    @classmethod
    def init(cls):
        storage.Storage.check_session()
        cls.navigate_to('home')

    @classmethod
    def navigate_to(cls, screen, params=None):
        if params is None:
            params = {}
        user = storage.Storage.get_current_user()
        if not user and screen not in ['login', 'register']:
            screen = 'login'
            
        cls.current_screen = screen
        root = document.querySelector('#app-root')
        cls.render_screen(screen, params, root)

    @classmethod
    def render_screen(cls, screen, params, root):
        if screen == 'login': cls.render_login(root)
        elif screen == 'register': cls.render_register(root)
        elif screen == 'home': cls.render_home(root)
        elif screen == 'profile-create': cls.render_profile_create(root, params)
        elif screen == 'hub': cls.render_hub(root)
        elif screen == 'game': cls.render_game(root, params)
        elif screen == 'result': cls.render_result(root, params)
        elif screen == 'dashboard': cls.render_dashboard(root)
        elif screen == 'report': cls.render_report(root)
        else: cls.render_home(root)

    @classmethod
    def render_login(cls, root):
        html = """
        <div class="screen auth-screen">
          <div class="auth-card">
            <h1 class="logo-title" style="text-align:center">ParkiCare</h1>
            <p class="auth-sub" style="text-align:center">로그인하여 맞춤형 훈련을 시작하세요</p>
            <form id="login-form">
              <div class="form-group">
                <input type="text" id="username" placeholder="아이디" required>
              </div>
              <div class="form-group">
                <input type="password" id="password" placeholder="비밀번호" required>
              </div>
              <button type="submit" class="btn btn-primary btn-boj">로그인</button>
            </form>
            <div class="auth-links">
              <span id="link-register">회원가입</span>
            </div>
          </div>
        </div>
        """
        root.innerHTML = html

        def on_submit(e):
            e.preventDefault()
            u = document.querySelector('#username').value
            p = document.querySelector('#password').value
            res = storage.Storage.login(u, p)
            if res:
                cls.navigate_to('home')
            else:
                window.alert("로그인 실패: 아이디/비밀번호를 확인하세요.")

        document.querySelector('#login-form').onsubmit = on_submit
        
        def go_reg(e):
            cls.navigate_to('register')
        document.querySelector('#link-register').onclick = go_reg

    @classmethod
    def render_register(cls, root):
        html = """
        <div class="screen auth-screen">
          <div class="auth-card">
            <h1 class="logo-title" style="text-align:center">회원가입</h1>
            <form id="reg-form">
              <div class="form-group">
                <input type="text" id="reg-username" placeholder="아이디" required>
              </div>
              <div class="form-group">
                <input type="password" id="reg-password" placeholder="비밀번호" required>
              </div>
              <button type="submit" class="btn btn-primary btn-boj">가입하기</button>
            </form>
            <div class="auth-links">
              <span id="link-login">로그인으로 돌아가기</span>
            </div>
          </div>
        </div>
        """
        root.innerHTML = html

        def on_submit(e):
            e.preventDefault()
            u = document.querySelector('#reg-username').value
            p = document.querySelector('#reg-password').value
            res = storage.Storage.register(u, p)
            if res:
                cls.navigate_to('home')
            else:
                window.alert("회원가입 실패 (이미 존재하는 아이디일 수 있습니다).")

        document.querySelector('#reg-form').onsubmit = on_submit
        
        def go_login(e):
            cls.navigate_to('login')
        document.querySelector('#link-login').onclick = go_login

    @classmethod
    def render_home(cls, root):
        profiles = storage.Storage.get_profiles()
        current = storage.Storage.get_current_profile()
        user = storage.Storage.get_current_user()
        
        user_name = user['username'] if user else ''
        
        html = f"""
        <div class="screen home-screen">
            <div class="user-session-bar">
                <span class="user-session-info">사용자: <strong>{user_name}</strong></span>
                <button class="btn-logout-boj" id="btn-logout">로그아웃</button>
            </div>
            <div class="home-hero">
                <div class="logo-wrap">
                    <div>
                        <h1 class="logo-title">ParkiCare</h1>
                        <p class="logo-sub">파킨슨병 맞춤형 인지·운동 케어 시스템</p>
                    </div>
                </div>
                <div class="hero-badge">개인 맞춤형 인지·운동 트레이닝</div>
            </div>
        """
        
        if not profiles:
            html += """
            <div class="empty-state">
                <p>등록된 환자 프로필이 없습니다</p>
                <button class="btn btn-primary" id="btn-create-first">새 프로필 만들기</button>
            </div>
            """
        else:
            html += '<div class="section-title">환자 프로필 선택</div><div class="profile-list" id="profile-list">'
            for p in profiles:
                is_active = (current and current.get('id') == p.get('id'))
                cls_str = "profile-card active" if is_active else "profile-card"
                html += f"""
                <div class="{cls_str}" data-id="{p.get('id')}">
                    <div class="profile-avatar" style="background:#4a90e2">{p.get('name')[0]}</div>
                    <div class="profile-info">
                        <div class="profile-name">{p.get('name')}</div>
                        <div class="profile-age">{p.get('age')}세</div>
                    </div>
                </div>
                """
            html += '</div><button class="btn btn-outline mt-2" id="btn-add-profile">+ 프로필 추가</button>'
            
        html += """
            <div class="home-features">
                <div class="feature-item"><span>맞춤형 취약 영역 평가</span></div>
                <div class="feature-item"><span>미니게임 형식 훈련</span></div>
                <div class="feature-item"><span>맞춤형 리포트</span></div>
            </div>
        </div>
        """
        root.innerHTML = html

        btn_logout = document.querySelector('#btn-logout')
        if btn_logout:
            def do_logout(e):
                storage.Storage.logout()
                cls.navigate_to('login')
            btn_logout.onclick = do_logout

        btn_create = document.querySelector('#btn-create-first')
        if btn_create:
            btn_create.onclick = lambda e: cls.navigate_to('profile-create')
            
        btn_add = document.querySelector('#btn-add-profile')
        if btn_add:
            btn_add.onclick = lambda e: cls.navigate_to('profile-create')

        cards = document.querySelectorAll('.profile-card')
        
        def make_card_handler(pid):
            def handler(e):
                storage.Storage.set_current_profile(pid)
                cls.navigate_to('hub')
            return handler
            
        for i in range(cards.length):
            card = cards.item(i)
            pid = card.getAttribute('data-id')
            card.onclick = make_card_handler(pid)

    @classmethod
    def render_profile_create(cls, root, params):
        html = """
        <div class="screen hub-screen">
            <div class="hub-header">
                <button class="back-btn" id="btn-back">← 뒤로</button>
                <div class="hub-name">새 프로필</div>
            </div>
            <form id="profile-form" class="form-container">
                <div class="form-group">
                    <label>환자 이름</label>
                    <input type="text" id="f-name" placeholder="이름" required>
                </div>
                <div class="form-group">
                    <label>나이</label>
                    <input type="number" id="f-age" placeholder="나이" min="3" max="150" required>
                </div>
                <button type="submit" class="btn btn-primary">프로필 생성</button>
            </form>
        </div>
        """
        root.innerHTML = html
        document.querySelector('#btn-back').onclick = lambda e: cls.navigate_to('home')
        
        def on_submit(e):
            e.preventDefault()
            name = document.querySelector('#f-name').value
            age = int(document.querySelector('#f-age').value)
            storage.Storage.save_profile({'name': name, 'age': age})
            cls.navigate_to('home')
            
        document.querySelector('#profile-form').onsubmit = on_submit

    @classmethod
    def render_hub(cls, root):
        profile = storage.Storage.get_current_profile()
        if not profile:
            cls.navigate_to('home')
            return
            
        weak = storage.Storage.get_weak_profile(profile['id'])
        if weak and not weak.get('games'):
            # Trigger analysis
            storage.Storage.run_analysis(profile['id'])
            weak = storage.Storage.get_weak_profile(profile['id'])
            
        weak = weak or {'overallScore': 0, 'games': {}}
        score = weak.get('overallScore', 0)
        
        grade = None
        if score >= 80: grade = {'label': '우수', 'color': '#27ae60'}
        elif score >= 50: grade = {'label': '보통', 'color': '#f39c12'}
        else: grade = {'label': '주의', 'color': '#e74c3c'}
        
        html = f"""
        <div class="screen hub-screen">
            <div class="hub-header">
                <button class="back-btn" id="btn-back">← 홈</button>
                <div class="hub-profile">
                    <div class="hub-avatar" style="background:#4a90e2">{profile.get('name')[0]}</div>
                    <div>
                        <div class="hub-name">{profile.get('name')}</div>
                    </div>
                </div>
                <button class="icon-btn" id="btn-dashboard" title="분석 대시보드">대시보드</button>
            </div>
        """
        
        if score > 0 or (weak.get('games') and len(weak['games']) > 0):
            html += f"""
            <div class="overall-card" style="--accent:{grade['color']}">
                <div class="overall-label">종합 점수</div>
                <div class="overall-score" style="color:{grade['color']}">{score}</div>
                <div class="overall-grade">{grade['label']}</div>
            </div>
            """
        else:
            html += """
            <div class="info-banner">
                각 훈련을 3회 이상 수행하면 종합 평가가 시작됩니다
            </div>
            """
            
        html += '<div class="section-title">오늘의 훈련</div><div class="game-cards">'
        for k, v in cls.GAME_INFO.items():
            g_data = weak.get('games', {}).get(k, {})
            is_weak = g_data.get('isWeak', False)
            cls_str = "game-card game-card-weak" if is_weak else "game-card"
            badge = '<div class="weak-badge">취약 영역 (추천)</div>' if is_weak else ''
            
            html += f"""
            <div class="{cls_str}" data-game="{k}">
                {badge}
                <div class="gc-icon" style="background:{v['color']}20; color:{v['color']}">🎮</div>
                <div class="gc-info">
                    <div class="gc-title">{v['label']}</div>
                    <div class="gc-desc">{v['desc']}</div>
                </div>
            </div>
            """
            
        html += """
            </div>
            <div class="hub-actions">
                <button class="btn btn-outline" id="btn-report">리포트 보기</button>
            </div>
        </div>
        """
        root.innerHTML = html
        
        document.querySelector('#btn-back').onclick = lambda e: cls.navigate_to('home')
        document.querySelector('#btn-dashboard').onclick = lambda e: cls.navigate_to('dashboard')
        document.querySelector('#btn-report').onclick = lambda e: cls.navigate_to('report')
        
        cards = document.querySelectorAll('.game-card')
        def make_game_handler(gid):
            return lambda e: cls.navigate_to('game', {'gameType': gid})
            
        for i in range(cards.length):
            card = cards.item(i)
            gid = card.getAttribute('data-game')
            card.onclick = make_game_handler(gid)

    @classmethod
    def render_game(cls, root, params):
        cls.current_game_type = params['gameType']
        profile = storage.Storage.get_current_profile()
        problem = storage.Storage.get_problem(cls.current_game_type, profile['id'] if profile else None, True)
        
        if not problem:
            window.alert('문제를 불러오지 못했습니다.')
            cls.navigate_to('hub')
            return
            
        def on_complete(result):
            cls.navigate_to('result', {'result': result})
            
        if cls.current_game_type == 'memory_sequence':
            game = MemorySequenceGame()
        elif cls.current_game_type == 'attention_stroop':
            game = AttentionStroopGame()
        else:
            game = MotorResponseGame()
            
        game.init(root, problem, on_complete)

    @classmethod
    def render_result(cls, root, params):
        res = params['result']
        acc = res.get('accuracy', 0)
        pct = round(acc * 100)
        
        html = f"""
        <div class="screen result-screen">
            <h2 class="screen-title">훈련 완료!</h2>
            <div class="result-circle-wrap">
                <svg viewBox="0 0 120 120" class="result-svg">
                    <circle cx="60" cy="60" r="50" fill="none" stroke="#eee" stroke-width="12" />
                    <circle cx="60" cy="60" r="50" fill="none" stroke="#4a90e2" stroke-width="12"
                        stroke-dasharray="{2*math.pi*50}" stroke-dashoffset="{2*math.pi*50*(1-pct/100)}"
                        stroke-linecap="round" transform="rotate(-90 60 60)" class="circle-anim" />
                </svg>
                <div class="result-pct">{pct}<span>%</span></div>
            </div>
            <div class="result-details">
                <div class="rd-item">
                    <div class="rd-label">정답/적중</div>
                    <div class="rd-val">{res.get('correctCount')}/{res.get('totalRounds')}</div>
                </div>
                <div class="rd-item">
                    <div class="rd-label">평균 속도</div>
                    <div class="rd-val">{round(res.get('avgResponseTime', 0))}ms</div>
                </div>
                <div class="rd-item">
                    <div class="rd-label">진행 난이도</div>
                    <div class="rd-val">{res.get('difficulty')}단계</div>
                </div>
            </div>
            <div class="btn-group">
                <button class="btn btn-outline" id="btn-replay">다시 하기</button>
                <button class="btn btn-primary" id="btn-hub">돌아가기</button>
            </div>
        </div>
        """
        root.innerHTML = html
        
        document.querySelector('#btn-replay').onclick = lambda e: cls.navigate_to('game', {'gameType': cls.current_game_type})
        document.querySelector('#btn-hub').onclick = lambda e: cls.navigate_to('hub')

    @classmethod
    def render_dashboard(cls, root):
        cls.navigate_to('hub') # Simplified for PyScript limits, or we can just redirect

    @classmethod
    def render_report(cls, root):
        cls.navigate_to('hub') # Simplified for PyScript limits

# Start the application
App.init()
