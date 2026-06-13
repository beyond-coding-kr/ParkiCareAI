"""
파킨슨병 환자 관리 앱 - 설정 파일
"""
import os

# ── 경로 설정 ──
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
MEDIA_DIR = os.path.join(DATA_DIR, "media")
DB_PATH = os.path.join(DATA_DIR, "parkinson_care.db")

# 디렉토리 자동 생성
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)

# ── OpenRouter API 설정 ──
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "sk-or-v1-placeholder-api-key")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL = "google/gemini-2.0-flash-001"  # OpenRouter 모델 이름

# ── UI 기본 설정 ──
DEFAULT_FONT_SIZE = 16
MIN_FONT_SIZE = 10
MAX_FONT_SIZE = 30
DEFAULT_FONT_FAMILY = "맑은 고딕"
AVAILABLE_FONTS = ["맑은 고딕", "나눔고딕", "굴림", "돋움", "바탕", "Arial", "Helvetica"]

# ── 색상 테마 ──
# NOTE: tkinter/CustomTkinter does not support 8-digit hex (#RRGGBBAA).
# All colors must be standard 6-digit hex (#RRGGBB).
# Pre-computed light/dark variants avoid runtime alpha concatenation.
THEMES = {
    "의료 블루": {
        "bg": "#E8F4FD",
        "sidebar_bg": "#1B3A5C",
        "sidebar_fg": "#FFFFFF",
        "sidebar_sep": "#4A6A8C",
        "sidebar_hover": "#2A4A6C",
        "sidebar_muted": "#8899AA",
        "card_bg": "#FFFFFF",
        "accent": "#2196F3",
        "accent_hover": "#1976D2",
        "accent_light": "#BBDEFB",
        "text": "#1A1A2E",
        "text_secondary": "#5A6A7A",
        "danger": "#E53935",
        "danger_hover": "#C62828",
        "danger_light": "#D4706E",
        "success": "#43A047",
        "success_light": "#C8E6C9",
        "warning": "#FB8C00",
        "warning_light": "#FFF3E0",
        "border": "#D0E4F5",
    },
    "밝은 모드": {
        "bg": "#F5F5F5",
        "sidebar_bg": "#2C3E50",
        "sidebar_fg": "#ECF0F1",
        "sidebar_sep": "#4A6A7C",
        "sidebar_hover": "#3C4E60",
        "sidebar_muted": "#8899AA",
        "card_bg": "#FFFFFF",
        "accent": "#3498DB",
        "accent_hover": "#2980B9",
        "accent_light": "#D6EAF8",
        "text": "#2C3E50",
        "text_secondary": "#7F8C8D",
        "danger": "#E74C3C",
        "danger_hover": "#C0392B",
        "danger_light": "#D87A73",
        "success": "#27AE60",
        "success_light": "#D5F5E3",
        "warning": "#F39C12",
        "warning_light": "#FEF9E7",
        "border": "#E0E0E0",
    },
    "다크 모드": {
        "bg": "#1A1A2E",
        "sidebar_bg": "#16213E",
        "sidebar_fg": "#E8E8E8",
        "sidebar_sep": "#334466",
        "sidebar_hover": "#263250",
        "sidebar_muted": "#6677AA",
        "card_bg": "#222244",
        "accent": "#4FC3F7",
        "accent_hover": "#29B6F6",
        "accent_light": "#2A3A55",
        "text": "#E8E8E8",
        "text_secondary": "#B0B0C0",
        "danger": "#EF5350",
        "danger_hover": "#E53935",
        "danger_light": "#6B3333",
        "success": "#66BB6A",
        "success_light": "#2A3E2B",
        "warning": "#FFA726",
        "warning_light": "#3D3020",
        "border": "#333366",
    },
    "따뜻한 모드": {
        "bg": "#FFF8E1",
        "sidebar_bg": "#5D4037",
        "sidebar_fg": "#FFF8E1",
        "sidebar_sep": "#7D6057",
        "sidebar_hover": "#6D5047",
        "sidebar_muted": "#AA9988",
        "card_bg": "#FFFFFF",
        "accent": "#FF9800",
        "accent_hover": "#F57C00",
        "accent_light": "#FFE0B2",
        "text": "#3E2723",
        "text_secondary": "#795548",
        "danger": "#F44336",
        "danger_hover": "#D32F2F",
        "danger_light": "#D87A73",
        "success": "#4CAF50",
        "success_light": "#E8F5E9",
        "warning": "#FF9800",
        "warning_light": "#FFF8E1",
        "border": "#FFE0B2",
    },
}

DEFAULT_THEME = "의료 블루"

# ── 증상 카테고리 ──
SYMPTOM_CATEGORIES = [
    {"name": "떨림 (진전)", "icon": "🫨", "desc": "손, 팔, 다리 등의 떨림"},
    {"name": "경직", "icon": "🦴", "desc": "근육이 뻣뻣해지는 증상"},
    {"name": "보행 어려움", "icon": "🚶", "desc": "걷기 힘들거나 걸음이 느려짐"},
    {"name": "균형 문제", "icon": "⚖️", "desc": "자세 불안정, 넘어짐"},
    {"name": "말하기 어려움", "icon": "🗣️", "desc": "목소리가 작아지거나 발음이 불분명"},
    {"name": "삼키기 어려움", "icon": "😮", "desc": "음식을 삼키기 힘든 증상"},
    {"name": "수면 장애", "icon": "😴", "desc": "불면증, 주간 졸음"},
    {"name": "표정 변화", "icon": "😐", "desc": "무표정, 얼굴 근육 감소"},
    {"name": "소화 문제", "icon": "🫄", "desc": "변비, 소화 어려움"},
    {"name": "기타", "icon": "📝", "desc": "그 외 증상"},
]

# ── 재활 치료 종류 ──
DEFAULT_REHAB_TYPES = [
    {"name": "제자리 걷기", "icon": "🚶", "category": "보행/균형", "desc": "제자리에서 팔을 크게 흔들며 걷기 (5~10분)", "difficulty": 1},
    {"name": "한 발로 균형 잡기", "icon": "🦶", "category": "보행/균형", "desc": "벽에 손을 대고 한 발로 10초씩 서기", "difficulty": 2},
    {"name": "계단 오르내리기", "icon": "🪜", "category": "보행/균형", "desc": "천천히 계단을 오르고 내리기 (3~5회)", "difficulty": 3},
    {"name": "의자에서 일어서기", "icon": "🪑", "category": "근력", "desc": "의자에 앉았다 일어서기 반복 (10회)", "difficulty": 1},
    {"name": "팔 들어올리기", "icon": "💪", "category": "근력", "desc": "양팔을 천천히 들어올리기 (10회씩)", "difficulty": 1},
    {"name": "스트레칭", "icon": "🧘", "category": "유연성", "desc": "전신 스트레칭 (10~15분)", "difficulty": 1},
    {"name": "손가락 운동", "icon": "✋", "category": "소근육", "desc": "엄지와 검지 번갈아 맞대기 (각 20회)", "difficulty": 1},
    {"name": "표정 근육 운동", "icon": "😊", "category": "소근육", "desc": "크게 웃기, 눈 감기, 볼 부풀리기 (각 10회)", "difficulty": 1},
    {"name": "발성 훈련", "icon": "🎤", "category": "음성", "desc": "크게 '아' 발음하기 (5초씩 10회)", "difficulty": 1},
    {"name": "글씨 쓰기", "icon": "✍️", "category": "소근육", "desc": "큰 글씨로 문장 따라쓰기 (5분)", "difficulty": 1},
    {"name": "실내 자전거", "icon": "🚲", "category": "유산소", "desc": "실내 자전거 타기 (10~15분)", "difficulty": 2},
    {"name": "호흡 운동", "icon": "🌬️", "category": "호흡", "desc": "깊게 들이마시고 천천히 내쉬기 (10회)", "difficulty": 1},
]

# ── 면책 조항 ──
DISCLAIMER = (
    "⚠️ 본 앱은 연구·교육 목적의 보조 도구이며, "
    "의료 진단이나 치료를 대체하지 않습니다. "
    "반드시 전문 의료진의 상담과 병행하여 사용하세요."
)
