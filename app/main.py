"""Sprint2 应用入口：修复 S1-F09 初始化、S1-I01 CORS、S1-F05 统计口径。"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .config import STATIC_DIR, CORS_ORIGINS, APP_NAME
from .models.database import init_db, import_sample_data
from .services import statistics as stats_service
from .auth import router as auth_router, current_user
from .templates_helpers import render
from .utils.i18n import resolve_lang
from .routers import books, plans, loans, statistics
from .ws import router as ws_router
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# S1-F09：启动时幂等初始化数据库（绝不清空）
init_db()
import_sample_data()

app = FastAPI(title=APP_NAME, version="2.0")

# S1-I01：明确白名单，不与 credentials 通配组合
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["GET", "POST"], allow_headers=["*"])

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(auth_router)
app.include_router(books.router, prefix="/books", tags=["books"])
app.include_router(plans.router, prefix="/plans", tags=["plans"])
app.include_router(loans.router, prefix="/loans", tags=["loans"])
app.include_router(statistics.router, prefix="/statistics", tags=["statistics"])
app.include_router(ws_router)


@app.get("/")
async def index(request: Request):
    user = current_user(request)
    lang = resolve_lang(request.cookies.get("lang"), user.lang if user else None)
    overview = stats_service.get_overview(user.id if user else None)
    recent = stats_service.get_recent_activity(user.id if user else None, limit=5)
    return render(request, "index.html", {
        "stats": overview, "recent": recent, "lang": lang, "current_user": user})
