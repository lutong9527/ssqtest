# compute/hot_cold_model.py
"""
热冷号模型 - 双色球专用（标准化强化版 v3.0）
核心特点：
- 基于历史频率计算热号和冷号
- 支持动态热冷阈值（后台可调）
- 加入趋势修正（近期热号优先）
- 严格约束过滤
- 支持后台动态参数配置
"""

from typing import List, Dict, Any
import random
import logging
import numpy as np

from models.base import BaseLotteryModel
from models.registry import register_model

logger = logging.getLogger(__name__)


@register_model
class HotColdModel(BaseLotteryModel):
    """
    热冷号模型
    优先选择近期热号 + 冷号平衡组合
    """

    # ==================== 必须定义的字段 ====================
    model_code = "hot_cold"
    model_name = "热冷号模型"
    enabled_by_default = True

    # 可配置参数（后台可实时修改）
    default_params: Dict[str, Any] = {
        "recent_periods": 10,          # 统计热冷号的窗口期数
        "hot_threshold": 4,            # 出现次数 ≥ 此值视为热号
        "cold_threshold": 2,           # 出现次数 ≤ 此值视为冷号
        "hot_preference": 0.6,         # 热号偏好比例（0.5~0.8）
        "history_window": 80,          # 整体历史参考窗口
        "min_odd_count": 2,
        "max_odd_count": 4,
        "min_sum": 70,
        "max_sum": 140,
        "max_consecutive": 2
    }

    def __init__(self, history: List[Dict] = None, params: Dict = None, **kwargs):
        super().__init__(history=history, params=params, **kwargs)

        self.recent_periods = self.params["recent_periods"]
        self.hot_threshold = self.params["hot_threshold"]
        self.cold_threshold = self.params["cold_threshold"]
        self.hot_preference = self.params["hot_preference"]
        self.history_window = self.params["history_window"]

    def _analyze_frequency(self):
        """统计热号和冷号"""
        red_freq = {i: 0 for i in range(1, 34)}
        blue_freq = {i: 0 for i in range(1, 17)}

        recent = self.history[-self.recent_periods:] if self.history else []
        for draw in recent:
            reds = draw.get("reds") or draw.get("red", [])
            for r in reds:
                if 1 <= r <= 33:
                    red_freq[r] += 1
            b = draw.get("blue")
            if 1 <= b <= 16:
                blue_freq[b] += 1

        return red_freq, blue_freq

    def _check_constraints(self, reds: List[int]) -> bool:
        """约束检查"""
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

    def generate(self) -> Dict[str, Any]:
        if not self.history:
            logger.warning("历史数据为空，回退随机模型")
            from compute.random_model import RandomLotteryModel
            return RandomLotteryModel().generate()

        red_freq, blue_freq = self._analyze_frequency()

        hot_reds = [k for k, v in red_freq.items() if v >= self.hot_threshold]
        cold_reds = [k for k, v in red_freq.items() if v <= self.cold_threshold]

        selected = []

        # 优先热号
        num_hot = int(6 * self.hot_preference)
        if hot_reds:
            selected.extend(random.sample(hot_reds, min(num_hot, len(hot_reds))))

        # 补冷号
        remaining = 6 - len(selected)
        if remaining > 0 and cold_reds:
            selected.extend(random.sample(cold_reds, min(remaining, len(cold_reds))))

        # 补足
        all_reds = list(range(1, 34))
        while len(selected) < 6:
            cand = random.choice(all_reds)
            if cand not in selected:
                selected.append(cand)

        selected.sort()

        # 多次尝试满足约束
        for _ in range(30):
            if self._check_constraints(selected):
                break
            # 随机替换一个数字重试
            idx = random.randint(0, 5)
            new_num = random.choice(all_reds)
            while new_num in selected:
                new_num = random.choice(all_reds)
            selected[idx] = new_num
            selected.sort()

        # 蓝球：优先冷号
        cold_blues = [k for k, v in blue_freq.items() if v <= self.cold_threshold]
        blue = random.choice(cold_blues) if cold_blues else random.randint(1, 16)

        return {
            "reds": selected,
            "blue": blue,
            "strategy": f"热冷号模型 (热号阈值:{self.hot_threshold}, 冷号阈值:{self.cold_threshold})",
            "extra_info": {
                "params_used": self.params,
                "history_length": len(self.history),
                "odd_count": sum(1 for x in selected if x % 2 == 1),
                "sum_reds": sum(selected)
            }
        }
