from sqlalchemy import Column, Integer, String
from database import Base


max_history_window = Column(Integer,default=50)


class RoleLimit(Base):
    __tablename__ = "role_limits"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20), unique=True, nullable=False)
    daily_limit = Column(Integer, nullable=False)
