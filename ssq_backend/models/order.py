# models/order.py
from sqlalchemy import Column, BigInteger, String, DECIMAL, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    order_no = Column(String(50), unique=True, nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    membership_months = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")  # pending/paid/failed/cancelled
    payment_method = Column(String(20), default="alipay")
    payment_no = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    paid_at = Column(DateTime, nullable=True)
    vip_expire = Column(DateTime, nullable=True)