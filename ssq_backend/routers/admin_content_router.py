from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from models.banner import Banner
from models.announcement import Announcement

router = APIRouter(prefix="/admin/content", tags=["admin-content"])


def admin_required(user):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")


# 新增 Banner
@router.post("/banner")
def create_banner(data: dict,
                  db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):

    admin_required(current_user)

    banner = Banner(**data)
    db.add(banner)
    db.commit()

    return {"message": "创建成功"}


# 修改 Banner
@router.put("/banner/{banner_id}")
def update_banner(banner_id: int,
                  data: dict,
                  db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):

    admin_required(current_user)

    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    for key, value in data.items():
        setattr(banner, key, value)

    db.commit()

    return {"message": "更新成功"}
