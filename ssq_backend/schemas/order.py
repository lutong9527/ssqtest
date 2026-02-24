# schemas/order.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CreateOrderRequest(BaseModel):
    months: int = Field(..., ge=1, le=12, description="购买月数")
    payment_method: str = Field("alipay", description="alipay 或 wechat")

class OrderResponse(BaseModel):
    order_no: str
    amount: float
    qr_code_url: Optional[str] = None
    status: str
    created_at: datetime