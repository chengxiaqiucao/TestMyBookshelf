-- Sprint2 结构迁移：支持从 sprint1 库幂等升级
-- 修复 S1-R01（待购买状态）、S1-F02（任务表名）、S1-F03（字段冲突）、S1-I04（数据库入库）

-- 版本表（S1-I05）
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户表扩展（S1-I03：哈希密码；S2-F02 数据隔离字段基础）
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';
ALTER TABLE users ADD COLUMN lang TEXT DEFAULT 'zh';

-- 图书表：统一状态字段并纳入"待购买"（S1-R01）
-- 旧库使用 reading_status / 无 storage_status，此处补齐
ALTER TABLE books ADD COLUMN owner_id INTEGER;
ALTER TABLE books ADD COLUMN storage_status TEXT DEFAULT '在库';
ALTER TABLE books ADD COLUMN notes TEXT;

-- 阅读计划：统一 notes/description 口径（S1-F03）
ALTER TABLE reading_plans ADD COLUMN owner_id INTEGER;
ALTER TABLE reading_plans ADD COLUMN description TEXT;

-- 阅读计划：用 description 覆盖 notes 的旧数据（若旧库存在 notes 列则迁移）
-- SQLite 无法在 SQL 中条件判断列存在，交由 Python 迁移钩子处理；此处仅建立 description。

-- 任务表：统一表名，旧 plan_tasks 数据在 Python 迁移钩子中搬运（S1-F02）
CREATE TABLE IF NOT EXISTS tasks (
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 借阅记录（1.2 用户故事3/4）
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    owner_id INTEGER NOT NULL,
    borrower TEXT NOT NULL,
    loan_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    return_date TEXT,
    status TEXT NOT NULL DEFAULT '借出',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_loans_owner ON loans(owner_id);
CREATE INDEX IF NOT EXISTS idx_loans_book ON loans(book_id);

-- 用户偏好（i18n 持久化，1.3）
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    lang TEXT DEFAULT 'zh'
);

-- 记录版本
INSERT INTO schema_version(version) VALUES (2);
