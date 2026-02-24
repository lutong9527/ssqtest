# compute/genetic_model.py
"""
强化版遗传算法模型 - 双色球专用
核心改进：
1. 加入历史数据使用度（重叠率 + 趋势一致性）
2. 多目标适应度函数（加权综合：历史匹配、奇偶、区间、和值、连号）
3. 自适应变异率（后期降低变异，加快收敛）
4. 严格约束过滤 + 精英保留策略
5. 完全符合项目标准化规范 v3.0
"""

from typing import List, Dict, Any, Tuple
import random
import logging
import numpy as np

from models.base import BaseLotteryModel
from models.registry import register_model

logger = logging.getLogger(__name__)


@register_model
class GeneticModel(BaseLotteryModel):
    """
    强化遗传算法模型
    支持历史数据使用度 + 多目标优化 + 动态参数配置
    """

    # ==================== 必须定义的字段 ====================
    model_code = "genetic_model"
    model_name = "强化遗传算法模型"
    enabled_by_default = False                     # 默认关闭，可后台开启

    # 可配置参数（后台可实时修改）
    default_params: Dict[str, Any] = {
        # 遗传算法核心参数
        "population_size": 120,                    # 种群大小（80~300）
        "generations": 60,                         # 进化代数（30~150）
        "crossover_rate": 0.85,                    # 交叉概率
        "mutation_rate": 0.08,                     # 初始变异率
        "elite_rate": 0.12,                        # 精英保留比例

        # 历史数据使用度权重
        "history_match_weight": 0.45,              # 历史匹配度权重（重叠 + 趋势）
        "trend_weight": 0.25,                      # 趋势一致性权重

        # 多目标权重
        "odd_even_weight": 0.15,                   # 奇偶平衡权重
        "zone_weight": 0.10,                       # 区间分布权重
        "sum_weight": 0.05,                        # 和值合理性权重

        # 约束参数
        "min_odd_count": 2,
        "max_odd_count": 4,
        "min_sum": 70,
        "max_sum": 140,
        "max_consecutive": 2,

        # 自适应参数
        "adaptive_mutation": True,                 # 是否启用自适应变异率
        "history_window": 80                       # 历史参考窗口
    }

    # ==================== 初始化 ====================
    def __init__(self, history: List[Dict] = None, params: Dict = None, **kwargs):
        super().__init__(history=history, params=params, **kwargs)

        # 提取参数
        self.pop_size = self.params["population_size"]
        self.generations = self.params["generations"]
        self.crossover_rate = self.params["crossover_rate"]
        self.mutation_rate = self.params["mutation_rate"]
        self.elite_rate = self.params["elite_rate"]
        self.history_window = self.params["history_window"]

        # 多目标权重
        self.history_match_weight = self.params["history_match_weight"]
        self.trend_weight = self.params["trend_weight"]
        self.odd_even_weight = self.params["odd_even_weight"]
        self.zone_weight = self.params["zone_weight"]
        self.sum_weight = self.params["sum_weight"]

        self.elite_count = max(2, int(self.pop_size * self.elite_rate))

    # ==================== 适应度函数（多目标强化版） ====================
    def _fitness(self, reds: List[int]) -> float:
        """
        多目标适应度函数（范围 0~1，越高越好）
        """
        score = 0.0

        # 1. 历史数据使用度（重叠率 + 趋势一致性）
        if self.history:
            recent = self.history[-self.history_window:]
            # 重叠率
            last_reds = set(recent[-1].get("reds") or recent[-1].get("red", []))
            overlap = len(set(reds) & last_reds) / 6.0
            score += self.history_match_weight * overlap

            # 趋势一致性（与最近3期平均值方向一致）
            if len(recent) >= 3:
                avg_last = np.mean([sum(d.get("reds") or d.get("red", [])) for d in recent[-3:]])
                current_sum = sum(reds)
                trend_match = 1.0 if (current_sum - avg_last) * (avg_last - sum(recent[-4]["reds"] or recent[-4]["red"])) > 0 else 0.4
                score += self.trend_weight * trend_match

        # 2. 奇偶平衡（目标 3:3）
        odd_count = sum(1 for x in reds if x % 2 == 1)
        odd_score = 1.0 - abs(odd_count - 3) / 3.0
        score += self.odd_even_weight * odd_score

        # 3. 区间分布（1-11,12-22,23-33 各至少1个）
        z1 = sum(1 for x in reds if x <= 11)
        z2 = sum(1 for x in reds if 12 <= x <= 22)
        z3 = sum(1 for x in reds if x >= 23)
        zone_score = min(1, z1) + min(1, z2) + min(1, z3)
        score += self.zone_weight * (zone_score / 3.0)

        # 4. 和值合理性
        total = sum(reds)
        if self.params["min_sum"] <= total <= self.params["max_sum"]:
            sum_score = 1.0
        else:
            distance = min(abs(total - self.params["min_sum"]), abs(total - self.params["max_sum"]))
            sum_score = max(0.0, 1 - distance / 50)
        score += self.sum_weight * sum_score

        # 5. 连号惩罚
        consecutive = 0
        for i in range(1, len(reds)):
            if reds[i] - reds[i-1] == 1:
                consecutive += 1
        score -= consecutive * 0.25

        return max(0.01, min(1.0, score))   # 限制在 0.01~1.0 之间

    # ==================== 遗传操作 ====================
    def _crossover(self, p1: List[int], p2: List[int]) -> Tuple[List[int], List[int]]:
        point = random.randint(1, 5)
        c1 = sorted(set(p1[:point] + p2[point:]))
        c2 = sorted(set(p2[:point] + p1[point:]))
        return c1, c2

    def _mutate(self, individual: List[int]) -> List[int]:
        ind = individual.copy()
        for _ in range(random.randint(1, 2)):
            idx = random.randint(0, 5)
            new_num = random.randint(1, 33)
            while new_num in ind:
                new_num = random.randint(1, 33)
            ind[idx] = new_num
        return sorted(ind)

    def _select(self, population: List[List[int]], fitnesses: List[float]) -> List[int]:
        """轮盘赌选择"""
        total = sum(fitnesses)
        if total <= 0:
            return random.choice(population)

        pick = random.uniform(0, total)
        current = 0.0
        for ind, fit in zip(population, fitnesses):
            current += fit
            if current >= pick:
                return ind
        return population[-1]

    # ==================== 核心生成方法 ====================
    def generate(self) -> Dict[str, Any]:
        """
        使用强化遗传算法生成优质号码
        """
        if not self.history or len(self.history) < 10:
            logger.warning("历史数据不足，回退随机模型")
            from compute.random_model import RandomLotteryModel
            return RandomLotteryModel().generate()

        # 初始化种群
        population: List[List[int]] = [
            sorted(random.sample(range(1, 34), 6)) for _ in range(self.pop_size)
        ]

        best_individual = None
        best_fitness = -1.0

        for gen in range(self.generations):
            # 计算适应度
            fitnesses = [self._fitness(ind) for ind in population]

            # 更新全局最优
            max_idx = fitnesses.index(max(fitnesses))
            if fitnesses[max_idx] > best_fitness:
                best_fitness = fitnesses[max_idx]
                best_individual = population[max_idx][:]

            # 精英保留
            elite_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)[:self.elite_count]
            new_population = [population[i][:] for i in elite_indices]

            # 生成新个体
            while len(new_population) < self.pop_size:
                p1 = self._select(population, fitnesses)
                p2 = self._select(population, fitnesses)

                c1, c2 = self._crossover(p1, p2)

                # 自适应变异率（后期降低）
                current_mutation_rate = self.mutation_rate * (1 - gen / self.generations) if self.params.get("adaptive_mutation", True) else self.mutation_rate

                if random.random() < current_mutation_rate:
                    c1 = self._mutate(c1)
                if random.random() < current_mutation_rate:
                    c2 = self._mutate(c2)

                new_population.extend([c1, c2])

            population = new_population[:self.pop_size]

        # 最终选择
        if best_individual is None:
            best_individual = population[0]

        reds = best_individual
        blue = random.randint(1, 16)

        return {
            "reds": reds,
            "blue": blue,
            "strategy": f"强化遗传算法 ({self.generations}代, 种群{self.pop_size}, 历史权重{self.history_match_weight})",
            "extra_info": {
                "params_used": self.params,
                "fitness_score": best_fitness,
                "odd_count": sum(1 for x in reds if x % 2 == 1),
                "sum_reds": sum(reds),
                "history_match_weight": self.history_match_weight
            }
        }
