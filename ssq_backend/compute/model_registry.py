from typing import Dict, Type


class ModelRegistry:

    _models: Dict[str, Type] = {}

    @classmethod
    def register(cls, code: str, model_cls):
        cls._models[code] = model_cls

    @classmethod
    def get_model(cls, code: str):
        return cls._models.get(code)
