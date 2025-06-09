import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
from pathlib import Path
import os

# 创建应用
app = FastAPI(title="我的书架")

# 确保日志目录存在
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 导入自定义日志配置
from app.utils.logger import setup_logger

# 配置日志
logger = setup_logger()

# 配置静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="app/templates")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
from app.routers import books, plans, reading_plans, statistics

# 注册路由
app.include_router(books.router, prefix="/books", tags=["books"])
app.include_router(plans.router, prefix="/plans", tags=["plans"])
app.include_router(reading_plans.router, prefix="/reading-plans", tags=["reading_plans"])
app.include_router(statistics.router, prefix="/statistics", tags=["statistics"])

from app.models.database import get_db_connection

@app.get("/")
async def root(request: Request):
    """首页"""
    logger.debug("访问首页")
    
    # 获取数据库连接
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取统计数据
        stats = {}
        
        # 获取总书籍数
        cursor.execute("SELECT COUNT(*) FROM books")
        stats['total_books'] = cursor.fetchone()[0]
        
        # 获取已读书籍数
        cursor.execute("SELECT COUNT(*) FROM reading_plans WHERE status = '已完成'")
        stats['read_books'] = cursor.fetchone()[0]
        
        # 获取正在阅读的书籍数
        cursor.execute("SELECT COUNT(*) FROM reading_plans WHERE status = '进行中'")
        stats['reading_books'] = cursor.fetchone()[0]
        
        # 获取待读书籍数（总书籍数减去已读和正在读的）
        stats['to_read_books'] = stats['total_books'] - stats['read_books'] - stats['reading_books']
        
        # 获取总投入金额
        cursor.execute("SELECT COALESCE(SUM(purchase_price), 0) FROM books")
        stats['total_investment'] = cursor.fetchone()[0]
        
        # 获取阅读计划总数
        cursor.execute("SELECT COUNT(*) FROM reading_plans")
        stats['total_plans'] = cursor.fetchone()[0]
        
        # 获取最近添加的书籍
        cursor.execute("""
            SELECT id, title, author, category, purchase_date 
            FROM books 
            ORDER BY id DESC 
            LIMIT 4
        """)
        recent_books = [
            {
                "id": row[0],
                "title": row[1],
                "author": row[2],
                "category": row[3],
                "purchase_date": row[4]
            }
            for row in cursor.fetchall()
        ]
        
        # 获取进行中的阅读计划
        cursor.execute("""
            SELECT rp.id, b.title as book_title, rp.planner, rp.start_date, rp.end_date, 
                   rp.status, rp.progress
            FROM reading_plans rp
            JOIN books b ON rp.book_id = b.id
            WHERE rp.status = '进行中'
            ORDER BY rp.start_date DESC
            LIMIT 3
        """)
        active_plans = [
            {
                "id": row[0],
                "book_title": row[1],
                "planner": row[2],
                "start_date": row[3],
                "end_date": row[4],
                "status": row[5],
                "progress": row[6]
            }
            for row in cursor.fetchall()
        ]
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": stats,
            "recent_books": recent_books,
            "active_plans": active_plans
        })
    finally:
        conn.close()

if __name__ == "__main__":
    # 确保必要的目录存在
    Path("static/uploads").mkdir(parents=True, exist_ok=True)
    
    # 启动应用
    logger.info("启动应用服务器...")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )