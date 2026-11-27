"""中英文支持（需求 1.3）。语言持久化到 Cookie；翻译覆盖所有页面文案。"""
from ..config import DEFAULT_LANG, SUPPORTED_LANGS

MESSAGES = {
    "zh": {
        "app_name": "我的书架", "nav_home": "首页", "nav_books": "图书", "nav_plans": "阅读计划",
        "nav_stats": "统计", "nav_loans": "借阅", "nav_login": "登录", "nav_register": "注册",
        "nav_logout": "退出", "lang_switch": "English",
        "book_title": "书名", "book_author": "作者", "book_isbn": "ISBN", "book_publisher": "出版社",
        "book_publish_date": "出版日期", "book_purchase_date": "购买时间", "book_purchaser": "购买者",
        "book_price": "发行价格", "book_purchase_price": "购买价格", "book_status": "阅读状态",
        "book_storage": "在库状态", "book_rating": "评分", "book_category": "分类", "book_desc": "简介",
        "book_cover": "封面", "book_notes": "备注", "action_add": "添加", "action_edit": "编辑",
        "action_delete": "删除", "action_save": "保存", "action_cancel": "取消", "action_search": "搜索",
        "action_detail": "详情", "action_return": "归还", "action_loan": "借出",
        "status_todo": "待读", "status_reading": "正在读", "status_read": "已读",
        "storage_in": "在库", "storage_borrowed": "借出", "storage_todo": "待购买",
        "loan_date": "借出日期", "loan_due": "应还日期", "loan_return": "归还日期",
        "loan_overdue": "已超期", "loan_borrower": "借用人", "loan_history": "借阅历史",
        "stats_total_books": "图书总数", "stats_in_stock": "在库数", "stats_borrowed": "借出数",
        "stats_total_plans": "计划总数", "stats_completion": "完成率", "stats_recent": "最近活动",
        "error_required": "此项为必填", "error_number": "请输入有效数字",
        "error_forbidden": "无权访问此资源", "error_login": "用户名或密码错误",
        "empty_books": "暂无图书，点击添加",
    },
    "en": {
        "app_name": "My Bookshelf", "nav_home": "Home", "nav_books": "Books", "nav_plans": "Plans",
        "nav_stats": "Statistics", "nav_loans": "Loans", "nav_login": "Login", "nav_register": "Register",
        "nav_logout": "Logout", "lang_switch": "中文",
        "book_title": "Title", "book_author": "Author", "book_isbn": "ISBN", "book_publisher": "Publisher",
        "book_publish_date": "Publish Date", "book_purchase_date": "Purchase Date", "book_purchaser": "Purchaser",
        "book_price": "Price", "book_purchase_price": "Purchase Price", "book_status": "Reading Status",
        "book_storage": "Storage Status", "book_rating": "Rating", "book_category": "Category", "book_desc": "Description",
        "book_cover": "Cover", "book_notes": "Notes", "action_add": "Add", "action_edit": "Edit",
        "action_delete": "Delete", "action_save": "Save", "action_cancel": "Cancel", "action_search": "Search",
        "action_detail": "Detail", "action_return": "Return", "action_loan": "Borrow",
        "status_todo": "To Read", "status_reading": "Reading", "status_read": "Read",
        "storage_in": "In Stock", "storage_borrowed": "Borrowed", "storage_todo": "To Purchase",
        "loan_date": "Loan Date", "loan_due": "Due Date", "loan_return": "Return Date",
        "loan_overdue": "Overdue", "loan_borrower": "Borrower", "loan_history": "Loan History",
        "stats_total_books": "Total Books", "stats_in_stock": "In Stock", "stats_borrowed": "Borrowed",
        "stats_total_plans": "Total Plans", "stats_completion": "Completion", "stats_recent": "Recent Activity",
        "error_required": "This field is required", "error_number": "Please enter a valid number",
        "error_forbidden": "You have no permission to access this resource", "error_login": "Invalid username or password",
        "empty_books": "No books yet, add one now",
    },
}


def resolve_lang(cookie_lang=None, user_lang=None, query_lang=None) -> str:
    for candidate in (query_lang, cookie_lang, user_lang, DEFAULT_LANG):
        if candidate in SUPPORTED_LANGS:
            return candidate
    return DEFAULT_LANG


def t(lang: str, key: str, **kwargs) -> str:
    text = MESSAGES.get(lang, MESSAGES[DEFAULT_LANG]).get(key, MESSAGES[DEFAULT_LANG].get(key, key))
    return text.format(**kwargs) if kwargs else text


def format_date(value, lang: str) -> str:
    """日期格式随语言切换（需求 1.3）。"""
    if not value:
        return ""
    v = str(value)[:10]
    parts = v.split("-")
    if len(parts) != 3:
        return v
    y, m, d = parts
    return f"{m}/{d}/{y}" if lang == "en" else f"{y}-{m}-{d}"


def currency(value, lang: str) -> str:
    try:
        num = float(value or 0)
    except (TypeError, ValueError):
        num = 0.0
    return f"${num:.2f}" if lang == "en" else f"¥{num:.2f}"
