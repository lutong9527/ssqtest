from dotenv import load_dotenv
load_dotenv()

import sys
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
import uvicorn

# ====== 路由注册 ======
from routers import (
    mall_router,
    points_router,
    commission_router,
    auth_router,
    recommend_router,
    order_router,
    proxy_router,
    withdraw_router,
    user_router,
    admin_router,
    task_router,
    content_router,
    admin_content_router,
    admin_commission_router,
)

from routers.backtest_router import router as backtest_router

# ====== 分布式任务和模型 ======
from models.loader import load_models
from tasks.order_timeout import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Scheduler starting...")
    scheduler.start()

    # 🔥 自动加载插件模型
    load_models()

    yield

    print("Scheduler shutting down...")
    scheduler.shutdown()


# Ensure lifespan only applied if running via Uvicorn
lifespan_flag = lifespan if __name__ != "__main__" else None

app = FastAPI(
    title="AI-SSQ Backend",
    description="双色球智能量化分析系统后端",
    version="2.0.0",
    docs_url=None,
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan_flag,
)

# ====== 静态文件 ======
app.mount("/static", StaticFiles(directory="static"), name="static")

# ====== CORS ======
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

# ====== 路由注册 - 统一使用中文标签，已全部修正为正确的 router 引用 ======
app.include_router(auth_router.router,              prefix=f"{API_PREFIX}/auth",              tags=["认证"])
app.include_router(recommend_router.router,         prefix=f"{API_PREFIX}/recommend",         tags=["推荐"])
app.include_router(order_router.router,             prefix=f"{API_PREFIX}/orders",            tags=["订单"])
app.include_router(proxy_router.router,             prefix=f"{API_PREFIX}/proxies",           tags=["代理"])
app.include_router(withdraw_router.router,          prefix=f"{API_PREFIX}/withdraws",         tags=["提现"])
app.include_router(user_router.router,              prefix=f"{API_PREFIX}/users",             tags=["用户"])
app.include_router(admin_router.router,             prefix=f"{API_PREFIX}/admin",             tags=["管理"])
app.include_router(points_router.router,            prefix=API_PREFIX,                        tags=["积分"])
app.include_router(mall_router.router,              prefix=API_PREFIX,                        tags=["商城"])
app.include_router(commission_router.router,        prefix=API_PREFIX,                        tags=["佣金"])
app.include_router(backtest_router,                 prefix=f"{API_PREFIX}/backtest",          tags=["回测"])
app.include_router(task_router.router,              prefix=f"{API_PREFIX}/tasks",             tags=["任务"])

# 内容管理相关（前台 + 后台）
app.include_router(content_router.router,           prefix=f"{API_PREFIX}/content",           tags=["内容管理"])
app.include_router(admin_content_router.router,     prefix=f"{API_PREFIX}/admin/content",     tags=["内容管理后台"])

# 后台佣金管理
app.include_router(admin_commission_router.router,  prefix=f"{API_PREFIX}/admin/commission", tags=["佣金管理"])

# 如果需要小程序/微信相关路由，可在此取消注释
# app.include_router(miniapp_router.router,           prefix=f"{API_PREFIX}/miniapp",           tags=["小程序"])
# app.include_router(wechat_router.router,            prefix=f"{API_PREFIX}/wechat",            tags=["微信"])


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get("/")
def root():
    return {"message": "AI-SSQ Backend is running - Distributed Mode"}


# Allow running directly using python main.py
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
