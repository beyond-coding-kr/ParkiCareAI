import sys
import os
import re
import io
from PIL import Image
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTextEdit, 
                             QLineEdit, QPushButton, QLabel, QHBoxLayout, 
                             QGraphicsDropShadowEffect, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QRect, QBuffer, QIODevice
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from dotenv import load_dotenv
import google.generativeai as genai
from local_api import push_command

# 환경 변수 로드
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

UNIVERSAL_PROMPT = """너는 로블록스 스튜디오의 수석 멀티모달 AI 도우미야.
답변은 항상 전문적이고 세련된 어조로 작성해.

[모드 1: 화면 캡처가 제공된 경우 (Circle Mode)]
사용자가 스튜디오 내 UI의 위치를 묻고 있을 때(이 버튼 어딨어? 등), 전달받은 화면 이미지를 분석하여 텍스트 대신 즉각적으로 좌표를 반환해.
- 형식: [UI_POINTER: ymin, xmin, ymax, xmax] (0~1000 단위로 정규화된 박스여야 함)
- 만약 화면에서 아무리 찾아도 보이지 않는다면, "현재 캡쳐된 화면에서 버튼을 찾을 수 없습니다. OOO 탭을 열고 다시 질문해주세요."와 같은 일반 텍스트로 안내해.

[모드 2: 텍스트 전용 질문 (Text Mode)]
만약 스크린샷 이미지가 함께 제공되지 않았다면, 어떠한 경우에도 [UI_POINTER] 명령어를 쓰지 말고, 순수 텍스트(마크다운 형태)로만 무조건적으로 최고로 상세하게 답변해 줘.

[로블록스 3D 모델 파트 강조]
만약 화면 UI 메뉴 포인터가 아니라, '3D 월드 상의 파트(Part)'나 '스폰 로케이션'을 강조해달라고 하면 기존처럼 [COMMAND:HIGHLIGHT_PART:오브젝트이름] 명령어를 텍스트 설명 어딘가에 포함 시켜서 보내면 돼.
"""

class PointerWidget(QWidget):
    """화면 특정 좌표에 포인터(동그라미)를 그려주는 투명 위젯"""
    def __init__(self, rect: QRect):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        margin = 10
        self.setGeometry(rect.x() - margin, rect.y() - margin, rect.width() + 2*margin, rect.height() + 2*margin)
        self.target_rect = QRect(margin, margin, rect.width(), rect.height())
        
        QTimer.singleShot(4000, self.close)
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor(255, 80, 80, 255))
        pen.setWidth(4)
        painter.setPen(pen)
        
        painter.setBrush(QColor(255, 40, 40, 60))
        painter.drawEllipse(self.target_rect)


class GeminiWorker(QThread):
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, user_text, chat_session, screenshot_image=None):
        super().__init__()
        self.user_text = user_text
        self.chat_session = chat_session
        self.screenshot_image = screenshot_image

    def run(self):
        try:
            if not GEMINI_API_KEY:
                self.error_signal.emit("⚠️ API 키가 `.env` 파일에 설정되지 않았습니다!")
                return

            if self.screenshot_image:
                response = self.chat_session.send_message([self.screenshot_image, self.user_text])
            else:
                response = self.chat_session.send_message(self.user_text)
                
            self.finished_signal.emit(response.text)
        except Exception as e:
            self.error_signal.emit(f"⚠️ API 통신 장애: {str(e)}")

class OverlayUI(QWidget):
    visibility_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.oldPos = self.pos()
        self.pointers = []
        self.initUI()
        self.visibility_signal.connect(self.set_visibility)

        self.chat_session = None
        if GEMINI_API_KEY:
            model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=UNIVERSAL_PROMPT)
            self.chat_session = model.start_chat()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, 400, 550) # 화면 크기 약간 확장

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.container = QWidget()
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            QWidget#MainContainer {
                background-color: rgba(20, 22, 30, 225);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 15px;
            }
            QLabel#TitleLabel {
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTextEdit {
                background-color: transparent;
                border: none;
                color: #E2E8F0;
                font-size: 14px;
                line-height: 1.5;
                font-family: 'Segoe UI', Arial;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 40);
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(255, 255, 255, 80);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QLineEdit {
                background-color: rgba(10, 10, 15, 180);
                border: 1px solid rgba(255, 255, 255, 15);
                border-radius: 12px;
                color: white;
                padding: 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(59, 130, 246, 120);
                background-color: rgba(15, 15, 25, 200);
            }
            QComboBox {
                background-color: rgba(255, 255, 255, 15);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 12px;
                font-family: 'Segoe UI';
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: rgb(30, 30, 42);
                color: white;
                selection-background-color: rgba(255, 255, 255, 30);
                outline: none;
            }
            QPushButton#HideBtn {
                background-color: transparent;
                color: #94A3B8;
                font-size: 14px;
                border: none;
                border-radius: 8px;
            }
            QPushButton#HideBtn:hover {
                background-color: rgba(239, 68, 68, 60);
                color: white;
            }
        """)

        # 은은한 그림자 이펙트 추가
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(15, 15, 15, 15)

        title_layout = QHBoxLayout()
        self.title_label = QLabel("✨ Studio AI Helper")
        self.title_label.setObjectName("TitleLabel")
        title_layout.addWidget(self.title_label)
        
        title_layout.addStretch()
        
        self.mode_toggle = QComboBox()
        self.mode_toggle.addItems(["📝 Text Mode", "⭕ Circle Mode"])
        # 기본값을 서클 모드로 (현재 화면 분석 가능)
        self.mode_toggle.setCurrentIndex(1)
        # 커서 변경시 포커스 방지
        self.mode_toggle.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        title_layout.addWidget(self.mode_toggle)

        self.hide_button = QPushButton("✕")
        self.hide_button.setObjectName("HideBtn")
        self.hide_button.setFixedSize(24, 24)
        self.hide_button.clicked.connect(self.hide)
        title_layout.addWidget(self.hide_button)
        
        container_layout.addLayout(title_layout)

        # 구분선 추가
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: rgba(255, 255, 255, 15); margin-top: 5px; margin-bottom: 5px;")
        container_layout.addWidget(divider)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        if not GEMINI_API_KEY:
            self.chat_history.append("<br><font color='#EF4444'>[경고] .env 파일에 GEMINI_API_KEY를 설정해주셔야 합니다.</font>")
        else:
            self.chat_history.append("<br><b>AI:</b> 안녕하세요! 로블록스 작업에 무엇을 도와드릴까요?<br>")
            
        container_layout.addWidget(self.chat_history)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("어떤 것을 물어보시겠어요?")
        self.input_field.returnPressed.connect(self.on_submit)
        container_layout.addWidget(self.input_field)

        layout.addWidget(self.container)
        self.setLayout(layout)

    def on_submit(self):
        text = self.input_field.text().strip()
        if not text:
            return

        self.chat_history.append(f"<b>You:</b> <font color='#A8C7FA'>{text}</font><br>")
        self.input_field.clear()
        
        if not self.chat_session:
            self.chat_history.append("<b>AI:</b> <font color='#EF4444'>API 키가 설정되지 않아 연결할 수 없습니다.</font><br>")
            return

        self.input_field.setDisabled(True)
        self.chat_history.append("<div id='loading_msg'><b>AI:</b> <i>(답변을 생성 중입니다...)</i></div>")

        # 토글 버튼 확인 (0: 일반 문자 모드, 1: 사진 기반 서클 캡처 모드)
        is_circle_mode = (self.mode_toggle.currentIndex() == 1)
        
        pil_image = None
        if is_circle_mode:
            self.chat_history.setHtml(self.chat_history.toHtml().replace("답변을 생성 중입니다...", "화면을 스캔하고 답변을 생성 중입니다..."))
            screen = QApplication.primaryScreen()
            pixmap = screen.grabWindow(0)
            image = pixmap.toImage()
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.ReadWrite)
            image.save(buffer, "PNG")
            pil_image = Image.open(io.BytesIO(buffer.data()))

        self.worker = GeminiWorker(text, self.chat_session, screenshot_image=pil_image)
        self.worker.finished_signal.connect(self.on_ai_response)
        self.worker.error_signal.connect(self.on_ai_error)
        self.worker.start()

    def on_ai_response(self, text):
        self.input_field.setDisabled(False)
        self.input_field.setFocus()
        
        clean_text = text
        pointer_match = re.search(r'\[UI_POINTER:\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', text)
        command_match = re.search(r'\[COMMAND:([^:]+):([^\]]+)\]', text)

        if pointer_match:
            ymin, xmin, ymax, xmax = map(int, pointer_match.groups())
            screen_rect = QApplication.primaryScreen().geometry()
            sw, sh = screen_rect.width(), screen_rect.height()
            
            real_x = int(xmin * sw / 1000.0)
            real_y = int(ymin * sh / 1000.0)
            real_w = int((xmax - xmin) * sw / 1000.0)
            real_h = int((ymax - ymin) * sh / 1000.0)
            
            real_w = max(real_w, 60)
            real_h = max(real_h, 60)
            target_rect = QRect(real_x, real_y, real_w, real_h)
            
            pointer = PointerWidget(target_rect)
            self.pointers.append(pointer)
            
            clean_text = clean_text.replace(pointer_match.group(0), "").strip()
            if not clean_text or clean_text.isspace():
                clean_text = "지정하신 요소 위치에 포인터를 띄워드렸습니다!"

        if command_match:
            cmd_type = command_match.group(1).strip()
            cmd_data = command_match.group(2).strip()
            if cmd_type == "HIGHLIGHT_PART":
                push_command("HIGHLIGHT_PART", {"part_name": cmd_data})
            clean_text = clean_text.replace(command_match.group(0), "").strip()

        # HTML 처리 방식으로 로딩 중복 메시지 삭제
        html = self.chat_history.toHtml()
        
        # 'loading_msg'라는 ID가 달린 div 통째로 날리기 꼼수 혹은 텍스트 자체 제거
        clean_html = re.sub(r"<b>AI:</b> <i>\(답변을.*?\)<br />", "", html)
        clean_html = re.sub(r"<div id='loading_msg'><b>AI:</b> <i>\(.*?\)<br /></div>", "", clean_html)  # 안전장치

        self.chat_history.setHtml(clean_html)
        
        # 줄바꿈을 html `<br>`로 변환 (Gemini 응답이 마크다운/텍스트일 수 있음)
        clean_text_html = clean_text.replace("\n", "<br>")
        self.chat_history.append(f"<b>AI:</b> {clean_text_html}<br>")

        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_ai_error(self, error_msg):
        self.input_field.setDisabled(False)
        self.input_field.setFocus()
        self.chat_history.append(f"<font color='#EF4444'><b>Error:</b> {error_msg}</font><br>")

    def set_visibility(self, visible):
        if visible:
            self.show()
        else:
            self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.oldPos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPosition().toPoint()
