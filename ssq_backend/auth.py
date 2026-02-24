# auth.py
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt  # 直接导入 bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models import User
from config.settings import settings

# ==============================
# 配置区
# ==============================
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时
BCRYPT_MAX_PASSWORD_LENGTH = 72  # bcrypt 5.0.0 的最大长度

# ==============================
# OAuth2 配置
# ==============================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ==============================
# 密码相关函数 - 直接使用 bcrypt
# ==============================
def truncate_password_to_bytes(password: str, max_bytes: int = 72) -> bytes:
    """
    将密码截断到指定字节数，确保不会截断UTF-8字符
    """
    password_bytes = password.encode('utf-8')
    if len(password_bytes) <= max_bytes:
        return password_bytes
    
    # 截断到最大字节数
    truncated = password_bytes[:max_bytes]
    
    # 确保不会截断在UTF-8字符中间
    while truncated:
        try:
            truncated.decode('utf-8')
            return truncated
        except UnicodeDecodeError:
            # 移除最后一个字节再试
            truncated = truncated[:-1]
    
    # 如果所有字节都无法解码，返回空字节
    return b''

def get_password_hash(password: str) -> str:
    """
    使用 bcrypt 5.0.0 生成密码哈希
    """
    # 截断密码到72字节
    password_bytes = truncate_password_to_bytes(password, BCRYPT_MAX_PASSWORD_LENGTH)
    
    if not password_bytes:
        raise ValueError("密码无效或为空")
    
    # 生成盐并哈希
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    
    # 解码为字符串存储
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    """
    try:
        # 截断明文密码到72字节
        plain_bytes = truncate_password_to_bytes(plain_password, BCRYPT_MAX_PASSWORD_LENGTH)
        
        if not plain_bytes:
            return False
        
        # 将哈希密码转换为字节
        hashed_bytes = hashed_password.encode('utf-8')
        
        # 使用 bcrypt 验证
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception as e:
        print(f"密码验证错误: {e}")
        return False

# ==============================
# JWT Token 相关函数
# ==============================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ==============================
# 认证相关函数
# ==============================
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    从 JWT 令牌获取当前认证用户
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise credentials_exception

    return user

# ==============================
# 向后兼容的 passlib 包装器（可选）
# ==============================
class BcryptContext:
    """为现有代码提供 passlib 兼容接口"""
    
    def __init__(self):
        self.schemes = ["bcrypt"]
    
    def hash(self, password: str) -> str:
        return get_password_hash(password)
    
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)

# 创建兼容对象
pwd_context = BcryptContext()
