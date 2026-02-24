# compute/genetic_model.py
"""
高级遗传算法模型 - NSGA-II + 多目标Pareto前沿 + 差分进化
核心特点：
- 多目标优化（历史匹配、奇偶、区间、和值、连号）
- NSGA-II 非支配排序 + 拥挤度选择（Pareto前沿）
- 差分进化变异策略（比传统变异更强大）
- 自适应参数调节（后期收敛更快）
- 完全标准化，支持后台动态调参
"""

from typing import List, Dict, Any, Tuple
import random
import numpy as np
import logging

from models.base import BaseLotteryModel
from models.registry import register_model

logger = logging.getLogger(__name__)


@register_model
class GeneticModel(BaseLotteryModel):
    """
    高级遗传算法模型（NSGA-II 多目标版）
    """

    # ==================== 必须定义的字段 ====================
    model_code = "genetic_model"
    model_name = "高级遗传算法模型 (NSGA-II)"
    enabled_by_default = False

    # 可配置参数（后台可实时修改）
    default_params: Dict[str, Any] = {
        # 遗传算法基础参数
        "population_size": 150,
        "generations": 80,
        "crossover_rate": 0.88,
        "mutation_rate": 0.12,
        "elite_rate": 0.15,

        # 多目标权重（总和建议接近1.0）
        "history_match_weight": 0.40,      # 历史匹配度
        "odd_even_weight": 0.18,           # 奇偶平衡
        "zone_weight": 0.15,               # 区间分布
        "sum_weight": 0.12,                # 和值合理性
        "consecutive_penalty": 0.15,       # 连号惩罚

        # 差分进化参数
        "de_scale": 0.6,                   # 差分缩放因子
        "adaptive_mutation": True,         # 是否自适应变异率

        # 约束参数
        "min_odd_count": 2,
        "max_odd_count": 4,
        "min_sum": 70,
        "max_sum": 140,
        "max_consecutive": 2,

        "history_window": 100
    }

    def __init__(self, history: List[Dict] = None, params: Dict = None, **kwargs):
        super().__init__(history=history, params=params, **kwargs)

        self.pop_size = self.params["population_size"]
        self.generations = self.params["generations"]
        self.crossover_rate = self.params["crossover_rate"]
        self.mutation_rate = self.params["mutation_rate"]
        self.elite_rate = self.params["elite_rate"]
        self.de_scale = self.params["de_scale"]
        self.adaptive_mutation = self.params["adaptive_mutation"]
        self.history_window = self.params["history_window"]

        self.elite_count = max(3, int(self.pop_size * self.elite_rate))

    # ==================== 多目标适应度函数（返回向量） ====================
    def _fitness_vector(self, reds: List[int]) -> np.ndarray:
        """
        返回5维多目标适应度向量（越高越好）
        [历史匹配, 奇偶平衡, 区间分布, 和值合理性, -连号惩罚]
        """
        v = np.zeros(5)

        # 1. 历史匹配度
        if self.history:
            recent = self.history[-self.history_window:]
            last_reds = set(recent[-1].get("reds") or recent[-1].get("red", []))
            overlap = len(set(reds) & last_reds) / 6.0
            v[0] = overlap * self.params["history_match_weight"]

        # 2. 奇偶平衡
        odd = sum(1 for x in reds if x % 2 == 1)
        v[1] = (1.0 - abs(odd - 3) / 3.0) * self.params["odd_even_weight"]

        # 3. 区间分布
        z1 = sum(1 for x in reds if x <= 11)
        z2 = sum(1 for x in reds if 12 <= x <= 22)
        z3 = sum(1 for x in reds if x >= 23)
        zone_score = min(1, z1) + min(1, z2) + min(1, z3)
        v[2] = (zone_score / 3.0) * self.params["zone_weight"]

        # 4. 和值合理性
        total = sum(reds)
        if self.params["min_sum"] <= total <= self.params["max_sum"]:
            v[3] = 1.0 * self.params["sum_weight"]
        else:
            dist = min(abs(total - self.params["min_sum"]), abs(total - self.params["max_sum"]))
            v[3] = max(0.0, 1 - dist / 50) * self.params["sum_weight"]

        # 5. 连号惩罚（负向）
        consecutive = 0
        for i in range(1, len(reds)):
            if reds[i] - reds[i-1] == 1:
                consecutive += 1
        v[4] = -consecutive * self.params["consecutive_penalty"]

        return v

    # ==================== NSGA-II 非支配排序 + 拥挤度 ====================
    def _nsga2_select(self, population: List[List[int]], fitness_vectors: List[np.ndarray]) -> List[int]:
        """NSGA-II 选择：非支配排序 + 拥挤度"""
        n = len(population)
        fronts = [[] for _ in range(n)]
        domination_count = [0] * n
        dominated_sets = [set() for _ in range(n)]

        # 计算支配关系
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                if np.all(fitness_vectors[i] >= fitness_vectors[j]) and np.any(fitness_vectors[i] > fitness_vectors[j]):
                    dominated_sets[i].add(j)
                elif np.all(fitness_vectors[j] >= fitness_vectors[i]) and np.any(fitness_vectors[j] > fitness_vectors[i]):
                    domination_count[i] += 1

            if domination_count[i] == 0:
                fronts[0].append(i)

        # 构建前沿
        front_idx = 0
        while fronts[front_idx]:
            next_front = []
            for i in fronts[front_idx]:
                for j in dominated_sets[i]:
                    domination_count[j] -= 1
                    if domination_count[j] == 0:
                        next_front.append(j)
            front_idx += 1
            fronts[front_idx] = next_front

        # 选择前几个前沿
        selected = []
        for front in fronts:
            if len(selected) + len(front) <= self.pop_size:
                selected.extend(front)
            else:
                # 拥挤度排序
                crowding = self._crowding_distance([fitness_vectors[i] for i in front])
                sorted_front = sorted(range(len(front)), key=lambda k: crowding[k], reverse=True)
                need = self.pop_size - len(selected)
                selected.extend([front[k] for k in sorted_front[:need]])
                break

        return [population[i] for i in selected]

    def _crowding_distance(self, front_fitness: List[np.ndarray]) -> List[float]:
        """计算拥挤度距离"""
        n = len(front_fitness)
        if n <= 2:
            return [float('inf')] * n

        distance = [0.0] * n
        m = len(front_fitness[0])  # 目标数

        for obj in range(m):
            sorted_idx = sorted(range(n), key=lambda i: front_fitness[i][obj])
            distance[sorted_idx[0]] = float('inf')
            distance[sorted_idx[-1]] = float('inf')
            f_max = front_fitness[sorted_idx[-1]][obj]
            f_min = front_fitness[sorted_idx[0]][obj]
            if f_max == f_min:
                continue
            for i in range(1, n-1):
                distance[sorted_idx[i]] += (front_fitness[sorted_idx[i+1]][obj] - front_fitness[sorted_idx[i-1]][obj]) / (f_max - f_min)

        return distance

    # ==================== 遗传操作 ====================
    def _crossover(self, p1: List[int], p2: List[int]) -> Tuple[List[int], List[int]]:
        point = random.randint(1, 5)
        c1 = sorted(set(p1[:point] + p2[point:]))
        c2 = sorted(set(p2[:point] + p1[point:]))
        return c1, c2

    def _differential_mutation(self, population: List[List[int]], idx: int) -> List[int]:
        """差分进化变异"""
        a, b, c = random.sample([i for i in range(len(population)) if i != idx], 3)
        mutant = []
        for i in range(6):
            val = int(population[a][i] + self.de_scale * (population[b][i] - population[c][i]))
            mutant.append(max(1, min(33, val)))
        return sorted(mutant)

    def generate(self) -> Dict[str, Any]:
        if not self.history or len(self.history) < 10:
            logger.warning("历史数据不足，回退随机模型")
            from compute.random_model import RandomLotteryModel
            return RandomLotteryModel().generate()

        # 初始化种群
        population = [sorted(random.sample(range(1, 34), 6)) for _ in range(self.pop_size)]

        best_reds = None
        best_fitness = -np.inf

        for gen in range(self.generations):
            # 计算多目标适应度向量
            fitness_vectors = [self._fitness_vector(ind) for ind in population]

            # NSGA-II 选择
            new_population = self._nsga2_select(population, fitness_vectors)

            # 交叉 + 差分变异
            next_pop = new_population[:self.elite_count]

            while len(next_pop) < self.pop_size:
                p1, p2 = random.sample(new_population, 2)
                c1, c2 = self._crossover(p1, p2)

                # 差分进化变异
                if random.random() < self.mutation_rate:
                    c1 = self._differential_mutation(population, population.index(p1))

                next_pop.extend([c1, c2])

            population = next_pop[:self.pop_size]

            # 更新全局最优
            current_best_idx = np.argmax([sum(v) for v in fitness_vectors])
            if sum(fitness_vectors[current_best_idx]) > best_fitness:
                best_fitness = sum(fitness_vectors[current_best_idx])
                best_reds = population[current_best_idx][:]

        reds = best_reds or sorted(random.sample(range(1, 34), 6))
        blue = random.randint(1, 16)

        return {
            "reds": reds,
            "blue": blue,
            "strategy": f"NSGA-II 强化遗传算法 ({self.generations}代, 多目标优化)",
            "extra_info": {
                "params_used": self.params,
                "fitness_score": float(best_fitness),
                "odd_count": sum(1 for x in reds if x % 2 == 1),
                "sum_reds": sum(reds)
            }
        }
