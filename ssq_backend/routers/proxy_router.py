from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from auth import get_current_user
from models.user import User
from models.proxy import Proxy

router = APIRouter(tags=["proxy"])


@router.get("/subordinates")
def get_subordinates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 先找到当前用户的代理记录
    current_proxy = db.query(Proxy).filter(
        Proxy.user_id == current_user.id
    ).first()

    if not current_proxy:
        return []

    # 查询直属下级代理
    subs = db.query(User).join(
        Proxy, User.id == Proxy.user_id
    ).filter(
        Proxy.parent_id == current_proxy.id
    ).all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "membership_level": u.membership_level,
            "created_at": u.created_at
        }
        for u in subs
    ]
