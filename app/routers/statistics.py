"""统计与分析（修复 S1-F05/R05；注入 S2-F08/F10 靶点）。

- S2-F08：CSV 导出未加 UTF-8 BOM，Excel 中文乱码。
- S2-F10：category 筛选参数接收但未用于 SQL。
"""
import csv
import io

from fastapi import APIRouter, Request, Query
from fastapi.responses import StreamingResponse

from ..auth import require_user
from ..templates_helpers import render
from ..utils.i18n import resolve_lang
from ..services import statistics as stats_service

router = APIRouter()


@router.get("/")
async def statistics_page(request: Request, category: str = Query(None)):
    user = require_user(request)
    lang = resolve_lang(request.cookies.get("lang"), user.lang)
    overview = stats_service.get_overview(user.id)
    # S2-F10 靶点：category 参数未参与任何过滤
    return render(request, "statistics.html", {
        "stats": overview,
        "distribution": stats_service.get_reading_distribution(user.id),
        "monthly": stats_service.get_monthly(user.id),
        "heatmap": stats_service.get_hourly_heatmap(user.id),
        "lang": lang, "current_user": user, "category": category or ""})


@router.get("/export.csv")
async def export_csv(request: Request, category: str = Query(None)):
    user = require_user(request)
    buf = io.StringIO()  # S2-F08：未写入 BOM
    writer = csv.writer(buf)
    writer.writerow(["书名", "作者", "状态", "购买价格"])
    from ..models.database import get_db_connection
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT title, author, reading_status, purchase_price FROM books WHERE owner_id=?",
                            (user.id,)).fetchall()
        for r in rows:
            writer.writerow([r["title"], r["author"], r["reading_status"], r["purchase_price"]])
    finally:
        conn.close()
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=books.csv"})
