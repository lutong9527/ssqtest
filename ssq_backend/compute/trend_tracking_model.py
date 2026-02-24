# compute/trend_tracking_model.py
"""
趋势追踪 + 冷热号 + 遗漏值加权模型 - 双色球专用（强化版 v3.1）
核心特点：
- 趋势追踪（近期上升/下降方向）
- 冷热号权重（近期热号 + 长期冷号平衡）
- 遗漏值加权（遗漏越久，选中概率越高）
- 多因素加权融合（趋势 + 冷热 + 遗漏）
- 支持后台动态调节所有权重
- 严格约束过滤 + 多次重试
"""

from typing import List, Dict, Any
import random
import logging
import numpy as np

from models.base import BaseLotteryModel
from models.registry import register_model

logger = logging.getLogger(__name__)


@register_model
class TrendTrackingModel(BaseLotteryModel):
    """
    趋势追踪 + 冷热号 + 遗漏值加权模型
    综合考虑近期趋势、热冷分布、遗漏期数
    """

    # ==================== 必须定义的字段 ====================
    model_code = "trend_tracking"
    model_name = "趋势追踪 + 冷热遗漏模型"
    enabled_by_default = True

    # 可配置参数（后台可实时修改）
    default_params: Dict[str, Any] = {
        # 趋势追踪
        "trend_strength": 0.65,                    # 趋势跟随强度（0.3~1.0）
        "max_offset": 7,                           # 单个数值最大偏移量

        # 冷热号权重
        "hot_weight": 0.45,                        # 热号偏好权重
        "cold_weight": 0.35,                       # 冷号偏好权重
        "recent_hot_periods": 8,                   # 热号统计窗口
        "long_cold_periods": 30,                   # 冷号统计窗口

        # 遗漏值加权
        "miss_weight": 0.25,                       # 遗漏期数权重
        "miss_boost": 1.8,                         # 遗漏加成系数（越高越偏好大遗漏）

        # 历史参考
        "history_window": 60,                      # 整体历史参考窗口

        # 约束参数
        "min_odd_count": 2,
        "max_odd_count": 4,
        "min_sum": 70,
        "max_sum": 140,
        "max_consecutive": 2
    }

    def __init__(self, history: List[Dict] = None, params: Dict = None, **kwargs):
        super().__init__(history=history, params=params, **kwargs)

        self.trend_strength = self.params["trend_strength"]
        self.max_offset = self.params["max_offset"]
        self.hot_weight = self.params["hot_weight"]
        self.cold_weight = self.params["cold_weight"]
        self.miss_weight = self.params["miss_weight"]
        self.miss_boost = self.params["miss_boost"]
        self.history_window = self.params["history_window"]

        # 预计算冷热号和遗漏值
        self.hot_reds, self.cold_reds = self._analyze_hot_cold()
        self.miss_values = self._analyze_miss_values()

    # ==================== 冷热号分析 ====================
    def _analyze_hot_cold(self):
        """统计近期热号和长期冷号"""
        recent = self.history[-self.params["recent_hot_periods"]:] if self.history else []
        long_term = self.history[-self.params["long_cold_periods"]:] if self.history else []

        red_freq_recent = {i: 0 for i in range(1, 34)}
        red_freq_long = {i: 0 for i in range(1, 34)}

        for draw in recent:
            reds = draw.get("reds") or draw.get("red", [])
            for r in reds:
                if 1 <= r <= 33:
                    red_freq_recent[r] += 1

        for draw in long_term:
            reds = draw.get("reds") or draw.get("red", [])
            for r in reds:
                if 1 <= r <= 33:
                    red_freq_long[r] += 1

        # 热号：近期高频
        hot_reds = [k for k, v in red_freq_recent.items() if v >= 3]
        # 冷号：长期低频
        cold_reds = [k for k, v in red_freq_long.items() if v <= 2]

        return hot_reds, cold_reds

    # ==================== 遗漏值分析 ====================
    def _analyze_miss_values(self) -> Dict[int, int]:
        """计算每个红球的当前遗漏期数"""
        if not self.history:
            return {i: 0 for i in range(1, 34)}

        last_appear = {i: 0 for i in range(1, 34)}
        for i, draw in enumerate(reversed(self.history)):
            reds = draw.get("reds") or draw.get("red", [])
            for r in reds:
                if r not in last_appear or last_appear[r] == 0:
                    last_appear[r] = i + 1

        return last_appear

    # ==================== 约束检查 ====================
    def _check_constraints(self, reds: List[int]) -> bool:
        """严格约束检查"""
        if len(reds) != 6:
            return False

        odd = sum(1 for x in reds if x % 2 == 1)
        if odd < self.params["min_odd_count"] or odd > self.params["max_odd_count"]:
            return False

        total = sum(reds)
        if total < self.params["min_sum"] or total > self.params["max_sum"]:
            return False

        consecutive = 0
        for i in range(1, len(reds)):
            if reds[i] - reds[i-1] == 1:
                consecutive += 1
                if consecutive > self.params["max_consecutive"]:
                    return False
        return True

    # ==================== 核心生成方法 ====================
    def generate(self) -> Dict[str, Any]:
        if not self.history or len(self.history) < 5:
            logger.warning("历史数据不足，回退随机模型")
            from compute.random_model import RandomLotteryModel
            return RandomLotteryModel().generate()

        # 趋势追踪基础号码
        base_reds = self.history[-1].get("reds") or self.history[-1].get("red", [])
        if not base_reds:
            base_reds = random.sample(range(1, 34), 6)

        reds = []
        all_reds = list(range(1, 34))

        for base in base_reds:
            # 趋势偏移
            direction = random.choice([-1, 1])  # 简单趋势方向
            offset = int(direction * self.trend_strength * self.max_offset * random.uniform(0.6, 1.4))
            candidate = base + offset
            candidate = max(1, min(33, candidate))

            # 加入冷热号权重
            if candidate in self.hot_reds:
                candidate = random.choice(self.hot_reds) if random.random() < self.hot_weight else candidate
            elif candidate in self.cold_reds:
                candidate = random.choice(self.cold_reds) if random.random() < self.cold_weight else candidate

            # 加入遗漏值加权
            miss = self.miss_values.get(candidate, 0)
            if miss > 15 and random.random() < self.miss_weight * (miss / 30):
                candidate = random.choice([k for k, v in self.miss_values.items() if v > 15])

            # 避免重复
            while candidate in reds:
                candidate = random.randint(1, 33)

            reds.append(candidate)

        reds.sort()

        # 多次尝试满足约束
        attempts = 0
        while attempts < 40:
            if self._check_constraints(reds):
                break
            idx = random.randint(0, 5)
            new_num = random.randint(1, 33)
            while new_num in reds:
                new_num = random.randint(1, 33)
            reds[idx] = new_num
            reds.sort()
            attempts += 1

        blue = random.randint(1, 16)

        return {
            "reds": reds,
            "blue": blue,
            "strategy": f"趋势追踪 + 冷热遗漏模型 (趋势强度:{self.trend_strength:.2f}, 冷热权重:{self.hot_weight:.2f})",
            "extra_info": {
                "params_used": self.params,
                "history_length": len(self.history),
                "odd_count": sum(1 for x in reds if x % 2 == 1),
                "sum_reds": sum(reds),
                "attempts": attempts,
                "hot_reds_used": len([r for r in reds if r in self.hot_reds]),
                "cold_reds_used": len([r for r in reds if r in self.cold_reds])
            }
        }
