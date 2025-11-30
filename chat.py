# chat.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import get_current_user
from db import get_session
from models import Message
from sqlmodel import Session
from dotenv import load_dotenv
import openai
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set. Put it in .env")

openai.api_key = OPENAI_API_KEY

router = APIRouter()

class ChatRequest(BaseModel):
    messages: list  # [{"role":"user","content":"..."}]
    save_history: bool = True

# @router.post("/chat")
# # async def chat(req: ChatRequest, user=Depends(get_current_user), session=Depends(get_session)):
# async def chat(req: ChatRequest, session=Depends(get_session)):
    
#     # ===== 模擬一個測試用 user =====
#     class TestUser:
#         id = 1
#     user = TestUser()

#     # 儲存使用者訊息到 DB（選擇性）
#     if req.save_history:
#         for m in req.messages:
#             session.add(Message(user_id=user.id, role=m.get("role","user"), content=m.get("content","")))
#         session.commit()

#     # 組成最近對話（若想用歷史記憶，可從 DB 撈）
#     # 這裡我們直接把傳來的 messages 送到 OpenAI
#     try:
#         resp = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             messages=req.messages,
#             max_tokens=512,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#     reply = resp.choices[0].message["content"]

#     # 儲存 assistant 回覆
#     if req.save_history:
#         session.add(Message(user_id=user.id, role="assistant", content=reply))
#         session.commit()

#     return {"reply": reply}

# chat.py
from openai import OpenAI

client = OpenAI(api_key="你的OPENAI_API_KEY")

@router.post("/chat")
async def chat(req: ChatRequest, session=Depends(get_session)):
    class TestUser:
        id = 1
    user = TestUser()

    if req.save_history:
        for m in req.messages:
            session.add(Message(user_id=user.id, role=m.get("role","user"), content=m.get("content","")))
        session.commit()

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=req.messages,
            max_tokens=512
        )
        reply = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if req.save_history:
        session.add(Message(user_id=user.id, role="assistant", content=reply))
        session.commit()

    return {"reply": reply}


@router.get("/history")
def get_history(limit: int = 100, user=Depends(get_current_user), session=Depends(get_session)):
    from sqlmodel import select
    statement = select(Message).where(Message.user_id == user.id).order_by(Message.created_at)
    msgs = session.exec(statement).all()
    return {"history": [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in msgs[-limit:]]}
