"""
파킨슨병 환자 관리 앱 - 메인 진입점
CustomTkinter 기반 데스크탑 앱
"""
import sys
import os

# 모듈 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from config import (
    DEFAULT_FONT_SIZE, DEFAULT_FONT_FAMILY, DEFAULT_THEME,
    THEMES, DISCLAIMER,
)
from database import Database
from ai_engine import AIEngine


class ParkinsonCareApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── 기본 설정 ──
        self.title("🏥 파킨슨 케어 - 환자 관리 시스템")
        self.geometry("1100x750")
        self.minsize(900, 600)

        # 아이콘 (없으면 무시)
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

        # ── DB & AI 초기화 ──
        self.db = Database()
        self.ai = AIEngine()

        # ── 설정 로드 ──
        self.font_size = int(self.db.get_setting("font_size", DEFAULT_FONT_SIZE))
        self.font_family = self.db.get_setting("font_family", DEFAULT_FONT_FAMILY)
        self.theme_name = self.db.get_setting("theme", DEFAULT_THEME)
        self.current_theme = THEMES.get(self.theme_name, THEMES[DEFAULT_THEME])

        # CustomTkinter 모드
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # ── UI 구축 ──
        self.pages = {}
        self.current_page = None
        self._build_layout()
        self.show_page("home")

        # 종료 시 DB 닫기
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self):
        """메인 레이아웃 구축"""
        self.configure(fg_color=self.current_theme["bg"])

        # ── 사이드바 ──
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=self.current_theme["sidebar_bg"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._build_sidebar()

        # ── 메인 컨텐츠 영역 ──
        self.main_area = ctk.CTkFrame(self, fg_color=self.current_theme["bg"], corner_radius=0)
        self.main_area.pack(side="left", fill="both", expand=True)

    def _build_sidebar(self):
        """사이드바 구축"""
        theme = self.current_theme
        fs = self.font_size

        # 로고
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=80)
        logo_frame.pack(fill="x", pady=(15, 5))
        logo_frame.pack_propagate(False)

        ctk.CTkLabel(logo_frame, text="🏥", font=(self.font_family, 28)).pack(pady=(10, 0))
        ctk.CTkLabel(logo_frame, text="파킨슨 케어", font=(self.font_family, fs + 2, "bold"), text_color=theme["sidebar_fg"]).pack()

        # 구분선
        ctk.CTkFrame(self.sidebar, height=2, fg_color=theme["sidebar_sep"]).pack(fill="x", padx=15, pady=10)

        # 네비게이션 버튼
        nav_items = [
            ("🏠", "홈", "home"),
            ("🚨", "긴급 연락", "emergency"),
            ("📋", "증상 업로드", "symptom"),
            ("💪", "재활 치료", "rehab"),
            ("🎤", "음성 검사", "voice"),
            ("📊", "현황 분석", "analysis"),
            ("⚙️", "설정", "settings"),
        ]

        self.nav_buttons = {}
        for icon, label, page_key in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f" {icon}  {label}",
                font=(self.font_family, fs + 1, "bold"),
                fg_color="transparent",
                hover_color=theme["sidebar_hover"],
                text_color=theme["sidebar_fg"],
                anchor="w",
                height=55,
                corner_radius=12,
                command=lambda p=page_key: self.show_page(p),
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[page_key] = btn

        # 하단 면책
        ctk.CTkFrame(self.sidebar, height=1, fg_color="transparent").pack(fill="both", expand=True)

        ver_label = ctk.CTkLabel(self.sidebar, text="v1.0 | 연구·교육용", font=(self.font_family, fs - 5), text_color=theme["sidebar_muted"])
        ver_label.pack(pady=(0, 10))

    def show_page(self, page_key):
        """페이지 전환"""
        # 현재 페이지 제거
        if self.current_page and self.current_page in self.pages:
            self.pages[self.current_page].pack_forget()

        # 페이지 생성 (lazy)
        if page_key not in self.pages:
            self.pages[page_key] = self._create_page(page_key)

        # 페이지 표시
        page = self.pages[page_key]
        page.pack(fill="both", expand=True)

        # 페이지 새로고침
        if hasattr(page, "refresh"):
            page.refresh()

        self.current_page = page_key

        # 네비게이션 버튼 활성화 표시
        for key, btn in self.nav_buttons.items():
            if key == page_key:
                btn.configure(fg_color=self.current_theme["accent"], text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=self.current_theme["sidebar_fg"])

    def _create_page(self, page_key):
        """페이지 인스턴스 생성"""
        if page_key == "home":
            from pages.home_page import HomePage
            return HomePage(self.main_area, self)
        elif page_key == "emergency":
            from pages.emergency_page import EmergencyPage
            return EmergencyPage(self.main_area, self)
        elif page_key == "symptom":
            from pages.symptom_page import SymptomPage
            return SymptomPage(self.main_area, self)
        elif page_key == "rehab":
            from pages.rehab_page import RehabPage
            return RehabPage(self.main_area, self)
        elif page_key == "voice":
            from pages.voice_page import VoicePage
            return VoicePage(self.main_area, self)
        elif page_key == "analysis":
            from pages.analysis_page import AnalysisPage
            return AnalysisPage(self.main_area, self)
        elif page_key == "settings":
            from pages.settings_page import SettingsPage
            return SettingsPage(self.main_area, self)

    # ── 설정 변경 메서드 ──
    def set_font_size(self, size):
        self.font_size = size
        self.db.set_setting("font_size", str(size))

    def set_font_family(self, family):
        self.font_family = family
        self.db.set_setting("font_family", family)
        self._rebuild_all()

    def set_theme(self, theme_name):
        self.theme_name = theme_name
        self.current_theme = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
        self.db.set_setting("theme", theme_name)
        self._rebuild_all()

    def _rebuild_all(self):
        """전체 UI 재구축"""
        # 사이드바 재구축
        self.sidebar.destroy()
        self.main_area.destroy()

        self.pages.clear()
        self.current_page = None

        self._build_layout()
        self.show_page("home")

    def _on_close(self):
        """앱 종료"""
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = ParkinsonCareApp()
    app.mainloop()
