# models/model_param_history.py
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class ModelParamHistory(Base):
    __tablename__ = "model_param_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_code = Column(String(50), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    params = Column(JSON, nullable=False)
    description = Column(String(500), nullable=True)
    updated_by = Column(String(100), nullable=True)  # 修改人用户名
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
