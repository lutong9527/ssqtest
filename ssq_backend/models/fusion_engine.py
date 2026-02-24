# models/fusion_engine.py

class FusionEngine:
    """
    一个用于多模型融合的引擎
    """

    def __init__(self, models, weights):
        """
        初始化模型融合引擎
        :param models: 模型列表
        :param weights: 每个模型的权重
        """
        self.models = models
        self.weights = weights

    def generate(self):
        """
        生成融合后的预测结果
        :return: 融合结果
        """
        weighted_results = []

        for model, weight in zip(self.models, self.weights):
            result = model.generate()  # 假设每个模型都有 generate() 方法
            weighted_results.append(self._apply_weight(result, weight))

        # 假设我们返回加权平均后的结果
        return self._combine_results(weighted_results)

    def _apply_weight(self, result, weight):
        """
        应用权重到模型结果上
        :param result: 模型结果
        :param weight: 权重
        :return: 加权后的结果
        """
        return [r * weight for r in result]

    def _combine_results(self, results):
        """
        融合多个加权后的结果
        :param results: 加权后的模型结果
        :return: 最终融合结果
        """
        # 假设简单地将结果平均
        combined_result = [sum(x) / len(x) for x in zip(*results)]
        return combined_result
