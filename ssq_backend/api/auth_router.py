from fastapi import APIRouter
from services.system_service import SystemService

router = APIRouter()


@router.post("/login")
def login():
    return {"message": "login success"}


@router.post("/email-verify")
def email_verify():
    if not SystemService.is_enabled("enable_email_auth"):
        return {"error": "email auth disabled"}
    return {"message": "email verify"}


@router.post("/sms-verify")
def sms_verify():
    if not SystemService.is_enabled("enable_sms_auth"):
        return {"error": "sms auth disabled"}
    return {"message": "sms verify"}


@router.post("/google-2fa")
def google_2fa():
    if not SystemService.is_enabled("enable_google_2fa"):
        return {"error": "2fa disabled"}
    return {"message": "2fa verify"}
