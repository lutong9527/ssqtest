# routers/order_router.py（完整简化版，可直接覆盖）
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from database import get_db
from auth import get_current_user
from models.user import User
from models.order import Order
from schemas.order import CreateOrderRequest, OrderResponse

router = APIRouter(tags=["order"])

# ==================== 临时硬编码配置（测试用） ====================
ALIPAY_APPID = "your_alipay_appid_here"
ALIPAY_APP_PRIVATE_KEY = """your_private_key_here"""
ALIPAY_ALIPAY_PUBLIC_KEY = """your_alipay_public_key_here"""
ALIPAY_NOTIFY_URL = "http://localhost:8000/api/order/alipay/notify"
ALIPAY_RETURN_URL = "http://localhost:8000/vip-upgrade/success"
ALIPAY_GATEWAY = "https://openapi.alipaydev.com/gateway.do"

# ==================== 支付宝客户端 ====================
# from alipay import AliPay   # 暂时注释，避免 alipay 版本问题
# alipay = AliPay(
#     appid=ALIPAY_APPID,
#     app_notify_url=ALIPAY_NOTIFY_URL,
#     app_private_key_string=ALIPAY_APP_PRIVATE_KEY,
#     alipay_public_key_string=ALIPAY_ALIPAY_PUBLIC_KEY,
#     sign_type="RSA2",
#     debug=True
# )

PRICE_TABLE = {
    1: 29.90,
    3: 79.90,
    12: 199.00
}

@router.post("/", response_model=OrderResponse)
def create_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if request.months not in PRICE_TABLE:
        raise HTTPException(400, "不支持的购买时长")

    amount = PRICE_TABLE[request.months]
    order_no = f"SSQ{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"

    order = Order(
        user_id=current_user.id,
        order_no=order_no,
        amount=amount,
        membership_months=request.months,
        payment_method="alipay",
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 临时返回一个假的支付链接（避免支付宝导入问题）
    full_pay_url = f"https://openapi.alipaydev.com/gateway.do?out_trade_no={order_no}&total_amount={amount}"

    return OrderResponse(
        order_no=order_no,
        amount=amount,
        qr_code_url=full_pay_url,
        status="pending",
        created_at=order.created_at
    )

@router.post("/alipay/notify")
async def alipay_notify(request: Request, db: Session = Depends(get_db)):
    return {"status": "success"}  # 临时返回成功，方便测试