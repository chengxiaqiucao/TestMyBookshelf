"""示例数据初始化：生成真实 bcrypt 哈希，幂等插入。"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from passlib.context import CryptContext
from app.models.database import get_db_connection

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    conn = get_db_connection()
    try:
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            print("示例数据已存在，跳过")
            return
        conn.execute(
            "INSERT INTO users(username,password,email,role,lang) VALUES (?,?,?,'admin','zh')",
            ("admin", pwd.hash("admin123"), "admin@example.com"))
        conn.execute(
            "INSERT INTO users(username,password,email,role,lang) VALUES (?,?,?,'user','zh')",
            ("user1", pwd.hash("user123"), "user1@example.com"))
        conn.execute("""INSERT INTO books(title,author,publish_date,purchase_date,purchaser,purchase_price,
            reading_status,storage_status,category,rating,owner_id) VALUES
            (?,?,?,?,?,?,?,?,?,?,?)""",
            ("三体", "刘慈欣", "2008-01-01", "2024-01-15", "admin", 45.0, "已读", "在库", "科幻", 5, 1))
        conn.commit()
        print("示例数据初始化完成：admin / admin123")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
