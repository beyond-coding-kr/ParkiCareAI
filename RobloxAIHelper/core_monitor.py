import psutil
import time
import threading

class RobloxMonitor:
    def __init__(self, callback):
        self.callback = callback
        self.is_running = False
        self._stop_event = threading.Event()

    def check_roblox_studio(self):
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info.get('name', '').lower()
                # 로블록스 스튜디오의 실행 파일명(RobloxStudioBeta.exe)을 감지합니다.
                if name and 'robloxstudio' in name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def monitor_loop(self):
        while not self._stop_event.is_set():
            running = self.check_roblox_studio()
            if running != self.is_running:
                self.is_running = running
                self.callback(self.is_running)
            time.sleep(2)  # 2초마다 체크

    def start(self):
        threading.Thread(target=self.monitor_loop, daemon=True).start()

    def stop(self):
        self._stop_event.set()
