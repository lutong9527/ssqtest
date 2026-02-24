from db.base import Base  # 统一导入 Base
from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
class Kaijiang(Base):
    """
    开奖历史记录表
    """

    __tablename__ = "kaijiang"  # 数据库中的表名

    qi_shu = Column(String(10), primary_key=True, comment="期号，如 26018")
    red1 = Column(Integer, nullable=False)
    red2 = Column(Integer, nullable=False)
    red3 = Column(Integer, nullable=False)
    red4 = Column(Integer, nullable=False)
    red5 = Column(Integer, nullable=False)
    red6 = Column(Integer, nullable=False)
    blue = Column(Integer, nullable=False)
    open_time = Column(DateTime, nullable=False, comment="开奖时间")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Kaijiang(qi_shu={self.qi_shu}, red1={self.red1}, red2={self.red2}, red3={self.red3})>"
