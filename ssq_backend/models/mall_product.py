from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base


class MallProduct(Base):
    __tablename__ = "mall_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    points_price = Column(Integer, nullable=False)
    stock = Column(Integer, default=0)
    status = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
