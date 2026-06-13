import customtkinter as ctk
import platform

class AccessibleScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        
        # 1. 기존 스크롤바 숨기기 (드래그 스크롤 전용)
        try:
            self._scrollbar.grid_forget()
        except Exception:
            pass

        # 2. 마우스 휠 스크롤 속도 증가 (Windows)
        if platform.system() == "Windows":
            self._parent_canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
            
        # 3. 화면 터치/마우스 드래그로 스크롤 가능하게
        self._parent_canvas.bind_all("<ButtonPress-1>", self._scroll_start, add="+")
        self._parent_canvas.bind_all("<B1-Motion>", self._scroll_move, add="+")
        
        self.y_start = 0

    def _on_mousewheel(self, event):
        """기본 스크롤보다 3배 빠르게 (접근성 향상)"""
        try:
            if self.winfo_exists() and self._parent_canvas.winfo_exists():
                self._parent_canvas.yview_scroll(int(-event.delta / 2), "units")
        except Exception:
            pass
            
    def _scroll_start(self, event):
        # y_root: 화면 전체 기준 Y 좌표
        self.y_start = getattr(event, 'y_root', event.y)

    def _scroll_move(self, event):
        """마우스 드래그로 스크롤 (스마트폰처럼)"""
        try:
            widget = event.widget
            parent = widget
            is_inside = False
            
            # 이벤트가 발생한 위젯이 이 스크롤 프레임 내부에 있는지 확인
            while parent:
                if parent == self._parent_canvas or parent == self._parent_frame:
                    is_inside = True
                    break
                if not hasattr(parent, 'master'):
                    break
                parent = parent.master
                
            if is_inside:
                y_root = getattr(event, 'y_root', event.y)
                dy = self.y_start - y_root
                if abs(dy) > 5:  # 데드존
                    self._parent_canvas.yview_scroll(int(dy/5), "units")
                    self.y_start = y_root
        except Exception:
            pass

