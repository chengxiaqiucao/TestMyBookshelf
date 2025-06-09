from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import logging
from datetime import datetime

from app.models.database import get_db_connection

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

@router.get("/")
async def list_reading_plans(request: Request):
    """列出所有阅读计划"""
    logger.debug("获取阅读计划列表")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取所有阅读计划
        cursor.execute("""
            SELECT rp.id, b.title, rp.planner, rp.start_date, rp.end_date, 
                   rp.status, rp.progress, rp.description
            FROM reading_plans rp
            JOIN books b ON rp.book_id = b.id
            ORDER BY rp.start_date DESC
        """)
        
        reading_plans = [
            {
                "id": row[0],
                "book_title": row[1],
                "planner": row[2],
                "start_date": row[3],
                "end_date": row[4],
                "status": row[5],
                "progress": row[6],
                "description": row[7]
            }
            for row in cursor.fetchall()
        ]
        
        return templates.TemplateResponse(
            "reading_plans/list.html", 
            {"request": request, "reading_plans": reading_plans}
        )
    finally:
        conn.close()

@router.get("/add")
async def add_reading_plan_form(request: Request):
    """显示添加阅读计划表单"""
    logger.debug("显示添加阅读计划表单")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取所有书籍
        cursor.execute("SELECT id, title FROM books ORDER BY title")
        books = [{"id": row[0], "title": row[1]} for row in cursor.fetchall()]
        
        return templates.TemplateResponse(
            "reading_plans/add.html", 
            {"request": request, "books": books}
        )
    finally:
        conn.close()

@router.post("/add")
async def add_reading_plan(
    request: Request,
    book_id: int = Form(...),
    planner: str = Form(...),
    start_date: str = Form(...),
    end_date: Optional[str] = Form(None),
    status: str = Form(...),
    progress: int = Form(...),
    notes: Optional[str] = Form(None)
):
    """添加新的阅读计划"""
    logger.debug(f"添加阅读计划: 书籍ID={book_id}, 计划人={planner}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 插入阅读计划
        cursor.execute(
            """
            INSERT INTO reading_plans 
            (book_id, planner, start_date, end_date, status, progress, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (book_id, planner, start_date, end_date, status, progress, notes)
        )
        conn.commit()
        
        return RedirectResponse(
            url="/reading-plans",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"添加阅读计划失败: {str(e)}")
        conn.rollback()
        
        # 获取所有书籍以重新渲染表单
        cursor.execute("SELECT id, title FROM books ORDER BY title")
        books = [{"id": row[0], "title": row[1]} for row in cursor.fetchall()]
        
        return templates.TemplateResponse(
            "reading_plans/add.html",
            {
                "request": request,
                "books": books,
                "error": f"添加阅读计划失败: {str(e)}",
                "form_data": {
                    "book_id": book_id,
                    "planner": planner,
                    "start_date": start_date,
                    "end_date": end_date,
                    "status": status,
                    "progress": progress,
                    "notes": notes
                }
            },
            status_code=400
        )
    finally:
        conn.close()

@router.get("/{reading_plan_id}")
async def view_reading_plan(request: Request, reading_plan_id: int):
    """查看阅读计划详情"""
    logger.debug(f"查看阅读计划详情: ID={reading_plan_id}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取阅读计划详情
        cursor.execute(
            """
            SELECT rp.id, b.title, rp.planner, rp.start_date, rp.end_date, 
                   rp.status, rp.progress, rp.description, b.id as book_id
            FROM reading_plans rp
            JOIN books b ON rp.book_id = b.id
            WHERE rp.id = ?
            """,
            (reading_plan_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="阅读计划不存在")
        
        reading_plan = {
            "id": row[0],
            "book_title": row[1],
            "planner": row[2],
            "start_date": row[3],
            "end_date": row[4],
            "status": row[5],
            "progress": row[6],
            "description": row[7],
            "book_id": row[8]
        }
        
        return templates.TemplateResponse(
            "reading_plans/view.html", 
            {"request": request, "reading_plan": reading_plan}
        )
    finally:
        conn.close()

@router.get("/{reading_plan_id}/edit")
async def edit_reading_plan_form(request: Request, reading_plan_id: int):
    """显示编辑阅读计划表单"""
    logger.debug(f"显示编辑阅读计划表单: ID={reading_plan_id}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取阅读计划详情
        cursor.execute(
            """
            SELECT rp.id, rp.book_id, b.title, rp.planner, rp.start_date, rp.end_date, 
                   rp.status, rp.progress, rp.notes
            FROM reading_plans rp
            JOIN books b ON rp.book_id = b.id
            WHERE rp.id = ?
            """,
            (reading_plan_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="阅读计划不存在")
        
        reading_plan = {
            "id": row[0],
            "book_id": row[1],
            "book_title": row[2],
            "planner": row[3],
            "start_date": row[4],
            "end_date": row[5],
            "status": row[6],
            "progress": row[7],
            "notes": row[8]
        }
        
        # 获取所有书籍
        cursor.execute("SELECT id, title FROM books ORDER BY title")
        books = [{"id": row[0], "title": row[1]} for row in cursor.fetchall()]
        
        return templates.TemplateResponse(
            "reading_plans/edit.html", 
            {"request": request, "reading_plan": reading_plan, "books": books}
        )
    finally:
        conn.close()

@router.post("/{reading_plan_id}/edit")
async def edit_reading_plan(
    request: Request,
    reading_plan_id: int,
    book_id: int = Form(...),
    planner: str = Form(...),
    start_date: str = Form(...),
    end_date: Optional[str] = Form(None),
    status: str = Form(...),
    progress: int = Form(...),
    notes: Optional[str] = Form(None)
):
    """更新阅读计划"""
    logger.debug(f"更新阅读计划: ID={reading_plan_id}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 更新阅读计划
        cursor.execute(
            """
            UPDATE reading_plans 
            SET book_id = ?, planner = ?, start_date = ?, end_date = ?, 
                status = ?, progress = ?, notes = ?
            WHERE id = ?
            """,
            (book_id, planner, start_date, end_date, status, progress, notes, reading_plan_id)
        )
        conn.commit()
        
        return RedirectResponse(
            url=f"/reading-plans/{reading_plan_id}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"更新阅读计划失败: {str(e)}")
        conn.rollback()
        
        # 获取所有书籍以重新渲染表单
        cursor.execute("SELECT id, title FROM books ORDER BY title")
        books = [{"id": row[0], "title": row[1]} for row in cursor.fetchall()]
        
        return templates.TemplateResponse(
            "reading_plans/edit.html",
            {
                "request": request,
                "books": books,
                "error": f"更新阅读计划失败: {str(e)}",
                "reading_plan": {
                    "id": reading_plan_id,
                    "book_id": book_id,
                    "planner": planner,
                    "start_date": start_date,
                    "end_date": end_date,
                    "status": status,
                    "progress": progress,
                    "notes": notes
                }
            },
            status_code=400
        )
    finally:
        conn.close()

@router.post("/{reading_plan_id}/delete")
async def delete_reading_plan(request: Request, reading_plan_id: int):
    """删除阅读计划"""
    logger.debug(f"删除阅读计划: ID={reading_plan_id}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 删除阅读计划
        cursor.execute("DELETE FROM reading_plans WHERE id = ?", (reading_plan_id,))
        conn.commit()
        
        return RedirectResponse(
            url="/reading-plans",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"删除阅读计划失败: {str(e)}")
        conn.rollback()
        
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": f"删除阅读计划失败: {str(e)}"
            },
            status_code=500
        )
    finally:
        conn.close()