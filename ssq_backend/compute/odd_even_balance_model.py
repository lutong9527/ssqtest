# compute/odd_even_balance_model.py
"""
奇偶平衡模型 - 双色球专用（标准化强化版 v3.0）
核心特点：
- 动态目标奇偶比例（后台可调，推荐 3:3）
- 参考历史奇偶分布趋势，避免极端分布
- 支持蓝球奇偶偏好
- 严格约束过滤（和值、连号、区间）
- 完全符合项目模型开发规范
"""

from typing import List, Dict, Any
import random
import logging
import numpy as np

from models.base import BaseLotteryModel
from models.registry import register_model

logger = logging.getLogger(__name__)


@register_model
class OddEvenBalanceModel(BaseLotteryModel):
    """
    奇偶平衡模型
    优先保证奇偶比例合理，同时参考历史趋势
    """

    # ==================== 必须定义的字段 ====================
    model_code = "odd_even_balance"
    model_name = "奇偶平衡模型"
    enabled_by_default = True  # 默认启用（适合大多数用户）

    # 可配置参数（后台可实时修改）
    default_params: Dict[str, Any] = {
        # 奇偶核心参数
        "target_odd_count": 3,                     # 目标奇数个数（2~4）
        "odd_tolerance": 1,                        # 允许偏差（±1）

        # 历史趋势参数
        "use_history_trend": True,                 # 是否参考历史奇偶分布
        "history_window": 50,                      # 历史参考窗口

        # 蓝球偏好
        "prefer_odd_blue": False,                  # 是否偏好奇数蓝球

        # 约束参数
        "min_sum": 70,
        "max_sum": 140,
        "max_consecutive": 2
    }

    # ==================== 初始化 ====================
    def __init__(self, history: List[Dict] = None, params: Dict = None, **kwargs):
        super().__init__(history=history, params=params, **kwargs)

        # 参数提取
        self.target_odd = self.params["target_odd_count"]
        self.odd_tolerance = self.params["odd_tolerance"]
        self.use_history_trend = self.params["use_history_trend"]
        self.history_window = self.params["history_window"]
        self.prefer_odd_blue = self.params["prefer_odd_blue"]

    # ==================== 历史奇偶趋势分析 ====================
    def _get_historical_odd_preference(self) -> float:
        """计算历史中奇数比例的平均偏好（0~1，>0.5 偏奇）"""
        if not self.history or not self.use_history_trend:
            return 0.5  # 中性

        recent = self.history[-self.history_window:]
        odd_ratios = []
        for draw in recent:
            reds = draw.get("reds") or draw.get("red", [])
            if len(reds) == 6:
                odd_count = sum(1 for x in reds if x % 2 == 1)
                odd_ratios.append(odd_count / 6.0)

        return np.mean(odd_ratios) if odd_ratios else 0.5

    # ==================== 约束检查 ====================
    def _check_constraints(self, reds: List[int]) -> bool:
        """严格约束检查"""
        if len(reds) != 6:
            return False

        odd_count = sum(1 for x in reds if x % 2 == 1)
        if abs(odd_count - self.target_odd) > self.odd_tolerance:
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
        """
        生成奇偶平衡的号码组合
        优先参考历史趋势，强制奇偶合理
        """
        if not self.history:
            logger.warning("历史数据为空，回退随机生成")
            from compute.random_model import RandomLotteryModel
            return RandomLotteryModel().generate()

        all_reds = list(range(1, 34))
        odds = [x for x in all_reds if x % 2 == 1]    # 17个奇数
        evens = [x for x in all_reds if x % 2 == 0]   # 16个偶数

        # 历史趋势偏好
        trend_odd_ratio = self._get_historical_odd_preference()
        adjusted_odd = round(self.target_odd + (trend_odd_ratio - 0.5) * 2)

        # 限制在合理范围内
        adjusted_odd = max(self.params["min_odd_count"], min(self.params["max_odd_count"], adjusted_odd))

        # 选奇数
        num_odd = adjusted_odd
        selected_odds = random.sample(odds, min(num_odd, len(odds)))

        # 补偶数
        num_even = 6 - len(selected_odds)
        selected_evens = random.sample(evens, min(num_even, len(evens)))

        reds = selected_odds + selected_evens
        reds.sort()

        # 多次尝试满足约束
        for _ in range(20):
            if self._check_constraints(reds):
                break
            # 随机替换一个数字重试
            idx = random.randint(0, 5)
            new_num = random.choice(all_reds)
            while new_num in reds:
                new_num = random.choice(all_reds)
            reds[idx] = new_num
            reds.sort()

        # 蓝球：根据偏好选择
        if self.prefer_odd_blue:
            odd_blues = [b for b in range(1, 17) if b % 2 == 1]
            blue = random.choice(odd_blues) if odd_blues else random.randint(1, 16)
        else:
            blue = random.randint(1, 16)

        return {
            "reds": reds,
            "blue": blue,
            "strategy": f"奇偶平衡模型 (目标奇数:{adjusted_odd}, 历史趋势:{trend_odd_ratio:.2f})",
            "extra_info": {
                "params_used": self.params,
                "history_length": len(self.history),
                "odd_count": sum(1 for x in reds if x % 2 == 1),
                "sum_reds": sum(reds),
                "trend_odd_ratio": trend_odd_ratio
            }
        }
