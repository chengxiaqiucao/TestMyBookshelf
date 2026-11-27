"""借阅管理（需求 1.2；注入 S2-F02/F03/F04/F05 靶点）。

靶点说明（均不在需求文档中）：
- S2-F02: get_loan() 不校验 owner_id，水平越权。
- S2-F03: return_book() 不同步图书 storage_status。
- S2-F04: 超期判定用 >= 边界错误。
- S2-F05: 借出时未校验"待购买"状态。
"""
from datetime import date, timedelta

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse

from ..models.database import execute_query, execute_update
from ..auth import require_user
from ..templates_helpers import render
from ..utils.i18n import resolve_lang

router = APIRouter()


def _is_overdue(loan) -> bool:
    """S2-F04 注入靶点：应还日期当天即判为超期（应为 > 而非 >=）。"""
    if loan["return_date"]:
        return date.fromisoformat(str(loan["return_date"])[:10]) >= date.fromisoformat(str(loan["due_date"])[:10])
    return date.today() >= date.fromisoformat(str(loan["due_date"])[:10])


@router.get("/")
async def loan_list(request: Request):
    user = require_user(request)
    lang = resolve_lang(request.cookies.get("lang"), user.lang)
    loans = execute_query(
        "SELECT l.*, b.title, b.cover_image FROM loans l JOIN books b ON b.id = l.book_id "
        "WHERE l.owner_id = ? ORDER BY l.id DESC", (user.id,))
    for loan in loans:
        loan_overdue = _is_overdue(loan)
    return render(request, "loans.html", {
        "loans": loans, "lang": lang, "current_user": user, "is_overdue": _is_overdue})


@router.get("/{loan_id}")
async def get_loan(loan_id: int, request: Request):
    # ---- S2-F02 注入靶点：缺少 owner_id 校验，水平越权 ----
    rows = execute_query(
        "SELECT l.*, b.title FROM loans l JOIN books b ON b.id = l.book_id WHERE l.id = ?", (loan_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="借阅记录不存在")
    return dict(rows[0])


@router.post("/{book_id}/loan")
async def borrow_book(book_id: int, request: Request, borrower: str = Form(...), days: int = Form(30)):
    user = require_user(request)
    rows = execute_query("SELECT id, storage_status FROM books WHERE id = ?", (book_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="图书不存在")
    # ---- S2-F05 注入靶点：未拦截"待购买"状态 ----
    if rows[0]["storage_status"] == "借出":
        raise HTTPException(status_code=400, detail="图书已借出")

    loan_date = date.today()
    due_date = loan_date + timedelta(days=days)
    execute_update(
        "INSERT INTO loans(book_id, owner_id, borrower, loan_date, due_date, status) VALUES (?, ?, ?, ?, ?, '借出')",
        (book_id, user.id, borrower, loan_date.isoformat(), due_date.isoformat()))
    execute_update("UPDATE books SET storage_status = '借出' WHERE id = ?", (book_id,))
    return RedirectResponse(url="/loans", status_code=303)


@router.post("/{loan_id}/return")
async def return_book(loan_id: int, request: Request):
    user = require_user(request)
    rows = execute_query("SELECT * FROM loans WHERE id = ? AND owner_id = ?", (loan_id, user.id))
    if not rows:
        raise HTTPException(status_code=404, detail="借阅记录不存在")
    loan = rows[0]
    execute_update("UPDATE loans SET return_date = ?, status = '已归还', updated_at = datetime('now') WHERE id = ?",
                   (date.today().isoformat(), loan_id))
    # ---- S2-F03 注入靶点：缺少下方这行，图书状态未恢复 ----
    # execute_update("UPDATE books SET storage_status = '在库' WHERE id = ?", (loan["book_id"],))
    return RedirectResponse(url="/loans", status_code=303)
