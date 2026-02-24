# tasks/lottery_tasks.py
from core.celery_app import celery_app   # ← 唯一正确的导入方式
from compute.model_manager import ModelManager   # ← 直接从 compute 导入 ModelManager（避免 models 循环）

@celery_app.task(name="tasks.lottery_tasks.run_model_task")
def run_model_task(model_code, params, user_id):
    manager = ModelManager()  # 注意：这里 ModelManager 可能需要传入参数
    result = manager.run_model(model_code, params, user_id)
    return result
