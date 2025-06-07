from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 数据库设置
DB_PATH = BASE_DIR / "data" / "bookshelf.db"
DB_PATH.parent.mkdir(exist_ok=True)  # 确保 data 目录存在

# 文件上传设置
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 模板设置
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

# 静态文件设置
STATIC_DIR = BASE_DIR / "app" / "static"

# 应用设置
APP_NAME = "我的书架"
DEBUG = True

# 安全设置
SECRET_KEY = "your-secret-key-here"  # 在生产环境中应该使用环境变量
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 