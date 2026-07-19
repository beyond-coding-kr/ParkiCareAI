import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
from datetime import datetime, timedelta
import threading
from server import app, db
from database import Profile, GameSession

# ==========================================
# [사용자 설정 영역]
# 본인의 Gmail 계정과 앱 비밀번호를 입력하세요.
# ==========================================
GMAIL_USER = "your_email@gmail.com"  # 예: myid@gmail.com
GMAIL_APP_PASSWORD = "your_app_password"  # 16자리 앱 비밀번호 (띄어쓰기 없이)

# 수신자 목록 (문자 게이트웨이 또는 이메일 주소)
# 예: 01012345678@vtext.com (통신사 게이트웨이), test@example.com
RECIPIENTS = [
    "recipient@example.com",
]

def send_email_report():
    print(f"[{datetime.now()}] 일일 훈련 리포트 발송을 시작합니다...")
    
    with app.app_context():
        # 오늘 0시 이후의 세션 검색
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        sessions_today = GameSession.query.filter(GameSession.timestamp >= today_start).all()
        
        if not sessions_today:
            print("오늘 진행된 훈련이 없습니다. 발송을 건너뜁니다.")
            return
            
        profiles_active = set([s.profile_id for s in sessions_today])
        
        report_lines = [f"[ParkiCare AI] 일일 훈련 리포트 ({datetime.now().strftime('%Y-%m-%d')})", ""]
        
        for pid in profiles_active:
            profile = Profile.query.get(pid)
            if not profile: continue
            
            p_sessions = [s for s in sessions_today if s.profile_id == pid]
            report_lines.append(f"환자명: {profile.name}")
            report_lines.append(f"오늘 훈련 횟수: {len(p_sessions)}회")
            
            # 게임별 평균 정확도 계산
            for game_type in ['memory_sequence', 'attention_stroop', 'motor_response']:
                g_sessions = [s for s in p_sessions if s.game_type == game_type]
                if g_sessions:
                    avg_acc = sum(s.accuracy for s in g_sessions) / len(g_sessions) * 100
                    game_name = {
                        'memory_sequence': '기억력',
                        'attention_stroop': '집중력(스트룹)',
                        'motor_response': '운동 반응'
                    }.get(game_type, game_type)
                    report_lines.append(f" - {game_name}: {avg_acc:.1f}%")
            
            report_lines.append("")
            
        report_text = "\n".join(report_lines)
    
    # 이메일 전송 (SMTP)
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = ", ".join(RECIPIENTS)
        msg['Subject'] = f"ParkiCare 일일 훈련 리포트 ({datetime.now().strftime('%m/%d')})"
        
        msg.attach(MIMEText(report_text, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("리포트 발송 완료!")
    except Exception as e:
        print(f"이메일 발송 중 오류 발생: {e}")

def run_scheduler():
    # 매일 오후 6시에 발송
    schedule.every().day.at("18:00").do(send_email_report)
    
    print("스케줄러가 시작되었습니다. (매일 18:00 발송)")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # 테스트로 즉시 1번 발송해보고 싶다면 아래 주석을 해제하세요.
    # send_email_report()
    
    # 백그라운드 스레드로 스케줄러 실행
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    try:
        # 메인 스레드 유지
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("스케줄러 종료.")
