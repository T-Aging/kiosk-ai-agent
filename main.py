from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
from cache.call_llm import agent_answer
from cache.session import l1_snapshot_load
# from stt.stt_openai import record_and_stt

app = FastAPI(title="AI Agent", version="1.0.0")

@app.get("/")
def root():
    return {"message": "AI Agent API is running"}

# L1 조회
@app.post("/session/start")
def start_session(store_id: str, menu_version: int):
    snapshot = l1_snapshot_load(store_id, menu_version)
    return {"status": "L1 cached", "menu_count": len(snapshot["menus"])}

# 음성 → STT → LLM(캐시 포함) → 텍스트 응답
# 노트북 테스트용
# @app.post("/voice-converse")
# def voice_converse_local(store_id: str, menu_version: int, duration: int = 5):
#     # 1) 녹음 + STT
#     user_text = record_and_stt(duration=duration)

#     # 2) LLM + Redis 캐시
#     result = agent_answer(store_id, menu_version, user_text)

#     # 3) 결과 반환 (STT 결과도 같이 보여주기)
#     return {
#         "store_id": result["store_id"],
#         "menu_version": result["menu_version"],
#         "user_text": user_text,
#         "reply": result["reply"],
#         "cache_hit": result["cache_hit"],
#     }

class ConverseRequest(BaseModel):
    store_id: str
    menu_version: int
    user_text: str

# 사용자 발화 이후, L1(redis) 캐시 Hit/Miss에 따른 답변 생성
@app.post("/converse")
def converse(req: ConverseRequest):
    result = agent_answer(req.store_id, req.menu_version, req.user_text)

    return {
        "store_id": result["store_id"],
        "menu_version": result["menu_version"],
        "user_text": req.user_text,
        "reply": result["reply"],
        "cache_hit": result["cache_hit"],
    }