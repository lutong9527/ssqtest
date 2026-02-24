# scripts/train_neural_model.py
"""
神经网络模型训练脚本 - 双色球专用
功能：
- 加载真实历史开奖数据（从数据库或文件）
- 构建训练数据集（特征：历史 N 期红球，标签：下一期红球 one-hot）
- 支持 LSTM / Transformer backbone
- 简单训练循环 + 权重保存
- 支持命令行参数配置（epochs、lr、batch_size 等）
"""

import argparse
import logging
import os
import random
from typing import List, Dict, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np

from compute.neural_network_model import NeuralNetworkModel, SimpleMLP, LSTMBackbone, TransformerBackbone
from database import SessionLocal  # 假设你有数据库 session
from models.kaijiang import Kaijiang  # 假设开奖数据表叫 Kaijiang

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class LotteryDataset(Dataset):
    """双色球历史数据 Dataset"""

    def __init__(self, history: List[Dict], seq_len: int = 10, use_onehot: bool = True):
        self.seq_len = seq_len
        self.use_onehot = use_onehot

        # 准备序列数据
        self.features = []
        self.labels_red = []   # 下一期红球 one-hot (33维)
        self.labels_blue = []  # 下一期蓝球 one-hot (16维)

        for i in range(len(history) - seq_len):
            seq = []
            for j in range(i, i + seq_len):
                draw = history[j]
                reds = draw.get("reds") or draw.get("red", [])
                vec = [0] * 33
                for r in reds:
                    if 1 <= r <= 33:
                        vec[r-1] = 1 if use_onehot else vec[r-1] + 1
                seq.append(vec)

            next_draw = history[i + seq_len]
            next_reds = next_draw.get("reds") or next_draw.get("red", [])
            next_blue = next_draw.get("blue") or next_draw.get("blues", [1])[0]

            red_label = [0] * 33
            for r in next_reds:
                if 1 <= r <= 33:
                    red_label[r-1] = 1

            blue_label = [0] * 16
            if 1 <= next_blue <= 16:
                blue_label[next_blue-1] = 1

            self.features.append(seq)
            self.labels_red.append(red_label)
            self.labels_blue.append(blue_label)

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        feature = torch.tensor(self.features[idx], dtype=torch.float32)
        label_red = torch.tensor(self.labels_red[idx], dtype=torch.float32)
        label_blue = torch.tensor(self.labels_blue[idx], dtype=torch.float32)
        return feature, label_red, label_blue


def load_training_data(db, periods: int = 2000) -> List[Dict]:
    """从数据库加载历史开奖数据"""
    draws = db.query(Kaijiang).order_by(Kaijiang.id.desc()).limit(periods).all()
    history = []
    for draw in draws:
        history.append({
            "reds": [draw.red1, draw.red2, draw.red3, draw.red4, draw.red5, draw.red6],
            "blue": draw.blue
        })
    history.reverse()  # 按时间顺序
    return history


def train_model(args):
    """训练主函数"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"使用设备: {device}")

    # 加载数据
    db = SessionLocal()
    history = load_training_data(db, args.data_periods)
    db.close()

    if len(history) < args.seq_len + 1:
        logger.error("历史数据不足，无法训练")
        return

    dataset = LotteryDataset(history, seq_len=args.seq_len, use_onehot=args.use_onehot)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

    # 构建模型（与推理时保持一致）
    model = NeuralNetworkModel(history=history, params={
        "backbone": args.backbone,
        "hidden_size": args.hidden_size,
        "num_layers": args.num_layers,
        "nhead": args.nhead,
        "dropout": args.dropout,
        "history_window": args.seq_len
    }).model.to(device)

    # 损失函数
    criterion = nn.BCEWithLogitsLoss()

    # 优化器
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)

    # 训练循环
    model.train()
    best_loss = float('inf')
    for epoch in range(args.epochs):
        total_loss = 0.0
        for features, labels_red, labels_blue in dataloader:
            features = features.to(device)      # (batch, seq_len, 33)
            labels_red = labels_red.to(device)  # (batch, 33)
            labels_blue = labels_blue.to(device)  # (batch, 16)

            optimizer.zero_grad()
            output = model(features)           # (batch, 33+16)
            pred_red = output[:, :33]
            pred_blue = output[:, 33:]

            loss_red = criterion(pred_red, labels_red)
            loss_blue = criterion(pred_blue, labels_blue)
            loss = loss_red + loss_blue

            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader)
        logger.info(f"Epoch [{epoch+1}/{args.epochs}] 损失: {avg_loss:.6f}")

        # 保存最佳权重
        if avg_loss < best_loss:
            best_loss = avg_loss
            save_path = f"weights/neural_model_best_epoch_{epoch+1}.pth"
            torch.save(model.state_dict(), save_path)
            logger.info(f"保存最佳权重: {save_path}")

    # 保存最终权重
    final_path = "weights/neural_model_final.pth"
    torch.save(model.state_dict(), final_path)
    logger.info(f"训练完成，最终权重保存: {final_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="训练神经网络双色球预测模型")
    parser.add_argument("--backbone", type=str, default="transformer", choices=["lstm", "transformer", "hybrid"],
                        help="模型 backbone 类型")
    parser.add_argument("--hidden_size", type=int, default=256, help="隐藏层大小")
    parser.add_argument("--num_layers", type=int, default=3, help="层数")
    parser.add_argument("--nhead", type=int, default=8, help="Transformer 注意力头数")
    parser.add_argument("--dropout", type=float, default=0.3, help="Dropout 比率")
    parser.add_argument("--seq_len", type=int, default=15, help="历史序列长度")
    parser.add_argument("--epochs", type=int, default=50, help="训练轮数")
    parser.add_argument("--batch_size", type=int, default=32, help="批大小")
    parser.add_argument("--lr", type=float, default=0.001, help="学习率")
    parser.add_argument("--data_periods", type=int, default=2000, help="加载历史开奖期数")

    args = parser.parse_args()
    train_model(args)
