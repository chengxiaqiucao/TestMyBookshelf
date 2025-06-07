import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.models.database import import_sample_data
from app.utils.logger import setup_logger

logger = setup_logger()

def main():
    """初始化示例数据"""
    try:
        logger.info("开始初始化示例数据...")
        import_sample_data()
        logger.info("示例数据初始化完成！")
    except Exception as e:
        logger.error(f"示例数据初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 