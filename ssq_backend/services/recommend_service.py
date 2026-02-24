# services/recommend_service.py
"""
推荐引擎服务
提供多种双色球号码生成策略
"""

from services.entropy_model import EntropyBalancedModel


class RecommendEngine:
    """
    推荐引擎类
    
    提供多种双色球号码生成策略：
    1. 高级模型（熵平衡模型）
    2. 熵平衡模型（可自定义历史窗口）
    """
    
    def __init__(self, db):
        """
        初始化推荐引擎
        
        参数：
            db: 数据库会话对象
        """
        self.db = db

    # ==============================
    # 高级模型（熵平衡模型）- 默认使用50期历史数据
    # ==============================
    def generate_one_advanced(self):
        """
        使用高级熵平衡模型生成一组号码
        默认使用最近50期历史数据进行概率计算
        
        返回：
            包含号码信息和统计数据的字典
        """
        # 使用50期历史数据初始化模型
        model = EntropyBalancedModel(self.db, mode="entropy", history_window=50)
        return model.generate()

    # ==============================
    # 可配置历史窗口的熵平衡模型
    # ==============================
    def generate_entropy(self, history_window=None):
        """
        使用熵平衡模型生成一组号码，可自定义历史窗口大小
        
        参数：
            history_window: 历史数据窗口大小（期数）
                         - None: 使用模型默认值（100期）
                         - int: 指定期数（范围30-200）
        
        返回：
            包含号码信息和统计数据的字典
        """
        # 初始化熵平衡模型
        model = EntropyBalancedModel(self.db, mode="entropy", history_window=history_window)
        return model.generate()
        
    # 新增：回测专用方法（支持传入历史切片）
    # ==============================
    def generate_with_custom_history(
        self,
        history: list,
        params: dict,
        mode: str = "entropy"
    ):
        """
        回测专用：使用指定的历史数据切片生成预测
        """
        window = params.get("history_window", 100)
        if len(history) < window:
            window = len(history)

        model = EntropyBalancedModel(
            db=self.db,
            mode=mode,
            history_window=window,
            entropy_tolerance=params.get("entropy_tolerance", 0.05),
            monte_carlo_samples=params.get("monte_carlo_samples", 5000)
        )
        # 强制注入历史数据（EntropyBalancedModel 已支持）
        model.history = history[-window:]

        result = model.generate()
        return {
            "reds": result.get("reds", []),
            "blue": result.get("blue", 0),
            "history_window": window
        }

    # ==============================
    # 蒙特卡洛模式生成多组号码
    # ==============================
    def generate_multiple_monte_carlo(self, history_window=None, top_k=5, samples=10000):
        """
        使用蒙特卡洛模式生成多组号码
        
        参数：
            history_window: 历史数据窗口大小（期数）
                         - None: 使用模型默认值（100期）
                         - int: 指定期数（范围30-200）
            top_k: 返回的最佳组合数量（默认5组）
            samples: 蒙特卡洛采样次数（默认10000次）
        
        返回：
            列表，包含多组号码信息和统计数据
        """
        # 初始化蒙特卡洛模型
        model = EntropyBalancedModel(
            db=self.db,
            mode="monte_carlo",
            history_window=history_window,
            monte_carlo_samples=samples
        )
        return model.generate_monte_carlo(top_k=top_k)

    # ==============================
    # 简化接口（兼容旧代码）
    # ==============================
    def generate_simple(self, history_window=None):
        """
        简化接口，生成基本号码信息
        兼容需要简单结果的调用
        
        参数：
            history_window: 历史数据窗口大小（期数）
        
        返回：
            简化版的号码信息字典
        """
        # 使用熵平衡模式
        model = EntropyBalancedModel(self.db, mode="entropy", history_window=history_window)
        result = model.generate()
        
        if result:
            return {
                "reds": result.get("reds", []),
                "blue": result.get("blue", 0),
                "history_window": result.get("history_window", 0),
                "entropy_diff": result.get("entropy_diff", 0)
            }
        return None

    # ==============================
    # 批量生成功能
    # ==============================
    def generate_batch(self, count=5, method="entropy", **kwargs):
        """
        批量生成多组号码
        
        参数：
            count: 生成数量（默认5组）
            method: 生成方法，可选值：
                   - "entropy": 熵平衡模式（默认）
                   - "monte_carlo": 蒙特卡洛模式
            **kwargs: 传递给底层模型的其他参数
        
        返回：
            列表，包含多组号码
        """
        results = []
        
        if method == "entropy":
            # 熵平衡模式 - 每次调用生成一组
            for i in range(count):
                result = self.generate_entropy(**kwargs)
                if result:
                    results.append(result)
        
        elif method == "monte_carlo":
            # 蒙特卡洛模式 - 一次生成多组
            top_k = kwargs.pop('top_k', count)  # 优先使用传入的top_k，否则使用count
            monte_results = self.generate_multiple_monte_carlo(top_k=top_k, **kwargs)
            results.extend(monte_results)
        
        else:
            raise ValueError(f"不支持的生成方法: {method}")
        
        return results

    # ==============================
    # 模型配置更新
    # ==============================
    def update_model_config(self, **config_params):
        """
        更新模型配置
        
        参数：
            **config_params: 配置参数，可包括：
                           - history_window: 历史窗口大小
                           - entropy_tolerance: 熵容忍度
                           - monte_carlo_samples: 蒙特卡洛样本数
        
        返回：
            布尔值，表示配置是否成功更新
        """
        # 创建一个临时模型实例来更新配置
        model = EntropyBalancedModel(self.db, mode="entropy")
        return model.update_config(**config_params)
        
        
def generate_with_custom_history(
        self,
        history: list,              # 传入历史切片
        params: dict,
        mode: str = "entropy"
    ):
        # 临时覆盖 history_window
        window = params.get("history_window", 100)
        if len(history) < window:
            window = len(history)

        model = EntropyBalancedModel(
            db=self.db,
            mode=mode,
            history_window=window,
            entropy_tolerance=params.get("entropy_tolerance", 0.05),
            monte_carlo_samples=params.get("monte_carlo_samples", 5000)
        )

        # 强制注入历史数据（需要模型支持）
        model.history = history[-window:]   # 只取最近 window 期

        return model.generate()
        



# 使用示例
if __name__ == "__main__":
    # 示例用法
    from database import SessionLocal
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 创建推荐引擎
        engine = RecommendEngine(db)
        
        # 1. 使用高级模型生成一组
        print("=== 高级模型生成 ===")
        result1 = engine.generate_one_advanced()
        print(f"红球: {result1['reds']}")
        print(f"蓝球: {result1['blue']}")
        
        # 2. 使用熵平衡模型（自定义历史窗口）
        print("\n=== 熵平衡模型（100期历史）===")
        result2 = engine.generate_entropy(history_window=100)
        print(f"红球: {result2['reds']}")
        print(f"蓝球: {result2['blue']}")
        
        # 3. 使用蒙特卡洛模式生成多组
        print("\n=== 蒙特卡洛模式（生成3组） ===")
        results3 = engine.generate_multiple_monte_carlo(top_k=3, samples=5000)
        for i, res in enumerate(results3, 1):
            print(f"第{i}组: 红球{res['reds']} 蓝球{res['blue']}")
        
        # 4. 批量生成
        print("\n=== 批量生成（5组） ===")
        batch_results = engine.generate_batch(count=5, method="monte_carlo")
        for i, res in enumerate(batch_results, 1):
            print(f"第{i}组: 红球{res['reds']}")
            
    finally:
        db.close()
