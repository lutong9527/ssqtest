# tasks/backtest_tasks.py
from core.celery_app import celery_app
from database import SessionLocal


@celery_app.task(bind=True, name="backtest.run", max_retries=3)
def run_backtest_task(
    self,
    user_id: int,
    params_version: str,
    start_qi_shu: str,
    end_qi_shu: str,
    bet_amount: float,
    model_mode: str = "entropy"
):
    # 延迟导入，打破循环导入
    from services.backtest_service import BacktestService

    db = SessionLocal()
    try:
        result = BacktestService.execute_backtest(
            db=db,
            record_id=self.request.id,
            params_version=params_version,
            start_qi_shu=start_qi_shu,
            end_qi_shu=end_qi_shu,
            bet_amount=bet_amount,
            model_mode=model_mode
        )
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()
