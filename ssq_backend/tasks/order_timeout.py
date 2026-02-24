# tasks/order_timeout.py
"""
订单超时自动取消任务
- 每 5 分钟运行一次
- 检查所有 status='pending' 且创建时间超过 30 分钟的订单
- 自动将它们改为 status='cancelled'
- 可通过 APScheduler 在 main.py 中启动
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from database import SessionLocal
from models.order import Order

def cancel_timeout_orders():
    """
    取消超时未支付的订单
    """
    db = SessionLocal()
    try:
        timeout_threshold = datetime.utcnow() - timedelta(minutes=30)  # 30分钟超时
        timeout_orders = db.query(Order).filter(
            Order.status == "pending",
            Order.created_at < timeout_threshold
        ).all()

        cancelled_count = 0
        for order in timeout_orders:
            order.status = "cancelled"
            cancelled_count += 1

        if cancelled_count > 0:
            db.commit()
            print(f"[{datetime.now()}] 已自动取消 {cancelled_count} 个超时订单")
        else:
            print(f"[{datetime.now()}] 无超时订单需要取消")

    except Exception as e:
        print(f"订单超时任务执行出错: {e}")
    finally:
        db.close()


# 全局调度器（在 main.py 中启动）
scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(
    cancel_timeout_orders,
    'interval',
    minutes=5,           # 每5分钟检查一次
    id='order_timeout_job',
    name='取消超时订单任务',
    replace_existing=True
)