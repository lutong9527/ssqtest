# schemas/backtest.py
from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


class BacktestRequest(BaseModel):
    params_version: str
    start_qi_shu: str
    end_qi_shu: str
    bet_amount: Decimal = Decimal("2.00")
    model_mode: str = "entropy"


class BacktestResponse(BaseModel):
    record_id: int
    task_id: Optional[str] = None
    status: str