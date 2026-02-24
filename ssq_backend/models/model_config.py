# models/model_config.py
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from models.user import User  # 用于记录谁修改的参数


class ModelConfig(Base):
    """
    模型参数配置表（每个模型一个记录，支持版本化）
    """
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_code = Column(String(50), nullable=False, index=True, unique=True)  # 模型唯一标识，如 "markov_improved"
    model_name = Column(String(100), nullable=True)  # 可读名称，如 "改进马尔科夫链模型"

    # 通用参数（所有模型都可能用到的）
    history_window = Column(Integer, default=200, comment="历史数据窗口期数")
    entropy_tolerance = Column(Float, default=0.05, comment="熵平衡容差")
    monte_carlo_samples = Column(Integer, default=2000, comment="蒙特卡洛采样次数")

    # 模型专属参数（JSON 存储，灵活扩展）
    custom_params = Column(JSON, nullable=False, default=dict, comment="模型专属参数字典")

    # 版本控制与审计
    version = Column(Integer, default=1, comment="参数版本号")
    description = Column(String(500), nullable=True, comment="本次修改说明")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建/修改人")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系：关联修改人信息
    creator = relationship("User", foreign_keys=[created_by], lazy="selectin")

    def __repr__(self):
        return f"<ModelConfig {self.model_code} v{self.version}>"

    @property
    def all_params(self) -> dict:
        """合并通用参数 + 自定义参数"""
        return {
            "history_window": self.history_window,
            "entropy_tolerance": self.entropy_tolerance,
            "monte_carlo_samples": self.monte_carlo_samples,
            **self.custom_params
        }
