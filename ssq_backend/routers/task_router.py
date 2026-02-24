# routers/task_router.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db.session import SessionLocal  # 确保正确导入数据库会话
from tasks.compute_tasks import run_cpu_model, run_gpu_model, run_rl_model  # 假设这些是分布式任务

# 创建 router 对象
router = APIRouter()

# 数据库会话获取器
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 路由：任务状态查询
@router.get("/task-status/{task_id}")
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    # 这里可以查询数据库中的任务状态，假设我们有一个任务模型
    # 查询任务状态（这只是一个示例，具体需要根据你项目的任务结构来实现）
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"task_id": task.id, "status": task.status}

# 路由：提交 CPU 任务
@router.post("/run-cpu-task")
def run_cpu_task(data: dict, db: Session = Depends(get_db)):
    # 假设这个方法运行 CPU 模型任务
    result = run_cpu_model(data)
    return {"message": "CPU task started", "result": result}

# 路由：提交 GPU 任务
@router.post("/run-gpu-task")
def run_gpu_task(data: dict, db: Session = Depends(get_db)):
    # 假设这个方法运行 GPU 模型任务
    result = run_gpu_model(data)
    return {"message": "GPU task started", "result": result}

# 路由：提交 RL 任务
@router.post("/run-rl-task")
def run_rl_task(data: dict, db: Session = Depends(get_db)):
    # 假设这个方法运行强化学习模型任务
    result = run_rl_model(data)
    return {"message": "Reinforcement Learning task started", "result": result}

