from fastapi import APIRouter
from api.auth_router import router as auth_router
from api.compute_router import router as compute_router
from api.wechat_router import router as wechat_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(compute_router, prefix="/compute", tags=["Compute"])
api_router.include_router(wechat_router, prefix="/wechat", tags=["WeChat"])

