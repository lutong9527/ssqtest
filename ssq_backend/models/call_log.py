from sqlalchemy import Column, BigInteger, String, DateTime
from database import Base
from sqlalchemy.sql import func


class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String(50), nullable=False)
    api_type = Column(String(50), nullable=False)
    algorithm_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
