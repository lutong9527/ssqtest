from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal

from database import get_db
from auth import get_current_user
from models.user import User
from models.proxy import Proxy
from models.withdraw import Withdraw

router = APIRouter(tags=["withdraw"])


class WithdrawRequest(BaseModel):
    amount: Decimal
    withdraw_to: str  # wechat / alipay
    account: str      # 提现账号


@router.post("/")
def create_withdraw(
    req: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 只有代理才能提现
    if not current_user.proxy_id:
        raise HTTPException(status_code=403, detail="只有代理才能提现")

    proxy = db.query(Proxy).filter(
        Proxy.user_id == current_user.id
    ).first()

    if not proxy:
        raise HTTPException(status_code=404, detail="代理不存在")

    if proxy.total_commission < req.amount:
        raise HTTPException(status_code=400, detail="佣金余额不足")

    # 扣减佣金
    proxy.total_commission -= req.amount

    # 生成提现记录
    withdraw = Withdraw(
        user_id=current_user.id,
        amount=req.amount,
        withdraw_to=req.withdraw_to,
        account=req.account,
        status="pending"
    )

    db.add(withdraw)
    db.commit()

    return {
        "success": True,
        "message": "提现申请已提交",
        "amount": float(req.amount),
        "remaining": float(proxy.total_commission)
    }
