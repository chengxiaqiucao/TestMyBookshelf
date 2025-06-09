from fastapi import APIRouter, Request, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime
from ..models.database import execute_query, execute_update, get_db_connection
from fastapi import HTTPException
from ..config import TEMPLATES_DIR, STATIC_DIR
import os
import re
import shutil
import logging
from pathlib import Path
from werkzeug.utils import secure_filename

# 获取日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除所有特殊字符"""
    if not filename or filename == 'None':
        return None
    # 移除所有非字母数字字符，只保留扩展名
    name, ext = os.path.splitext(filename)
    # 使用正则表达式只保留字母、数字和下划线
    safe_name = re.sub(r'[^a-zA-Z0-9_]', '', name)
    # 如果清理后的名称为空，使用时间戳
    if not safe_name:
        safe_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_name}{ext}"

def format_date(date_str: str) -> str:
    """格式化日期字符串为 yyyy-MM-dd 格式"""
    if not date_str or date_str == 'None':
        return ''
    try:
        # 尝试多种日期格式
        date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d']
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                # 检查日期是否在合理范围内（例如：1900-01-01 到 2100-12-31）
                if date_obj.year < 1900 or date_obj.year > 2100:
                    return ''
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        return ''
    except Exception as e:
        print(f"Error formatting date {date_str}: {e}")
        return ''

def save_upload_file(upload_file: UploadFile) -> Optional[str]:
    """保存上传的文件到静态目录"""
    if not upload_file:
        return None
        
    try:
        # 确保文件名是安全的
        safe_filename = sanitize_filename(upload_file.filename)
        if not safe_filename:
            return None
            
        # 创建目标目录
        upload_dir = STATIC_DIR / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(safe_filename)[1]
        unique_filename = f"{timestamp}{file_extension}"
        
        # 完整的文件路径
        file_path = upload_dir / unique_filename
        
        # 保存文件
        with open(file_path, "wb") as f:
            content = upload_file.file.read()
            f.write(content)
            
        logger.info(f"文件已保存: {file_path}")
        return f"uploads/{unique_filename}"
    except Exception as e:
        logger.error(f"保存文件时出错: {e}")
        return None
    finally:
        upload_file.file.close()

def get_safe_file_path(file_path: str) -> str:
    """获取安全的文件路径，如果文件存在则重命名"""
    if not file_path or file_path == 'None':
        return None
        
    # 如果文件名已经是安全的，直接返回
    if os.path.exists(os.path.join(STATIC_DIR, file_path)):
        return file_path
        
    # 生成新的安全文件名
    safe_filename = sanitize_filename(file_path)
    if not safe_filename:
        return None
        
    # 如果原文件存在，重命名它
    old_path = os.path.join(STATIC_DIR, file_path)
    new_path = os.path.join(STATIC_DIR, safe_filename)
    
    try:
        if os.path.exists(old_path):
            # 如果目标文件已存在，添加时间戳
            if os.path.exists(new_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(safe_filename)
                safe_filename = f"{name}_{timestamp}{ext}"
                new_path = os.path.join(STATIC_DIR, safe_filename)
            shutil.move(old_path, new_path)
            return safe_filename
        return None
    except Exception as e:
        print(f"Error moving file: {e}")
        return None

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
    cover_image: UploadFile = File(None),
    reading_status: str = Form(None),
    purchase_price: float = Form(None),
    category: str = Form(None),
    purchase_date: str = Form(None),
    purchaser: str = Form(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 处理文件上传
    cover_image_path = None
    if cover_image:
        cover_image_path = save_upload_file(cover_image)
    
    # 插入数据库
    cursor.execute(
        """INSERT INTO books (
            title, author, isbn, publisher, publish_date, description,
            reading_status, purchase_price, category, purchase_date,
            purchaser, cover_image
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (title, author, isbn, publisher, publish_date, description,
         reading_status, purchase_price, category, purchase_date,
         purchaser, cover_image_path)
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

@router.get("/{book_id}/edit", response_class=HTMLResponse)
async def edit_book(request: Request, book_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    conn.close()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # 将元组转换为列表以便修改
    book = list(book)
    
    # 格式化日期
    if len(book) > 4:
        book[4] = format_date(book[4])  # 出版日期
    if len(book) > 12:
        book[12] = format_date(book[12])  # 购买日期
    
    # 安全地处理文件路径
    try:
        # 封面图片 (索引13)
        if len(book) > 13 and book[13] and book[13] != 'None':
            book[13] = get_safe_file_path(book[13])
            if book[13]:  # 如果文件路径已更新，更新数据库
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE books SET cover_image = ? WHERE id = ?", (book[13], book_id))
                conn.commit()
                conn.close()
        
        # 笔记文件 (索引15)
        if len(book) > 15 and book[15] and book[15] != 'None':
            book[15] = get_safe_file_path(book[15])
            if book[15]:  # 如果文件路径已更新，更新数据库
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE books SET notes_file = ? WHERE id = ?", (book[15], book_id))
                conn.commit()
                conn.close()
    except Exception as e:
        print(f"Error processing file paths: {e}")
        # 继续处理，不中断请求
    
    return templates.TemplateResponse(
        "book_edit.html",
        {"request": request, "book": book}
    )

@router.post("/{book_id}/update")
async def update_book(
    book_id: int,
    title: str = Form(...),
    author: str = Form(None),
    isbn: str = Form(None),
    publisher: str = Form(None),
    publish_date: str = Form(None),
    description: str = Form(None),
    cover_image: UploadFile = File(None),
    reading_status: str = Form(None),
    purchase_price: float = Form(None),
    category: str = Form(None),
    purchase_date: str = Form(None),
    purchaser: str = Form(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 处理文件上传
    cover_image_path = None
    if cover_image:
        cover_image_path = save_upload_file(cover_image)
    
    # 更新数据库
    cursor.execute(
        """UPDATE books SET 
            title = ?, author = ?, isbn = ?, publisher = ?, 
            publish_date = ?, description = ?, reading_status = ?,
            purchase_price = ?, category = ?, purchase_date = ?,
            purchaser = ?, cover_image = COALESCE(?, cover_image)
            WHERE id = ?""",
        (title, author, isbn, publisher, publish_date, description,
         reading_status, purchase_price, category, purchase_date,
         purchaser, cover_image_path, book_id)
    )
    
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/books/{book_id}", status_code=303)

def get_book_by_id(book_id: int):
    """根据ID获取图书信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()
        conn.close()
        return book
    except Exception as e:
        logger.error(f"获取图书信息时出错 ID: {book_id}, 错误: {e}")
        raise

@router.post("/{book_id}")
async def delete_book(book_id: int, request: Request):
    """删除图书"""
    logger.info(f"尝试删除图书 ID: {book_id}")
    try:
        # 获取图书信息
        book = get_book_by_id(book_id)
        if not book:
            logger.warning(f"图书不存在 ID: {book_id}")
            raise HTTPException(status_code=404, detail="图书不存在")
            
        # 删除图书
        delete_book_by_id(book_id)
        logger.info(f"成功删除图书 ID: {book_id}")
        
        # 重定向到图书列表页面
        return RedirectResponse(url="/books", status_code=303)
    except Exception as e:
        logger.error(f"删除图书时出错 ID: {book_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def delete_book_by_id(book_id: int):
    """从数据库中删除图书"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 首先删除相关的图片文件
        cursor.execute("SELECT cover_image FROM books WHERE id = ?", (book_id,))
        result = cursor.fetchone()
        if result and result[0] and result[0] != 'None':
            try:
                image_path = STATIC_DIR / result[0]
                if image_path.exists():
                    image_path.unlink()
                    logger.info(f"删除图片文件: {image_path}")
            except Exception as e:
                logger.error(f"删除图片文件时出错: {e}")
        
        # 删除图书记录
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        logger.info(f"从数据库中删除图书 ID: {book_id}")
        
        conn.close()
    except Exception as e:
        logger.error(f"删除图书时出错 ID: {book_id}, 错误: {e}")
        raise

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