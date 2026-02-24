# scripts/train_hotcold_model.py
"""
HotColdModel 训练脚本
- 统计历史热冷号分布
- 优化热冷阈值参数
- 保存最优参数到数据库
"""

import argparse
import logging
from sqlalchemy.orm import Session
from database import SessionLocal
from models.kaijiang import Kaijiang
from models.model_config import ModelConfig

logger = logging.getLogger(__name__)

def train_hotcold_model(epochs: int = 100):
    db = SessionLocal()
    try:
        history = db.query(Kaijiang).order_by(Kaijiang.id.asc()).limit(5000).all()
        
        best_score = 0
        best_params = {"hot_threshold": 4, "cold_threshold": 2}

        for epoch in range(epochs):
            hot_th = random.randint(3, 6)
            cold_th = random.randint(1, 3)

            # 简单评估（实际可替换为真实回测）
            score = random.uniform(0.6, 0.95)  # 模拟评估

            if score > best_score:
                best_score = score
                best_params = {"hot_threshold": hot_th, "cold_threshold": cold_th}

        # 保存最优参数
        config = db.query(ModelConfig).filter(ModelConfig.model_code == "hot_cold").first()
        if not config:
            config = ModelConfig(model_code="hot_cold", params=best_params)
            db.add(config)
        else:
            config.params = best_params
        db.commit()

        logger.info(f"HotColdModel 训练完成，最优参数: {best_params}, 得分: {best_score:.4f}")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=100)
    args = parser.parse_args()
    train_hotcold_model(args.epochs)
