"""模板渲染统一入口：注入语言、翻译函数与日期/货币格式化。"""
from fastapi.templating import Jinja2Templates
from .config import TEMPLATES_DIR
from .utils.i18n import t, resolve_lang, format_date, currency

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def render(request, name: str, context: dict = None, status_code: int = 200):
    ctx = dict(context or {})
    lang = ctx.get("lang") or resolve_lang(
        request.cookies.get("lang"),
        ctx.get("user_lang"),
        request.query_params.get("lang"),
    )
    ctx.update({
        "request": request,
        "lang": lang,
        "t": lambda key, **kw: t(lang, key, **kw),
        "fmt_date": lambda v: format_date(v, lang),
        "money": lambda v: currency(v, lang),
        "current_user": ctx.get("current_user"),
    })
    return templates.TemplateResponse(name, ctx, status_code=status_code)
