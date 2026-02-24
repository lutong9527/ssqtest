from sqlalchemy import Column, BigInteger, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100))
    rate_limit = Column(Integer, default=1000)
    daily_quota = Column(Integer, default=10000)
    is_active = Column(Integer, default=1)
    expire_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())