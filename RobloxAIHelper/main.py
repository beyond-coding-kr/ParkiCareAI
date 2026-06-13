import sys
from PyQt6.QtWidgets import QApplication
from core_monitor import RobloxMonitor
from overlay_ui import OverlayUI
from local_api import start_api_server

def main():
    print("Starting Local API Server on port 8000...")
    # Flask/FastAPI 로컬 통신 서버 스레드 시작
    start_api_server()

    # PyQt 애플리케이션 초기화
    app = QApplication(sys.argv)
    
    # 오버레이 UI 객체 생성
    overlay = OverlayUI()
    
    # 윈도우 환경에서 디버그를 원하시면 아래 주석을 풀고 스튜디오 실행 없이도 UI를 띄워볼 수 있습니다.
    # overlay.show() 

    # 프로세스 감지 콜백 함수
    def on_studio_status_changed(is_running):
        if is_running:
            print("Roblox Studio detected! Showing Overlay.")
            # GUI 스레드 안전성을 위해 시그널 사용
            overlay.visibility_signal.emit(True)
        else:
            print("Roblox Studio closed. Hiding Overlay.")
            overlay.visibility_signal.emit(False)

    # 프로세스 감시 스레드 시작
    monitor = RobloxMonitor(callback=on_studio_status_changed)
    monitor.start()
    
    print("AI Helper is running in the background. Please open Roblox Studio.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
