from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ..models.database import get_db_connection
from ..config import TEMPLATES_DIR
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@router.get("/", response_class=HTMLResponse)
@router.get("/{path:path}", response_class=HTMLResponse)
async def statistics(request: Request, path: str = None):
    """统计页面"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取基本统计数据
        stats = {
            "total_books": cursor.execute("SELECT COUNT(*) FROM books").fetchone()[0],
            "read_books": cursor.execute("SELECT COUNT(*) FROM books WHERE reading_status = '已读'").fetchone()[0],
            "reading_books": cursor.execute("SELECT COUNT(*) FROM books WHERE reading_status = '正在读'").fetchone()[0],
            "to_read_books": cursor.execute("SELECT COUNT(*) FROM books WHERE reading_status = '待读'").fetchone()[0],
            "total_investment": cursor.execute("SELECT COALESCE(SUM(purchase_price), 0) FROM books").fetchone()[0],
            "avg_rating": 0,  # 暂时不显示评分
            "total_plans": cursor.execute("SELECT COUNT(*) FROM reading_plans").fetchone()[0],
            "active_plans": cursor.execute("SELECT COUNT(*) FROM reading_plans WHERE status = '进行中'").fetchone()[0],
            "completed_plans": cursor.execute("SELECT COUNT(*) FROM reading_plans WHERE status = '已完成'").fetchone()[0]
        }
        
        # 获取阅读状态分布
        reading_status = cursor.execute("""
            SELECT reading_status, COUNT(*) as count 
            FROM books 
            GROUP BY reading_status
        """).fetchall()
        
        # 获取每月阅读计划数量
        monthly_plans = cursor.execute("""
            SELECT strftime('%Y-%m', start_date) as month, COUNT(*) as count 
            FROM reading_plans 
            GROUP BY month 
            ORDER BY month DESC 
            LIMIT 12
        """).fetchall()
        
        # 获取每月购买图书数量
        monthly_purchases = cursor.execute("""
            SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
            FROM books 
            GROUP BY month 
            ORDER BY month DESC 
            LIMIT 12
        """).fetchall()
        
        # 获取每月阅读完成数量
        monthly_completions = cursor.execute("""
            SELECT strftime('%Y-%m', updated_at) as month, COUNT(*) as count 
            FROM books 
            WHERE reading_status = '已读' 
            GROUP BY month 
            ORDER BY month DESC 
            LIMIT 12
        """).fetchall()
        
        return templates.TemplateResponse(
            "statistics.html",
            {
                "request": request,
                "stats": stats,
                "reading_status": reading_status,
                "monthly_plans": monthly_plans,
                "monthly_purchases": monthly_purchases,
                "monthly_completions": monthly_completions
            }
        )
    except Exception as e:
        logger.error(f"统计页面查询失败: {str(e)}")
        # 如果发生错误，返回空数据
        return templates.TemplateResponse(
            "statistics.html",
            {
                "request": request,
                "stats": {
                    "total_books": 0,
                    "read_books": 0,
                    "reading_books": 0,
                    "to_read_books": 0,
                    "total_investment": 0,
                    "avg_rating": 0,
                    "total_plans": 0,
                    "active_plans": 0,
                    "completed_plans": 0
                },
                "reading_status": [],
                "monthly_plans": [],
                "monthly_purchases": [],
                "monthly_completions": []
            }
        )
    finally:
        conn.close() 