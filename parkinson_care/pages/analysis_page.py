"""
현황 분석 페이지 - 증상/재활/AI 분석 현황 (그래프 및 표)
"""
import customtkinter as ctk
from datetime import datetime
from utils.ui import AccessibleScrollableFrame


class AnalysisPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.period_days = 30
        self.charts = []  # (widget, fig) 쌍 저장
        self.build_ui()

    def build_ui(self):
        self.scroll = AccessibleScrollableFrame(self, app=self.app, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        theme = self.app.current_theme
        fs = self.app.font_size

        # ── 제목 ──
        ctk.CTkLabel(self.scroll, text="📊 현황 분석", font=(self.app.font_family, fs + 6, "bold"), text_color=theme["text"]).pack(pady=(0, 5))
        ctk.CTkLabel(self.scroll, text="증상, 재활 치료, AI 분석 현황을 한눈에 확인합니다", font=(self.app.font_family, fs - 1), text_color=theme["text_secondary"]).pack(pady=(0, 15))

        # ── 기간 선택 ──
        period_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        period_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(period_frame, text="📅 기간:", font=(self.app.font_family, fs, "bold"), text_color=theme["text"]).pack(side="left", padx=(0, 10))

        self.period_btns = []
        for days, label in [(7, "1주"), (30, "1개월"), (90, "3개월"), (365, "전체")]:
            btn = ctk.CTkButton(
                period_frame, text=label,
                font=(self.app.font_family, fs - 1),
                width=70, height=35, corner_radius=8,
                fg_color=theme["accent"] if days == self.period_days else theme["card_bg"],
                text_color="white" if days == self.period_days else theme["text"],
                command=lambda d=days: self._set_period(d),
            )
            btn.pack(side="left", padx=3)
            self.period_btns.append((btn, days))

        # ── AI 효과 분석 버튼 ──
        ctk.CTkButton(
            self.scroll, text="🤖 AI 종합 효과 분석",
            font=(self.app.font_family, fs, "bold"),
            fg_color="#8E24AA", hover_color="#6A1B9A",
            height=45, corner_radius=10,
            command=self._run_ai_analysis,
        ).pack(fill="x", pady=(0, 15))

        self.ai_frame = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=12)
        self.ai_label = ctk.CTkLabel(self.ai_frame, text="", font=(self.app.font_family, fs - 1), text_color=theme["text"], wraplength=650, justify="left")

        # ── 증상 현황 ──
        self._create_symptom_section()

        # ── 재활 치료 현황 ──
        self._create_rehab_section()

        # ── AI 분석 기록 ──
        self._create_ai_history_section()

    def _set_period(self, days):
        self.period_days = days
        self.refresh()

    def _create_symptom_section(self):
        theme = self.app.current_theme
        fs = self.app.font_size

        ctk.CTkLabel(self.scroll, text="📋 증상 현황", font=(self.app.font_family, fs + 2, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(10, 10))

        stats = self.app.db.get_symptom_stats(days=self.period_days)

        if not stats:
            ctk.CTkLabel(self.scroll, text="해당 기간에 기록된 증상이 없습니다", font=(self.app.font_family, fs - 2), text_color=theme["text_secondary"]).pack(anchor="w", padx=10, pady=5)
            return

        # 표
        table_card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=12, border_width=1, border_color=theme["border"])
        table_card.pack(fill="x", pady=(0, 10))

        # 헤더
        header = ctk.CTkFrame(table_card, fg_color=theme["accent_light"], corner_radius=0)
        header.pack(fill="x")
        for col, text in enumerate(["증상", "횟수", "평균 심각도"]):
            ctk.CTkLabel(header, text=text, font=(self.app.font_family, fs - 2, "bold"), text_color=theme["text"], width=180).grid(row=0, column=col, padx=10, pady=8)

        # 데이터
        for i, s in enumerate(stats):
            row_frame = ctk.CTkFrame(table_card, fg_color="transparent" if i % 2 == 0 else theme["bg"], corner_radius=0)
            row_frame.pack(fill="x")
            ctk.CTkLabel(row_frame, text=s["category"], font=(self.app.font_family, fs - 2), text_color=theme["text"], width=180).grid(row=0, column=0, padx=10, pady=5)
            ctk.CTkLabel(row_frame, text=str(s["cnt"]), font=(self.app.font_family, fs - 2, "bold"), text_color=theme["accent"], width=180).grid(row=0, column=1, padx=10, pady=5)
            avg = s["avg_sev"]
            sev_color = theme["success"] if avg <= 3 else theme["warning"] if avg <= 6 else theme["danger"]
            ctk.CTkLabel(row_frame, text=f"{avg:.1f}/10", font=(self.app.font_family, fs - 2, "bold"), text_color=sev_color, width=180).grid(row=0, column=2, padx=10, pady=5)

        # 차트
        try:
            from utils.charts import create_bar_chart
            data = [(s["category"][:4], s["cnt"]) for s in stats]
            chart_frame = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=12)
            chart_frame.pack(fill="x", pady=5)
            widget, fig = create_bar_chart(chart_frame, data, title="증상별 빈도", ylabel="횟수", bg_color=theme["card_bg"], text_color=theme["text"])
            widget.pack(fill="x", padx=10, pady=10)
            self.charts.append((widget, fig))
        except Exception:
            pass

    def _create_rehab_section(self):
        theme = self.app.current_theme
        fs = self.app.font_size

        ctk.CTkLabel(self.scroll, text="💪 재활 치료 현황", font=(self.app.font_family, fs + 2, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(20, 10))

        stats = self.app.db.get_rehab_stats(days=self.period_days)

        if not stats:
            ctk.CTkLabel(self.scroll, text="해당 기간에 기록된 재활 치료가 없습니다", font=(self.app.font_family, fs - 2), text_color=theme["text_secondary"]).pack(anchor="w", padx=10, pady=5)
            return

        # 표
        table_card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=12, border_width=1, border_color=theme["border"])
        table_card.pack(fill="x", pady=(0, 10))

        header = ctk.CTkFrame(table_card, fg_color=theme["success_light"], corner_radius=0)
        header.pack(fill="x")
        for col, text in enumerate(["치료명", "분류", "예정", "완료", "평균 평점"]):
            ctk.CTkLabel(header, text=text, font=(self.app.font_family, fs - 2, "bold"), text_color=theme["text"], width=120).grid(row=0, column=col, padx=5, pady=8)

        for i, s in enumerate(stats):
            row_frame = ctk.CTkFrame(table_card, fg_color="transparent" if i % 2 == 0 else theme["bg"], corner_radius=0)
            row_frame.pack(fill="x")
            ctk.CTkLabel(row_frame, text=s["name"], font=(self.app.font_family, fs - 3), text_color=theme["text"], width=120).grid(row=0, column=0, padx=5, pady=4)
            ctk.CTkLabel(row_frame, text=s["category"], font=(self.app.font_family, fs - 3), text_color=theme["text_secondary"], width=120).grid(row=0, column=1, padx=5, pady=4)
            ctk.CTkLabel(row_frame, text=str(s["total"]), font=(self.app.font_family, fs - 3), text_color=theme["text"], width=120).grid(row=0, column=2, padx=5, pady=4)
            done = s["done"] or 0
            ctk.CTkLabel(row_frame, text=str(done), font=(self.app.font_family, fs - 3, "bold"), text_color=theme["success"], width=120).grid(row=0, column=3, padx=5, pady=4)
            rating = s["avg_rating"]
            rating_text = f"{rating:.1f}/5 ⭐" if rating else "-"
            ctk.CTkLabel(row_frame, text=rating_text, font=(self.app.font_family, fs - 3), text_color=theme["warning"], width=120).grid(row=0, column=4, padx=5, pady=4)

        # 파이 차트
        try:
            from utils.charts import create_pie_chart
            data = [(s["name"][:6], s["done"] or 0) for s in stats if (s["done"] or 0) > 0]
            if data:
                chart_frame = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=12)
                chart_frame.pack(fill="x", pady=5)
                widget, fig = create_pie_chart(chart_frame, data, title="재활 치료 완료 비율", bg_color=theme["card_bg"], text_color=theme["text"])
                widget.pack(fill="x", padx=10, pady=10)
                self.charts.append((widget, fig))
        except Exception:
            pass

    def _create_ai_history_section(self):
        theme = self.app.current_theme
        fs = self.app.font_size

        ctk.CTkLabel(self.scroll, text="🤖 AI 분석 기록", font=(self.app.font_family, fs + 2, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(20, 10))

        analyses = self.app.db.get_ai_analyses(limit=5)
        if not analyses:
            ctk.CTkLabel(self.scroll, text="아직 AI 분석 기록이 없습니다", font=(self.app.font_family, fs - 2), text_color=theme["text_secondary"]).pack(anchor="w", padx=10, pady=5)
            return

        for a in analyses:
            card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=10, border_width=1, border_color=theme["border"])
            card.pack(fill="x", pady=3)

            ctk.CTkLabel(card, text=f"📅 {a['analyzed_at']}  |  유형: {a['analysis_type']}", font=(self.app.font_family, fs - 3, "bold"), text_color=theme["accent"]).pack(anchor="w", padx=15, pady=(8, 2))

            result_text = a["result"][:200] + "..." if len(a["result"]) > 200 else a["result"]
            ctk.CTkLabel(card, text=result_text, font=(self.app.font_family, fs - 3), text_color=theme["text_secondary"], wraplength=600, justify="left").pack(anchor="w", padx=15, pady=(0, 8))

    def _run_ai_analysis(self):
        theme = self.app.current_theme

        self.ai_frame.pack(fill="x", pady=(0, 15))
        self.ai_label.pack(padx=20, pady=15)
        self.ai_label.configure(text="🔄 AI가 종합 분석 중...")

        # 데이터 수집
        symptom_stats = self.app.db.get_symptom_stats(days=self.period_days)
        rehab_stats = self.app.db.get_rehab_stats(days=self.period_days)

        s_text = "\n".join([f"- {s['category']}: {s['cnt']}회 (평균 심각도 {s['avg_sev']:.1f}/10)" for s in symptom_stats]) if symptom_stats else "증상 기록 없음"
        r_text = "\n".join([f"- {s['name']}: 예정 {s['total']}회, 완료 {s['done'] or 0}회" for s in rehab_stats]) if rehab_stats else "재활 기록 없음"

        def on_result(result):
            self.app.db.add_ai_analysis(1, "progress_analysis", f"증상:\n{s_text}\n\n재활:\n{r_text}", result)
            self.after(0, lambda: self.ai_label.configure(text=f"🤖 AI 종합 분석\n\n{result}"))

        self.app.ai.analyze_rehab_progress(r_text, s_text, callback=on_result)

    def refresh(self):
        # 차트 정리
        from utils.charts import destroy_chart
        for widget, fig in self.charts:
            try:
                destroy_chart(widget, fig)
            except Exception:
                pass
        self.charts.clear()



        for w in self.scroll.winfo_children():
            w.destroy()
        self.scroll.destroy()
        self.build_ui()
