from pyscript import document, window
import storage

class AttentionStroopGame:
    def __init__(self):
        self.problem = None
        self.current_idx = 0
        self.correct_count = 0
        self.response_times = []
        self.start_time = None
        self.on_complete = None
        self.timer_id = None
        self.timeout_ids = []

    def clear_timeouts(self):
        for tid in self.timeout_ids:
            window.clearTimeout(tid)
        self.timeout_ids = []
        if self.timer_id:
            window.clearInterval(self.timer_id)
            self.timer_id = None

    def set_timeout(self, callback, ms):
        tid = window.setTimeout(callback, ms)
        self.timeout_ids.append(tid)
        return tid

    def init(self, container, problem_data, complete_cb):
        self.problem = problem_data
        self.current_idx = 0
        self.correct_count = 0
        self.response_times = []
        self.on_complete = complete_cb
        self.clear_timeouts()
        self.render(container)
        self.show_problem(container)

    def render(self, container):
        html = f"""
        <div class="game-wrap stroop-game">
            <div class="game-header">
                <div class="game-title">집중력 훈련</div>
                <div class="game-meta">
                    <span class="round-badge">문제 <span id="sg-round">1</span> / {len(self.problem['problems'])}</span>
                    <span class="diff-badge">난이도 {self.problem['difficulty']}</span>
                </div>
            </div>
            <p class="game-desc">글자의 <strong>색상</strong>을 선택하세요 (글자 내용이 아닙니다)</p>
            <div class="stroop-stage" id="sg-stage">
                <div class="stroop-time-bar-wrap">
                    <div class="stroop-time-bar" id="sg-time-bar"></div>
                </div>
                <div class="stroop-word-wrap">
                    <div class="stroop-word" id="sg-word"></div>
                    <div class="stroop-hint">이 글자의 <em>색상</em>은?</div>
                </div>
                <div class="stroop-options" id="sg-options"></div>
            </div>
            <div class="progress-row" id="sg-progress"></div>
        </div>
        """
        container.innerHTML = html
        self.render_progress()

    def render_progress(self):
        prog = document.querySelector('#sg-progress')
        if not prog: return
        html = ""
        for i in range(len(self.problem['problems'])):
            html += f'<div class="prog-dot" id="sg-prog-{i}"></div>'
        prog.innerHTML = html

    def show_problem(self, container):
        if self.current_idx >= len(self.problem['problems']):
            self.finish_game()
            return
            
        p = self.problem['problems'][self.current_idx]
        document.querySelector('#sg-round').textContent = str(self.current_idx + 1)
        
        wordEl = document.querySelector('#sg-word')
        wordEl.textContent = p['text']
        wordEl.style.color = p['textColor']
        wordEl.classList.remove('pop')
        window.requestAnimationFrame(lambda: wordEl.classList.add('pop'))
        
        optEl = document.querySelector('#sg-options')
        optEl.innerHTML = ""
        
        def make_handler(opt_name):
            return lambda e: self.handle_answer(opt_name, p, container)
            
        for opt in p['options']:
            btn = document.createElement('button')
            btn.className = 'stroop-opt-btn'
            btn.innerHTML = f'<span class="color-dot" style="background:{opt["hex"]}"></span><span>{opt["name"]}</span>'
            btn.onclick = make_handler(opt['name'])
            optEl.appendChild(btn)
            
        if self.timer_id:
            window.clearInterval(self.timer_id)
            
        self.start_time = window.Date.now()
        
        bar = document.querySelector('#sg-time-bar')
        bar.style.transition = 'none'
        bar.style.width = '100%'
        bar.style.background = '#4a90e2'
        
        def do_transition():
            bar.style.transition = f"width {p['timeLimit']}ms linear"
            bar.style.width = '0%'
        window.requestAnimationFrame(do_transition)
        
        def check_time():
            elapsed = window.Date.now() - self.start_time
            if elapsed >= p['timeLimit']:
                window.clearInterval(self.timer_id)
                self.timer_id = None
                self.handle_answer(None, p, container)
                
        self.timer_id = window.setInterval(check_time, 100)

    def handle_answer(self, selected, p, container):
        if self.timer_id is None and selected is not None:
            # Already handled by timeout, but user clicked right as it expired
            return
            
        if self.timer_id is not None:
            window.clearInterval(self.timer_id)
            self.timer_id = None
            
        elapsed = window.Date.now() - self.start_time
        self.response_times.append(min(elapsed, p['timeLimit']))
        
        is_correct = selected == p['correctAnswer']
        if is_correct:
            self.correct_count += 1
            
        optEls = document.querySelectorAll('.stroop-opt-btn')
        for i in range(optEls.length):
            btn = optEls.item(i)
            btn.disabled = True
            name = btn.querySelector('span:last-child').textContent
            if name == p['correctAnswer']:
                btn.classList.add('opt-correct')
            elif name == selected and not is_correct:
                btn.classList.add('opt-wrong')
                
        dot = document.querySelector(f'#sg-prog-{self.current_idx}')
        if dot:
            dot.className = f"prog-dot {'correct' if is_correct else 'wrong'}"
            
        self.current_idx += 1
        self.set_timeout(lambda: self.show_problem(container), 900)

    def finish_game(self):
        accuracy = self.correct_count / len(self.problem['problems'])
        avg_resp = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        session_data = {
            'accuracy': accuracy,
            'avgResponseTime': avg_resp,
            'correctCount': self.correct_count,
            'totalRounds': len(self.problem['problems']),
            'difficulty': self.problem['difficulty']
        }
        
        prof = storage.Storage.get_current_profile()
        if prof:
            storage.Storage.save_session(prof['id'], 'attention_stroop', session_data)
            
        if self.on_complete:
            self.on_complete(session_data)
