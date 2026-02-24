# routers/user_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import SessionLocal
from models.user import User  # 引用 User 模型
from pydantic import BaseModel
from passlib.context import CryptContext

router = APIRouter()

# 创建一个 Pydantic 模型来验证请求体
class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str  # 新增 full_name 字段
    password: str

    class Config:
        from_attributes = True  # 允许 Pydantic 从 ORM 模型读取数据

# 创建密码哈希的工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 函数：通过加密存储密码
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 数据库会话获取器
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 路由：创建用户
@router.post("/users/", response_model=UserCreate)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 创建新的用户实例并加密密码
    password_hash = password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,  # 保存 full_name 字段
        password_hash=password_hash
    )

    # 将新用户添加到数据库
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

# 路由：获取所有用户
@router.get("/users/", response_model=list[UserCreate])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

# 路由：根据用户名查询用户
@router.get("/users/{username}", response_model=UserCreate)
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
