# models/withdraw.py
from sqlalchemy import Column, BigInteger, DECIMAL, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Withdraw(Base):
    __tablename__ = "withdraws"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    withdraw_to = Column(String(20), nullable=False)  # wechat / alipay
    account = Column(String(100), nullable=False)     # 账号
    status = Column(String(20), default="pending")    # pending/approved/rejected
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)
    remark = Column(String(255), nullable=True)