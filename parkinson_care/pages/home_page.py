"""
홈 페이지 - 대시보드
"""
import customtkinter as ctk
from datetime import datetime
from utils.ui import AccessibleScrollableFrame


class HomePage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.build_ui()

    def build_ui(self):
        # 스크롤 가능 프레임 (접근성 향상)
        self.scroll = AccessibleScrollableFrame(self, app=self.app, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # ── 상단 인사 카드 ──
        self._create_greeting_card()

        # ── 면책 조항 ──
        self._create_disclaimer()

        # ── 빠른 접근 버튼들 ──
        self._create_quick_actions()

        # ── 오늘의 현황 ──
        self._create_today_summary()

    def _create_greeting_card(self):
        theme = self.app.current_theme
        fs = self.app.font_size

        card = ctk.CTkFrame(self.scroll, fg_color=theme["accent"], corner_radius=15, height=120)
        card.pack(fill="x", pady=(0, 15))
        card.pack_propagate(False)

        user = self.app.db.get_user()
        name = user["name"] if user else "환자"
        hour = datetime.now().hour
        greeting = "좋은 아침이에요" if hour < 12 else "좋은 오후에요" if hour < 18 else "좋은 저녁이에요"

        title = ctk.CTkLabel(card, text=f"🌟 {greeting}, {name}님!", font=(self.app.font_family, fs + 6, "bold"), text_color="white")
        title.pack(anchor="w", padx=25, pady=(20, 5))

        streak = self.app.db.get_streak()
        sub = ctk.CTkLabel(card, text=f"🔥 연속 {streak}일 재활 운동 중  |  📅 {datetime.now().strftime('%Y년 %m월 %d일')}", font=(self.app.font_family, fs - 2), text_color="white")
        sub.pack(anchor="w", padx=25)

    def _create_disclaimer(self):
        from config import DISCLAIMER
        theme = self.app.current_theme
        fs = self.app.font_size

        frame = ctk.CTkFrame(self.scroll, fg_color=theme["warning_light"], corner_radius=10, border_width=1, border_color=theme["warning"])
        frame.pack(fill="x", pady=(0, 15))

        lbl = ctk.CTkLabel(frame, text=DISCLAIMER, font=(self.app.font_family, fs - 3), text_color=theme["text_secondary"], wraplength=700, justify="left")
        lbl.pack(padx=15, pady=10)

    def _create_quick_actions(self):
        theme = self.app.current_theme
        fs = self.app.font_size

        title_label = ctk.CTkLabel(self.scroll, text="⚡ 빠른 접근", font=(self.app.font_family, fs + 2, "bold"), text_color=theme["text"], anchor="w")
        title_label.pack(fill="x", pady=(0, 10))

        btn_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 15))

        buttons = [
            ("🚨", "긴급 연락", theme["danger"], "emergency"),
            ("📋", "증상 업로드", theme["accent"], "symptom"),
            ("💪", "재활 치료", theme["success"], "rehab"),
            ("🎤", "음성 검사", "#8E24AA", "voice"),
            ("📊", "현황 보기", "#FB8C00", "analysis"),
        ]

        # 2행으로 배치
        for i, (icon, text, color, page) in enumerate(buttons):
            row = i // 3
            col = i % 3

            btn = ctk.CTkButton(
                btn_frame, text=f"{icon}  {text}",
                font=(self.app.font_family, fs + 2, "bold"),
                fg_color=color, hover_color=theme["accent_hover"],
                width=200, height=80, corner_radius=15,
                command=lambda p=page: self.app.show_page(p),
            )
            btn.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        for c in range(3):
            btn_frame.columnconfigure(c, weight=1)

    def _create_today_summary(self):
        theme = self.app.current_theme
        fs = self.app.font_size

        title_label = ctk.CTkLabel(self.scroll, text="📌 오늘의 현황", font=(self.app.font_family, fs + 2, "bold"), text_color=theme["text"], anchor="w")
        title_label.pack(fill="x", pady=(10, 10))

        summary_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        summary_frame.pack(fill="x")

        # 오늘 재활 치료
        today_rehab = self.app.db.get_today_rehab_sessions()
        done = sum(1 for s in today_rehab if s["completed"])
        total = len(today_rehab)

        cards_data = [
            ("재활 치료", f"{done}/{total} 완료" if total > 0 else "오늘 예정 없음", theme["success"]),
            ("최근 증상", f"{len(self.app.db.get_symptoms(days=1))}건 기록", theme["accent"]),
            ("AI 분석", f"{len(self.app.db.get_ai_analyses(limit=5))}건", "#8E24AA"),
        ]

        for i, (label, value, color) in enumerate(cards_data):
            card = ctk.CTkFrame(summary_frame, fg_color=theme["card_bg"], corner_radius=12, border_width=1, border_color=theme["border"])
            card.grid(row=0, column=i, padx=8, pady=5, sticky="nsew")

            clbl = ctk.CTkLabel(card, text=label, font=(self.app.font_family, fs - 2), text_color=theme["text_secondary"])
            clbl.pack(padx=15, pady=(12, 2))

            vlbl = ctk.CTkLabel(card, text=value, font=(self.app.font_family, fs + 2, "bold"), text_color=color)
            vlbl.pack(padx=15, pady=(0, 12))

        for c in range(3):
            summary_frame.columnconfigure(c, weight=1)

    def refresh(self):
        """페이지 새로고침"""
        for w in self.scroll.winfo_children():
            w.destroy()
        self.scroll.destroy()
        self.build_ui()
