"""
증상 업로드 페이지
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from config import SYMPTOM_CATEGORIES
from utils.ui import AccessibleScrollableFrame


class SymptomPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.selected_category = None
        self.severity = 5
        self.media_path = ""
        self.media_type = ""
        self.build_ui()

    def build_ui(self):
        self.scroll = AccessibleScrollableFrame(self, app=self.app, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        theme = self.app.current_theme
        fs = self.app.font_size

        # ── 제목 ──
        ctk.CTkLabel(self.scroll, text="📋 증상 업로드", font=(self.app.font_family, fs + 6, "bold"), text_color=theme["text"]).pack(pady=(0, 5))
        ctk.CTkLabel(self.scroll, text="현재 증상을 기록하여 AI가 분석합니다", font=(self.app.font_family, fs - 1), text_color=theme["text_secondary"]).pack(pady=(0, 20))

        # ── 증상 카테고리 선택 ──
        ctk.CTkLabel(self.scroll, text="1. 증상 종류 선택", font=(self.app.font_family, fs + 1, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(0, 10))

        cat_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        cat_frame.pack(fill="x", pady=(0, 15))

        self.cat_buttons = []
        for i, cat in enumerate(SYMPTOM_CATEGORIES):
            btn = ctk.CTkButton(
                cat_frame,
                text=f"{cat['icon']} {cat['name']}",
                font=(self.app.font_family, fs, "bold"),
                fg_color=theme["card_bg"],
                hover_color=theme["accent_light"],
                text_color=theme["text"],
                border_width=2,
                border_color=theme["border"],
                width=140, height=60,
                corner_radius=12,
                command=lambda c=cat, idx=i: self._select_category(c, idx),
            )
            btn.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky="nsew")
            self.cat_buttons.append(btn)

        for c in range(4):
            cat_frame.columnconfigure(c, weight=1)

        # ── 심각도 슬라이더 ──
        ctk.CTkLabel(self.scroll, text="2. 심각도 (1~10)", font=(self.app.font_family, fs + 1, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(10, 5))

        sev_frame = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=12)
        sev_frame.pack(fill="x", pady=(0, 15))

        self.sev_label = ctk.CTkLabel(sev_frame, text="5", font=(self.app.font_family, fs + 4, "bold"), text_color=theme["accent"])
        self.sev_label.pack(pady=(10, 0))

        self.sev_slider = ctk.CTkSlider(
            sev_frame, from_=1, to=10, number_of_steps=9,
            width=400, height=25,
            progress_color=theme["accent"],
            button_color=theme["accent"],
            command=self._on_severity_change,
        )
        self.sev_slider.set(5)
        self.sev_slider.pack(padx=30, pady=(5, 5))

        sev_labels = ctk.CTkFrame(sev_frame, fg_color="transparent")
        sev_labels.pack(fill="x", padx=30, pady=(0, 10))
        ctk.CTkLabel(sev_labels, text="약함", font=(self.app.font_family, fs - 3), text_color=theme["text_secondary"]).pack(side="left")
        ctk.CTkLabel(sev_labels, text="심함", font=(self.app.font_family, fs - 3), text_color=theme["text_secondary"]).pack(side="right")

        # ── 상세 설명 ──
        ctk.CTkLabel(self.scroll, text="3. 상세 설명 (선택)", font=(self.app.font_family, fs + 1, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(10, 5))

        self.desc_text = ctk.CTkTextbox(self.scroll, height=100, font=(self.app.font_family, fs - 1), fg_color=theme["card_bg"], text_color=theme["text"], corner_radius=12)
        self.desc_text.pack(fill="x", pady=(0, 15))

        # ── 미디어 첨부 ──
        ctk.CTkLabel(self.scroll, text="4. 사진/동영상 첨부 (선택)", font=(self.app.font_family, fs + 1, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(10, 5))

        media_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        media_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkButton(
            media_frame, text="📸 사진 촬영",
            font=(self.app.font_family, fs, "bold"),
            fg_color=theme["accent"], height=55, corner_radius=12,
            command=self._capture_photo,
        ).pack(side="left", padx=(0, 10), expand=True, fill="x")

        ctk.CTkButton(
            media_frame, text="🎥 동영상 촬영",
            font=(self.app.font_family, fs, "bold"),
            fg_color="#8E24AA", height=55, corner_radius=12,
            command=self._capture_video,
        ).pack(side="left", padx=(0, 10), expand=True, fill="x")

        ctk.CTkButton(
            media_frame, text="📁 파일 선택",
            font=(self.app.font_family, fs, "bold"),
            fg_color=theme["text_secondary"], height=55, corner_radius=12,
            command=self._select_file,
        ).pack(side="left", expand=True, fill="x")

        self.media_label = ctk.CTkLabel(self.scroll, text="첨부 파일 없음", font=(self.app.font_family, fs - 2), text_color=theme["text_secondary"])
        self.media_label.pack(anchor="w", pady=(0, 15))

        # ── 제출 버튼 ──
        ctk.CTkButton(
            self.scroll, text="✅ 증상 업로드 및 AI 분석",
            font=(self.app.font_family, fs + 2, "bold"),
            fg_color=theme["success"], hover_color="#2E7D32",
            height=65, corner_radius=15,
            command=self._submit,
        ).pack(fill="x", pady=(10, 10))

        # ── AI 분석 결과 표시 영역 ──
        self.result_frame = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=15)
        self.result_label = ctk.CTkLabel(self.result_frame, text="", font=(self.app.font_family, fs - 1), text_color=theme["text"], wraplength=650, justify="left")

        # ── 최근 증상 기록 ──
        ctk.CTkLabel(self.scroll, text="📜 최근 증상 기록", font=(self.app.font_family, fs + 1, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(20, 10))
        self._show_recent_symptoms()

    def _select_category(self, cat, idx):
        theme = self.app.current_theme
        self.selected_category = cat["name"]
        for i, btn in enumerate(self.cat_buttons):
            if i == idx:
                btn.configure(fg_color=theme["accent"], text_color="white", border_color=theme["accent"])
            else:
                btn.configure(fg_color=theme["card_bg"], text_color=theme["text"], border_color=theme["border"])

    def _on_severity_change(self, val):
        self.severity = int(val)
        self.sev_label.configure(text=str(self.severity))
        theme = self.app.current_theme
        if self.severity <= 3:
            color = theme["success"]
        elif self.severity <= 6:
            color = theme["warning"]
        else:
            color = theme["danger"]
        self.sev_label.configure(text_color=color)

    def _capture_photo(self):
        from utils.camera import CameraUtil
        cam = CameraUtil()

        def on_done(result):
            if result["status"] == "success":
                self.media_path = result["path"]
                self.media_type = "photo"
                self.after(0, lambda: self.media_label.configure(text=f"📸 사진 첨부됨: {result['path'][-30:]}"))
            else:
                self.after(0, lambda: self.media_label.configure(text=f"❌ {result.get('error', '촬영 실패')}"))

        cam.capture_photo(callback=on_done)
        self.media_label.configure(text="📸 촬영 중...")

    def _capture_video(self):
        """간단 동영상 촬영 (5초)"""
        from utils.camera import CameraUtil
        import threading

        cam = CameraUtil()
        path = cam.start_video()
        if path:
            self.media_label.configure(text="🎥 녹화 중... (5초)")

            def stop():
                import time
                time.sleep(5)
                final_path = cam.stop_video()
                self.media_path = final_path or ""
                self.media_type = "video"
                self.after(0, lambda: self.media_label.configure(text=f"🎥 동영상 첨부됨: {(final_path or '')[-30:]}"))

            threading.Thread(target=stop, daemon=True).start()
        else:
            self.media_label.configure(text="❌ 카메라를 열 수 없습니다")

    def _select_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("이미지/동영상", "*.jpg *.jpeg *.png *.mp4 *.avi *.mov"), ("모든 파일", "*.*")]
        )
        if path:
            self.media_path = path
            ext = path.lower().split(".")[-1]
            self.media_type = "video" if ext in ("mp4", "avi", "mov") else "photo"
            self.media_label.configure(text=f"📁 파일 선택됨: {path[-40:]}")

    def _submit(self):
        theme = self.app.current_theme
        fs = self.app.font_size

        if not self.selected_category:
            self._show_toast("⚠️ 증상 종류를 선택해주세요")
            return

        desc = self.desc_text.get("1.0", "end").strip()

        # DB 저장
        self.app.db.add_symptom(
            user_id=1,
            category=self.selected_category,
            severity=self.severity,
            description=desc,
            media_path=self.media_path,
            media_type=self.media_type,
        )

        # AI 분석 요청
        symptom_text = f"증상: {self.selected_category}\n심각도: {self.severity}/10\n상세: {desc or '없음'}"

        self.result_frame.pack(fill="x", pady=(10, 10))
        self.result_label.pack(padx=20, pady=15)
        self.result_label.configure(text="🔄 AI 분석 중... 잠시 기다려주세요...")

        def on_ai_result(result):
            self.app.db.add_ai_analysis(1, "symptom", symptom_text, result)
            self.after(0, lambda: self.result_label.configure(text=f"🤖 AI 분석 결과\n\n{result}"))

        self.app.ai.analyze_symptoms(symptom_text, callback=on_ai_result)
        self._show_toast("✅ 증상이 기록되었습니다")

    def _show_recent_symptoms(self):
        theme = self.app.current_theme
        fs = self.app.font_size

        symptoms = self.app.db.get_symptoms(limit=5)
        if not symptoms:
            ctk.CTkLabel(self.scroll, text="아직 기록된 증상이 없습니다", font=(self.app.font_family, fs - 2), text_color=theme["text_secondary"]).pack(anchor="w", padx=10)
            return

        for s in symptoms:
            card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=10, border_width=1, border_color=theme["border"])
            card.pack(fill="x", pady=3)

            sev_color = theme["success"] if s["severity"] <= 3 else theme["warning"] if s["severity"] <= 6 else theme["danger"]
            text = f"📌 {s['category']}  |  심각도: {s['severity']}/10  |  {s['recorded_at']}"
            ctk.CTkLabel(card, text=text, font=(self.app.font_family, fs - 3), text_color=sev_color).pack(anchor="w", padx=15, pady=8)

    def _show_toast(self, msg):
        theme = self.app.current_theme
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.geometry("+500+50")
        toast.configure(fg_color=theme["accent"])
        lbl = ctk.CTkLabel(toast, text=msg, font=(self.app.font_family, 14, "bold"), text_color="white")
        lbl.pack(padx=20, pady=10)
        toast.after(2000, toast.destroy)

    def refresh(self):

        for w in self.scroll.winfo_children():
            w.destroy()
        self.scroll.destroy()
        self.selected_category = None
        self.media_path = ""
        self.media_type = ""
        self.build_ui()
