"""Sprint2 配置：全部路径基于项目根目录，敏感配置来自环境变量。

修复 S0-I03（硬编码运行时配置）、S1-I02（密钥硬编码）、S1-I08（路径三处不一致）。
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "data" / "bookshelf.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# 唯一上传目录定义，所有模块均引用此处（S1-I08）
UPLOAD_DIR = BASE_DIR / "app" / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "app" / "static"

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = "我的书架"
DEBUG = os.getenv("DEBUG", "0") == "1"

# 密钥从环境变量读取，缺失时启动失败（S1-I02）
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("环境变量 SECRET_KEY 未设置，应用拒绝启动")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

DEFAULT_LANG = "zh"
SUPPORTED_LANGS = ("zh", "en")

# CORS 白名单（S1-I01）
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000").split(",") if o.strip()]
