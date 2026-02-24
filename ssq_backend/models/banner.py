from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base


class Banner(Base):
    __tablename__ = "banners"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    image_url = Column(String(255), nullable=False)
    link_url = Column(String(255))
    position = Column(String(50), default="home_top")
    sort_order = Column(Integer, default=0)
    status = Column(Integer, default=1)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
