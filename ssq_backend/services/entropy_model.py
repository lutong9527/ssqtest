import random
import math
from collections import Counter
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session

# 模型与配置 ORM
from models.lottery_history import LotteryHistory
from models.model_config import ModelConfig


class EntropyBalancedModel:
    """
    熵平衡 + 可选蒙特卡洛扩展的双色球号码生成模型。
    主要目标：在合法选号约束下，让组合的"概率熵"接近目标区间。
    
    核心思想：
    1. 基于历史开奖数据计算每个红球的出现概率
    2. 使用蒙特卡洛方法随机生成候选号码组合
    3. 通过信息熵平衡确保组合的概率分布接近历史平均水平
    4. 结合多种统计学约束条件（区间、奇偶、和值等）
    
    特点：
    - 避免过于热门的号码组合
    - 避免过于冷门的号码组合
    - 生成的组合在统计特征上符合历史规律
    - 支持两种生成模式：熵平衡和蒙特卡洛
    """

    # ------------------------------------------------------------------
    # 构造与配置
    # ------------------------------------------------------------------
    def __init__(
        self,
        db: Session,
        mode: str = "entropy",           # "entropy" 或 "monte_carlo"
        history_window: Optional[int] = None,
        entropy_tolerance: Optional[float] = None,
        monte_carlo_samples: Optional[int] = None,
    ):
        """
        初始化模型
        
        参数：
            db: 数据库会话对象
            mode: 生成模式，"entropy" 或 "monte_carlo"
            history_window: 历史数据窗口大小（默认从配置读取）
            entropy_tolerance: 熵容差，控制生成的组合熵与目标熵的偏差
            monte_carlo_samples: 蒙特卡洛采样次数
        
        流程：
            1. 从数据库加载或创建模型配置
            2. 设置历史数据窗口大小（30-200期）
            3. 计算红球概率分布
            4. 计算目标信息熵
        """
        self.db = db

        # 读取或创建配置
        self.config = db.query(ModelConfig).first()
        if not self.config:
            self.config = ModelConfig()
            db.add(self.config)
            db.commit()
            db.refresh(self.config)

        # -------------------------
        # 历史窗口
        # -------------------------
        if history_window is not None:
            # 限定范围在30-200期之间
            history_window = max(30, min(history_window, 200))
            self.history_window = history_window
        else:
            # 取数据库配置，如果没有则默认100
            self.history_window = self.config.history_window or 100

        # -------------------------
        # 熵容忍度
        # -------------------------
        if entropy_tolerance is not None:
            self.entropy_tolerance = entropy_tolerance
        else:
            self.entropy_tolerance = self.config.entropy_tolerance or 0.05

        # -------------------------
        # 蒙特卡洛样本数
        # -------------------------
        if monte_carlo_samples is not None:
            self.samples = monte_carlo_samples
        else:
            self.samples = self.config.monte_carlo_samples or 5000

        # -------------------------
        # 模型运行模式
        # -------------------------
        if mode not in ("entropy", "monte_carlo"):
            raise ValueError("mode 必须是 'entropy' 或 'monte_carlo'")
        self.mode = mode

        # -------------------------
        # 计算历史概率与目标熵
        # -------------------------
        self.red_probs = self._calculate_red_probabilities()
        self.target_entropy = self._calculate_entropy(list(self.red_probs.values()))

    # ------------------------------------------------------------------
    # 历史数据与概率
    # ------------------------------------------------------------------
    def _calculate_red_probabilities(self) -> dict:
        """
        计算过去 self.history_window 期的红球概率分布，
        使用 Laplace 平滑。
        
        算法：
            1. 查询最近N期历史数据
            2. 统计每个红球出现的次数
            3. 使用Laplace平滑：P(i) = (count_i + α) / (total_balls + 33α)
               α=1为平滑参数
        
        返回：
            字典：{红球号码: 出现概率}
        """
        history = (
            self.db.query(LotteryHistory)
            .order_by(LotteryHistory.issue.desc())
            .limit(self.history_window)
            .all()
        )

        counter = Counter()  # 使用Counter统计出现次数

        # 统计每个红球的出现次数
        for h in history:
            # 从数据库中获取6个红球
            reds = [h.red1, h.red2, h.red3, h.red4, h.red5, h.red6]
            counter.update(reds)

        total_draws = len(history)  # 总期数
        alpha = 1  # Laplace平滑参数

        probs = {}  # 存储概率结果

        # 计算1-33每个红球的概率
        for i in range(1, 34):
            count = counter[i]  # 红球i的出现次数
            
            # Laplace平滑公式：P(i) = (count_i + α) / (total_balls + 33α)
            # total_balls = total_draws * 6（每期6个红球）
            probs[i] = (count + alpha) / (total_draws * 6 + 33 * alpha)

        return probs

    # ------------------------------------------------------------------
    # 熵与约束检查
    # ------------------------------------------------------------------
    @staticmethod
    def _calculate_entropy(probabilities: List[float]) -> float:
        """
        计算信息熵
        
        公式：H(X) = -∑ p(x) * log(p(x))
        
        参数：
            probabilities: 概率列表
        
        返回：
            熵值（浮点数）
        """
        entropy = 0.0
        for p in probabilities:
            if p > 0:  # 避免对0取对数
                entropy -= p * math.log(p)

        return entropy

    # 区间控制：1-11 / 12-22 / 23-33，每区间 1~3 个红球
    @staticmethod
    def _check_zone_balance(reds: List[int]) -> bool:
        """
        检查区间分布是否平衡
        
        红球33个号码分为3个区间：
            1-11：第一区间
            12-22：第二区间
            23-33：第三区间
        
        约束条件：每个区间必须有1-3个号码
        
        参数：
            reds: 红球列表（6个号码）
        
        返回：
            bool: 是否满足区间平衡条件
        """
        zone1 = len([r for r in reds if 1 <= r <= 11])
        zone2 = len([r for r in reds if 12 <= r <= 22])
        zone3 = len([r for r in reds if 23 <= r <= 33])

        # 检查每个区间是否有1-3个号码
        return (
            1 <= zone1 <= 3 and
            1 <= zone2 <= 3 and
            1 <= zone3 <= 3
        )

    # 奇偶控制
    @staticmethod
    def _check_odd_even(reds: List[int]) -> bool:
        """
        检查奇偶比例
        
        历史统计显示，红球奇偶比例通常为：
            2奇4偶：约30%
            3奇3偶：约40%
            4奇2偶：约30%
        
        参数：
            reds: 红球列表
        
        返回：
            bool: 是否满足奇偶比例
        """
        # 统计奇数号码数量
        odd = len([r for r in reds if r % 2 == 1])
        even = 6 - odd  # 偶数号码数量

        # 检查是否为常见的奇偶比例
        return (odd, even) in [(2, 4), (3, 3), (4, 2)]

    # 和值控制
    @staticmethod
    def _check_sum_range(reds: List[int]) -> bool:
        """
        检查和值范围
        
        双色球红球和值（6个红球的和）历史范围：
            最小值：约21（1+2+3+4+5+6）
            最大值：约183（28+29+30+31+32+33）
            常见范围：80-140
        
        参数：
            reds: 红球列表
        
        返回：
            bool: 和值是否在合理范围内
        """
        total = sum(reds)
        return 80 <= total <= 140

    # 组合熵
    def _combo_entropy(self, reds: List[int]) -> float:
        """
        计算组合的信息熵
        
        参数：
            reds: 红球组合（6个号码）
        
        返回：
            该组合的熵值
        """
        # 获取组合中每个号码的概率
        probs = [self.red_probs[r] for r in reds]
        
        # 计算该组合的熵
        return self._calculate_entropy(probs)

    # ------------------------------------------------------------------
    # 生成策略：熵平衡
    # ------------------------------------------------------------------
    def generate_entropy(self) -> Optional[dict]:
        """
        基于熵平衡的生成策略。
        遍历 self.samples 次（采样），从满足约束的组合中选择与目标熵最接近的一组。
        
        流程：
            1. 使用蒙特卡洛方法随机生成候选组合
            2. 对每个候选组合应用约束条件筛选
            3. 计算筛选后组合的熵值
            4. 选择最接近目标熵的组合
        
        返回：
            字典包含：
                mode: 生成模式
                reds: 红球号码列表
                blue: 蓝球号码
                history_window: 使用的历史窗口大小
                target_entropy: 目标熵值
                combo_entropy: 组合熵值
                entropy_diff: 与目标熵的差值
                samples_used: 使用的样本数
        """
        best_combo: Optional[Tuple[List[int], int]] = None
        best_diff = float("inf")
        samples_used = 0  # 记录实际使用的样本数

        for i in range(self.samples):
            # 随机生成6个不同的红球（1-33），并排序
            reds = sorted(random.sample(range(1, 34), 6))
            
            # 随机生成蓝球（1-16）
            blue = random.randint(1, 16)

            # 应用约束条件筛选
            if not self._check_zone_balance(reds):
                continue

            if not self._check_odd_even(reds):
                continue

            if not self._check_sum_range(reds):
                continue

            # 计算当前组合的熵值
            combo_entropy = self._combo_entropy(reds)
            
            # 计算与目标熵的绝对差值
            diff = abs(combo_entropy - self.target_entropy)

            # 更新最佳组合
            if diff < best_diff:
                best_diff = diff
                best_combo = (reds, blue)

            # 记录使用的样本数
            samples_used = i + 1

            # 早停：如果差值已经非常小，可选
            if best_diff <= self.entropy_tolerance:
                break

        if not best_combo:
            return None

        reds, blue = best_combo
        return {
            "mode": "entropy",
            "reds": reds,
            "blue": blue,
            "history_window": self.history_window,
            "target_entropy": self.target_entropy,
            "combo_entropy": self._combo_entropy(reds),
            "entropy_diff": best_diff,
            "samples_used": samples_used
        }

    # ------------------------------------------------------------------
    # 生成策略：蒙特卡洛受约束
    # ------------------------------------------------------------------
    def generate_monte_carlo(self, top_k: int = 1) -> List[dict]:
        """
        蒙特卡洛生成策略：
          1) 采样 self.samples 次随机组合
          2) 过滤合法约束
          3) 根据熵与 target_entropy 的距离排序
          4) 返回 top_k 组最优结果
        
        参数：
            top_k: 返回的最佳组合数量
        
        返回：
            字典列表，每个字典包含一组号码信息
        """
        candidates = []

        for _ in range(self.samples):
            # 随机生成组合
            reds = sorted(random.sample(range(1, 34), 6))
            blue = random.randint(1, 16)

            # 约束检查
            if not self._check_zone_balance(reds):
                continue
            if not self._check_odd_even(reds):
                continue
            if not self._check_sum_range(reds):
                continue

            # 计算熵差值
            combo_entropy = self._combo_entropy(reds)
            diff = abs(combo_entropy - self.target_entropy)

            # 保存候选组合
            candidates.append((diff, reds, blue))

        # 按熵差值排序（从小到大）
        candidates.sort(key=lambda x: x[0])

        # 只保留 top_k 个最佳组合
        top = candidates[:max(1, top_k)]
        
        # 构建返回结果
        results = []
        for diff, reds, blue in top:
            results.append({
                "mode": "monte_carlo",
                "reds": reds,
                "blue": blue,
                "history_window": self.history_window,
                "target_entropy": self.target_entropy,
                "combo_entropy": self._combo_entropy(reds),
                "entropy_diff": diff,
            })
        return results

    # ------------------------------------------------------------------
    # 统一生成接口
    # ------------------------------------------------------------------
    def generate(self, **kwargs) -> Optional[dict]:
        """
        根据 mode 生成组合：
          - mode="entropy": 返回单个结果 dict
          - mode="monte_carlo": 返回 top 1 结果 dict（外层包装）
        
        可以通过 kwargs 调整 top_k（仅对 monte_carlo 生效）
        
        参数：
            top_k: 仅对 monte_carlo 模式有效，指定返回的最佳组合数量
        
        返回：
            字典包含号码信息和相关数据
        """
        if self.mode == "entropy":
            return self.generate_entropy()
        elif self.mode == "monte_carlo":
            top_k = kwargs.get("top_k", 1)
            results = self.generate_monte_carlo(top_k=top_k)
            # 若只想返回一组
            return results[0] if results else None
        else:
            return None

    # ------------------------------------------------------------------
    # 更新配置接口（可选）
    # ------------------------------------------------------------------
    def update_config(
        self,
        history_window: Optional[int] = None,
        entropy_tolerance: Optional[float] = None,
        monte_carlo_samples: Optional[int] = None,
    ):
        """
        同步更新数据库配置并刷新模型当前设置。
        
        参数：
            history_window: 历史数据窗口大小
            entropy_tolerance: 熵容忍度
            monte_carlo_samples: 蒙特卡洛采样次数
        """
        changed = False
        
        # 更新历史窗口
        if history_window is not None:
            # 限定范围在30-200期之间
            history_window = max(30, min(history_window, 200))
            self.history_window = history_window
            self.config.history_window = history_window
            changed = True

        # 更新熵容忍度
        if entropy_tolerance is not None:
            self.entropy_tolerance = entropy_tolerance
            self.config.entropy_tolerance = entropy_tolerance
            changed = True

        # 更新蒙特卡洛样本数
        if monte_carlo_samples is not None:
            self.samples = monte_carlo_samples
            self.config.monte_carlo_samples = monte_carlo_samples
            changed = True

        # 如果有配置改变，保存到数据库
        if changed:
            self.db.commit()

        # 如果配置改变，需重新计算概率与目标熵
        if changed:
            self.red_probs = self._calculate_red_probabilities()
            self.target_entropy = self._calculate_entropy(list(self.red_probs.values()))
            
        return changed

    # ------------------------------------------------------------------
    # 简化接口（兼容旧代码）
    # ------------------------------------------------------------------
    def generate_simple(self):
        """
        简化生成接口，兼容原始代码的调用方式。
        使用默认的 entropy 模式。
        
        返回：
            字典包含：
                reds: 红球号码列表
                blue: 蓝球号码
                history_window: 使用的历史窗口大小
                entropy_diff: 与目标熵的差值
        """
        result = self.generate_entropy()
        if result:
            return {
                "reds": result["reds"],
                "blue": result["blue"],
                "history_window": result["history_window"],
                "entropy_diff": result["entropy_diff"]
            }
        return None


# 使用示例
if __name__ == "__main__":
    # 示例用法
    from database import SessionLocal
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 初始化模型 - 熵平衡模式
        model = EntropyBalancedModel(
            db=db,
            mode="entropy",
            history_window=100,
            entropy_tolerance=0.05,
            monte_carlo_samples=5000
        )
        
        # 生成号码
        result = model.generate()
        if result:
            print("生成结果:")
            print(f"模式: {result.get('mode', 'N/A')}")
            print(f"红球: {result['reds']}")
            print(f"蓝球: {result['blue']}")
            print(f"目标熵: {result.get('target_entropy', 'N/A'):.4f}")
            print(f"组合熵: {result.get('combo_entropy', 'N/A'):.4f}")
            print(f"熵差值: {result.get('entropy_diff', 'N/A'):.4f}")
        
        # 使用蒙特卡洛模式生成多组
        model.mode = "monte_carlo"
        results = model.generate_monte_carlo(top_k=3)
        print(f"\n蒙特卡洛模式生成 {len(results)} 组结果:")
        for i, res in enumerate(results, 1):
            print(f"第{i}组: 红球{res['reds']} 蓝球{res['blue']} 熵差{res['entropy_diff']:.4f}")
            
    finally:
        db.close()
