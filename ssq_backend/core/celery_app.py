# core/celery_app.py
# 注意：这个文件**绝对不能**出现任何 from celery_app import ... 的语句
# 否则会自循环导致 ModuleNotFoundError 或警告

from celery import Celery
from kombu import Queue
import os

# ────────────────────────────────────────────────
# 环境变量读取
# ────────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
#REDIS_PASSWORD = os.getenv("REDIS_PORT","")
# ────────────────────────────────────────────────
# 创建 Celery 实例
# ────────────────────────────────────────────────
celery_app = Celery(
    "compute_engine",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
#    broker=f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0",
#    backend=f"redis://:{REDIS_PASSOWRD}@{REDIS_HOST}:{REDIS_PORT}/1"
)

# ────────────────────────────────────────────────
# Celery 配置
# ────────────────────────────────────────────────
celery_app.conf.update(
    task_queues=(
        Queue("cpu_queue"),
        Queue("gpu_queue"),
        Queue("rl_queue"),
        Queue("backtest_queue"),
    ),
    task_routes={
        "tasks.compute_tasks.run_cpu_model": {"queue": "cpu_queue"},
        "tasks.compute_tasks.run_gpu_model": {"queue": "gpu_queue"},
        "tasks.compute_tasks.run_rl_model": {"queue": "rl_queue"},
        "backtest.run": {"queue": "backtest_queue"},
    },
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_time_limit=120,
    task_soft_time_limit=100,
    broker_connection_retry_on_startup=True,
)

# ────────────────────────────────────────────────
# 强制导入所有任务模块（关键，让 worker 认识你的任务）
# 必须使用绝对路径 from tasks.xxx import *
# ────────────────────────────────────────────────
imported_tasks = 0

try:
    from tasks.compute_tasks import *
    imported_tasks += 1
    print("[INFO] 成功导入 compute_tasks")
except ImportError as e:
    print(f"[WARNING] compute_tasks 导入失败：{e}")

try:
    from tasks.backtest_tasks import *
    imported_tasks += 1
    print("[INFO] 成功导入 backtest_tasks")
except ImportError as e:
    print(f"[WARNING] backtest_tasks 导入失败：{e}")

try:
    from tasks.order_timeout import *
    imported_tasks += 1
    print("[INFO] 成功导入 order_timeout")
except ImportError as e:
    print(f"[WARNING] order_timeout 导入失败：{e}")

try:
    from tasks.lottery_tasks import *
    imported_tasks += 1
    print("[INFO] 成功导入 lottery_tasks")
except ImportError as e:
    print(f"[WARNING] lottery_tasks 导入失败：{e}")

print(f"[INFO] 总共成功导入 {imported_tasks} 个任务模块")

# ────────────────────────────────────────────────
# 调试：打印所有已注册的任务（启动 worker 时查看）
# ────────────────────────────────────────────────
print("Celery 已注册的任务列表：")
for task_name in sorted(celery_app.tasks.keys()):
    print(f"  - {task_name}")
print(f"共 {len(celery_app.tasks)} 个任务已注册\n")
