# compute/bayesian_model.py
"""
贝叶斯概率模型 - 双色球专用（标准化版本）
核心思路：
- 使用 Dirichlet 先验对红球33个号码建模
- 使用 Beta-Binomial 对蓝球建模
- 基于历史数据更新后验分布
- 从后验分布中采样生成号码
- 支持后台动态参数调节
- 严格遵守项目模型开发规范
"""

from typing import List, Dict, Any
import numpy as np
import random
import logging

from models.base import BaseLotteryModel
from models.registry import register_model

logger = logging.getLogger(__name__)


@register_model
class BayesianModel(BaseLotteryModel):
    """
    贝叶斯概率模型
    支持后验采样 + 动态参数配置 + 约束过滤
    """

    # ==================== 必须定义的字段 ====================
    model_code = "bayesian_model"
    model_name = "贝叶斯概率模型"
    enabled_by_default = False                     # 默认关闭，可在后台开启

    # 可配置参数（后台可实时修改）
    default_params: Dict[str, Any] = {
        # Dirichlet 先验参数（红球）
        "prior_alpha": 1.0,                        # 先验强度（越大越平滑）
        "likelihood_weight": 1.0,                  # 历史数据权重（越大越相信历史）

        # Beta 先验参数（蓝球）
        "blue_prior_alpha": 1.0,
        "blue_prior_beta": 1.0,

        # 采样与约束参数
        "temperature": 1.0,                        # 采样温度（<1 更集中，>1 更随机）
        "min_prob_threshold": 0.001,               # 最小概率阈值，避免极端小概率
        "history_window": 100,                     # 历史参考窗口

        # 约束参数
        "min_odd_count": 2,
        "max_odd_count": 4,
        "min_sum": 70,
        "max_sum": 140,
        "max_consecutive": 2                       # 最大连号个数
    }

    # ==================== 初始化 ====================
    def __init__(self, history: List[Dict] = None, params: Dict = None, **kwargs):
        super().__init__(history=history, params=params, **kwargs)

        # 提取常用参数
        self.prior_alpha = self.params["prior_alpha"]
        self.likelihood_weight = self.params["likelihood_weight"]
        self.blue_prior_alpha = self.params["blue_prior_alpha"]
        self.blue_prior_beta = self.params["blue_prior_beta"]
        self.temperature = self.params["temperature"]
        self.min_prob_threshold = self.params["min_prob_threshold"]
        self.history_window = self.params["history_window"]

        # 构建后验分布
        self.red_posterior = self._build_red_posterior()
        self.blue_posterior = self._build_blue_posterior()

    # ==================== 后验分布构建 ====================
    def _build_red_posterior(self) -> np.ndarray:
        """构建红球 Dirichlet 后验分布"""
        # 先验：Dirichlet(α, α, ..., α)
        alpha = np.full(33, self.prior_alpha)

        # 似然：统计历史出现次数
        counts = np.zeros(33)
        recent = self.history[-self.history_window:] if self.history else []

        for draw in recent:
            reds = draw.get("reds") or draw.get("red", [])
            for r in reds:
                if 1 <= r <= 33:
                    counts[r-1] += 1

        # 后验 = 先验 + 似然 * 权重
        posterior = alpha + counts * self.likelihood_weight
        return posterior

    def _build_blue_posterior(self) -> tuple[float, float]:
        """构建蓝球 Beta 后验分布"""
        alpha = self.blue_prior_alpha
        beta = self.blue_prior_beta

        recent = self.history[-self.history_window:] if self.history else []
        count_appear = sum(1 for draw in recent if draw.get("blue") == 1)

        posterior_alpha = alpha + count_appear * self.likelihood_weight
        posterior_beta = beta + (len(recent) - count_appear) * self.likelihood_weight

        return posterior_alpha, posterior_beta

    # ==================== 约束检查 ====================
    def _check_constraints(self, reds: List[int]) -> bool:
        """严格约束检查"""
        if len(reds) != 6:
            return False

        odd_count = sum(1 for x in reds if x % 2 == 1)
        if odd_count < self.params["min_odd_count"] or odd_count > self.params["max_odd_count"]:
            return False

        zone1 = sum(1 for x in reds if x <= 11)
        zone2 = sum(1 for x in reds if 12 <= x <= 22)
        zone3 = sum(1 for x in reds if x >= 23)
        if zone1 == 0 or zone2 == 0 or zone3 == 0:
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
        从后验分布中采样生成号码
        """
        if not self.history or len(self.history) < 10:
            logger.warning("历史数据不足，回退随机模型")
            from compute.random_model import RandomLotteryModel
            return RandomLotteryModel().generate()

        # 红球采样（Dirichlet-Multinomial）
        red_probs = np.random.dirichlet(self.red_posterior)
        red_probs = np.maximum(red_probs, self.min_prob_threshold)
        red_probs = red_probs / red_probs.sum()

        # 温度采样
        if self.temperature != 1.0:
            red_probs = np.power(red_probs, 1.0 / self.temperature)
            red_probs = red_probs / red_probs.sum()

        # 选6个不重复红球 + 约束过滤
        reds = []
        for _ in range(40):  # 最多尝试40次
            selected = np.random.choice(range(1, 34), size=6, replace=False, p=red_probs)
            selected = sorted(selected.tolist())
            if self._check_constraints(selected):
                reds = selected
                break

        if not reds:
            # 约束失败时取概率最高的6个
            top_indices = np.argsort(red_probs)[-6:]
            reds = sorted([int(i) + 1 for i in top_indices])

        # 蓝球采样（Beta-Binomial）
        alpha, beta = self.blue_posterior
        blue_prob = np.random.beta(alpha, beta)
        blue = 1 if random.random() < blue_prob else random.randint(1, 16)

        return {
            "reds": reds,
            "blue": blue,
            "strategy": "贝叶斯后验采样模型",
            "extra_info": {
                "params_used": self.params,
                "history_length": len(self.history),
                "odd_count": sum(1 for x in reds if x % 2 == 1),
                "sum_reds": sum(reds),
                "posterior_strength": float(self.red_posterior.sum()),
                "blue_posterior_mean": alpha / (alpha + beta)
            }
        }
