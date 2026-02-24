# schemas/user.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None  # ← 改成 str，不用 EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    full_name: Optional[str] = None  # 新增 full_name 字段

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)

class UserOut(UserBase):
    id: int
    role: str
    membership_level: str
    membership_expire: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
