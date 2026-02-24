# schemas/withdraw.py
from pydantic import BaseModel, Field
from decimal import Decimal

class WithdrawRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="提现金额")
    withdraw_to: str = Field(..., description="wechat 或 alipay")
    account: str = Field(..., min_length=5, max_length=100, description="提现账号")