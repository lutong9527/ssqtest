from models.registry import ModelRegistry
from db.session import SessionLocal


class ModelSyncService:

    @staticmethod
    def sync_models():

        db = SessionLocal()

        for code, model_cls in ModelRegistry.all_models().items():

            db.execute("""
                INSERT IGNORE INTO compute_models
                (model_code, model_name, enabled)
                VALUES (:code, :name, :enabled)
            """, {
                "code": code,
                "name": model_cls.model_name,
                "enabled": 1 if model_cls.enabled_by_default else 0
            })

        db.commit()
