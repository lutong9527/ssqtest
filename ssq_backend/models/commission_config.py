from sqlalchemy import Column, Integer, Float
from database import Base


class CommissionConfig(Base):
    __tablename__ = "commission_config"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, nullable=False)
    commission_rate = Column(Float, nullable=False)
