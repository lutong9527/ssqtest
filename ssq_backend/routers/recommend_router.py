from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models.user import User
from tasks.compute_tasks import run_cpu_model, run_gpu_model, run_rl_model

router = APIRouter(
    prefix="",                  # 前缀已在 main.py 统一设置，此处留空
    tags=["推荐"]
)


@router.post("/distributed")
def distributed_recommend(
    periods: int = Query(200, ge=50, le=1000, description="历史参考期数，建议50~1000"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    提交分布式推荐任务（根据用户角色分配不同算力队列）
    
    - normal → cpu_queue
    - vip    → gpu_queue
    - 其他（钻石/管理员等） → rl_queue
    """
    if current_user.role == "visitor":
        return {"error": "游客角色暂无推荐权限，请升级会员"}

    if current_user.role == "normal" or current_user.role == "regular":
        task = run_cpu_model.delay(current_user.id, periods)
        queue_name = "cpu_queue"
    elif current_user.role in ["vip", "diamond"]:
        task = run_gpu_model.delay(current_user.id, periods)
        queue_name = "gpu_queue"
    else:
        # admin 或其他高级角色使用强化学习队列
        task = run_rl_model.delay(current_user.id, periods)
        queue_name = "rl_queue"

    return {
        "message": "推荐任务已提交",
        "task_id": task.id,
        "queue": queue_name,
        "user_role": current_user.role,
        "periods": periods
    }