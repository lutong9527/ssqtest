from sqlalchemy import Column, BigInteger, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class APIUsageLog(Base):
    __tablename__ = "api_usage_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    api_key_id = Column(BigInteger, ForeignKey("api_keys.id", ondelete="CASCADE"))
    endpoint = Column(String(200))
    ip = Column(String(45))
    status_code = Column(Integer)
    response_time = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())