from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.sql import func
from database import Base


class CommissionLog(Base):
    __tablename__ = "commission_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    from_user_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    level = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
