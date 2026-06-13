"""
카메라 유틸리티 - 웹캠 캡처 (OpenCV 기반)
"""
import cv2
import os
import threading
from datetime import datetime
from config import MEDIA_DIR


class CameraUtil:
    def __init__(self):
        self.cap = None
        self.is_recording = False
        self.video_writer = None

    def capture_photo(self, callback=None):
        """웹캠으로 사진 촬영"""
        def _run():
            try:
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    result = {"path": None, "status": "error", "error": "카메라를 열 수 없습니다"}
                    if callback:
                        callback(result)
                    return result

                ret, frame = cap.read()
                cap.release()

                if ret:
                    filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    filepath = os.path.join(MEDIA_DIR, filename)
                    cv2.imwrite(filepath, frame)
                    result = {"path": filepath, "status": "success"}
                else:
                    result = {"path": None, "status": "error", "error": "사진 촬영 실패"}
            except Exception as e:
                result = {"path": None, "status": "error", "error": str(e)}

            if callback:
                callback(result)
            return result

        if callback:
            t = threading.Thread(target=_run, daemon=True)
            t.start()
        else:
            return _run()

    def start_video(self):
        """동영상 녹화 시작"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                return None

            filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
            filepath = os.path.join(MEDIA_DIR, filename)

            fourcc = cv2.VideoWriter_fourcc(*"XVID")
            fps = 20.0
            w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.video_writer = cv2.VideoWriter(filepath, fourcc, fps, (w, h))
            self.is_recording = True
            self._video_path = filepath

            # 녹화 루프
            def _record():
                while self.is_recording and self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret and self.video_writer:
                        self.video_writer.write(frame)

            self._record_thread = threading.Thread(target=_record, daemon=True)
            self._record_thread.start()
            return filepath
        except Exception:
            return None

    def stop_video(self):
        """동영상 녹화 중지"""
        self.is_recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        if self.cap:
            self.cap.release()
            self.cap = None
        return getattr(self, "_video_path", None)

    def get_preview_frame(self):
        """미리보기 프레임 (tkinter 표시용)"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None
