from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True)
    content = Column(String(255), nullable=False)
    type = Column(String(50), default="system")
    sort_order = Column(Integer, default=0)
    status = Column(Integer, default=1)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
