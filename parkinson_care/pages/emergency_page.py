"""
긴급 연락 페이지
"""
import customtkinter as ctk
import os
import platform
from datetime import datetime
from utils.ui import AccessibleScrollableFrame


class EmergencyPage(ctk.CTkFrame):
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
        title = ctk.CTkLabel(self.scroll, text="🚨 긴급 연락", font=(self.app.font_family, fs + 6, "bold"), text_color=theme["danger"])
        title.pack(pady=(0, 5))

        desc = ctk.CTkLabel(self.scroll, text="위급 상황 시 보호자에게 즉시 연락합니다", font=(self.app.font_family, fs - 1), text_color=theme["text_secondary"])
        desc.pack(pady=(0, 20))

        # ── 보호자 정보 카드 ──
        user = self.app.db.get_user()
        guardian_name = user["guardian_name"] if user and user["guardian_name"] else "미등록"
        guardian_phone = user["guardian_phone"] if user and user["guardian_phone"] else "미등록"

        info_card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=15, border_width=1, border_color=theme["border"])
        info_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(info_card, text="👤 보호자 정보", font=(self.app.font_family, fs, "bold"), text_color=theme["text"]).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(info_card, text=f"이름: {guardian_name}", font=(self.app.font_family, fs - 1), text_color=theme["text_secondary"]).pack(anchor="w", padx=20, pady=2)
        ctk.CTkLabel(info_card, text=f"전화: {guardian_phone}", font=(self.app.font_family, fs - 1), text_color=theme["text_secondary"]).pack(anchor="w", padx=20, pady=(2, 15))

        # ── 큰 긴급 버튼 ──
        emergency_btn = ctk.CTkButton(
            self.scroll,
            text="🚨\n긴급 연락하기",
            font=(self.app.font_family, fs + 10, "bold"),
            fg_color=theme["danger"],
            hover_color=theme["danger_hover"],
            width=400, height=200,
            corner_radius=25,
            command=lambda: self._call_emergency(guardian_phone),
        )
        emergency_btn.pack(pady=20)

        # ── 긴급 상황 유형 버튼들 ──
        ctk.CTkLabel(self.scroll, text="상황 유형 선택 (선택 시 긴급 연락)", font=(self.app.font_family, fs - 1, "bold"), text_color=theme["text"]).pack(pady=(10, 10))

        types_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        types_frame.pack(fill="x")

        emergency_types = [
            ("🤕 넘어짐", "넘어짐"),
            ("🦴 심한 경직", "경직"),
            ("😵 어지러움", "어지러움"),
            ("💨 호흡곤란", "호흡곤란"),
            ("⚡ 기타 위급", "기타"),
        ]

        for i, (text, etype) in enumerate(emergency_types):
            btn = ctk.CTkButton(
                types_frame, text=text,
                font=(self.app.font_family, fs, "bold"),
                fg_color=theme["danger_light"],
                hover_color=theme["danger"],
                height=70, corner_radius=12,
                command=lambda e=etype, p=guardian_phone: self._call_emergency(p, e),
            )
            btn.grid(row=i // 3, column=i % 3, padx=6, pady=6, sticky="nsew")

        for c in range(3):
            types_frame.columnconfigure(c, weight=1)

        # ── 긴급 연락 기록 ──
        ctk.CTkLabel(self.scroll, text="📋 최근 긴급 연락 기록", font=(self.app.font_family, fs, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(20, 10))

        logs = self.app.db.get_emergency_logs()
        if logs:
            for log in logs:
                log_frame = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=10, height=40)
                log_frame.pack(fill="x", pady=2)
                log_frame.pack_propagate(False)
                text = f"⏰ {log['logged_at']}  |  {log['emergency_type']}  |  📞 {log['contacted_number']}"
                ctk.CTkLabel(log_frame, text=text, font=(self.app.font_family, fs - 3), text_color=theme["text_secondary"]).pack(anchor="w", padx=15, pady=8)
        else:
            ctk.CTkLabel(self.scroll, text="기록 없음", font=(self.app.font_family, fs - 2), text_color=theme["text_secondary"]).pack(anchor="w", padx=10)

    def _call_emergency(self, phone, emergency_type="긴급"):
        """긴급 전화 발신"""
        if phone and phone != "미등록":
            # 긴급 연락 기록
            self.app.db.log_emergency(1, emergency_type, phone)

            # 전화 연결 (Windows)
            try:
                if platform.system() == "Windows":
                    os.startfile(f"tel:{phone}")
                self._show_called(phone, emergency_type)
            except Exception:
                self._show_called(phone, emergency_type)
        else:
            self._show_no_phone()

    def _show_called(self, phone, etype):
        theme = self.app.current_theme
        fs = self.app.font_size

        popup = ctk.CTkToplevel(self)
        popup.title("긴급 연락")
        popup.geometry("400x250")
        popup.grab_set()
        popup.configure(fg_color=theme["bg"])

        ctk.CTkLabel(popup, text="📞 긴급 연락 발신", font=(self.app.font_family, fs + 4, "bold"), text_color=theme["danger"]).pack(pady=(30, 10))
        ctk.CTkLabel(popup, text=f"보호자 전화번호: {phone}", font=(self.app.font_family, fs), text_color=theme["text"]).pack(pady=5)
        ctk.CTkLabel(popup, text=f"상황: {etype}", font=(self.app.font_family, fs), text_color=theme["text"]).pack(pady=5)
        ctk.CTkLabel(popup, text=f"시간: {datetime.now().strftime('%H:%M:%S')}", font=(self.app.font_family, fs - 1), text_color=theme["text_secondary"]).pack(pady=5)
        ctk.CTkButton(popup, text="확인", font=(self.app.font_family, fs), width=120, height=45, command=popup.destroy).pack(pady=15)

    def _show_no_phone(self):
        theme = self.app.current_theme
        fs = self.app.font_size

        popup = ctk.CTkToplevel(self)
        popup.title("알림")
        popup.geometry("400x200")
        popup.grab_set()
        popup.configure(fg_color=theme["bg"])

        ctk.CTkLabel(popup, text="⚠️ 보호자 전화번호가 등록되지 않았습니다", font=(self.app.font_family, fs, "bold"), text_color=theme["warning"]).pack(pady=(30, 10))
        ctk.CTkLabel(popup, text="설정에서 보호자 정보를 등록해주세요", font=(self.app.font_family, fs - 1), text_color=theme["text_secondary"]).pack(pady=5)
        ctk.CTkButton(popup, text="설정으로 이동", font=(self.app.font_family, fs), width=150, height=45, command=lambda: [popup.destroy(), self.app.show_page("settings")]).pack(pady=15)

    def refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.scroll.destroy()
        self.build_ui()
