# compute/model_manager.py
from typing import Dict, List, Any
from models.registry import ModelRegistry
from services.history_service import HistoryService
from compute.random_model import RandomLotteryModel
from models.fusion_engine import FusionEngine
from services.role_permission_service import get_permissions_by_role
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(
        self,
        user,
        db,
        periods: int = 200,
        model_params: Dict[str, Any] = None  # 全局参数（可覆盖所有模型）
    ):
        """
        :param user: 当前用户对象
        :param db: SQLAlchemy Session
        :param periods: 参考历史期数
        :param model_params: 全局参数字典，会覆盖所有模型的默认参数
        """
        self.user = user
        self.db = db
        self.periods = periods
        self.global_model_params = model_params or {}  # 全局参数

    def execute(self) -> Dict[str, Any]:
        """
        执行推荐流程
        返回格式统一，便于前端展示
        """
        # 使用随机模型（普通用户）
        if self.user.role == "normal":
            logger.info(f"普通用户 {self.user.username} 使用随机模型")
            return RandomLotteryModel().generate()

        # 获取历史数据
        history = HistoryService.get_last_n_draws(self.db, self.periods)
        if not history:
            logger.warning("历史数据为空，回退随机模型")
            return RandomLotteryModel().generate()

        # 获取权限
        permissions = get_permissions_by_role(self.db, self.user.role)
        if not permissions:
            logger.info(f"用户 {self.user.username} 无权限，回退随机模型")
            return RandomLotteryModel().generate()

        models = []
        weights = []

        # 遍历权限，加载模型
        for perm in permissions:
            model_code = perm.model_code
            model_cls = ModelRegistry.get(model_code)

            if not model_cls:
                logger.warning(f"模型 {model_code} 未注册，跳过")
                continue

            # 合并参数：全局参数 + 权限自定义参数 + 默认参数
            model_params = {
                **model_cls.default_params,           # 模型默认
                **(perm.params or {}),                # 权限表自定义
                **self.global_model_params            # 全局覆盖（最高优先级）
            }

            try:
                # 实例化模型并传入参数
                model = model_cls(history=history, params=model_params)
                models.append(model)
                weights.append(perm.weight)
                logger.info(f"模型 {model_code} 加载成功，权重 {perm.weight}")
            except Exception as e:
                logger.error(f"模型 {model_code} 实例化失败: {e}")
                continue

        # 打印已加载的模型数量和名称
        logger.info(f"已加载 {len(models)} 个模型：")
        for model in models:
            logger.info(f"- {model.model_code}: {model.__class__.__name__}")

        # 没有有效模型 → 回退随机
        if not models:
            logger.warning("无有效模型，回退随机模型")
            return RandomLotteryModel().generate()

        # 单模型直接返回
        if len(models) == 1:
            try:
                result = models[0].generate()
                result["model_used"] = models[0].model_code
                result["weight"] = weights[0]
                return result
            except Exception as e:
                logger.error(f"单模型生成失败: {e}")
                return RandomLotteryModel().generate()

        # 多模型融合
        try:
            fusion = FusionEngine(models, weights)
            result = fusion.generate()
            result["model_used"] = "fusion"
            result["models"] = [m.model_code for m in models]
            result["weights"] = weights
            return result
        except Exception as e:
            logger.error(f"融合引擎失败: {e}")
            return RandomLotteryModel().generate()
