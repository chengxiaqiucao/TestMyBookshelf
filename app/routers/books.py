from fastapi import APIRouter, Request, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime
from ..models.database import execute_query, execute_update, get_db_connection
from fastapi import HTTPException
from ..config import TEMPLATES_DIR

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@router.get("/add", response_class=HTMLResponse)
async def add_book_form(request: Request):
    """添加图书表单"""
    return templates.TemplateResponse("book_add.html", {"request": request})

@router.post("/add")
async def add_book(
    title: str = Form(...),
    author: str = Form(None),
    isbn: str = Form(None),
    publisher: str = Form(None),
    publish_date: str = Form(None),
    description: str = Form(None),
    cover_image: UploadFile = File(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO books (title, author, isbn, publisher, publish_date, description) VALUES (?, ?, ?, ?, ?, ?)",
        (title, author, isbn, publisher, publish_date, description)
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/books", status_code=303)

@router.get("/{book_id}", response_class=HTMLResponse)
async def book_detail(request: Request, book_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    conn.close()
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    return templates.TemplateResponse("book_detail.html", {"request": request, "book": book})

@router.post("/{book_id}/update")
async def update_book(
    book_id: int,
    title: str = Form(...),
    author: str = Form(None),
    isbn: str = Form(None),
    publisher: str = Form(None),
    publish_date: str = Form(None),
    description: str = Form(None),
    cover_image: UploadFile = File(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE books SET title = ?, author = ?, isbn = ?, publisher = ?, publish_date = ?, description = ? WHERE id = ?",
        (title, author, isbn, publisher, publish_date, description, book_id)
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/books/{book_id}", status_code=303)

@router.post("/{book_id}/delete")
async def delete_book(book_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/books", status_code=303)

@router.get("/", response_class=HTMLResponse)
async def book_list(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取总记录数
    cursor.execute("SELECT COUNT(*) FROM books")
    total_books = cursor.fetchone()[0]
    
    # 计算总页数
    total_pages = (total_books + per_page - 1) // per_page
    
    # 获取当前页的数据
    offset = (page - 1) * per_page
    cursor.execute("SELECT * FROM books ORDER BY id DESC LIMIT ? OFFSET ?", (per_page, offset))
    books = cursor.fetchall()
    
    conn.close()
    
    return templates.TemplateResponse(
        "book_list.html",
        {
            "request": request,
            "books": books,
            "page": page,
            "per_page": per_page,
            "total_books": total_books,
            "total_pages": total_pages
        }
    ) 