# compute/random_model.py
"""
随机模型 - 双色球专用（标准化强化版 v3.0）
核心特点：
- 纯随机生成作为基准模型
- 支持后台动态参数调节（奇偶偏好、和值范围等）
- 加入约束检查（奇偶、区间、和值、连号）
- 严格遵守项目模型开发规范
- 作为其他模型数据不足时的回退模型
"""

from typing import List, Dict, Any
import random
import logging

from models.base import BaseLotteryModel
from models.registry import register_model

logger = logging.getLogger(__name__)


@register_model
class RandomLotteryModel(BaseLotteryModel):
    """
    随机模型（基准模型）
    提供纯随机生成，同时支持轻度约束与偏好
    """

    # ==================== 必须定义的字段 ====================
    model_code = "random"
    model_name = "随机基准模型"
    enabled_by_default = True  # 默认启用，作为保底

    # 可配置参数（后台可实时修改）
    default_params: Dict[str, Any] = {
        # 随机生成偏好（可选）
        "prefer_odd_red": False,          # 是否偏好奇数红球
        "prefer_odd_blue": False,         # 是否偏好奇数蓝球

        # 约束参数（随机时也会尽量满足）
        "min_odd_count": 2,
        "max_odd_count": 4,
        "min_sum": 70,
        "max_sum": 140,
        "max_consecutive": 2,

        # 其他
        "max_attempts": 50                # 满足约束的最大尝试次数
    }

    # ==================== 初始化 ====================
    def __init__(self, history: List[Dict] = None, params: Dict = None, **kwargs):
        super().__init__(history=history, params=params, **kwargs)

        self.prefer_odd_red = self.params["prefer_odd_red"]
        self.prefer_odd_blue = self.params["prefer_odd_blue"]
        self.max_attempts = self.params["max_attempts"]

    # ==================== 约束检查 ====================
    def _check_constraints(self, reds: List[int]) -> bool:
        """检查生成的红球是否满足约束"""
        if len(reds) != 6:
            return False

        odd_count = sum(1 for x in reds if x % 2 == 1)
        if odd_count < self.params["min_odd_count"] or odd_count > self.params["max_odd_count"]:
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
        生成随机双色球号码，尽量满足约束
        """
        all_reds = list(range(1, 34))
        odds = [x for x in all_reds if x % 2 == 1]
        evens = [x for x in all_reds if x % 2 == 0]

        reds = None

        # 尝试多次生成符合约束的组合
        for attempt in range(self.max_attempts):
            if self.prefer_odd_red:
                # 偏好奇数
                num_odd = random.randint(3, 4)
                selected_odd = random.sample(odds, num_odd)
                selected_even = random.sample(evens, 6 - num_odd)
                reds = selected_odd + selected_even
            else:
                # 纯随机
                reds = random.sample(all_reds, 6)

            reds.sort()

            if self._check_constraints(reds):
                break

        # 如果多次尝试仍未满足约束，直接取随机结果（不强制约束）
        if reds is None:
            reds = random.sample(all_reds, 6)
            reds.sort()
            logger.warning("多次尝试未满足约束，使用无约束随机结果")

        # 蓝球
        if self.prefer_odd_blue:
            odd_blues = [b for b in range(1, 17) if b % 2 == 1]
            blue = random.choice(odd_blues) if odd_blues else random.randint(1, 16)
        else:
            blue = random.randint(1, 16)

        return {
            "reds": reds,
            "blue": blue,
            "strategy": "随机基准模型" + (" (偏好奇数)" if self.prefer_odd_red else ""),
            "extra_info": {
                "params_used": self.params,
                "attempts": attempt + 1 if reds else "无约束生成",
                "odd_count": sum(1 for x in reds if x % 2 == 1),
                "sum_reds": sum(reds)
            }
        }
