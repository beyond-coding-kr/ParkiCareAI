from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import threading

app = FastAPI()

# 명령어 대기열 (파이썬이 플러그인으로 보낼 명령을 저장)
command_queue = []

class CommandResponse(BaseModel):
    has_command: bool
    command_type: str = ""
    command_data: dict = {}

@app.get("/poll", response_model=CommandResponse)
def poll_commands():
    """
    로블록스 스튜디오 플러그인에서 주기적으로(GET) 호출하는 엔드포인트입니다.
    가장 오래된 명령 하나를 꺼내서 전달합니다.
    """
    if command_queue:
        cmd = command_queue.pop(0)
        return CommandResponse(has_command=True, command_type=cmd['type'], command_data=cmd['data'])
    return CommandResponse(has_command=False)

def push_command(cmd_type: str, data: dict):
    """
    오버레이 UI나 AI 엔진에서 새로운 명령을 생성할 때 호출합니다.
    """
    command_queue.append({'type': cmd_type, 'data': data})

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

def start_api_server():
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
