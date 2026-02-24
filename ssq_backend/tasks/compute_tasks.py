# tasks/compute_tasks.py
from core.celery_app import celery_app
from compute.model_manager import ModelManager
from db.session import SessionLocal
from models.user import User   # 必须导入 User 模型


def _execute_model(user_id: int, periods: int):
    """
    统一执行入口，防止数据库连接泄露
    """
    db = SessionLocal()
    try:
        # 先查询出 User 对象，而不是直接传 user_id
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        # 现在传入的是 User 对象，而不是 int
        manager = ModelManager(user=user, db=db, periods=periods)
        result = manager.execute()
        return result
    except Exception as e:
        # 可以在这里记录错误日志，方便调试
        print(f"执行模型出错: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(name="tasks.compute_tasks.run_cpu_model")
def run_cpu_model(user_id: int, periods: int):
    return _execute_model(user_id, periods)


@celery_app.task(name="tasks.compute_tasks.run_gpu_model")
def run_gpu_model(user_id: int, periods: int):
    return _execute_model(user_id, periods)


@celery_app.task(name="tasks.compute_tasks.run_rl_model")
def run_rl_model(user_id: int, periods: int):
    return _execute_model(user_id, periods)
