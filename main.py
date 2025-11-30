# main.py
from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, Session, select
from db import init_db, engine, get_session
from models import User
from auth import hash_password, verify_password, create_access_token, oauth2_scheme
from chat import router as chat_router
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
init_db()

app = FastAPI()

# 如果前端是從不同 origin 訪問，允許 CORS（開發時可用 *，正式環境請限制來源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],  # 前端使用的 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...), session=Depends(get_session)):
    statement = select(User).where(User.username == username)
    exists = session.exec(statement).first()
    if exists:
        raise HTTPException(status_code=400, detail="user exists")
    user = User(username=username, hashed_password=hash_password(password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"ok": True, "username": user.username}

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...), session=Depends(get_session)):
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/", response_class=HTMLResponse)
async def root():
    with open(os.path.join("static", "index.html"), "r", encoding="utf-8") as f:
        return f.read()

# include chat router, protected endpoints will use get_current_user
app.include_router(chat_router, prefix="", tags=["chat"])
