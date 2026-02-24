# services/prediction_service.py

from db.session import SessionLocal


class PredictionService:

    @staticmethod
    def record_prediction(user_id, model_code, result):

        db = SessionLocal()

        sql = """
        INSERT INTO model_predictions
        (user_id, model_code, red1, red2, red3, red4, red5, red6, blue)
        VALUES (:user_id, :model_code, :r1, :r2, :r3, :r4, :r5, :r6, :blue)
        """

        db.execute(sql, {
            "user_id": user_id,
            "model_code": model_code,
            "r1": result["red"][0],
            "r2": result["red"][1],
            "r3": result["red"][2],
            "r4": result["red"][3],
            "r5": result["red"][4],
            "r6": result["red"][5],
            "blue": result["blue"]
        })

        db.commit()
