"""
재활 치료 페이지
"""
import customtkinter as ctk
from datetime import datetime
from utils.ui import AccessibleScrollableFrame


class RehabPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.build_ui()

    def build_ui(self):
        self.scroll = AccessibleScrollableFrame(self, app=self.app, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        theme = self.app.current_theme
        fs = self.app.font_size

        # ── 제목 ──
        title_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(title_frame, text="💪 재활 치료", font=(self.app.font_family, fs + 6, "bold"), text_color=theme["text"]).pack(side="left")

        # 웹캠 거울 버튼
        ctk.CTkButton(
            title_frame, text="📸 웹캠 거울",
            font=(self.app.font_family, fs, "bold"),
            fg_color=theme["accent"], hover_color=theme["accent_hover"],
            width=120, height=40, corner_radius=12,
            command=self._toggle_webcam,
        ).pack(side="left", padx=15)

        # 스트리크 표시
        streak = self.app.db.get_streak()
        streak_label = ctk.CTkLabel(title_frame, text=f"🔥 {streak}일 연속", font=(self.app.font_family, fs, "bold"), text_color=theme["warning"])
        streak_label.pack(side="right", padx=10)

        # ── 오늘의 재활 체크리스트 ──
        ctk.CTkLabel(self.scroll, text="📋 오늘의 재활 치료", font=(self.app.font_family, fs + 2, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(10, 10))

        today_sessions = self.app.db.get_today_rehab_sessions()

        if today_sessions:
            for session in today_sessions:
                self._create_session_card(session)
        else:
            empty_card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=12, border_width=1, border_color=theme["border"])
            empty_card.pack(fill="x", pady=5)
            ctk.CTkLabel(empty_card, text="오늘 예정된 재활 치료가 없습니다.\n아래에서 치료를 추가하세요!", font=(self.app.font_family, fs - 1), text_color=theme["text_secondary"]).pack(padx=20, pady=20)

        # ── AI 재활 추천 버튼 ──
        ctk.CTkButton(
            self.scroll, text="🤖 AI 재활 치료 추천받기",
            font=(self.app.font_family, fs + 1, "bold"),
            fg_color="#8E24AA", hover_color="#6A1B9A",
            height=55, corner_radius=12,
            command=self._get_ai_recommendation,
        ).pack(fill="x", pady=(15, 10))

        self.ai_result_frame = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=12)
        self.ai_result_label = ctk.CTkLabel(self.ai_result_frame, text="", font=(self.app.font_family, fs - 1), text_color=theme["text"], wraplength=650, justify="left")

        # ── 재활 치료 추가 ──
        ctk.CTkLabel(self.scroll, text="➕ 재활 치료 추가", font=(self.app.font_family, fs + 2, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(20, 10))

        rehab_types = self.app.db.get_rehab_types()
        types_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        types_frame.pack(fill="x", pady=(0, 15))

        for i, rt in enumerate(rehab_types):
            btn = ctk.CTkButton(
                types_frame,
                text=f"{rt['icon']} {rt['name']}",
                font=(self.app.font_family, fs - 1, "bold"),
                fg_color=theme["card_bg"],
                hover_color=theme["accent_light"],
                text_color=theme["text"],
                border_width=1, border_color=theme["border"],
                height=50, corner_radius=10,
                command=lambda r=rt: self._add_to_today(r),
            )
            btn.grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky="nsew")

        for c in range(3):
            types_frame.columnconfigure(c, weight=1)

        # ── 보호자 커스텀 치료 추가 ──
        ctk.CTkLabel(self.scroll, text="🔧 보호자 맞춤 치료 추가", font=(self.app.font_family, fs + 1, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(15, 10))

        custom_frame = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=12)
        custom_frame.pack(fill="x", pady=(0, 10))

        row1 = ctk.CTkFrame(custom_frame, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(row1, text="이름:", font=(self.app.font_family, fs - 1), text_color=theme["text"]).pack(side="left", padx=(0, 5))
        self.custom_name = ctk.CTkEntry(row1, font=(self.app.font_family, fs - 1), fg_color=theme["bg"], text_color=theme["text"], width=200)
        self.custom_name.pack(side="left", padx=(0, 15))

        ctk.CTkLabel(row1, text="분류:", font=(self.app.font_family, fs - 1), text_color=theme["text"]).pack(side="left", padx=(0, 5))
        self.custom_cat = ctk.CTkComboBox(row1, values=["보행/균형", "근력", "유연성", "소근육", "음성", "유산소", "호흡", "기타"], font=(self.app.font_family, fs - 2), width=130)
        self.custom_cat.pack(side="left")

        row2 = ctk.CTkFrame(custom_frame, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(5, 15))

        ctk.CTkLabel(row2, text="설명:", font=(self.app.font_family, fs - 1), text_color=theme["text"]).pack(side="left", padx=(0, 5))
        self.custom_desc = ctk.CTkEntry(row2, font=(self.app.font_family, fs - 1), fg_color=theme["bg"], text_color=theme["text"], width=300)
        self.custom_desc.pack(side="left", padx=(0, 15))

        ctk.CTkButton(row2, text="추가", font=(self.app.font_family, fs - 1, "bold"), width=80, height=35, command=self._add_custom_rehab).pack(side="left")

    def _create_session_card(self, session):
        theme = self.app.current_theme
        fs = self.app.font_size

        card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=12, border_width=1, border_color=theme["border"], height=70)
        card.pack(fill="x", pady=4)
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=15, pady=10)

        # 왼쪽: 아이콘 + 이름
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="y")

        icon = session["icon"] or "💪"
        completed = session["completed"]
        check = "✅" if completed else "⬜"

        ctk.CTkLabel(left, text=f"{check} {icon} {session['rehab_name']}", font=(self.app.font_family, fs, "bold"), text_color=theme["success"] if completed else theme["text"]).pack(anchor="w")
        ctk.CTkLabel(left, text=session["category"], font=(self.app.font_family, fs - 3), text_color=theme["text_secondary"]).pack(anchor="w")

        # 오른쪽: 완료 버튼
        if not completed:
            btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
            btn_frame.pack(side="right")

            for rating in [1, 2, 3, 4, 5]:
                stars = "⭐" * rating
                ctk.CTkButton(
                    btn_frame, text=str(rating),
                    font=(self.app.font_family, fs - 3),
                    width=35, height=30,
                    fg_color=theme["accent_light"],
                    hover_color=theme["accent"],
                    command=lambda s=session, r=rating: self._complete_session(s["id"], r),
                ).pack(side="left", padx=1)

            ctk.CTkButton(
                btn_frame, text="완료",
                font=(self.app.font_family, fs - 1, "bold"),
                width=60, height=30,
                fg_color=theme["success"],
                command=lambda s=session: self._complete_session(s["id"], 3),
            ).pack(side="left", padx=(5, 0))

    def _add_to_today(self, rehab_type):
        self.app.db.schedule_rehab(1, rehab_type["id"])
        self._show_toast(f"✅ '{rehab_type['name']}' 추가됨")
        self.refresh()

    def _complete_session(self, session_id, rating):
        self.app.db.complete_rehab(session_id, rating)
        self._show_toast(f"✅ 재활 치료 완료! (평가: {rating}/5)")
        self.refresh()

    def _add_custom_rehab(self):
        name = self.custom_name.get().strip()
        if not name:
            self._show_toast("⚠️ 치료 이름을 입력하세요")
            return
        cat = self.custom_cat.get()
        desc = self.custom_desc.get().strip() or name
        self.app.db.add_custom_rehab(name, "🔧", cat, desc, 1, 1)
        self._show_toast(f"✅ '{name}' 커스텀 치료 추가됨")
        self.refresh()

    def _get_ai_recommendation(self):
        theme = self.app.current_theme
        fs = self.app.font_size

        self.ai_result_frame.pack(fill="x", pady=(5, 10))
        self.ai_result_label.pack(padx=20, pady=15)
        self.ai_result_label.configure(text="🔄 AI가 재활 치료를 추천하고 있습니다...")

        # 최근 증상 가져오기
        symptoms = self.app.db.get_symptoms(limit=10)
        symptom_text = "\n".join([f"- {s['category']} (심각도 {s['severity']}/10)" for s in symptoms]) if symptoms else "최근 기록된 증상 없음"

        def on_result(result):
            self.app.db.add_ai_analysis(1, "rehab_recommendation", symptom_text, result)
            self.after(0, lambda: self.ai_result_label.configure(text=f"🤖 AI 재활 추천\n\n{result}"))

        self.app.ai.recommend_rehab(symptom_text, callback=on_result)

    def _toggle_webcam(self):
        import cv2
        from PIL import Image, ImageTk

        if hasattr(self, 'webcam_window') and self.webcam_window is not None and self.webcam_window.winfo_exists():
            self.webcam_window.destroy()
            self.webcam_window = None
            return

        theme = self.app.current_theme
        fs = self.app.font_size

        self.webcam_window = ctk.CTkToplevel(self)
        self.webcam_window.title("거울 모드 (웹캠)")
        self.webcam_window.geometry("680x540")
        self.webcam_window.attributes('-topmost', True)

        lbl = ctk.CTkLabel(self.webcam_window, text="웹캠 로딩 중...", font=(self.app.font_family, fs))
        lbl.pack(fill="both", expand=True, padx=10, pady=10)

        cap = cv2.VideoCapture(0)

        def update_frame():
            if not self.webcam_window.winfo_exists():
                cap.release()
                return

            ret, frame = cap.read()
            if ret:
                frame = cv2.flip(frame, 1)  # 좌우 반전 (거울 모드)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img_tk = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
                lbl.configure(image=img_tk, text="")
                lbl.image = img_tk  # 참조 유지
            else:
                lbl.configure(text="카메라를 찾을 수 없습니다", image="")

            if self.webcam_window.winfo_exists():
                self.webcam_window.after(30, update_frame)

        update_frame()

    def _show_toast(self, msg):
        theme = self.app.current_theme
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.geometry("+500+50")
        toast.configure(fg_color=theme["accent"])
        ctk.CTkLabel(toast, text=msg, font=(self.app.font_family, 14, "bold"), text_color="white").pack(padx=20, pady=10)
        toast.after(2000, toast.destroy)

    def refresh(self):

        for w in self.scroll.winfo_children():
            w.destroy()
        self.scroll.destroy()
        self.build_ui()
