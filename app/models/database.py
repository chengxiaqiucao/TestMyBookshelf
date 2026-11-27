"""数据库层：版本化迁移、幂等初始化、统一的按列名访问。

修复 S0-F01（启动清库）、S1-F09（未初始化）、S1-F07（固定索引错位）、S1-I05（无迁移版本）。
"""
import sqlite3
import logging
from pathlib import Path

from ..config import DB_PATH, BASE_DIR

logger = logging.getLogger(__name__)


def get_db_connection():
    """获取数据库连接，按列名返回 Row（S1-F07：消除固定索引访问）。"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _current_version(conn) -> int:
    """读取当前 schema 版本；无版本表时依据已有表推断为 1。"""
    try:
        row = conn.execute("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.OperationalError:
        # 旧库没有版本表：若已有 books 表，视为 sprint1
        try:
            conn.execute("SELECT 1 FROM books LIMIT 1").fetchone()
            return 1
        except sqlite3.OperationalError:
            return 0


def _apply_script(conn, path: Path):
    if not path.exists():
        raise FileNotFoundError(f"迁移脚本缺失: {path}")
    conn.executescript(path.read_text(encoding="utf-8"))


def _add_column_if_missing(conn, table, column, ddl):
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
        logger.info("已为 %s 添加列 %s", table, column)


def _ensure_sprint2_columns(conn):
    """幂等补齐所有 Sprint2 新增列，兼容半升级状态的库。"""
    _add_column_if_missing(conn, "users", "role", "TEXT DEFAULT 'user'")
    _add_column_if_missing(conn, "users", "lang", "TEXT DEFAULT 'zh'")
    _add_column_if_missing(conn, "books", "owner_id", "INTEGER")
    _add_column_if_missing(conn, "books", "storage_status", "TEXT DEFAULT '在库'")
    _add_column_if_missing(conn, "books", "notes", "TEXT")
    _add_column_if_missing(conn, "reading_plans", "owner_id", "INTEGER")
    _add_column_if_missing(conn, "reading_plans", "description", "TEXT")
    conn.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER NOT NULL REFERENCES reading_plans(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        status TEXT DEFAULT '未开始',
        priority TEXT DEFAULT '中',
        executor TEXT,
        owner_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    for col, ddl in [("executor", "TEXT"), ("owner_id", "INTEGER"), ("priority", "TEXT DEFAULT '中'")]:
        _add_column_if_missing(conn, "tasks", col, ddl)
    conn.execute("""CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
        owner_id INTEGER NOT NULL,
        borrower TEXT NOT NULL,
        loan_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        return_date TEXT,
        status TEXT NOT NULL DEFAULT '借出',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_loans_owner ON loans(owner_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_loans_book ON loans(book_id)")
    conn.execute("""CREATE TABLE IF NOT EXISTS user_preferences (
        user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        lang TEXT DEFAULT 'zh')""")


def _backfill_owner_ids(conn):
    """幂等回填遗留数据的 owner_id（计划外缺陷修复）。

    sprint1 遗留的 books/reading_plans/tasks 记录 owner_id 为 NULL，
    按用户过滤后全部落空，导致"书架为空但统计有数据"。
    将 NULL 归属统一归给 admin 用户，重复执行安全。
    """
    admin = conn.execute("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1").fetchone()
    if not admin:
        logger.warning("未找到 admin 用户，跳过 owner_id 回填")
        return
    admin_id = admin["id"]
    for table in ("books", "reading_plans", "tasks"):
        try:
            cur = conn.execute(f"UPDATE {table} SET owner_id = ? WHERE owner_id IS NULL", (admin_id,))
            if cur.rowcount:
                logger.info("已回填 %s 的 %s 条 NULL 归属", table, cur.rowcount)
        except sqlite3.OperationalError:
            logger.warning("跳过 %s 的 owner_id 回填（列不存在）", table)


# 示例书封面（按书名匹配），与 scripts/gen_sample_covers.py 生成的文件对应
SAMPLE_COVERS = {
    "三体": "/static/covers/santi.svg",
    "活着": "/static/covers/huozhe.svg",
    "百年孤独": "/static/covers/bainian.svg",
    "围城": "/static/covers/weicheng.svg",
    "平凡的世界": "/static/covers/pingfan.svg",
}


def _ensure_sample_covers(conn):
    """为示例书预置封面，仅填空值、幂等，不覆盖用户上传的封面。"""
    for title, path in SAMPLE_COVERS.items():
        conn.execute(
            "UPDATE books SET cover_image = ? WHERE title = ? "
            "AND (cover_image IS NULL OR cover_image = '')",
            (path, title),
        )


# 示例书初始阅读状态：sprint1 基线值（用于判定用户是否改动过）
BASELINE_READING_STATUS = {
    "三体": "已读",
    "活着": "正在读",
    "百年孤独": "待读",
    "围城": "待读",
    "平凡的世界": "待读",
}
# 目标均衡分布：已读 2 / 正在读 2 / 待读 1，使统计页阅读状态饼图三类均有呈现
TARGET_READING_STATUS = {
    "三体": "已读",
    "活着": "正在读",
    "百年孤独": "待读",
    "围城": "已读",
    "平凡的世界": "正在读",
}


def _ensure_sample_reading_status(conn):
    """均衡示例书初始阅读状态分布，幂等且不覆盖用户改动。

    仅当某本书当前状态仍等于 sprint1 基线值（说明未被用户编辑）时才调整；
    已是目标值或用户自定义值均保持不动。重复执行结果一致。
    """
    for title, target in TARGET_READING_STATUS.items():
        baseline = BASELINE_READING_STATUS.get(title)
        conn.execute(
            "UPDATE books SET reading_status = ? WHERE title = ? AND reading_status = ?",
            (target, title, baseline),
        )


def _migrate_sprint2(conn):
    """Sprint2 幂等迁移：逐列检查，搬运旧表数据，记录版本。"""
    # 版本表
    conn.execute("""CREATE TABLE IF NOT EXISTS schema_version (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version INTEGER NOT NULL,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    # 用户表
    _add_column_if_missing(conn, "users", "role", "TEXT DEFAULT 'user'")
    _add_column_if_missing(conn, "users", "lang", "TEXT DEFAULT 'zh'")

    # 图书表
    _add_column_if_missing(conn, "books", "owner_id", "INTEGER")
    _add_column_if_missing(conn, "books", "storage_status", "TEXT DEFAULT '在库'")
    _add_column_if_missing(conn, "books", "notes", "TEXT")

    # 阅读计划：统一 notes/description（S1-F03）
    cols = {r[1] for r in conn.execute("PRAGMA table_info(reading_plans)").fetchall()}
    if "description" not in cols and "notes" in cols:
        conn.execute("ALTER TABLE reading_plans RENAME COLUMN notes TO description")
    elif "description" not in cols:
        conn.execute("ALTER TABLE reading_plans ADD COLUMN description TEXT")
    elif "notes" in cols:
        conn.execute("UPDATE reading_plans SET description = notes WHERE description IS NULL OR description = ''")
    _add_column_if_missing(conn, "reading_plans", "owner_id", "INTEGER")

    # 任务表：统一为 tasks（S1-F02），旧库需补列
    conn.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER NOT NULL REFERENCES reading_plans(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        status TEXT DEFAULT '未开始',
        priority TEXT DEFAULT '中',
        executor TEXT,
        owner_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    for col, ddl in [("executor", "TEXT"), ("owner_id", "INTEGER"), ("priority", "TEXT DEFAULT '中'")]:
        _add_column_if_missing(conn, "tasks", col, ddl)
    # 搬运旧 plan_tasks 数据
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='plan_tasks'").fetchone():
        old_cols = {r[1] for r in conn.execute("PRAGMA table_info(plan_tasks)").fetchall()}
        if "title" in old_cols:
            conn.execute("""INSERT INTO tasks(plan_id, title, description, status, executor)
                            SELECT plan_id, title, description, status, executor FROM plan_tasks""")
        conn.execute("DROP TABLE plan_tasks")

    # 借阅记录
    conn.execute("""CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
        owner_id INTEGER NOT NULL,
        borrower TEXT NOT NULL,
        loan_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        return_date TEXT,
        status TEXT NOT NULL DEFAULT '借出',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_loans_owner ON loans(owner_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_loans_book ON loans(book_id)")

    # 用户偏好
    conn.execute("""CREATE TABLE IF NOT EXISTS user_preferences (
        user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        lang TEXT DEFAULT 'zh')""")

    conn.execute("INSERT INTO schema_version(version) VALUES (2)")


def init_db():
    """幂等初始化/升级数据库。绝不清空已有数据（S0-F01）。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    try:
        version = _current_version(conn)
        logger.info("当前数据库版本: %s", version)

        if version == 0:
            _apply_script(conn, BASE_DIR / "migrations" / "sprint1.sql")
            version = 1

        if version == 1:
            _migrate_sprint2(conn)
            version = 2

        # 幂等补齐：即使已是 v2，也确保所有列存在（支持半升级库）
        _ensure_sprint2_columns(conn)

        # 幂等回填遗留数据的 owner_id（计划外缺陷修复）
        _backfill_owner_ids(conn)

        # 幂等预置示例书封面（仅填空值，不覆盖用户上传）
        _ensure_sample_covers(conn)

        # 幂等均衡示例书阅读状态分布（仅调整未被用户改动的书）
        _ensure_sample_reading_status(conn)

        conn.commit()
        logger.info("数据库已就绪，版本: %s", version)
        return version
    except Exception:
        conn.rollback()
        logger.exception("数据库初始化失败")
        raise
    finally:
        conn.close()


def is_database_empty():
    if not DB_PATH.exists():
        return True
    conn = get_db_connection()
    try:
        return conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0
    except sqlite3.OperationalError:
        return True
    finally:
        conn.close()


def import_sample_data():
    """导入示例数据，幂等且使用真实 bcrypt 哈希（S1-I03/I04 配套）。"""
    conn = get_db_connection()
    try:
        from passlib.context import CryptContext
        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # 升级 sprint1 遗留的明文密码与角色（S1-I03）
        for row in conn.execute("SELECT id, username, password, role FROM users").fetchall():
            pw = row["password"] or ""
            if not pw.startswith("$2"):
                conn.execute("UPDATE users SET password=? WHERE id=?", (pwd.hash(pw or "admin123"), row["id"]))
            if row["username"] == "admin" and row["role"] != "admin":
                conn.execute("UPDATE users SET role='admin' WHERE id=?", (row["id"],))
        conn.commit()
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            logger.info("示例数据已存在，密码与角色已升级")
            return
        conn.execute(
            "INSERT INTO users(username,password,email,role,lang) VALUES (?,?,?,'admin','zh')",
            ("admin", pwd.hash("admin123"), "admin@example.com"))
        conn.execute(
            "INSERT INTO users(username,password,email,role,lang) VALUES (?,?,?,'user','zh')",
            ("user1", pwd.hash("user123"), "user1@example.com"))
        conn.execute("""INSERT INTO books(title,author,publish_date,purchase_date,purchaser,
            purchase_price,reading_status,storage_status,category,rating,owner_id,cover_image) VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("三体", "刘慈欣", "2008-01-01", "2024-01-15", "admin", 45.0, "已读", "在库", "科幻", 5,
             1, SAMPLE_COVERS["三体"]))
        conn.commit()
        logger.info("示例数据导入完成：admin / admin123")
    except Exception:
        conn.rollback()
        logger.exception("示例数据导入失败")
        raise
    finally:
        conn.close()


def execute_query(query, params=None):
    """执行查询并返回 Row 列表（修复 S1-F01 中错误的返回值用法）。"""
    conn = get_db_connection()
    try:
        cur = conn.execute(query, params or ())
        rows = cur.fetchall()
        conn.commit()
        return rows
    except Exception:
        conn.rollback()
        logger.exception("执行查询失败")
        raise
    finally:
        conn.close()


def execute_update(query, params=None):
    """执行更新，返回受影响行数。"""
    conn = get_db_connection()
    try:
        cur = conn.execute(query, params or ())
        conn.commit()
        return cur.rowcount
    except Exception:
        conn.rollback()
        logger.exception("执行更新失败")
        raise
    finally:
        conn.close()
