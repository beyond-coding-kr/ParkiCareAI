from pyscript import document, window
import time
import math
import storage

class MotorResponseGame:
    def __init__(self):
        self.problem = None
        self.hit_count = 0
        self.miss_count = 0
        self.response_times = []
        self.current_target = None
        self.appear_time = None
        self.on_complete = None
        self.remaining_targets = 0
        self.is_finished = False
        self.timeout_ids = []

    def clear_timeouts(self):
        for tid in self.timeout_ids:
            window.clearTimeout(tid)
        self.timeout_ids = []

    def set_timeout(self, callback, ms):
        tid = window.setTimeout(callback, ms)
        self.timeout_ids.append(tid)
        return tid

    def init(self, container, problem_data, complete_cb):
        self.problem = problem_data
        self.hit_count = 0
        self.miss_count = 0
        self.response_times = []
        self.current_target = None
        self.is_finished = False
        self.remaining_targets = self.problem['targetCount']
        self.on_complete = complete_cb
        self.clear_timeouts()
        self.render(container)
        self.set_timeout(lambda: self.spawn_target(container), 800)

    def render(self, container):
        html = f"""
        <div class="game-wrap motor-game">
            <div class="game-header">
                <div class="game-title">운동 훈련</div>
                <div class="game-meta">
                    <span class="round-badge">남은 타겟 <span id="mtr-remain">{self.problem['targetCount']}</span></span>
                    <span class="diff-badge">난이도 {self.problem['difficulty']}</span>
                </div>
            </div>
            <p class="game-desc">{self.problem['description']}</p>
            <div class="motor-stage" id="mtr-stage">
                <div class="motor-overlay" id="mtr-overlay">
                    <div class="motor-ready-text">준비!</div>
                </div>
            </div>
            <div class="motor-stats">
                <div class="mstat">
                    <span class="mstat-val" id="mtr-hit">0</span>
                    <span class="mstat-label">적중</span>
                </div>
                <div class="mstat mstat-miss">
                    <span class="mstat-val" id="mtr-miss">0</span>
                    <span class="mstat-label">실패</span>
                </div>
            </div>
        </div>
        """
        container.innerHTML = html

    def spawn_target(self, container):
        if self.is_finished: return
        stage = document.querySelector('#mtr-stage')
        overlay = document.querySelector('#mtr-overlay')
        if overlay:
            overlay.remove()
        if not stage: return
        
        old = document.querySelector('#mtr-target')
        if old: old.remove()
        
        stageW = stage.offsetWidth or 340
        stageH = stage.offsetHeight or 300
        size = self.problem['targetSize']
        pad = size / 2 + 10
        
        x = pad + window.Math.random() * (stageW - pad * 2)
        y = pad + window.Math.random() * (stageH - pad * 2)
        
        target = document.createElement('div')
        target.id = 'mtr-target'
        target.className = 'motor-target'
        target.style.cssText = f"width:{size}px; height:{size}px; left:{x - size/2}px; top:{y - size/2}px;"
        
        stage.appendChild(target)
        self.current_target = target
        self.appear_time = window.Date.now()
        
        def hit_handler(e):
            if hasattr(e, 'preventDefault'):
                e.preventDefault()
            self.handle_hit(container)
            
        target.onclick = hit_handler
        
        def miss_handler():
            if not self.is_finished:
                self.handle_miss(container)
        
        self.set_timeout(miss_handler, self.problem['timeLimit'])

    def handle_hit(self, container):
        if self.is_finished or not self.current_target: return
        target = self.current_target
        self.current_target = None
        self.clear_timeouts() # Clears miss handler
        
        elapsed = window.Date.now() - self.appear_time
        self.response_times.append(elapsed)
        self.hit_count += 1
        self.remaining_targets -= 1
        self.update_stats()
        target.remove()
        self.next_or_finish(container)

    def handle_miss(self, container):
        if self.is_finished or not self.current_target: return
        target = self.current_target
        self.current_target = None
        self.clear_timeouts()
        
        self.miss_count += 1
        self.remaining_targets -= 1
        self.response_times.append(self.problem['timeLimit'])
        self.update_stats()
        target.remove()
        self.next_or_finish(container)

    def next_or_finish(self, container):
        old = document.querySelector('#mtr-target')
        if old: old.remove()
        if self.remaining_targets <= 0:
            self.finish_game()
            return
            
        document.querySelector('#mtr-remain').textContent = str(self.remaining_targets)
        self.set_timeout(lambda: self.spawn_target(container), 300)

    def update_stats(self):
        hitEl = document.querySelector('#mtr-hit')
        missEl = document.querySelector('#mtr-miss')
        if hitEl: hitEl.textContent = str(self.hit_count)
        if missEl: missEl.textContent = str(self.miss_count)

    def finish_game(self):
        if self.is_finished: return
        self.is_finished = True
        self.clear_timeouts()
        
        total = self.problem['targetCount']
        accuracy = self.hit_count / total
        avg_resp = sum(self.response_times)/len(self.response_times) if self.response_times else self.problem['timeLimit']
        
        session_data = {
            'accuracy': accuracy,
            'avgResponseTime': avg_resp,
            'correctCount': self.hit_count,
            'totalRounds': total,
            'difficulty': self.problem['difficulty']
        }
        
        prof = storage.Storage.get_current_profile()
        if prof:
            storage.Storage.save_session(prof['id'], 'motor_response', session_data)
            
        if self.on_complete:
            self.on_complete(session_data)
