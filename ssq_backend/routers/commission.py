# routers/commission.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.commission_service import CommissionService
from decimal import Decimal

router = APIRouter()

@router.post("/simulate_order")
def simulate_order(
    user_id: int,
    amount: Decimal,
    db: Session = Depends(get_db)
):
    CommissionService.create_commission_records(
        db=db,
        user_id=user_id,
        source_type="vip_upgrade",
        source_id=1,
        order_amount=amount
    )
    return {"msg": "commission generated"}
