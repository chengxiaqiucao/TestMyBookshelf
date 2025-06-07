import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.models.database import get_db_connection

def check_db():
    """检查数据库状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查books表
    cursor.execute("SELECT COUNT(*) FROM books")
    book_count = cursor.fetchone()[0]
    print(f"Books count: {book_count}")
    
    # 检查reading_plans表
    cursor.execute("SELECT COUNT(*) FROM reading_plans")
    plan_count = cursor.fetchone()[0]
    print(f"Reading plans count: {plan_count}")
    
    conn.close()

if __name__ == "__main__":
    check_db() 