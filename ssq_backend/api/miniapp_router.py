from fastapi import APIRouter
from services.system_service import SystemService


router = APIRouter()


@router.post("/wx-miniapp")
def wx_miniapp_api():

    if not SystemService.is_enabled("enable_miniapp_api"):
        return {"error": "miniapp disabled"}

    return {"message": "wx miniapp endpoint"}


@router.post("/alipay-miniapp")
def alipay_miniapp_api():

    if not SystemService.is_enabled("enable_alipay_miniapp_api"):
        return {"error": "alipay miniapp disabled"}

    return {"message": "alipay miniapp endpoint"}
