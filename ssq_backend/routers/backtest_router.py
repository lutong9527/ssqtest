# routers/backtest_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models.user import User
from schemas.backtest import BacktestRequest
from services.backtest_service import BacktestService

router = APIRouter(prefix="/backtest", tags=["回测"])


@router.post("/run")
def start_backtest(
    req: BacktestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.membership_level not in ["diamond"] and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅钻石会员及管理员可使用回测")

    return BacktestService.start_backtest(
        db=db,
        user_id=current_user.id,
        params_version=req.params_version,
        start_qi_shu=req.start_qi_shu,
        end_qi_shu=req.end_qi_shu,
        bet_amount=req.bet_amount,
        model_mode=req.model_mode
    )


@router.get("/{record_id}", response_model=dict)
def get_result(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.query(BacktestRecord).filter_by(id=record_id).first()
    if not record:
        raise HTTPException(404, "记录不存在")
    if record.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(403, "无权查看")
    return record
