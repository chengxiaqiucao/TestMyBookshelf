import os
import uvicorn

if __name__ == "__main__":
    # SECRET_KEY 由 config.py 强制校验
    os.environ.setdefault("SECRET_KEY", "dev-only-secret-change-me")
    os.environ.setdefault("CORS_ORIGINS", "http://127.0.0.1:8000")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
