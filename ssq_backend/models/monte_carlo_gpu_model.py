from models.base import BaseLotteryModel
from models.registry import register_model
import torch


@register_model
class MonteCarloGPUModel(BaseLotteryModel):

    model_code = "monte_gpu"
    model_name = "Monte Carlo GPU"
    enabled_by_default = False

    def generate(self):

        trials = 200000

        nums = torch.randint(1, 34, (trials, 6), device="cuda")

        scores = torch.sum(nums, dim=1)

        best_idx = torch.argmax(scores)

        best = nums[best_idx].cpu().tolist()

        return {
            "red": sorted(best),
            "blue": int(torch.randint(1, 17, (1,)).item())
        }
