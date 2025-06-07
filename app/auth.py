from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
from .models.database import execute_query

security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> Optional[dict]:
    """
    验证用户凭据并返回用户信息
    """
    conn = execute_query("SELECT * FROM users WHERE username = %s", (credentials.username,))
    user = conn.fetchone()
    
    if not user or user['password'] != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return dict(user) 