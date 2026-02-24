from db.session import SessionLocal
from sqlalchemy import text
from services.system_service import SystemService


class HitStatisticsService:

    @staticmethod
    def process_latest_draw():

        if not SystemService.is_enabled("enable_model_stats"):
            return

        db = SessionLocal()

        # 1️⃣ 取最新一期
        latest = db.execute(text("""
            SELECT qi_shu, red1, red2, red3, red4, red5, red6, blue
            FROM kaijiang
            ORDER BY open_time DESC
            LIMIT 1
        """)).fetchone()

        if not latest:
            return

        reds = {
            latest.red1,
            latest.red2,
            latest.red3,
            latest.red4,
            latest.red5,
            latest.red6
        }

        blue = latest.blue

        # 2️⃣ 找未统计的预测
        predictions = db.execute(text("""
            SELECT * FROM model_predictions
            WHERE qi_shu IS NULL
        """)).fetchall()

        for p in predictions:

            pred_reds = {
                p.red1, p.red2, p.red3,
                p.red4, p.red5, p.red6
            }

            hit_red = len(pred_reds & reds)
            hit_blue = 1 if p.blue == blue else 0

            db.execute(text("""
                UPDATE model_predictions
                SET hit_red=:hr,
                    hit_blue=:hb,
                    qi_shu=:qi
                WHERE id=:id
            """), {
                "hr": hit_red,
                "hb": hit_blue,
                "qi": latest.qi_shu,
                "id": p.id
            })

        db.commit()

        HitStatisticsService.update_model_stats()
