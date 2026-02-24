from db.base import Base  # 统一导入 Base
from sqlalchemy import Column, String, Integer, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

# 枚举类用于 'role' 和 'membership_level'
class Role(enum.Enum):
    visitor = "visitor"
    regular = "regular"
    vip = "vip"
    diamond = "diamond"
    admin = "admin"

class MembershipLevel(enum.Enum):
    none = "none"
    regular = "regular"
    vip = "vip"
    diamond = "diamond"

class User(Base):
    """
    用户模型，存储用户信息
    """

    __tablename__ = "users"  # 数据库中的表名

    # 定义数据库字段
    id = Column(Integer, primary_key=True, index=True)  # 主键
    username = Column(String, unique=True, index=True)  # 用户名，唯一
    email = Column(String, unique=True, index=True)  # 用户邮箱，唯一
    phone = Column(String,nullable=True)
    full_name = Column(String)  # 用户的全名
    password_hash = Column(String)  # 存储密码的哈希值
    role = Column(Enum(Role), default=Role.visitor)  # 用户角色
    membership_level = Column(Enum(MembershipLevel), default=MembershipLevel.none)  # 会员等级
    membership_expire = Column(DateTime, default=None)  # 会员到期时间
    status = Column(Integer, default=1)  # 用户状态，默认值为1（正常）
    created_at = Column(DateTime, default=datetime.utcnow)  # 记录用户创建时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 记录用户更新时间

    # 使用字符串引用，防止类的加载顺序问题
    commissions = relationship('Commissions', back_populates="user")  # 修改为 back_populates

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email}, role={self.role})>"
