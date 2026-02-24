# models/params_snapshot.py
from sqlalchemy import Column, BigInteger, String, JSON, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from database import Base

class ParamsSnapshot(Base):
    __tablename__ = "params_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    version = Column(String(50), nullable=False, unique=True)
    params_json = Column(JSON, nullable=False)
    description = Column(String(255), nullable=True)
    coverage_rate = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())