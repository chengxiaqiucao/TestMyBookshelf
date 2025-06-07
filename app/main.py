from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
from .models.database import get_db_connection
from urllib.parse import urlencode, parse_qs
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import logging
import os

from .config import APP_NAME, TEMPLATES_DIR, STATIC_DIR, DB_PATH
from .models.database import init_db
from .routers import books, plans, statistics, index
from app.utils.logger import setup_logger

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建应用实例
app = FastAPI(title=APP_NAME)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 设置模板目录
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# 添加自定义过滤器
def remove_param(query_params, param):
    """从查询参数中移除指定参数"""
    params = dict(query_params)
    params.pop(param, None)
    return urlencode(params)

templates.env.filters["remove_param"] = remove_param

# 注册路由
app.include_router(index.router)  # 添加 index 路由
app.include_router(books.router, prefix="/books", tags=["books"])
app.include_router(plans.router, prefix="/plans", tags=["plans"])
app.include_router(statistics.router, prefix="/statistics", tags=["statistics"])

@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def get_chrome_devtools_config():
    config_path = os.path.join(STATIC_DIR, ".well-known", "appspecific", "com.chrome.devtools.json")
    if os.path.exists(config_path):
        return FileResponse(config_path)
    return {"error": "Configuration not found"}, 404

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    try:
        init_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 