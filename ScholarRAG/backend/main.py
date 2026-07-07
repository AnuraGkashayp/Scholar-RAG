import os
import json as _json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Form, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from rag import init, query_rag, query_rag_stream, clear_memory
from db import init_db, get_db
from auth import hash_password, verify_password, create_token, get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print("Starting init...")
        init_db()
        init()
        print("Init complete.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    email:    str
    password: str


class LoginRequest(BaseModel):
    email:    str
    password: str


class ClearRequest(BaseModel):
    session_id: str


@app.post("/register")
def register(req: RegisterRequest):
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (req.email,)).fetchone()
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(req.password)
    cursor = db.execute(
        "INSERT INTO users (email, password_hash) VALUES (?, ?)",
        (req.email, hashed),
    )
    db.commit()
    user_id = cursor.lastrowid
    db.close()
    token = create_token(user_id, req.email)
    return {"token": token, "user": {"id": user_id, "email": req.email}}


@app.post("/login")
def login(req: LoginRequest):
    db = get_db()
    row = db.execute("SELECT id, password_hash FROM users WHERE email = ?", (req.email,)).fetchone()
    db.close()
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(row["id"], req.email)
    return {"token": token, "user": {"id": row["id"], "email": req.email}}


@app.post("/query")
async def query(
    question:   str                  = Form(...),
    session_id: str                  = Form("default"),
    model:      str                  = Form("claude-haiku-4-5-20251001"),
    file:       Optional[UploadFile] = File(None),
    user:       dict                 = Depends(get_current_user),
):
    if not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    pdf_bytes = None
    file_name = None
    if file and file.filename:
        pdf_bytes = await file.read()
        file_name = file.filename

    scoped_session = f"{user['sub']}_{session_id}"

    db = get_db()
    db_msgs = db.execute(
        "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id ASC",
        (scoped_session,),
    ).fetchall()
    preloaded = [
        {"role": m["role"], "content": m["content"]}
        for m in db_msgs
        if m["role"] in ("user", "assistant")
    ]
    db.close()

    result = query_rag(question, scoped_session, pdf_bytes, preloaded_history=preloaded, model=model)

    db = get_db()
    existing_chat = db.execute("SELECT id FROM chats WHERE id = ?", (scoped_session,)).fetchone()
    if not existing_chat:
        db.execute(
            "INSERT INTO chats (id, user_id, title) VALUES (?, ?, ?)",
            (scoped_session, int(user["sub"]), question[:60]),
        )
    if file_name:
        db.execute(
            "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
            (scoped_session, "document", file_name),
        )
    db.execute(
        "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
        (scoped_session, "user", question),
    )
    db.execute(
        "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
        (scoped_session, "assistant", result["answer"]),
    )
    for src in result.get("sources", []):
        key = src.get("arxiv_id") or src.get("title", "")
        if key:
            db.execute(
                "INSERT OR IGNORE INTO sources (chat_id, source_json, source_key) VALUES (?, ?, ?)",
                (scoped_session, _json.dumps(src), key),
            )
    db.commit()
    db.close()

    return result


@app.post("/query/stream")
async def query_stream(
    question:   str                  = Form(...),
    session_id: str                  = Form("default"),
    model:      str                  = Form("claude-haiku-4-5-20251001"),
    file:       Optional[UploadFile] = File(None),
    user:       dict                 = Depends(get_current_user),
):
    if not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    pdf_bytes = None
    file_name = None
    if file and file.filename:
        pdf_bytes = await file.read()
        file_name = file.filename

    scoped_session = f"{user['sub']}_{session_id}"

    db = get_db()
    db_msgs = db.execute(
        "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id ASC",
        (scoped_session,),
    ).fetchall()
    preloaded = [
        {"role": m["role"], "content": m["content"]}
        for m in db_msgs
        if m["role"] in ("user", "assistant")
    ]
    db.close()

    async def event_generator():
        answer  = ""
        sources = []
        async for chunk in query_rag_stream(question, scoped_session, pdf_bytes, preloaded_history=preloaded, model=model):
            if chunk.startswith("data: "):
                try:
                    data = _json.loads(chunk[6:])
                    if data.get("type") == "token":
                        answer += data["text"]
                    elif data.get("type") == "done":
                        sources = data.get("sources", [])
                except Exception:
                    pass
            yield chunk

        db = get_db()
        existing_chat = db.execute("SELECT id FROM chats WHERE id = ?", (scoped_session,)).fetchone()
        if not existing_chat:
            db.execute(
                "INSERT INTO chats (id, user_id, title) VALUES (?, ?, ?)",
                (scoped_session, int(user["sub"]), question[:60]),
            )
        if file_name:
            db.execute(
                "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
                (scoped_session, "document", file_name),
            )
        db.execute(
            "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
            (scoped_session, "user", question),
        )
        db.execute(
            "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
            (scoped_session, "assistant", answer),
        )
        for src in sources:
            key = src.get("arxiv_id") or src.get("title", "")
            if key:
                db.execute(
                    "INSERT OR IGNORE INTO sources (chat_id, source_json, source_key) VALUES (?, ?, ?)",
                    (scoped_session, _json.dumps(src), key),
                )
        db.commit()
        db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/chats")
def get_chats(user: dict = Depends(get_current_user)):
    db = get_db()
    chats = db.execute(
        "SELECT id, title, pinned, starred FROM chats WHERE user_id = ? ORDER BY pinned DESC, created_at DESC",
        (int(user["sub"]),),
    ).fetchall()

    prefix = f"{user['sub']}_"
    result = []
    for chat in chats:
        msgs = db.execute(
            "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id ASC",
            (chat["id"],),
        ).fetchall()
        srcs = db.execute(
            "SELECT source_json FROM sources WHERE chat_id = ?",
            (chat["id"],),
        ).fetchall()
        raw_id = chat["id"][len(prefix):] if chat["id"].startswith(prefix) else chat["id"]
        result.append({
            "id":       raw_id,
            "title":    chat["title"],
            "pinned":   bool(chat["pinned"]),
            "starred":  bool(chat["starred"]),
            "messages": [{"role": m["role"], "text": m["content"]} for m in msgs],
            "sources":  [_json.loads(s["source_json"]) for s in srcs],
        })
    db.close()
    return result


@app.post("/chats/{chat_id}/pin")
def toggle_pin(chat_id: str, user: dict = Depends(get_current_user)):
    scoped = f"{user['sub']}_{chat_id}"
    db = get_db()
    db.execute(
        "UPDATE chats SET pinned = CASE WHEN pinned = 1 THEN 0 ELSE 1 END WHERE id = ? AND user_id = ?",
        (scoped, int(user["sub"])),
    )
    db.commit()
    row = db.execute("SELECT pinned FROM chats WHERE id = ?", (scoped,)).fetchone()
    db.close()
    return {"pinned": bool(row["pinned"]) if row else False}


@app.post("/chats/{chat_id}/star")
def toggle_star(chat_id: str, user: dict = Depends(get_current_user)):
    scoped = f"{user['sub']}_{chat_id}"
    db = get_db()
    db.execute(
        "UPDATE chats SET starred = CASE WHEN starred = 1 THEN 0 ELSE 1 END WHERE id = ? AND user_id = ?",
        (scoped, int(user["sub"])),
    )
    db.commit()
    row = db.execute("SELECT starred FROM chats WHERE id = ?", (scoped,)).fetchone()
    db.close()
    return {"starred": bool(row["starred"]) if row else False}


@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: str, user: dict = Depends(get_current_user)):
    scoped = f"{user['sub']}_{chat_id}"
    db = get_db()
    db.execute("DELETE FROM messages WHERE chat_id = ?", (scoped,))
    db.execute("DELETE FROM sources WHERE chat_id = ?", (scoped,))
    db.execute("DELETE FROM chats WHERE id = ? AND user_id = ?", (scoped, int(user["sub"])))
    db.commit()
    db.close()
    clear_memory(scoped)
    return {"status": "deleted"}


@app.post("/clear")
def clear(req: ClearRequest, user: dict = Depends(get_current_user)):
    scoped_session = f"{user['sub']}_{req.session_id}"
    clear_memory(scoped_session)
    return {"status": "cleared"}


@app.get("/health")
def health():
    return {"status": "ok", "version": os.getenv("APP_VERSION", "dev")}
