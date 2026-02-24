# models/registry.py
"""
全局模型注册中心
所有彩票预测模型必须在此注册，才能被 ModelManager 动态加载

支持两种注册方式：
1. 装饰器：@register_model
2. 手动注册：在文件末尾调用 ModelRegistry.register(YourModel)

启动时会自动注册所有核心模型（compute/ 目录下）
"""

from typing import Dict, Type, Optional, List
import logging

from models.base import BaseLotteryModel

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    模型注册中心（单例模式）
    """
    _models: Dict[str, Type[BaseLotteryModel]] = {}

    @classmethod
    def register(cls, model_cls: Type[BaseLotteryModel]):
        """
        注册单个模型类
        - 如果代码已存在且是同一类对象，则静默跳过（避免重复注册警告）
        - 如果是不同类，则警告覆盖
        """
        if not hasattr(model_cls, "model_code"):
            raise ValueError(f"模型 {model_cls.__name__} 缺少 model_code 属性，必须定义")

        code = model_cls.model_code.strip().lower()

        # 防重注册：如果已存在且是同一类，直接跳过，不打印任何警告
        if code in cls._models and cls._models[code] is model_cls:
            logger.debug(f"模型 '{code}' 已注册（同一类），跳过重复注册")
            return

        # 如果同 code 但不同类，才打印警告并覆盖
        if code in cls._models:
            old_cls = cls._models[code]
            logger.warning(
                f"模型代码 '{code}' 已存在，原模型: {old_cls.__name__}，将被新模型 {model_cls.__name__} 覆盖"
            )

        cls._models[code] = model_cls
        logger.info(
            f"模型注册成功 → code: {code} | class: {model_cls.__name__} | "
            f"name: {getattr(model_cls, 'model_name', '未命名')} | "
            f"enabled: {getattr(model_cls, 'enabled_by_default', False)}"
        )

    @classmethod
    def get(cls, model_code: str) -> Optional[Type[BaseLotteryModel]]:
        """
        根据 model_code 获取模型类（忽略大小写）
        """
        code = model_code.strip().lower()
        model_cls = cls._models.get(code)
        if not model_cls:
            logger.warning(f"未找到模型: {model_code}")
        return model_cls

    @classmethod
    def all_models(cls) -> Dict[str, Type[BaseLotteryModel]]:
        """返回所有已注册模型的字典副本"""
        return cls._models.copy()

    @classmethod
    def exists(cls, model_code: str) -> bool:
        """判断模型代码是否存在（忽略大小写）"""
        return model_code.strip().lower() in cls._models

    @classmethod
    def list_registered(cls) -> List[dict]:
        """
        返回所有注册模型的详细信息（供后台管理界面使用）
        """
        return [
            {
                "code": code,
                "class_name": cls.__name__,
                "display_name": getattr(cls, "model_name", code),
                "default_params": getattr(cls, "default_params", {}),
                "enabled_by_default": getattr(cls, "enabled_by_default", False),
                "description": getattr(cls, "__doc__", "").strip().split("\n")[0] if cls.__doc__ else ""
            }
            for code, cls in sorted(cls._models.items())
        ]

    @classmethod
    def get_model_info(cls, model_code: str) -> Optional[dict]:
        """
        获取单个模型的详细信息
        """
        model_cls = cls.get(model_code)
        if not model_cls:
            return None
        return {
            "code": model_code.lower(),
            "class_name": model_cls.__name__,
            "display_name": getattr(model_cls, "model_name", model_code),
            "default_params": getattr(model_cls, "default_params", {}),
            "enabled_by_default": getattr(model_cls, "enabled_by_default", False),
            "description": getattr(model_cls, "__doc__", "").strip()
        }


def register_model(model_cls: Type[BaseLotteryModel]):
    """
    装饰器方式注册模型（推荐使用）

    示例：
        @register_model
        class MyModel(BaseLotteryModel):
            model_code = "my_model"
            model_name = "我的新模型"
            ...
    """
    ModelRegistry.register(model_cls)
    return model_cls


# ────────────────────────────────────────────────
# 自动注册所有核心模型（项目启动时自动执行）
# 请根据你的实际文件路径和类名调整
# ────────────────────────────────────────────────
logger.info("开始自动注册核心模型...")

registered_count = 0

# 基础随机模型
try:
    from compute.random_model import RandomLotteryModel
    ModelRegistry.register(RandomLotteryModel)
    registered_count += 1
except ImportError as e:
    logger.warning(f"random_model 导入失败：{e}")

# 改进马尔科夫链模型（确认类名是 MarkovModel）
try:
    from compute.markov_model import GeneticModel
    ModelRegistry.register(GeneticModel)
    registered_count += 1
except ImportError as e:
    logger.error(f"markov_model 导入失败：{e}")
    logger.error("请检查 compute/markov_model.py 中是否定义了 class MarkovModel(BaseLotteryModel)")

# 新增的三个模型
try:
    from compute.hot_cold_model import HotColdModel
    ModelRegistry.register(HotColdModel)
    registered_count += 1
except ImportError as e:
    logger.warning(f"hot_cold_model 导入失败：{e}")

try:
    from compute.odd_even_balance_model import OddEvenBalanceModel
    ModelRegistry.register(OddEvenBalanceModel)
    registered_count += 1
except ImportError as e:
    logger.warning(f"odd_even_balance_model 导入失败：{e}")

try:
    from compute.neural_network_model import NeuralNetworkModel
    ModelRegistry.register(NeuralNetworkModel)
    registered_count += 1
except ImportError as e:
    logger.warning(f"neural_network_model 导入失败：{e}")

# 如果有其他模型，继续添加 try-except 块
# try:
#     from compute.your_model import YourModel
#     ModelRegistry.register(YourModel)
#     registered_count += 1
# except ImportError as e:
#     logger.warning(f"your_model 导入失败：{e}")

logger.info(f"自动注册完成，共注册 {registered_count} 个模型（当前总数 {len(ModelRegistry.all_models())}）")
logger.info("已注册模型列表：")
for code in sorted(ModelRegistry.all_models().keys()):
    logger.info(f"  - {code}")
