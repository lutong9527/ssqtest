from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from models.user_points import UserPoints

router = APIRouter(prefix="/points", tags=["points"])


@router.get("/balance")
def get_balance(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    account = db.query(UserPoints).filter(UserPoints.user_id == current_user.id).first()

    if not account:
        return {"balance": 0}

    return {"balance": account.balance}
