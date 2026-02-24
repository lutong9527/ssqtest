# routers/recommend_router.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

# 关键：导入 get_current_user
from auth import get_current_user
from database import get_db
from models.user import User

# 导入你的 Celery 任务（根据实际路径调整）
from tasks.compute_tasks import run_cpu_model, run_gpu_model, run_rl_model

router = APIRouter(
    prefix="",                  # 前缀已在 main.py 统一设置，此处留空
    tags=["推荐"]
)


@router.post("/distributed")
def distributed_recommend(
    periods: int = Query(
        200,
        ge=50,
        le=1000,
        description="历史参考期数，建议50~1000"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    提交分布式推荐任务（根据用户角色分配不同算力队列）
    
    - visitor/normal/regular → cpu_queue（普通随机模型）
    - vip/diamond → gpu_queue（高级模型）
    - admin 或其他 → rl_queue（强化学习模型）
    """
    if current_user.role == "visitor":
        raise HTTPException(
            status_code=403,
            detail="游客角色暂无推荐权限，请登录或升级会员"
        )

    if current_user.role in ["normal", "regular"]:
        task = run_cpu_model.delay(current_user.id, periods)
        queue_name = "cpu_queue"
        group_count = 1  # 普通用户只返回一组

    elif current_user.role in ["vip", "diamond"]:
        task = run_gpu_model.delay(current_user.id, periods)
        queue_name = "gpu_queue"
        group_count = 5  # VIP 返回多组（可根据需求调整）

    else:
        # admin 或其他高级角色
        task = run_rl_model.delay(current_user.id, periods)
        queue_name = "rl_queue"
        group_count = 5

    return {
        "message": "推荐任务已提交，请稍后查询结果",
        "task_id": task.id,
        "queue": queue_name,
        "user_role": current_user.role,
        "periods": periods,
        "expected_groups": group_count,
        "next_step": f"轮询 GET /api/v1/tasks/{task.id} 获取结果"
    }
