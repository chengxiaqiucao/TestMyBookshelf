"""统一统计服务：首页与统计页共用同一口径（修复 S1-F05）。"""
from datetime import datetime, timedelta
from ..models.database import get_db_connection


def get_overview(user_id=None) -> dict:
    """全站概览指标。所有页面均调用此函数，杜绝口径分歧。"""
    conn = get_db_connection()
    try:
        where = "WHERE owner_id = ?" if user_id is not None else ""
        params = (user_id,) if user_id is not None else ()

        total = conn.execute(f"SELECT COUNT(*) FROM books {where}", params).fetchone()[0]
        in_stock = conn.execute(
            f"SELECT COUNT(*) FROM books {where} {'AND' if where else 'WHERE'} storage_status = '在库'", params
        ).fetchone()[0]
        borrowed = conn.execute(
            f"SELECT COUNT(*) FROM books {where} {'AND' if where else 'WHERE'} storage_status = '借出'", params
        ).fetchone()[0]
        total_plans = conn.execute(f"SELECT COUNT(*) FROM reading_plans {where}", params).fetchone()[0]
        done_plans = conn.execute(
            f"SELECT COUNT(*) FROM reading_plans {where} {'AND' if where else 'WHERE'} status = '已完成'", params
        ).fetchone()[0]

        # 任务完成率同样按 owner_id 过滤（口径统一，避免全局数据混入）
        task_where = "WHERE owner_id = ?" if user_id is not None else ""
        task_params = (user_id,) if user_id is not None else ()
        completed_tasks = conn.execute(
            f"SELECT COUNT(*) FROM tasks {task_where} {'AND' if task_where else 'WHERE'} status = '已完成'",
            task_params,
        ).fetchone()[0]
        all_tasks = conn.execute(f"SELECT COUNT(*) FROM tasks {task_where}", task_params).fetchone()[0]
        progress = round(completed_tasks / all_tasks * 100) if all_tasks else 0

        return {
            "total_books": total,
            "in_stock": in_stock,
            "borrowed": borrowed,
            "to_read": max(0, total - in_stock - borrowed),  # 不会出现负数
            "total_plans": total_plans,
            "completed_plans": done_plans,
            "completion_rate": progress,
        }
    finally:
        conn.close()


def get_reading_distribution(user_id=None):
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT reading_status AS label, COUNT(*) AS count FROM books "
            + ("WHERE owner_id = ? " if user_id is not None else "")
            + "GROUP BY reading_status",
            (user_id,) if user_id is not None else (),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_monthly(user_id=None):
    """月度聚合：计划、购买、完成（口径统一来自 books/reading_plans）。"""
    conn = get_db_connection()
    try:
        where = "WHERE owner_id = ?" if user_id is not None else ""
        params = (user_id,) if user_id is not None else ()
        plans = conn.execute(
            "SELECT strftime('%Y-%m', start_date) AS month, COUNT(*) AS count "
            f"FROM reading_plans {where} GROUP BY month ORDER BY month DESC LIMIT 12",
            params,
        ).fetchall()
        purchases = conn.execute(
            "SELECT strftime('%Y-%m', purchase_date) AS month, COUNT(*) AS count "
            f"FROM books {where} {'AND' if where else 'WHERE'} purchase_date IS NOT NULL "
            "GROUP BY month ORDER BY month DESC LIMIT 12",
            params,
        ).fetchall()
        completions = conn.execute(
            "SELECT strftime('%Y-%m', updated_at) AS month, COUNT(*) AS count "
            f"FROM books {where} {'AND' if where else 'WHERE'} reading_status = '已读' "
            "GROUP BY month ORDER BY month DESC LIMIT 12",
            params,
        ).fetchall()
        return {"plans": [dict(r) for r in plans],
                "purchases": [dict(r) for r in purchases],
                "completions": [dict(r) for r in completions]}
    finally:
        conn.close()


def get_hourly_heatmap(user_id=None):
    """24 小时阅读热力图数据（需求 1.4）。基于借阅记录的借出小时分布。"""
    conn = get_db_connection()
    try:
        where = "WHERE owner_id = ?" if user_id is not None else ""
        rows = conn.execute(
            "SELECT CAST(strftime('%H', loan_date) AS INTEGER) AS hour, COUNT(*) AS count "
            f"FROM loans {where} GROUP BY hour",
            (user_id,) if user_id is not None else (),
        ).fetchall()
        data = {h: 0 for h in range(24)}
        for r in rows:
            data[int(r["hour"])] = r["count"]
        return data
    finally:
        conn.close()


def get_recent_activity(user_id=None, limit=5):
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT l.id, l.book_id, b.title, b.cover_image, l.status, l.loan_date, l.return_date "
            "FROM loans l JOIN books b ON b.id = l.book_id "
            + ("WHERE l.owner_id = ? " if user_id is not None else "")
            + "ORDER BY COALESCE(l.return_date, l.loan_date) DESC LIMIT ?",
            ((user_id, limit) if user_id is not None else (limit,)),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
