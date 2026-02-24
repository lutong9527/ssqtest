# services/backtest_service.py
from decimal import Decimal
from typing import Dict
from datetime import datetime
from sqlalchemy.orm import Session

from models.backtest_records import BacktestRecord
from models.params_snapshot import ParamsSnapshot
from services.recommend_service import RecommendEngine
from services.history_service import HistoryService


class BacktestService:

    # 简化奖级表（实际可根据真实奖金规则调整）
    PRIZE_RULES = {
        (6, 1): Decimal("5000000"),
        (6, 0): Decimal("1000000"),
        (5, 1): Decimal("300000"),
        (5, 0): Decimal("100000"),
        (4, 1): Decimal("3000"),
        (4, 0): Decimal("200"),
        (3, 1): Decimal("200"),
        (2, 1): Decimal("10"),
        (1, 1): Decimal("5"),
        (0, 1): Decimal("5"),
    }

    @staticmethod
    def start_backtest(
        db: Session,
        user_id: int,
        params_version: str,
        start_qi_shu: str,
        end_qi_shu: str,
        bet_amount: Decimal = Decimal("2.00"),
        model_mode: str = "entropy"
    ) -> Dict:
        snapshot = db.query(ParamsSnapshot).filter_by(version=params_version).first()
        if not snapshot:
            raise ValueError(f"参数版本 {params_version} 不存在")

        # 延迟导入，避免循环
        from tasks.backtest_tasks import run_backtest_task

        task = run_backtest_task.delay(
            user_id=user_id,
            params_version=params_version,
            start_qi_shu=start_qi_shu,
            end_qi_shu=end_qi_shu,
            bet_amount=float(bet_amount),
            model_mode=model_mode
        )

        record = BacktestRecord(
            params_version=params_version,
            start_qi_shu=start_qi_shu,
            end_qi_shu=end_qi_shu,
            status="running",
            task_id=task.id,
            created_by=user_id,
            bet_amount=bet_amount,
            model_mode=model_mode
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return {"record_id": record.id, "task_id": task.id, "status": "running"}

    @staticmethod
    def execute_backtest(
        db: Session,
        record_id: int,
        params_version: str,
        start_qi_shu: str,
        end_qi_shu: str,
        bet_amount: float,
        model_mode: str
    ):
        snapshot = db.query(ParamsSnapshot).filter_by(version=params_version).first()
        params = snapshot.params_json if snapshot and snapshot.params_json else {}

        engine = RecommendEngine(db)

        # 使用高效范围查询（不加载全表）
        all_draws = HistoryService.get_draws_in_period_range(db, start_qi_shu, end_qi_shu)
        if len(all_draws) < 50:
            raise ValueError("回测区间数据量过少（至少50期）")

        curve = []
        total_profit = Decimal("0")
        total_bets = Decimal("0")
        win_3plus = 0
        current_streak = 0
        max_streak = 0
        red_hits = []

        for i in range(params.get("history_window", 50), len(all_draws)):
            history_slice = all_draws[:i]
            actual = all_draws[i]

            pred = engine.generate_with_custom_history(
                history=history_slice,
                params=params,
                mode=model_mode
            )

            red_set = {actual.red1, actual.red2, actual.red3, actual.red4, actual.red5, actual.red6}
            red_hit = len(set(pred["reds"]) & red_set)
            blue_hit = 1 if pred["blue"] == actual.blue else 0

            prize = BacktestService.PRIZE_RULES.get((red_hit, blue_hit), Decimal("0"))
            profit = prize - Decimal(bet_amount)

            total_profit += profit
            total_bets += Decimal(bet_amount)
            red_hits.append(red_hit)

            if red_hit >= 3:
                win_3plus += 1
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

            curve.append({
                "qi_shu": actual.qi_shu,
                "pred_red": pred["reds"],
                "pred_blue": pred["blue"],
                "actual_red": [actual.red1, actual.red2, actual.red3, actual.red4, actual.red5, actual.red6],
                "actual_blue": actual.blue,
                "red_hit": red_hit,
                "blue_hit": blue_hit,
                "profit": float(profit),
                "cum_profit": float(total_profit)
            })

        periods = len(curve)
        avg_hit = sum(red_hits) / periods if periods else 0
        hit_rate = (win_3plus / periods * 100) if periods else 0
        roi = float(total_profit / total_bets * 100) if total_bets > 0 else 0

        # 更新记录
        record = db.query(BacktestRecord).filter_by(id=record_id).first()
        if record:
            record.periods = periods
            record.avg_hit = round(float(avg_hit), 4)
            record.hit_rate = round(float(hit_rate), 2)
            record.total_profit = float(total_profit)
            record.roi = round(roi, 2)
            record.max_streak = max_streak
            record.curve_data = curve
            record.status = "completed"
            record.finished_at = datetime.utcnow()
            db.commit()

        return {
            "record_id": record_id,
            "periods": periods,
            "avg_hit": round(float(avg_hit), 4),
            "hit_rate": round(float(hit_rate), 2),
            "total_profit": float(total_profit),
            "roi": round(roi, 2),
            "max_streak": max_streak
        }
