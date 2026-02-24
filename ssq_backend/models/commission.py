from db.base import Base  # 统一导入 Base
from sqlalchemy import Column, BigInteger, ForeignKey, Integer, String, DateTime, DECIMAL
from sqlalchemy.orm import relationship
import datetime
from models.proxy import Proxy  # 导入 Proxy 类

class CommissionRules(Base):
    """
    分佣规则表
    """

    __tablename__ = "commission_rules"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    level = Column(Integer, nullable=False)  # 代理等级（1,2,3...）
    source_type = Column(String(50), nullable=False)  # 来源类型：order / vip / mall 等
    commission_rate = Column(DECIMAL(5, 2), nullable=False)  # 分佣比例（例如 5.00 表示 5%）
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Commissions(Base):
    """
    分佣记录表
    """

    __tablename__ = "commissions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proxy_id = Column(BigInteger, ForeignKey("proxies.id"), nullable=False)  # 代理ID
    from_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)  # 来源用户ID
    source_type = Column(String(50), nullable=False)  # 来源类型
    source_id = Column(BigInteger)  # 来源业务ID（订单ID等）
    amount = Column(DECIMAL(12, 2), nullable=False)  # 分佣金额
    commission_rate = Column(DECIMAL(5, 2), nullable=False)  # 分佣比例
    status = Column(Integer, default=0)  # 0=待结算, 1=已结算
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    settled_at = Column(DateTime)

    # 关系（与 Proxy 和 User 类的关系）
    proxy = relationship("Proxy", backref="commissions")  # 使用字符串引用
    user = relationship("User", back_populates="commissions")  # 确保使用相同的 back_populates 名称

    def __repr__(self):
        return f"<Commissions(id={self.id}, proxy_id={self.proxy_id}, amount={self.amount})>"
