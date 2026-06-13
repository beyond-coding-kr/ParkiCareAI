"""
설정 페이지 - 폰트, 배경색, 사용자 정보
"""
import customtkinter as ctk
from config import AVAILABLE_FONTS, THEMES, MIN_FONT_SIZE, MAX_FONT_SIZE
from utils.ui import AccessibleScrollableFrame


class SettingsPage(ctk.CTkFrame):
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
        ctk.CTkLabel(self.scroll, text="⚙️ 설정", font=(self.app.font_family, fs + 6, "bold"), text_color=theme["text"]).pack(pady=(0, 20))

        # ══════════════════════════════
        # 1. 사용자 정보
        # ══════════════════════════════
        self._section_title("👤 사용자 정보")

        user_card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=15, border_width=1, border_color=theme["border"])
        user_card.pack(fill="x", pady=(0, 20))

        user = self.app.db.get_user()

        fields = [
            ("환자 이름", "name", user["name"] if user else ""),
            ("환자 전화번호", "phone", user["phone"] if user and user["phone"] else ""),
            ("보호자 이름", "guardian_name", user["guardian_name"] if user and user["guardian_name"] else ""),
            ("보호자 전화번호", "guardian_phone", user["guardian_phone"] if user and user["guardian_phone"] else ""),
        ]

        self.user_entries = {}
        for label, key, value in fields:
            row = ctk.CTkFrame(user_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=5)

            ctk.CTkLabel(row, text=label, font=(self.app.font_family, fs - 1), text_color=theme["text"], width=140, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, font=(self.app.font_family, fs - 1), fg_color=theme["bg"], text_color=theme["text"], width=250, height=38)
            entry.insert(0, value)
            entry.pack(side="left", padx=(10, 0))
            self.user_entries[key] = entry

        ctk.CTkButton(user_card, text="💾 사용자 정보 저장", font=(self.app.font_family, fs, "bold"), fg_color=theme["accent"], height=45, corner_radius=10, command=self._save_user).pack(padx=20, pady=15)

        # ══════════════════════════════
        # 2. 글꼴 크기
        # ══════════════════════════════
        self._section_title("🔤 글꼴 크기")

        font_size_card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=15, border_width=1, border_color=theme["border"])
        font_size_card.pack(fill="x", pady=(0, 20))

        self.font_size_label = ctk.CTkLabel(font_size_card, text=f"현재: {fs}pt", font=(self.app.font_family, fs + 2, "bold"), text_color=theme["accent"])
        self.font_size_label.pack(pady=(15, 5))

        preview_text = "가나다라마바사 - 글꼴 미리보기"
        self.font_preview = ctk.CTkLabel(font_size_card, text=preview_text, font=(self.app.font_family, fs), text_color=theme["text"])
        self.font_preview.pack(pady=5)

        self.font_slider = ctk.CTkSlider(
            font_size_card, from_=MIN_FONT_SIZE, to=MAX_FONT_SIZE,
            number_of_steps=MAX_FONT_SIZE - MIN_FONT_SIZE,
            width=400, height=25,
            progress_color=theme["accent"], button_color=theme["accent"],
            command=self._on_font_size_change,
        )
        self.font_slider.set(fs)
        self.font_slider.pack(padx=30, pady=5)

        size_labels = ctk.CTkFrame(font_size_card, fg_color="transparent")
        size_labels.pack(fill="x", padx=30, pady=(0, 15))
        ctk.CTkLabel(size_labels, text=f"{MIN_FONT_SIZE}pt", font=(self.app.font_family, fs - 3), text_color=theme["text_secondary"]).pack(side="left")
        ctk.CTkLabel(size_labels, text=f"{MAX_FONT_SIZE}pt", font=(self.app.font_family, fs - 3), text_color=theme["text_secondary"]).pack(side="right")

        # ══════════════════════════════
        # 3. 글꼴 종류
        # ══════════════════════════════
        self._section_title("✏️ 글꼴 종류")

        font_family_card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=15, border_width=1, border_color=theme["border"])
        font_family_card.pack(fill="x", pady=(0, 20))

        self.font_btns = []
        fonts_frame = ctk.CTkFrame(font_family_card, fg_color="transparent")
        fonts_frame.pack(padx=20, pady=15)

        for i, font_name in enumerate(AVAILABLE_FONTS):
            is_active = font_name == self.app.font_family
            btn = ctk.CTkButton(
                fonts_frame,
                text=f"가나다 ({font_name})",
                font=(font_name, fs - 1),
                fg_color=theme["accent"] if is_active else theme["bg"],
                text_color="white" if is_active else theme["text"],
                hover_color=theme["accent_hover"],
                height=45, corner_radius=10,
                command=lambda f=font_name: self._set_font_family(f),
            )
            btn.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="nsew")
            self.font_btns.append((btn, font_name))

        for c in range(3):
            fonts_frame.columnconfigure(c, weight=1)

        # ══════════════════════════════
        # 4. 배경색 테마
        # ══════════════════════════════
        self._section_title("🎨 배경색 테마")

        theme_card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=15, border_width=1, border_color=theme["border"])
        theme_card.pack(fill="x", pady=(0, 20))

        themes_frame = ctk.CTkFrame(theme_card, fg_color="transparent")
        themes_frame.pack(padx=20, pady=15)

        for i, (tname, tdata) in enumerate(THEMES.items()):
            is_active = tname == self.app.theme_name
            t_frame = ctk.CTkFrame(themes_frame, fg_color="transparent")
            t_frame.grid(row=0, column=i, padx=8, pady=5)

            # 미리보기 색상 블록
            preview = ctk.CTkFrame(t_frame, fg_color=tdata["bg"], width=80, height=50, corner_radius=10, border_width=3, border_color=theme["accent"] if is_active else tdata["border"])
            preview.pack()
            preview.pack_propagate(False)

            inner = ctk.CTkFrame(preview, fg_color=tdata["sidebar_bg"], width=25, height=40, corner_radius=5)
            inner.place(x=5, y=5)

            ctk.CTkButton(
                t_frame, text=tname,
                font=(self.app.font_family, fs - 3, "bold" if is_active else "normal"),
                fg_color="transparent", hover_color=theme["accent_light"],
                text_color=theme["accent"] if is_active else theme["text"],
                width=90, height=30,
                command=lambda tn=tname: self._set_theme(tn),
            ).pack(pady=(5, 0))

        # ══════════════════════════════
        # 5. 모드 전환
        # ══════════════════════════════
        self._section_title("🔄 모드 전환")

        mode_card = ctk.CTkFrame(self.scroll, fg_color=theme["card_bg"], corner_radius=15, border_width=1, border_color=theme["border"])
        mode_card.pack(fill="x", pady=(0, 20))

        mode_frame = ctk.CTkFrame(mode_card, fg_color="transparent")
        mode_frame.pack(padx=20, pady=15)

        current_mode = self.app.db.get_setting("mode", "patient")

        for mode, label, icon, color in [("patient", "환자 모드", "🏥", theme["accent"]), ("guardian", "보호자 모드", "👨‍⚕️", theme["success"])]:
            is_active = mode == current_mode
            ctk.CTkButton(
                mode_frame, text=f"{icon} {label}",
                font=(self.app.font_family, fs, "bold"),
                fg_color=color if is_active else theme["bg"],
                text_color="white" if is_active else theme["text"],
                hover_color=color, width=200, height=55, corner_radius=12,
                command=lambda m=mode: self._set_mode(m),
            ).pack(side="left", padx=10)

        # ══════════════════════════════
        # 6. 데이터 관리
        # ══════════════════════════════
        self._section_title("🗄️ 데이터 관리")

        ctk.CTkButton(
            self.scroll, text="🗑️ 모든 데이터 초기화",
            font=(self.app.font_family, fs, "bold"),
            fg_color=theme["danger"], hover_color=theme["danger_hover"],
            height=45, corner_radius=10,
            command=self._confirm_reset,
        ).pack(fill="x", pady=(0, 20))

    def _section_title(self, text):
        theme = self.app.current_theme
        fs = self.app.font_size
        ctk.CTkLabel(self.scroll, text=text, font=(self.app.font_family, fs + 1, "bold"), text_color=theme["text"]).pack(anchor="w", pady=(10, 5))

    def _save_user(self):
        data = {k: v.get().strip() for k, v in self.user_entries.items()}
        self.app.db.update_user(1, **data)
        self._show_toast("✅ 사용자 정보가 저장되었습니다")

    def _on_font_size_change(self, val):
        size = int(val)
        self.font_size_label.configure(text=f"현재: {size}pt")
        self.font_preview.configure(font=(self.app.font_family, size))
        self.app.set_font_size(size)

    def _set_font_family(self, font_name):
        self.app.set_font_family(font_name)
        self.refresh()

    def _set_theme(self, theme_name):
        self.app.set_theme(theme_name)
        self.refresh()

    def _set_mode(self, mode):
        self.app.db.set_setting("mode", mode)
        self._show_toast(f"✅ {'환자' if mode == 'patient' else '보호자'} 모드로 전환되었습니다")
        self.refresh()

    def _confirm_reset(self):
        theme = self.app.current_theme
        fs = self.app.font_size

        popup = ctk.CTkToplevel(self)
        popup.title("데이터 초기화")
        popup.geometry("400x200")
        popup.grab_set()
        popup.configure(fg_color=theme["bg"])

        ctk.CTkLabel(popup, text="⚠️ 정말 모든 데이터를 초기화하시겠습니까?", font=(self.app.font_family, fs, "bold"), text_color=theme["danger"]).pack(pady=(30, 10))
        ctk.CTkLabel(popup, text="이 작업은 되돌릴 수 없습니다", font=(self.app.font_family, fs - 2), text_color=theme["text_secondary"]).pack(pady=5)

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=15)

        ctk.CTkButton(btn_frame, text="취소", font=(self.app.font_family, fs), fg_color=theme["text_secondary"], width=120, height=40, command=popup.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="초기화", font=(self.app.font_family, fs, "bold"), fg_color=theme["danger"], width=120, height=40, command=lambda: [self._reset_data(), popup.destroy()]).pack(side="left", padx=10)

    def _reset_data(self):
        import os
        from config import DB_PATH
        self.app.db.close()
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        from database import Database
        self.app.db = Database()
        self._show_toast("✅ 데이터가 초기화되었습니다")
        self.app.show_page("home")

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
