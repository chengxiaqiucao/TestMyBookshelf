"""图书管理（修复 S0 全量、S1-F06/F07/F08/F10、S1-R08）。

修复要点：LIKE 模糊搜索、中文校验、列名访问、UUID 文件名、空状态、数据隔离。
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Request, Form, UploadFile, File, Query, HTTPException
from fastapi.responses import RedirectResponse

from ..config import UPLOAD_DIR
from ..models.database import get_db_connection
from ..auth import require_user
from ..templates_helpers import render
from ..utils.i18n import resolve_lang

router = APIRouter()
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def _save_cover(upload: Optional[UploadFile]) -> Optional[str]:
    if not upload or not upload.filename:
        return None
    ext = "." + upload.filename.rsplit(".", 1)[-1].lower() if "." in upload.filename else ""
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="不支持的图片格式")
    name = f"{uuid.uuid4().hex}{ext}"  # S1-F10：UUID 文件名
    (UPLOAD_DIR / name).write_bytes(upload.file.read())
    return f"/static/uploads/{name}"


def _validate(title, author, price_str, lang):
    if not title or len(title) > 100:
        raise HTTPException(400, "书名必填且不超过100字符")
    if not author or len(author) > 50:
        raise HTTPException(400, "作者必填且不超过50字符")
    if price_str not in (None, ""):
        try:
            if float(price_str) < 0:
                raise ValueError
        except (TypeError, ValueError):
            raise HTTPException(400, "请输入有效数字")


@router.get("/")
async def book_list(request: Request, page: int = Query(1, ge=1), per_page: int = Query(10, ge=1, le=100),
                    search: str = Query(None)):
    user = require_user(request)
    lang = resolve_lang(request.cookies.get("lang"), user.lang)
    conn = get_db_connection()
    try:
        where, params = "WHERE b.owner_id = ?", [user.id]
        if search:
            where += " AND (LOWER(b.title) LIKE LOWER(?) OR LOWER(b.author) LIKE LOWER(?))"
            params += [f"%{search}%", f"%{search}%"]
        total = conn.execute(f"SELECT COUNT(*) FROM books b {where}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT b.* FROM books b {where} ORDER BY b.id DESC LIMIT ? OFFSET ?",
            params + [per_page, (page - 1) * per_page]).fetchall()
        return render(request, "book_list.html", {
            "books": [dict(r) for r in rows], "lang": lang, "current_user": user, "search": search or "",
            "page": page, "total_pages": max(1, (total + per_page - 1) // per_page)})
    finally:
        conn.close()


@router.get("/add")
async def add_form(request: Request):
    user = require_user(request)
    lang = resolve_lang(request.cookies.get("lang"), user.lang)
    return render(request, "book_add.html", {"lang": lang, "current_user": user, "error": None})


@router.post("/add")
async def add_book(request: Request, title: str = Form(...), author: str = Form(...),
                   isbn: str = Form(None), publisher: str = Form(None), publish_date: str = Form(None),
                   description: str = Form(None), purchase_date: str = Form(None), purchaser: str = Form(None),
                   purchase_price: str = Form(None), reading_status: str = Form("待读"),
                   storage_status: str = Form("在库"), category: str = Form(None), rating: int = Form(3),
                   cover_image: UploadFile = File(None)):
    user = require_user(request)
    lang = resolve_lang(request.cookies.get("lang"), user.lang)
    try:
        _validate(title, author, purchase_price, lang)
        cover = _save_cover(cover_image)
        conn = get_db_connection()
        try:
            conn.execute("""INSERT INTO books(title, author, isbn, publisher, publish_date, description,
                purchase_date, purchaser, purchase_price, reading_status, storage_status, category, rating,
                cover_image, owner_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (title, author, isbn, publisher, publish_date, description, purchase_date, purchaser,
                 purchase_price or 0, reading_status, storage_status, category, rating, cover, user.id))
            conn.commit()
        finally:
            conn.close()
        return RedirectResponse(url="/books", status_code=303)
    except HTTPException as e:
        return render(request, "book_add.html", {"lang": lang, "current_user": user, "error": e.detail}, status_code=400)


@router.get("/{book_id}")
async def book_detail(book_id: int, request: Request):
    user = require_user(request)
    lang = resolve_lang(request.cookies.get("lang"), user.lang)
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM books WHERE id=? AND owner_id=?", (book_id, user.id)).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "图书不存在")
    return render(request, "book_detail.html", {"book": dict(row), "lang": lang, "current_user": user})


@router.get("/{book_id}/edit")
async def edit_form(book_id: int, request: Request):
    user = require_user(request)
    lang = resolve_lang(request.cookies.get("lang"), user.lang)
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM books WHERE id=? AND owner_id=?", (book_id, user.id)).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "图书不存在")
    return render(request, "book_edit.html", {"book": dict(row), "lang": lang, "current_user": user, "error": None})


@router.post("/{book_id}/edit")
async def edit_book(book_id: int, request: Request, title: str = Form(...), author: str = Form(...),
                    description: str = Form(None), publish_date: str = Form(None), purchase_date: str = Form(None),
                    purchaser: str = Form(None), purchase_price: str = Form(None), reading_status: str = Form("待读"),
                    storage_status: str = Form("在库"), category: str = Form(None), rating: int = Form(3),
                    cover_image: UploadFile = File(None)):
    user = require_user(request)
    lang = resolve_lang(request.cookies.get("lang"), user.lang)
    try:
        _validate(title, author, purchase_price, lang)
        conn = get_db_connection()
        try:
            # S1-F07：列名访问，不再使用 book[13]/book[15]
            conn.execute("""UPDATE books SET title=?, author=?, description=?, publish_date=?, purchase_date=?,
                purchaser=?, purchase_price=?, reading_status=?, storage_status=?, category=?, rating=?,
                cover_image=COALESCE(?, cover_image) WHERE id=? AND owner_id=?""",
                (title, author, description, publish_date, purchase_date, purchaser, purchase_price or 0,
                 reading_status, storage_status, category, rating, _save_cover(cover_image), book_id, user.id))
            conn.commit()
        finally:
            conn.close()
        return RedirectResponse(url=f"/books/{book_id}", status_code=303)
    except HTTPException as e:
        return render(request, "book_edit.html", {"error": e.detail, "lang": lang, "current_user": user}, status_code=400)


@router.post("/{book_id}/delete")
async def delete_book(book_id: int, request: Request):
    user = require_user(request)
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM books WHERE id=? AND owner_id=?", (book_id, user.id))
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/books", status_code=303)
