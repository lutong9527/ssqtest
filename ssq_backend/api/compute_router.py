from fastapi import APIRouter, Depends
from tasks.compute_tasks import (
    run_cpu_model,
    run_gpu_model,
    run_rl_model
)
from auth.dependencies import get_current_user

router = APIRouter()


@router.post("/recommend")
def recommend(periods: int = 200, current_user=Depends(get_current_user)):

    if current_user.role == "normal":
        task = run_cpu_model.delay(current_user.id, periods)

    elif current_user.role == "vip":
        task = run_gpu_model.delay(current_user.id, periods)

    else:
        task = run_rl_model.delay(current_user.id, periods)

    return {"task_id": task.id}
