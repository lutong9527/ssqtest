from sqlalchemy import Column, Integer, Date
from database import Base


class LotteryHistory(Base):
    __tablename__ = "kaijiang"

    id = Column(Integer, primary_key=True, index=True)
    qi_shu = Column(Integer, unique=True, index=True)
    red1 = Column(Integer)
    red2 = Column(Integer)
    red3 = Column(Integer)
    red4 = Column(Integer)
    red5 = Column(Integer)
    red6 = Column(Integer)
    blue = Column(Integer)
