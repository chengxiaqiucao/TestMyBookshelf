import os
import uvicorn

if __name__ == "__main__":
    # SECRET_KEY 由 config.py 强制校验
    os.environ.setdefault("SECRET_KEY", "dev-only-secret-change-me")
    # 同源请求不受 CORS 限制；需要跨域时用 CORS_ORIGINS 环境变量（逗号分隔）自行扩展
    os.environ.setdefault("CORS_ORIGINS", "http://127.0.0.1:8001")
    # 绑定 0.0.0.0 以允许同局域网设备访问；127.0.0.1 仅限本机
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=False)
