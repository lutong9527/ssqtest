# models/backtest_records.py
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from database import Base


class BacktestRecord(Base):
    __tablename__ = "backtest_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    params_version = Column(String(50), nullable=False, index=True)
    start_qi_shu = Column(String(10), nullable=False)
    end_qi_shu = Column(String(10), nullable=False)
    periods = Column(Integer, default=0)
    avg_hit = Column(Float, default=0.0)           # 平均红球命中数
    hit_rate = Column(Float, default=0.0)          # 红球≥3命中率(%)
    total_profit = Column(DECIMAL(12, 2), default=0.00)
    roi = Column(Float, default=0.0)               # 投资回报率(%)
    max_streak = Column(Integer, default=0)        # 最大连中次数
    curve_data = Column(JSON, default=list)        # 每期详细曲线
    status = Column(String(20), default="pending") # pending/running/completed/failed
    task_id = Column(String(50), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    bet_amount = Column(DECIMAL(10, 2), default=2.00)
    model_mode = Column(String(20), default="entropy")
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<BacktestRecord {self.params_version} {self.status}>"