from pyscript import document, window
import random
import time
import json

class MemorySequenceGame:
    def __init__(self):
        self.problem = None
        self.user_input = []
        self.start_time = None
        self.response_times = []
        self.correct_count = 0
        self.total_rounds = 3
        self.current_round = 0
        self.on_complete = None
        self.show_phase = False
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
        self.user_input = []
        self.response_times = []
        self.correct_count = 0
        self.current_round = 0
        self.on_complete = complete_cb
        self.clear_timeouts()
        self.render(container)
        self.start_round(container)

    def render(self, container):
        html = f"""
        <div class="game-wrap memory-game">
            <div class="game-header">
                <div class="game-title">기억력 훈련</div>
                <div class="game-meta">
                    <span class="round-badge">라운드 <span id="mg-round">1</span> / {self.total_rounds}</span>
                    <span class="diff-badge">난이도 {self.problem['difficulty']}</span>
                </div>
            </div>
            <p class="game-desc">{self.problem['description']}</p>
            <div class="memory-stage">
                <div id="mg-display" class="mg-display hidden">
                    <div class="mg-nums" id="mg-nums"></div>
                    <div class="mg-timer-bar-wrap"><div class="mg-timer-bar" id="mg-timer-bar"></div></div>
                </div>
                <div id="mg-input-area" class="mg-input-area hidden">
                    <p class="input-hint">기억한 숫자를 순서대로 입력하세요</p>
                    <div class="mg-entered" id="mg-entered"></div>
                    <div class="mg-keypad">
        """
        keys = [1, 2, 3, 4, 5, 6, 7, 8, 9, '←', 0, '✓']
        for k in keys:
            cls = "keypad-del" if k == '←' else ("keypad-ok" if k == '✓' else "")
            html += f'<button class="keypad-btn {cls}" data-key="{k}" id="kp-{k}">{k}</button>'
        
        html += f"""
                    </div>
                </div>
                <div id="mg-result" class="mg-result hidden"></div>
                <div id="mg-ready" class="mg-ready">
                    <div class="ready-text">곧 숫자가 표시됩니다.</div>
                    <div class="ready-sub">화면에 나오는 숫자를 기억해 주세요.</div>
                </div>
            </div>
            <div class="progress-row">
        """
        for i in range(self.total_rounds):
            html += f'<div class="prog-dot" id="prog-{i}"></div>'
        html += """
            </div>
        </div>
        """
        container.innerHTML = html

        # Add event listeners
        def make_handler(key):
            def handler(event):
                self.handle_keypad(key, container)
            return handler

        btns = container.querySelectorAll('.keypad-btn')
        for i in range(btns.length):
            btn = btns.item(i)
            btn.onclick = make_handler(btn.getAttribute("data-key"))

    def start_round(self, container):
        self.current_round += 1
        self.user_input = []
        self.show_phase = True
        document.querySelector('#mg-round').textContent = str(self.current_round)
        
        length = len(self.problem['sequence'])
        self.problem['sequence'] = [random.randint(1, 9) for _ in range(length)]
        
        self.show_el('mg-ready')
        self.hide_el('mg-display')
        self.hide_el('mg-input-area')
        self.hide_el('mg-result')
        
        def step1():
            self.hide_el('mg-ready')
            self.show_el('mg-display')
            nums_html = "".join([f'<span class="mg-num">{n}</span>' for n in self.problem['sequence']])
            document.querySelector('#mg-nums').innerHTML = nums_html
            
            bar = document.querySelector('#mg-timer-bar')
            bar.style.transition = 'none'
            bar.style.width = '100%'
            bar.offsetHeight
            
            def do_transition():
                bar.style.transition = f"width {self.problem['displayTime']}ms linear"
                bar.style.width = '0%'
            window.requestAnimationFrame(do_transition)
            
            def step2():
                self.show_phase = False
                self.hide_el('mg-display')
                self.show_el('mg-input-area')
                self.update_entered()
                self.start_time = window.Date.now()
            
            self.set_timeout(step2, self.problem['displayTime'])
            
        self.set_timeout(step1, 900)

    def handle_keypad(self, key, container):
        if self.show_phase:
            return
        if key == '←':
            if self.user_input:
                self.user_input.pop()
        elif key == '✓':
            self.submit_answer(container)
            return
        elif len(self.user_input) < len(self.problem['sequence']):
            self.user_input.append(int(key))
            if len(self.user_input) == len(self.problem['sequence']):
                self.submit_answer(container)
        self.update_entered()

    def update_entered(self):
        el = document.querySelector('#mg-entered')
        if not el:
            return
        html = ""
        seq_len = len(self.problem['sequence'])
        for i in range(seq_len):
            val = self.user_input[i] if i < len(self.user_input) else ""
            cls = "filled" if i < len(self.user_input) else ""
            html += f'<div class="entered-slot {cls}">{val}</div>'
        el.innerHTML = html

    def submit_answer(self, container):
        self.show_phase = True
        elapsed = window.Date.now() - self.start_time
        self.response_times.append(elapsed)
        
        is_correct = len(self.user_input) == len(self.problem['sequence']) and self.user_input == self.problem['sequence']
        if is_correct:
            self.correct_count += 1
            
        self.hide_el('mg-input-area')
        self.show_el('mg-result')
        
        result_el = document.querySelector('#mg-result')
        icon_cls = "correct" if is_correct else "wrong"
        icon_char = "✓" if is_correct else "✗"
        text_str = "정답!" if is_correct else "오답"
        ans_str = " → ".join(map(str, self.problem['sequence']))
        inp_str = " → ".join(map(str, self.user_input)) if self.user_input else "-"
        
        result_el.innerHTML = f"""
          <div class="result-icon {icon_cls}">{icon_char}</div>
          <div class="result-text">{text_str}</div>
          <div class="result-answer">
            정답: <strong>{ans_str}</strong><br>
            입력: <strong>{inp_str}</strong>
          </div>
        """
        result_el.classList.add('show')
        
        dot = document.querySelector(f'#prog-{self.current_round-1}')
        if dot:
            dot.className = f"prog-dot {icon_cls}"
            
        def next_step():
            if self.current_round < self.total_rounds:
                result_el.classList.remove('show')
                self.start_round(container)
            else:
                self.finish_game()
        self.set_timeout(next_step, 1500)

    def finish_game(self):
        accuracy = self.correct_count / self.total_rounds
        avg_resp = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        session_data = {
            'accuracy': accuracy,
            'avgResponseTime': avg_resp,
            'correctCount': self.correct_count,
            'totalRounds': self.total_rounds,
            'difficulty': self.problem['difficulty']
        }
        
        # Save session (assuming storage is globally available or imported)
        import py_frontend.storage as storage
        prof = storage.Storage.get_current_profile()
        if prof:
            storage.Storage.save_session(prof['id'], 'memory_sequence', session_data)
            
        if self.on_complete:
            self.on_complete(session_data)

    def show_el(self, id_str):
        el = document.querySelector(f'#{id_str}')
        if el:
            el.classList.remove('hidden')

    def hide_el(self, id_str):
        el = document.querySelector(f'#{id_str}')
        if el:
            el.classList.add('hidden')
