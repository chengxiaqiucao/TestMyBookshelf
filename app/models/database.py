import sqlite3
import logging
import os
from pathlib import Path
from ..config import DB_PATH, BASE_DIR

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def is_database_empty():
    """检查数据库是否为空"""
    if not DB_PATH.exists():
        return True
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 检查books表是否有数据
        cursor.execute("SELECT COUNT(*) FROM books")
        count = cursor.fetchone()[0]
        return count == 0
    except sqlite3.OperationalError:
        return True
    finally:
        conn.close()

def create_db_structure():
    """创建数据库结构"""
    try:
        # 确保数据库目录存在
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果数据库文件不存在，创建新的数据库
        if not DB_PATH.exists():
            logger.info("创建新的数据库文件")
            conn = get_db_connection()
            cursor = conn.cursor()

            # 读取并执行数据库结构SQL
            structure_sql_path = BASE_DIR / "migrations" / "sprint1.sql"
            with open(structure_sql_path, "r", encoding="utf-8") as f:
                cursor.executescript(f.read())
            conn.commit()
            conn.close()
            logger.info("数据库结构创建成功")
            
    except Exception as e:
        logger.error(f"数据库结构创建失败: {str(e)}")
        raise

def import_sample_data():
    """导入示例数据"""
    try:
        if not DB_PATH.exists():
            create_db_structure()
            
        logger.info("开始导入示例数据")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 读取并执行示例数据SQL
            sample_data_path = BASE_DIR / "migrations" / "sample_data.sql"
            with open(sample_data_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
                logger.info("读取示例数据SQL文件成功")
                cursor.executescript(sql_script)
                logger.info("执行示例数据SQL成功")
            
            # 验证数据是否导入成功
            cursor.execute("SELECT COUNT(*) FROM books")
            book_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM reading_plans")
            plan_count = cursor.fetchone()[0]
            
            logger.info(f"示例数据导入完成：{book_count} 本书，{plan_count} 个阅读计划")
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"导入示例数据失败: {str(e)}")
            raise
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"示例数据导入失败: {str(e)}")
        raise

def init_db():
    """初始化数据库（仅创建结构）"""
    create_db_structure()

def execute_query(query, params=None):
    """执行查询"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.fetchall()
    except Exception as e:
        conn.rollback()
        logger.error(f"执行查询失败: {str(e)}")
        raise
    finally:
        conn.close()

def execute_update(query, params=None):
    """执行更新操作"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close() 