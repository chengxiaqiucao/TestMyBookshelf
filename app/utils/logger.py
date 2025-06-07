import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

def setup_logger():
    # 获取项目根目录
    root_dir = Path(__file__).parent.parent.parent
    logs_dir = root_dir / 'logs'
    
    # 创建 logs 目录（如果不存在）
    logs_dir.mkdir(exist_ok=True)
    
    # 日志文件路径
    log_file = logs_dir / 'bookshelf.log'

    # 创建 logger
    logger = logging.getLogger('bookshelf')
    logger.setLevel(logging.INFO)

    # 如果已经有处理器，先清除
    if logger.handlers:
        logger.handlers.clear()

    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 创建文件处理器（使用 RotatingFileHandler 限制文件大小）
    file_handler = RotatingFileHandler(
        str(log_file),
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)  # 使用 stdout 而不是默认的 stderr
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 添加处理器到 logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # 设置 propagate 为 False，避免日志被父级 logger 处理
    logger.propagate = False

    logger.info(f"Logger initialized. Log file: {log_file}")
    return logger 