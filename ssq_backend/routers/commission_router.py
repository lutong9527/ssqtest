from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from models.commission_log import CommissionLog

router = APIRouter(prefix="/commission", tags=["commission"])


@router.get("/logs")
def get_commission_logs(db: Session = Depends(get_db),
                        current_user=Depends(get_current_user)):
    logs = db.query(CommissionLog).filter(
        CommissionLog.user_id == current_user.id
    ).all()

    return logs
