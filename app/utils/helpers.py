import os
from pathlib import Path
from datetime import datetime
import uuid

def ensure_upload_dir():
    """确保上传目录存在"""
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    return upload_dir

def save_upload_file(file, prefix=""):
    """保存上传的文件
    
    Args:
        file: 上传的文件对象
        prefix: 文件名前缀
        
    Returns:
        str: 保存后的文件路径
    """
    if not file:
        return None
        
    # 生成唯一文件名
    filename = f"{prefix}_{uuid.uuid4()}_{file.filename}"
    filepath = ensure_upload_dir() / filename
    
    # 保存文件
    with open(filepath, "wb") as f:
        f.write(file.file.read())
    
    return str(filepath)

def delete_file(filepath):
    """删除文件
    
    Args:
        filepath: 文件路径
    """
    if filepath and os.path.exists(filepath):
        os.remove(filepath)

def format_datetime(dt: datetime) -> str:
    """格式化日期时间"""
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_price(price: float) -> str:
    """格式化价格"""
    if price is None:
        return "0.00"
    return f"{price:.2f}"

def get_status_badge_class(status):
    """获取状态对应的Bootstrap标签样式
    
    Args:
        status: 状态字符串
        
    Returns:
        str: Bootstrap标签样式类名
    """
    status_classes = {
        '已完成': 'bg-success',
        '进行中': 'bg-primary',
        '已取消': 'bg-secondary',
        '未开始': 'bg-warning'
    }
    return status_classes.get(status, 'bg-secondary') 