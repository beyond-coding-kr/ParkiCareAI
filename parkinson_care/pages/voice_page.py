"""
음성 분석 페이지 - 파킨슨병 조기 진단 보조
"""
import customtkinter as ctk
import threading
import numpy as np
from datetime import datetime
from utils.ui import AccessibleScrollableFrame


class VoicePage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.is_recording = False
        self.build_ui()

    def build_ui(self):
        self.scroll = AccessibleScrollableFrame(self, app=self.app, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        theme = self.app.current_theme
        fs = self.app.font_size

        # ── 제목 ──
        ctk.CTkLabel(self.scroll, text="🎤 음성 분석", font=(self.app.font_family, fs + 6, "bold"), text_color=theme["text"]).pack(pady=(0, 5))
        ctk.CTkLabel(self.scroll, text="음성 변화를 분석하여 파킨슨병 초기 증상을 확인합니다", font=(self.app.font_family, fs - 1), text_color=theme["text_secondary"]).pack(pady=(0, 10))

        # 면책 조항
        warn_frame = ctk.CTkFrame(self.scroll, fg_color=theme["warning_light"], corner_radius=10, border_width=1, border_color=theme["warning"])
        warn_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(warn_frame, text="⚠️ 이 검사는 참고용이며, 정확한 진단은 전문 의료진 상담이 필요합니다.", font=(self.app.font_family, fs - 2), text_color=theme["warning"], wraplength=600).pack(padx=15, pady=10)

        # ── 녹음 안내 ──
        guide_card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=15, border_width=1, border_color=theme["border"])
        guide_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(guide_card, text="📖 검사 방법", font=(self.app.font_family, fs + 1, "bold"), text_color=theme["text"]).pack(anchor="w", padx=20, pady=(15, 5))
        steps = [
            "1. 조용한 환경에서 마이크를 준비하세요",
            "2. 아래 '녹음 시작' 버튼을 누르세요",
            "3. '아~~' 소리를 5초 동안 일정하게 내세요",
            "4. 녹음이 끝나면 AI가 자동으로 분석합니다",
        ]
        for step in steps:
            ctk.CTkLabel(guide_card, text=step, font=(self.app.font_family, fs - 1), text_color=theme["text_secondary"]).pack(anchor="w", padx=25, pady=1)
        ctk.CTkLabel(guide_card, text="", font=(self.app.font_family, 4)).pack(pady=3)

        # ── 녹음 버튼 ──
        self.record_btn = ctk.CTkButton(
            self.scroll, text="🎙️\n녹음 시작 (5초)",
            font=(self.app.font_family, fs + 4, "bold"),
            fg_color=theme["danger"], hover_color=theme["danger_hover"],
            width=300, height=120, corner_radius=20,
            command=self._start_recording,
        )
        self.record_btn.pack(pady=15)

        self.status_label = ctk.CTkLabel(self.scroll, text="", font=(self.app.font_family, fs, "bold"), text_color=theme["accent"])
        self.status_label.pack(pady=(0, 10))

        # ── 분석 결과 영역 ──
        self.result_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.result_container.pack(fill="x", pady=(10, 10))

        # ── 이전 기록 ──
        ctk.CTkLabel(self.scroll, text="📊 이전 음성 분석 기록", font=(self.app.font_family, fs + 1, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(20, 10))
        self._show_history()

    def _start_recording(self):
        if self.is_recording:
            return

        self.is_recording = True
        self.record_btn.configure(text="🔴\n녹음 중...", fg_color="#C62828")
        self.status_label.configure(text="🎙️ 녹음 중... '아~~' 소리를 내세요")

        # 카운트다운
        self._countdown(5)

    def _countdown(self, seconds):
        if seconds > 0:
            self.status_label.configure(text=f"🎙️ 녹음 중... {seconds}초 남음")
            self.after(1000, lambda: self._countdown(seconds - 1))
        else:
            self.status_label.configure(text="⏳ 분석 중...")
            self._do_record()

    def _do_record(self):
        """실제 녹음 + 분석"""
        theme = self.app.current_theme

        def on_record_done(rec_result):
            if rec_result["status"] == "success":
                self.after(0, lambda: self.status_label.configure(text="🔬 음성 분석 중..."))
                # 분석 시작
                self.app.ai.analyze_voice(rec_result["path"], callback=lambda r: self.after(0, lambda: self._show_results(r, rec_result["path"])))
            else:
                self.after(0, lambda: [
                    self.status_label.configure(text=f"❌ 녹음 실패: {rec_result.get('error', '')}"),
                    self.record_btn.configure(text="🎙️\n녹음 시작 (5초)", fg_color=theme["danger"]),
                ])
                self.is_recording = False

        self.app.ai.record_audio(duration=5, callback=on_record_done)

    def _show_results(self, result, audio_path):
        theme = self.app.current_theme
        fs = self.app.font_size

        self.is_recording = False
        self.record_btn.configure(text="🎙️\n다시 녹음 (5초)", fg_color=theme["danger"])

        # 결과 영역 초기화
        for w in self.result_container.winfo_children():
            w.destroy()

        if result["status"] == "error":
            self.status_label.configure(text="❌ 분석 오류")
            ctk.CTkLabel(self.result_container, text=result["interpretation"], font=(self.app.font_family, fs - 1), text_color=theme["danger"]).pack()
            return

        features = result["features"]
        interpretation = result["interpretation"]

        self.status_label.configure(text="✅ 분석 완료!")

        # DB 저장
        self.app.db.add_voice_analysis(
            1, audio_path, features["jitter"], features["shimmer"], features["hnr"],
            features["mfcc_means"], interpretation, features["risk_level"]
        )

        # ── 수치 카드 ──
        metrics_card = ctk.CTkFrame(self.result_container, fg_color=theme["card_bg"], corner_radius=15, border_width=1, border_color=theme["border"])
        metrics_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(metrics_card, text="📊 분석 수치", font=(self.app.font_family, fs + 1, "bold"), text_color=theme["text"]).pack(anchor="w", padx=20, pady=(15, 10))

        metrics_frame = ctk.CTkFrame(metrics_card, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=20, pady=(0, 15))

        metrics = [
            ("Jitter\n(주파수 변동)", f"{features['jitter']:.4f}%", "< 1.0%", features["jitter"] < 1.0),
            ("Shimmer\n(진폭 변동)", f"{features['shimmer']:.4f}%", "< 3.0%", features["shimmer"] < 3.0),
            ("HNR\n(조음대잡음비)", f"{features['hnr']:.2f} dB", "> 20 dB", features["hnr"] > 20),
            ("기본 주파수\n(F0)", f"{features['f0_mean']:.1f} Hz", "-", True),
            ("위험도", features["risk_level"], "-", features["risk_level"] == "낮음"),
        ]

        for i, (name, value, normal, is_normal) in enumerate(metrics):
            m_frame = ctk.CTkFrame(metrics_frame, fg_color=theme["bg"], corner_radius=10)
            m_frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

            color = theme["success"] if is_normal else theme["danger"]
            ctk.CTkLabel(m_frame, text=name, font=(self.app.font_family, fs - 3), text_color=theme["text_secondary"]).pack(padx=10, pady=(8, 2))
            ctk.CTkLabel(m_frame, text=value, font=(self.app.font_family, fs, "bold"), text_color=color).pack(padx=10)
            ctk.CTkLabel(m_frame, text=f"정상: {normal}", font=(self.app.font_family, fs - 4), text_color=theme["text_secondary"]).pack(padx=10, pady=(0, 8))

        for c in range(5):
            metrics_frame.columnconfigure(c, weight=1)

        # ── AI 해석 ──
        ai_card = ctk.CTkFrame(self.result_container, fg_color=theme["card_bg"], corner_radius=15, border_width=1, border_color=theme["border"])
        ai_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(ai_card, text="🤖 AI 종합 해석", font=(self.app.font_family, fs + 1, "bold"), text_color=theme["text"]).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(ai_card, text=interpretation, font=(self.app.font_family, fs - 1), text_color=theme["text"], wraplength=650, justify="left").pack(padx=20, pady=(5, 15))

    def _show_history(self):
        theme = self.app.current_theme
        fs = self.app.font_size

        analyses = self.app.db.get_voice_analyses(limit=5)
        if not analyses:
            ctk.CTkLabel(self.scroll, text="아직 음성 분석 기록이 없습니다", font=(self.app.font_family, fs - 2), text_color=theme["text_secondary"]).pack(anchor="w", padx=10)
            return

        for a in analyses:
            card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=10, border_width=1, border_color=theme["border"])
            card.pack(fill="x", pady=3)

            risk_color = theme["success"] if a["risk_level"] == "낮음" else theme["warning"] if a["risk_level"] == "보통" else theme["danger"]
            text = f"📅 {a['analyzed_at']}  |  Jitter: {a['jitter']:.4f}%  |  Shimmer: {a['shimmer']:.4f}%  |  HNR: {a['hnr']:.2f}dB  |  위험도: {a['risk_level']}"
            ctk.CTkLabel(card, text=text, font=(self.app.font_family, fs - 3), text_color=risk_color).pack(anchor="w", padx=15, pady=8)

        # 추이 그래프 (데이터 충분할 때)
        if len(analyses) >= 2:
            self._show_trend_chart(analyses)

    def _show_trend_chart(self, analyses):
        theme = self.app.current_theme
        fs = self.app.font_size

        try:
            from utils.charts import create_line_chart

            dates = [a["analyzed_at"][:10] for a in reversed(analyses)]
            jitters = [a["jitter"] for a in reversed(analyses)]
            shimmers = [a["shimmer"] for a in reversed(analyses)]

            ctk.CTkLabel(self.scroll, text="📈 음성 수치 변화 추이", font=(self.app.font_family, fs, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(15, 5))

            chart_frame = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=12)
            chart_frame.pack(fill="x", pady=5)

            widget, fig = create_line_chart(
                chart_frame, dates, [jitters, shimmers],
                title="음성 분석 추이", xlabel="날짜", ylabel="수치 (%)",
                labels=["Jitter", "Shimmer"],
                bg_color=theme["card_bg"], text_color=theme["text"],
            )
            widget.pack(fill="x", padx=10, pady=10)
        except Exception:
            pass

    def refresh(self):

        for w in self.scroll.winfo_children():
            w.destroy()
        self.scroll.destroy()
        self.is_recording = False
        self.build_ui()
