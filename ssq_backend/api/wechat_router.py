from fastapi import APIRouter
from services.system_service import SystemService


router = APIRouter()


@router.get("/qr-login")
def wechat_qr_login():

    if not SystemService.is_enabled("enable_wechat_login"):
        return {"error": "wechat login disabled"}

    return {"qr_url": "generate_wechat_qr_here"}
