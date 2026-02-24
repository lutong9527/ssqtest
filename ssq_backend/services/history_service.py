# services/history_service.py（完整替换原文件）

from typing import List, Optional
from sqlalchemy.orm import Session
from models.kaijiang import Kaijiang


class HistoryService:
    """
    开奖历史数据服务
    """

    @staticmethod
    def get_last_n_draws(db: Session, n: int = 200) -> List[Kaijiang]:
        """获取最近 n 期（按期号降序，最新的在前面）"""
        return db.query(Kaijiang)\
                 .order_by(Kaijiang.qi_shu.desc())\
                 .limit(n)\
                 .all()

    @staticmethod
    def get_all_draws(db: Session) -> List[Kaijiang]:
        """获取全部历史（按期号升序）—— 仅用于小数据量"""
        return db.query(Kaijiang)\
                 .order_by(Kaijiang.qi_shu.asc())\
                 .all()

    @staticmethod
    def get_draws_in_period_range(
        db: Session,
        start_qi_shu: str,
        end_qi_shu: str
    ) -> List[Kaijiang]:
        """
        【回测推荐使用】获取指定期号范围内的开奖记录（按期号升序）
        高效，支持大范围查询
        """
        return db.query(Kaijiang)\
                 .filter(
                     Kaijiang.qi_shu >= start_qi_shu,
                     Kaijiang.qi_shu <= end_qi_shu
                 )\
                 .order_by(Kaijiang.qi_shu.asc())\
                 .all()

    @staticmethod
    def get_draw_by_qishu(db: Session, qi_shu: str) -> Optional[Kaijiang]:
        """根据期号精确查询单期"""
        return db.query(Kaijiang).filter_by(qi_shu=qi_shu).first()

    @staticmethod
    def get_latest_draw(db: Session) -> Optional[Kaijiang]:
        """获取最新一期"""
        return db.query(Kaijiang)\
                 .order_by(Kaijiang.qi_shu.desc())\
                 .first()