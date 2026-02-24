from models.base import BaseLotteryModel
from models.registry import register_model
import random


@register_model
class GeneticLotteryModel(BaseLotteryModel):

    model_code = "genetic"
    model_name = "Genetic Algorithm"
    enabled_by_default = False  # 新模型默认关闭

    def __init__(self, history=None, population=200, generations=100):
        super().__init__(history)
        self.population = population
        self.generations = generations

    def generate(self):

        return {
            "red": sorted(random.sample(range(1, 34), 6)),
            "blue": random.randint(1, 16)
        }
