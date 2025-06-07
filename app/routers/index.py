from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.models.database import get_db_connection
from app.utils.helpers import format_datetime, format_price
from app.utils.logger import setup_logger

logger = setup_logger()
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取统计数据
    cursor.execute("""
        SELECT 
            COUNT(*) as total_books,
            SUM(CASE WHEN reading_status = '已读' THEN 1 ELSE 0 END) as read_books,
            SUM(CASE WHEN reading_status = '正在读' THEN 1 ELSE 0 END) as reading_books,
            SUM(CASE WHEN reading_status = '待读' THEN 1 ELSE 0 END) as to_read_books,
            SUM(purchase_price) as total_investment
        FROM books
    """)
    book_stats = cursor.fetchone()
    
    stats = {
        'total_books': book_stats[0] or 0,
        'read_books': book_stats[1] or 0,
        'reading_books': book_stats[2] or 0,
        'to_read_books': book_stats[3] or 0,
        'total_investment': book_stats[4] or 0
    }

    # 获取计划总数
    cursor.execute("SELECT COUNT(*) as total_plans FROM reading_plans")
    total_plans_result = cursor.fetchone()
    if total_plans_result:
        stats['total_plans'] = total_plans_result[0]
    
    # 获取进行中的计划数量
    cursor.execute("SELECT COUNT(*) as active_plans FROM reading_plans WHERE status = '进行中'")
    active_plans_result = cursor.fetchone()
    if active_plans_result:
        stats['active_plans'] = active_plans_result[0]
    
    # 获取最近添加的书籍
    cursor.execute("""
        SELECT 
            id,
            title,
            author,
            reading_status,
            cover_image,
            category,
            purchase_date
        FROM books
        ORDER BY created_at DESC
        LIMIT 3
    """)
    recent_books = cursor.fetchall()
    
    # 获取进行中的阅读计划
    cursor.execute("""
        SELECT 
            rp.id,
            b.title as book_title,
            rp.planner,
            rp.priority,
            rp.status,
            rp.progress,
            rp.start_date,
            rp.end_date
        FROM reading_plans rp
        JOIN books b ON rp.book_id = b.id
        WHERE rp.status = '进行中'
        ORDER BY rp.created_at DESC
        LIMIT 5
    """)
    active_plans = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "stats": stats,
            "recent_books": recent_books,
            "active_plans": active_plans
        }
    ) 