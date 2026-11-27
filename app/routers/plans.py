"""阅读计划（统一路由，修复 S1-F02/F03/F04、S1-R02/R03、S2-F09 靶点）。

S2-F09 靶点：WebSocket 推送的进度用未取整原始比例，与 HTTP 接口不同（在 ws.py 实现）。
"""
from fastapi import APIRouter, Request, Form, Query, HTTPException
from fastapi.responses import RedirectResponse

from ..models.database import get_db_connection
from ..auth import require_user
from ..templates_helpers import render
from ..utils.i18n import resolve_lang

router = APIRouter()


def _sync_progress(conn, plan_id):
    """S1-R02/R03：按任务完成比例更新进度，全部完成则计划状态改为已完成。"""
    total = conn.execute("SELECT COUNT(*) FROM tasks WHERE plan_id=?", (plan_id,)).fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM tasks WHERE plan_id=? AND status='已完成'", (plan_id,)).fetchone()[0]
    progress = round(done / total * 100) if total else 0
    status = "已完成" if total and done == total else "进行中"
    conn.execute("UPDATE reading_plans SET progress=?, status=?, updated_at=datetime('now') WHERE id=?",
                 (progress, status, plan_id))


@router.get("/")
async def plan_list(request: Request, page: int = Query(1, ge=1)):
    user = require_user(request)
    lang = resolve_lang(request.cookies.get("lang"), user.lang)
    conn = get_db_connection()
    try:
        plans = conn.execute("""SELECT p.*, b.title AS book_title FROM reading_plans p
            JOIN books b ON b.id=p.book_id WHERE p.owner_id=? ORDER BY p.id DESC LIMIT 20 OFFSET ?""",
            (user.id, (page - 1) * 20)).fetchall()
        books = conn.execute("SELECT id, title FROM books WHERE owner_id=?", (user.id,)).fetchall()
        return render(request, "plans.html", {
            "plans": [dict(p) for p in plans], "books": [dict(b) for b in books],
            "lang": lang, "current_user": user})
    finally:
        conn.close()


@router.get("/add")
async def add_form(request: Request):
    user = require_user(request)
    lang = resolve_lang(request.cookies.get("lang"), user.lang)
    conn = get_db_connection()
    try:
        books = conn.execute("SELECT id, title FROM books WHERE owner_id=?", (user.id,)).fetchall()
        return render(request, "plan_add.html", {
            "books": [dict(b) for b in books], "lang": lang, "current_user": user})
    finally:
        conn.close()


@router.post("/add")
async def add_plan(request: Request, book_id: int = Form(...), planner: str = Form(...),
                   description: str = Form(None), start_date: str = Form(...), end_date: str = Form(None),
                   status: str = Form("进行中"), priority: str = Form("中"), progress: int = Form(0)):
    user = require_user(request)
    conn = get_db_connection()
    try:
        conn.execute("""INSERT INTO reading_plans(book_id, planner, description, start_date, end_date,
            status, priority, progress, owner_id) VALUES (?,?,?,?,?,?,?,?,?)""",
            (book_id, planner, description, start_date, end_date, status, priority, progress, user.id))
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/plans", status_code=303)


@router.get("/{plan_id}")
async def plan_detail(plan_id: int, request: Request):
    user = require_user(request)
    lang = resolve_lang(request.cookies.get("lang"), user.lang)
    conn = get_db_connection()
    try:
        plan = conn.execute("""SELECT p.*, b.title AS book_title FROM reading_plans p
            JOIN books b ON b.id=p.book_id WHERE p.id=? AND p.owner_id=?""", (plan_id, user.id)).fetchone()
        if not plan:
            raise HTTPException(404, "计划不存在")
        tasks = conn.execute("SELECT * FROM tasks WHERE plan_id=? ORDER BY id", (plan_id,)).fetchall()
        return render(request, "plan_detail.html", {
            "plan": dict(plan), "tasks": [dict(t) for t in tasks], "lang": lang, "current_user": user})
    finally:
        conn.close()


@router.post("/{plan_id}/edit")
async def edit_plan(plan_id: int, request: Request, book_id: int = Form(...), planner: str = Form(...),
                    description: str = Form(None), start_date: str = Form(...), end_date: str = Form(None),
                    status: str = Form("进行中"), priority: str = Form("中"), progress: int = Form(0)):
    user = require_user(request)
    conn = get_db_connection()
    try:
        conn.execute("""UPDATE reading_plans SET book_id=?, planner=?, description=?, start_date=?, end_date=?,
            status=?, priority=?, progress=?, updated_at=datetime('now') WHERE id=? AND owner_id=?""",
            (book_id, planner, description, start_date, end_date, status, priority, progress, plan_id, user.id))
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url=f"/plans/{plan_id}", status_code=303)


@router.post("/{plan_id}/delete")
async def delete_plan(plan_id: int, request: Request):
    user = require_user(request)
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM reading_plans WHERE id=? AND owner_id=?", (plan_id, user.id))
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/plans", status_code=303)


@router.post("/{plan_id}/task/add")
async def add_task(plan_id: int, request: Request, title: str = Form(...), description: str = Form(None),
                   due_date: str = Form(None), executor: str = Form(None), priority: str = Form("中")):
    """S1-F02：统一写入 tasks 表。"""
    user = require_user(request)
    conn = get_db_connection()
    try:
        conn.execute("""INSERT INTO tasks(plan_id, title, description, due_date, executor, priority, owner_id)
            VALUES (?,?,?,?,?,?,?)""", (plan_id, title, description, due_date, executor, priority, user.id))
        _sync_progress(conn, plan_id)
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url=f"/plans/{plan_id}", status_code=303)


@router.post("/{plan_id}/task/{task_id}/update")
async def update_task(plan_id: int, task_id: int, request: Request, status: str = Form(...)):
    user = require_user(request)
    conn = get_db_connection()
    try:
        conn.execute("UPDATE tasks SET status=?, updated_at=datetime('now') WHERE id=? AND plan_id=? AND owner_id=?",
                     (status, task_id, plan_id, user.id))
        _sync_progress(conn, plan_id)
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url=f"/plans/{plan_id}", status_code=303)
