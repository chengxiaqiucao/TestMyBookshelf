"""认证与授权（修复 S1-F01、S1-I03；注入 S2-F01 靶点）。

S2-F01（注入靶点）：login() 中不重新生成 session ID，保留登录前的会话标识，
形成会话固定（Session Fixation）测试点。此行为不在需求文档中描述。
"""
import uuid

from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext

from .models.database import execute_query, execute_update
from .utils.i18n import t, resolve_lang
from .templates_helpers import render
from .config import SUPPORTED_LANGS, DEFAULT_LANG

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 简易内存会话存储（演示用；生产应使用持久化会话）
SESSIONS = {}


class LoginUser:
    def __init__(self, id, username, role, lang):
        self.id, self.username, self.role, self.lang = id, username, role, lang


def current_user(request: Request):
    sid = request.cookies.get("session_id")
    uid = SESSIONS.get(sid)
    if not uid:
        return None
    rows = execute_query("SELECT id, username, role, lang FROM users WHERE id = ?", (uid,))
    if not rows:
        return None
    r = rows[0]
    return LoginUser(r["id"], r["username"], r["role"], r["lang"])


def require_user(request: Request) -> LoginUser:
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    return user


@router.get("/login")
async def login_form(request: Request):
    lang = resolve_lang(request.cookies.get("lang"))
    return render(request, "login.html", {"lang": lang})


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    rows = execute_query("SELECT id, username, password, role, lang FROM users WHERE username = ?", (username,))
    lang = resolve_lang(request.cookies.get("lang"))
    if not rows or not pwd_context.verify(password, rows[0]["password"]):
        raise HTTPException(status_code=400, detail=t(lang, "error_login"))

    user = rows[0]
    # ---- S2-F01 注入靶点：未重新生成会话 ID（会话固定）----
    sid = request.cookies.get("session_id") or str(uuid.uuid4())
    SESSIONS[sid] = user["id"]

    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie("session_id", sid, httponly=True)
    return resp


@router.get("/register")
async def register_form(request: Request):
    lang = resolve_lang(request.cookies.get("lang"))
    return render(request, "register.html", {"lang": lang})


@router.post("/register")
async def register(request: Request, username: str = Form(...), password: str = Form(...), email: str = Form(None)):
    lang = resolve_lang(request.cookies.get("lang"))
    if not username or not password:
        raise HTTPException(status_code=400, detail=t(lang, "error_required"))
    if execute_query("SELECT 1 FROM users WHERE username = ?", (username,)):
        raise HTTPException(status_code=400, detail="用户名已存在")

    hashed = pwd_context.hash(password)
    execute_update("INSERT INTO users(username, password, email, role, lang) VALUES (?, ?, ?, 'user', ?)",
                   (username, hashed, email, lang))
    return RedirectResponse(url="/login", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    sid = request.cookies.get("session_id")
    if sid:
        SESSIONS.pop(sid, None)
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("session_id")
    return resp


@router.get("/lang/{lang}")
async def switch_lang(lang: str, request: Request):
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    user = current_user(request)
    if user:
        execute_update("UPDATE users SET lang = ? WHERE id = ?", (lang, user.id))
    resp = RedirectResponse(url=request.headers.get("referer", "/"), status_code=303)
    resp.set_cookie("lang", lang)
    return resp
