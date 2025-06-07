from fastapi import APIRouter, Request, Query, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models.database import get_db_connection
from app.utils.helpers import format_datetime, format_price
from typing import Optional
import uuid
import os
from pathlib import Path
import json
from datetime import datetime
from ..config import TEMPLATES_DIR
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def row_to_dict(row, row_type='plan'):
    """将数据库行转换为字典
    
    Args:
        row: 数据库行数据
        row_type: 行数据类型，'plan' 或 'book'
    """
    if row_type == 'plan':
        return {
            "id": row[0],
            "book_id": row[1],
            "plan_name": row[2],
            "description": row[3],
            "start_date": row[4],
            "end_date": row[5],
            "status": row[6],
            "priority": row[7],
            "progress": row[8],
            "planner": row[9],
            "created_at": row[10],
            "updated_at": row[11]
        }
    elif row_type == 'book':
        return {
            "id": row[0],
            "title": row[1]
        }
    return None

@router.get("/", response_class=HTMLResponse)
async def plan_list(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取所有书籍（用于添加计划时选择）
    cursor.execute("SELECT id, title FROM books")
    books = [row_to_dict(row, 'book') for row in cursor.fetchall()]
    
    # 获取总记录数
    cursor.execute("SELECT COUNT(*) FROM reading_plans")
    total_plans = cursor.fetchone()[0]
    
    # 计算总页数
    total_pages = (total_plans + per_page - 1) // per_page
    
    # 获取当前页的数据
    offset = (page - 1) * per_page
    cursor.execute("""
        SELECT p.*, b.title as book_title 
        FROM reading_plans p
        JOIN books b ON p.book_id = b.id
        ORDER BY p.id DESC 
        LIMIT ? OFFSET ?
    """, (per_page, offset))
    plans = cursor.fetchall()
    
    conn.close()
    
    return templates.TemplateResponse(
        "plans.html",
        {
            "request": request,
            "plans": plans,
            "books": books,
            "page": page,
            "per_page": per_page,
            "total_plans": total_plans,
            "total_pages": total_pages
        }
    )

@router.post("/add", response_class=RedirectResponse)
async def add_plan(
    book_id: int = Form(...),
    plan_name: str = Form(...),
    description: str = Form(None),
    start_date: str = Form(...),
    end_date: str = Form(None),
    status: str = Form("进行中"),
    priority: str = Form("中"),
    progress: int = Form(0),
    planner: str = Form(...)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO reading_plans (
                book_id, plan_name, description, start_date, end_date,
                status, priority, progress, planner, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            book_id, plan_name, description, start_date, end_date,
            status, priority, progress, planner
        ))
        conn.commit()
        return RedirectResponse(url="/plans", status_code=303)
    except Exception as e:
        logger.error(f"添加阅读计划失败: {str(e)}")
        raise HTTPException(status_code=500, detail="添加阅读计划失败")
    finally:
        conn.close()

@router.post("/{plan_id}/update", response_class=RedirectResponse)
async def update_plan(
    plan_id: int,
    book_id: int = Form(...),
    plan_name: str = Form(...),
    description: str = Form(None),
    start_date: str = Form(...),
    end_date: str = Form(None),
    status: str = Form(...),
    priority: str = Form(...),
    progress: int = Form(...),
    planner: str = Form(...)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE reading_plans SET
                book_id = ?,
                plan_name = ?,
                description = ?,
                start_date = ?,
                end_date = ?,
                status = ?,
                priority = ?,
                progress = ?,
                planner = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            book_id, plan_name, description, start_date, end_date,
            status, priority, progress, planner, plan_id
        ))
        conn.commit()
        return RedirectResponse(url="/plans", status_code=303)
    except Exception as e:
        logger.error(f"更新阅读计划失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新阅读计划失败")
    finally:
        conn.close()

@router.post("/{plan_id}/delete", response_class=RedirectResponse)
async def delete_plan(plan_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM reading_plans WHERE id = ?", (plan_id,))
        conn.commit()
        return RedirectResponse(url="/plans", status_code=303)
    except Exception as e:
        logger.error(f"删除阅读计划失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除阅读计划失败")
    finally:
        conn.close()

@router.get("/add", response_class=HTMLResponse)
async def add_plan_form(request: Request):
    """添加计划表单"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取所有书籍
    cursor.execute("SELECT id, title FROM books")
    books = [row_to_dict(row, 'book') for row in cursor.fetchall()]
    
    conn.close()
    
    return templates.TemplateResponse("plan_add.html", {
        "request": request,
        "books": books
    })

@router.get("/{plan_id}", response_class=HTMLResponse)
async def plan_detail(request: Request, plan_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reading_plans WHERE id = ?", (plan_id,))
    plan = cursor.fetchone()
    conn.close()
    if not plan:
        raise HTTPException(status_code=404, detail="阅读计划不存在")
    return templates.TemplateResponse("plan_detail.html", {"request": request, "plan": plan})

@router.post("/{plan_id}/edit")
async def edit_plan(
    plan_id: int,
    book_id: int = Form(...),
    planner: str = Form(...),
    description: str = Form(None),
    start_date: str = Form(...),
    end_date: str = Form(...),
    target_pages: int = Form(None),
    status: str = Form(...),
    priority: str = Form(...),
    notes: str = Form(None)
):
    """编辑计划"""
    try:
        # 更新数据库
        execute_update(
            """
            UPDATE reading_plans
            SET book_id = ?, planner = ?, description = ?, start_date = ?,
                end_date = ?, target_pages = ?, status = ?, priority = ?, notes = ?
            WHERE id = ?
            """,
            (
                book_id, planner, description, start_date, end_date,
                target_pages, status, priority, notes, plan_id
            )
        )
        
        return RedirectResponse(url=f"/plans/{plan_id}", status_code=303)
    except Exception as e:
        # 处理错误
        return {"error": str(e)}

@router.post("/{plan_id}/task/add")
async def add_task(
    plan_id: int,
    description: str = Form(...),
    start_time: str = Form(None),
    end_time: str = Form(None),
    executor: str = Form(None)
):
    """添加新任务"""
    try:
        execute_update(
            """
            INSERT INTO plan_tasks (
                plan_id, description, start_time, end_time,
                status, executor
            ) VALUES (?, ?, ?, ?, '未开始', ?)
            """,
            (plan_id, description, start_time, end_time, executor)
        )
        return RedirectResponse(url=f"/plans/{plan_id}", status_code=303)
    except Exception as e:
        return {"error": str(e)}

@router.post("/{plan_id}/task/{task_id}/update")
async def update_task_status(
    plan_id: int,
    task_id: int,
    status: str = Form(...)
):
    """更新任务状态"""
    try:
        execute_update(
            "UPDATE plan_tasks SET status = ? WHERE id = ? AND plan_id = ?",
            (status, task_id, plan_id)
        )
        return RedirectResponse(url=f"/plans/{plan_id}", status_code=303)
    except Exception as e:
        return {"error": str(e)} 