from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import sqlite3
from datetime import datetime
import re
import logging
import traceback
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="templates")

# 数据库初始化
def init_db():
    try:
        # 如果数据库文件存在，先删除它
        if os.path.exists('books.db'):
            os.remove('books.db')
            logger.info("删除旧的数据库文件")
        
        conn = sqlite3.connect('books.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            description TEXT CHECK(length(description) <= 500),
            publish_date TEXT,
            original_price REAL CHECK(original_price >= 0),
            purchase_price REAL CHECK(purchase_price >= 0),
            user_notes TEXT CHECK(length(user_notes) <= 1000),
            reading_status TEXT CHECK(reading_status IN ('待读', '已读', '正在读')) DEFAULT '待读',
            storage_status TEXT CHECK(storage_status IN ('在库', '借入', '借出', '归档')) DEFAULT '在库',
            rating INTEGER CHECK(rating BETWEEN 1 AND 5) DEFAULT 3
        )
        ''')

        # 插入示例数据
        sample_books = [
            (
                "三体", 
                "刘慈欣", 
                "科幻小说，讲述了人类文明与三体文明的第一次接触", 
                "2008-01-01", 
                39.00, 
                35.00, 
                "非常经典的科幻作品", 
                "已读", 
                "在库", 
                5
            ),
            (
                "活着", 
                "余华", 
                "讲述了一个人一生的故事，展现了生命的坚韧", 
                "2012-08-01", 
                45.00, 
                40.00, 
                "值得反复阅读", 
                "正在读", 
                "在库", 
                4
            ),
            (
                "百年孤独", 
                "加西亚·马尔克斯", 
                "魔幻现实主义文学代表作", 
                "2011-06-01", 
                55.00, 
                50.00, 
                "需要静下心来慢慢读", 
                "待读", 
                "在库", 
                3
            )
        ]
        
        cursor.executemany("""
            INSERT INTO books (
                title, author, description, publish_date,
                original_price, purchase_price, user_notes,
                reading_status, storage_status, rating
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_books)
        
        conn.commit()
        conn.close()
        logger.info("数据库初始化成功，已添加示例数据")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise

init_db()

@app.get("/")
async def list_books(request: Request, search: str = None):
    try:
        conn = sqlite3.connect('books.db')
        cursor = conn.cursor()
        
        if search:
            cursor.execute("""
                SELECT * FROM books 
                WHERE title = ? OR author = ?
            """, (search, search))
        else:
            cursor.execute("SELECT * FROM books")
        
        books = cursor.fetchall()
        conn.close()
        
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "books": books, "search": search}
        )
    except Exception as e:
        logger.error(f"获取图书列表失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="获取图书列表失败")

@app.get("/add")
async def add_form(request: Request):
    try:
        return templates.TemplateResponse("add.html", {"request": request})
    except Exception as e:
        logger.error(f"加载添加表单失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="加载添加表单失败")

@app.post("/add")
async def add_book(
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(None),
    publish_date: str = Form(None),
    original_price: float = Form(None),
    purchase_price: float = Form(None),
    user_notes: str = Form(None),
    reading_status: str = Form("待读"),
    storage_status: str = Form("在库"),
    rating: int = Form(3)
):
    try:
        # 验证日期格式
        if publish_date:
            try:
                datetime.strptime(publish_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式必须为YYYY-MM-DD")
        
        # 验证状态值
        valid_reading_status = ['待读', '已读', '正在读']
        if reading_status not in valid_reading_status:
            raise HTTPException(status_code=400, detail="无效的阅读状态")
        
        valid_storage_status = ['在库', '借入', '借出', '归档']
        if storage_status not in valid_storage_status:
            raise HTTPException(status_code=400, detail="无效的在库状态")
        
        # 验证评分
        if not 1 <= rating <= 5:
            raise HTTPException(status_code=400, detail="评分必须在1-5之间")
        
        conn = sqlite3.connect('books.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO books (
                title, author, description, publish_date, 
                original_price, purchase_price, user_notes,
                reading_status, storage_status, rating
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, author, description, publish_date,
            original_price, purchase_price, user_notes,
            reading_status, storage_status, rating
        ))
        conn.commit()
        conn.close()
        return RedirectResponse(url="/", status_code=303)
    except HTTPException:
        raise
    except sqlite3.IntegrityError as e:
        # 直接抛出数据库错误
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"添加图书失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="添加图书失败")

@app.get("/edit/{book_id}")
async def edit_form(request: Request, book_id: int):
    try:
        conn = sqlite3.connect('books.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()
        conn.close()
        
        if not book:
            raise HTTPException(status_code=404, detail="图书不存在")
        
        return templates.TemplateResponse(
            "edit.html",
            {"request": request, "book": book}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载编辑表单失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="加载编辑表单失败")

@app.post("/edit/{book_id}")
async def edit_book(
    book_id: int,
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(None),
    publish_date: str = Form(None),
    original_price: float = Form(None),
    purchase_price: float = Form(None),
    user_notes: str = Form(None),
    reading_status: str = Form("待读"),
    storage_status: str = Form("在库"),
    rating: int = Form(3)
):
    try:
        # 验证日期格式
        if publish_date:
            try:
                datetime.strptime(publish_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式必须为YYYY-MM-DD")
        
        # 验证状态值
        valid_reading_status = ['待读', '已读', '正在读']
        if reading_status not in valid_reading_status:
            raise HTTPException(status_code=400, detail="无效的阅读状态")
        
        valid_storage_status = ['在库', '借入', '借出', '归档']
        if storage_status not in valid_storage_status:
            raise HTTPException(status_code=400, detail="无效的在库状态")
        
        # 验证评分
        if not 1 <= rating <= 5:
            raise HTTPException(status_code=400, detail="评分必须在1-5之间")
        
        conn = sqlite3.connect('books.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE books SET 
                title = ?, author = ?, description = ?, publish_date = ?,
                original_price = ?, purchase_price = ?, user_notes = ?,
                reading_status = ?, storage_status = ?, rating = ?
            WHERE id = ?
        """, (
            title, author, description, publish_date,
            original_price, purchase_price, user_notes,
            reading_status, storage_status, rating,
            book_id
        ))
        conn.commit()
        conn.close()
        return RedirectResponse(url="/", status_code=303)
    except HTTPException:
        raise
    except sqlite3.IntegrityError as e:
        # 直接抛出数据库错误
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"编辑图书失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="编辑图书失败")

@app.post("/delete/{book_id}")
async def delete_book(book_id: int):
    try:
        conn = sqlite3.connect('books.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        conn.close()
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        logger.error(f"删除图书失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="删除图书失败")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 