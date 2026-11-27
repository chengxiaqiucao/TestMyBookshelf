# 个人图书管理系统 - Sprint2

测试练习项目：按 Scrum 迭代演进，每迭代一个分支，含功能改进与故意注入的测试靶点。

## 当前版本（Sprint2）

- 用户系统：注册/登录、bcrypt 密码哈希、会话管理、数据隔离
- 图书管理：CRUD、分页、模糊搜索、封面上传（UUID 文件名）
- 借阅管理：借出/归还/超期标记/借阅历史
- 阅读计划：计划与任务管理、进度自动联动
- 统计：ECharts 图表、CSV 导出、24 小时热力图、WebSocket 实时推送
- 中英文支持：界面双语、日期与货币本地化

## 环境与启动

Python 3.10+，依赖见 `requirements.txt`。

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt

# 必须设置 SECRET_KEY（缺失时应用拒绝启动）
export SECRET_KEY=your-secret        # Linux/macOS
set SECRET_KEY=your-secret           # Windows CMD

python run.py
```

访问 `http://127.0.0.1:8000`，默认账号 `admin / admin123`（首次启动自动初始化）。

可选环境变量：`CORS_ORIGINS`（逗号分隔白名单）、`DEBUG`、`ACCESS_TOKEN_EXPIRE_MINUTES`。

## 项目结构

```
app/
  main.py            应用入口
  auth.py            认证与授权
  config.py          配置（环境变量）
  models/database.py 版本化迁移与数据访问
  services/          统一统计服务
  routers/           图书/计划/借阅/统计路由
  utils/i18n.py      中英文与格式化
  templates_helpers.py 模板渲染
  ws.py              WebSocket 推送
  templates/         Jinja2 模板
migrations/          sprint1.sql / sprint2.sql（幂等迁移）
scripts/             初始化脚本
documents/           各迭代需求文档
BUG_LIST.md          本地 Bug 清单（不推送远端）
```

## 注意事项

- 本项目为测试靶场，包含有意注入的故障；这些故障不安排修复，按 `BUG_LIST.md` 练习发现与验证。
- 数据库位于 `data/bookshelf.db`，启动时幂等初始化，不清空已有数据。
- Bug 清单仅存本地迭代分支，不得推送远端。
