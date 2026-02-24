# models/recommend_result.py
# models/recommend_result.py 顶部修改为：
from sqlalchemy import (
    Column, BigInteger, String, JSON, DateTime, ForeignKey, Integer
)
from sqlalchemy.sql import func
from database import Base

class RecommendResult(Base):
    __tablename__ = "recommend_results"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    qi_shu = Column(String(10), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    red_balls = Column(JSON, nullable=False)          # [3,11,18,21,29,32]
    blue_ball = Column(Integer, nullable=False)
    strategy = Column(String(200), nullable=True)
    prob_red = Column(JSON, nullable=True)           # [{"number":1,"prob":4.5}, ...]
    created_at = Column(DateTime, server_default=func.now())