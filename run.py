import uvicorn

if __name__ == "__main__":
    # 开发环境使用127.0.0.1
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True) 