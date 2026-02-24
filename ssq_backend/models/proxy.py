from db.base import Base  # 统一导入 Base
from sqlalchemy import Column, BigInteger, Integer, DECIMAL, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship  # 确保导入 relationship
from sqlalchemy.sql import func  # 导入 func

class Proxy(Base):
    __tablename__ = "proxies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, unique=True)  # 外键引用 User
    parent_id = Column(BigInteger, ForeignKey("proxies.id"), nullable=True)
    level = Column(Integer, default=1, nullable=False)  # 代理级别 1~3
    commission_rate = Column(DECIMAL(5, 2), default=10.00)  # 佣金比例 %
    total_commission = Column(DECIMAL(12, 2), default=0.00)  # 累计佣金
    invite_code = Column(String(20), unique=True, nullable=True)  # 邀请码
    status = Column(Integer, default=1)  # 1正常 0禁用
    created_at = Column(DateTime, server_default=func.now())  # 使用 func.now()

    # 关系（与 User 类的关系）
    user = relationship("User", backref="proxy")  # 使用字符串引用

    def __repr__(self):
        return f"<Proxy(id={self.id}, user_id={self.user_id}, level={self.level})>"
