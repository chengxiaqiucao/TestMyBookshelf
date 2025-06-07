import sqlite3

def check_database():
    """检查数据库结构和数据"""
    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()
    
    # 检查表结构
    print("=== 表结构 ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"\n表名: {table[0]}")
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    
    # 检查数据
    print("\n=== 数据统计 ===")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"{table_name}: {count} 条记录")
        
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            row = cursor.fetchone()
            print(f"示例数据: {row}")
    
    conn.close()

if __name__ == "__main__":
    check_database() 