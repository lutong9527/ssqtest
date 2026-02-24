from fastapi import Header, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from database import SessionLocal
from models.api_key import APIKey
from datetime import datetime


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_api_key(
    request: Request,
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    if not x_api_key:
        return None

    api_key_obj = db.query(APIKey).filter(
        APIKey.api_key == x_api_key,
        APIKey.is_active == 1
    ).first()

    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    if api_key_obj.expire_at and api_key_obj.expire_at < datetime.utcnow():
        raise HTTPException(status_code=403, detail="API Key expired")

    request.state.api_key = api_key_obj
    return api_key_obj