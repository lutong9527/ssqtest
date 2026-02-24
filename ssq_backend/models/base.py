# models/base.py
from typing import Any, Dict, Optional

class BaseLotteryModel:
    """
    所有模型必须继承此基类
    """
    model_code: str = "base"
    model_name: str = "Base Model"
    enabled_by_default: bool = False

    # 新增：模型默认参数配置
    default_params: Dict[str, Any] = {}

    def __init__(self, history: Optional[list] = None, params: Optional[Dict] = None, **kwargs):
        """
        :param history: 历史开奖数据
        :param params: 运行时参数（会覆盖 default_params）
        """
        self.history = history or []
        self.params = {**self.default_params, **(params or {})}
        self.kwargs = kwargs

    def generate(self) -> Dict[str, Any]:
        raise NotImplementedError("Model must implement generate()")

    def update_params(self, new_params: Dict):
        """动态更新参数"""
        self.params.update(new_params)
