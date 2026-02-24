# db/base.py

from sqlalchemy import Column, Integer, String
from db.session import Base  # 引入之前在 session.py 中定义的 Base 类

class BaseModel(Base):
    """
    所有数据库模型的基类
    """
    __abstract__ = True  # 这确保了 BaseModel 不会被直接用作数据库表
    id = Column(Integer, primary_key=True, index=True)  # 每个模型都会有一个 id 字段
    created_at = Column(String)  # 创建时间（你可以根据实际需求调整字段类型）

