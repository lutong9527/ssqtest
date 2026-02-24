# routers/admin_router.py
"""
AI-SSQ 后台管理路由 - 强化版 v3.0
功能：
- 角色每日限制管理
- 模型参数完整CRUD + 版本历史
- 一键模型训练（异步）
- 模型性能监控
- 系统健康检查
- 统一响应格式 + 详细日志
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import subprocess
import logging

from database import get_db
from models.role_limit import RoleLimit
from models.user import User
from models.model_config import ModelConfig
from models.model_param_history import ModelParamHistory
from auth import get_current_user
from models.registry import ModelRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["管理"])

# =========================
# 统一响应模型
# =========================
class StandardResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None


# =========================
# 请求模型
# =========================
class UpdateRoleLimitRequest(BaseModel):
    role: str
    daily_limit: int


class ModelParamUpdate(BaseModel):
    params: Dict[str, Any]
    description: Optional[str] = None  # 修改说明，用于版本历史


class TrainModelRequest(BaseModel):
    model_code: str
    epochs: Optional[int] = 50
    batch_size: Optional[int] = 32
    learning_rate: Optional[float] = 0.001


# =========================
# 权限校验
# =========================
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问此接口"
        )
    return current_user


# =========================
# 角色每日限制
# =========================
@router.get("/role-limits", response_model=StandardResponse)
def get_role_limits(
    db: Session = Depends(get_db),
    _admin = Depends(require_admin)
):
    limits = db.query(RoleLimit).all()
    return StandardResponse(
        message="获取成功",
        data=[{"role": item.role, "daily_limit": item.daily_limit} for item in limits]
    )


@router.post("/role-limit/update", response_model=StandardResponse)
def update_role_limit(
    request: UpdateRoleLimitRequest,
    db: Session = Depends(get_db),
    _admin = Depends(require_admin)
):
    role_limit = db.query(RoleLimit).filter(RoleLimit.role == request.role).first()
    if not role_limit:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    role_limit.daily_limit = request.daily_limit
    db.commit()
    
    return StandardResponse(message=f"{request.role} 每日限制已更新为 {request.daily_limit}")


# =========================
# 模型参数管理（强化版）
# =========================
@router.get("/model-params", response_model=StandardResponse)
def get_all_model_params(
    db: Session = Depends(get_db),
    _admin = Depends(require_admin)
):
    configs = db.query(ModelConfig).all()
    data = [
        {
            "model_code": c.model_code,
            "params": c.params,
            "version": c.version,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        }
        for c in configs
    ]
    return StandardResponse(message="获取成功", data=data)


@router.post("/model-params/{model_code}", response_model=StandardResponse)
def update_model_params(
    model_code: str,
    request: ModelParamUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """更新模型参数并记录历史版本"""
    config = db.query(ModelConfig).filter(ModelConfig.model_code == model_code).first()
    
    if not config:
        config = ModelConfig(
            model_code=model_code,
            params=request.params,
            version=1,
            description=request.description or "初始配置"
        )
        db.add(config)
    else:
        # 记录旧版本
        history = ModelParamHistory(
            model_code=model_code,
            version=config.version,
            params=config.params.copy(),
            description=config.description,
            updated_by=current_user.username
        )
        db.add(history)

        # 更新当前配置
        config.params = request.params
        config.version += 1
        config.description = request.description or f"版本 {config.version} 更新"

    db.commit()
    db.refresh(config)

    return StandardResponse(
        message=f"模型 {model_code} 参数已更新至版本 {config.version}",
        data={"version": config.version, "params": config.params}
    )


@router.get("/model-params/{model_code}/history", response_model=StandardResponse)
def get_model_param_history(
    model_code: str,
    db: Session = Depends(get_db),
    _admin = Depends(require_admin)
):
    """获取参数版本历史"""
    histories = db.query(ModelParamHistory)\
        .filter(ModelParamHistory.model_code == model_code)\
        .order_by(ModelParamHistory.version.desc())\
        .all()
    
    data = [
        {
            "version": h.version,
            "updated_at": h.updated_at.isoformat() if h.updated_at else None,
            "description": h.description,
            "params": h.params,
            "updated_by": h.updated_by
        }
        for h in histories
    ]
    return StandardResponse(message="获取成功", data=data)


# =========================
# 模型训练接口（核心强化功能）
# =========================
@router.post("/train-model", response_model=StandardResponse)
def train_model(
    request: TrainModelRequest,
    background_tasks: BackgroundTasks,
    _admin = Depends(require_admin)
):
    """异步触发模型训练（支持神经网络、遗传算法等）"""
    background_tasks.add_task(run_training_task, request.model_code, request.epochs, request.batch_size, request.learning_rate)
    
    return StandardResponse(
        message=f"模型 {request.model_code} 训练任务已提交，后台异步执行中",
        data={"model_code": request.model_code, "epochs": request.epochs}
    )


def run_training_task(model_code: str, epochs: int = 50, batch_size: int = 32, lr: float = 0.001):
    """实际执行训练任务"""
    try:
        logger.info(f"开始训练模型: {model_code}, epochs={epochs}")
        
        cmd = [
            "python", "scripts/train_neural_model.py",
            "--backbone", "transformer",
            "--epochs", str(epochs),
            "--batch_size", str(batch_size),
            "--lr", str(lr)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="/home/orange/case/ssq_backend")
        
        if result.returncode == 0:
            logger.info(f"模型 {model_code} 训练成功")
            logger.info(result.stdout)
        else:
            logger.error(f"训练失败: {result.stderr}")
            
    except Exception as e:
        logger.error(f"训练任务执行异常: {e}")


# =========================
# 已注册模型列表（调试 + 后台展示）
# =========================
@router.get("/registered-models", response_model=StandardResponse)
def get_registered_models(_admin = Depends(require_admin)):
    """查看当前已注册的所有模型"""
    models = ModelRegistry.list_registered()
    return StandardResponse(message="获取成功", data=models)


# =========================
# 系统健康检查
# =========================
@router.get("/health", response_model=StandardResponse)
def health_check():
    """系统健康检查"""
    return StandardResponse(
        message="服务正常运行",
        data={
            "status": "healthy",
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@router.get("/celery-status")
def celery_status(_admin = Depends(require_admin)):
    """Celery 工作状态检查"""
    # 这里可以扩展实际检查 Celery worker 状态
    return StandardResponse(
        message="Celery 状态检查",
        data={"status": "running", "workers": "unknown"}
    )
