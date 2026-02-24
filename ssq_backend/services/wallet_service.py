from sqlalchemy import text
from db.session import SessionLocal
from decimal import Decimal


class WalletService:

    @staticmethod
    def change_balance(
        user_id: int,
        amount: Decimal = Decimal("0"),
        points: int = 0,
        biz_id: str = "",
        change_type: str = ""
    ):

        db = SessionLocal()

        try:
            # 1️⃣ 开启事务
            db.begin()

            # 2️⃣ 幂等检查
            existing = db.execute(text("""
                SELECT id FROM wallet_transactions
                WHERE user_id=:uid AND biz_id=:biz
            """), {"uid": user_id, "biz": biz_id}).fetchone()

            if existing:
                db.rollback()
                return {"status": "duplicate"}

            # 3️⃣ 行级锁
            wallet = db.execute(text("""
                SELECT balance, points
                FROM user_wallets
                WHERE user_id=:uid
                FOR UPDATE
            """), {"uid": user_id}).fetchone()

            if not wallet:
                db.rollback()
                raise Exception("Wallet not found")

            before_balance = wallet.balance
            before_points = wallet.points

            new_balance = before_balance + amount
            new_points = before_points + points

            if new_balance < 0:
                db.rollback()
                raise Exception("Insufficient balance")

            if new_points < 0:
                db.rollback()
                raise Exception("Insufficient points")

            # 4️⃣ 更新余额
            db.execute(text("""
                UPDATE user_wallets
                SET balance=:balance,
                    points=:points
                WHERE user_id=:uid
            """), {
                "balance": new_balance,
                "points": new_points,
                "uid": user_id
            })

            # 5️⃣ 写流水
            db.execute(text("""
                INSERT INTO wallet_transactions
                (user_id, change_amount, change_points,
                 type, biz_id,
                 before_balance, after_balance)
                VALUES
                (:uid, :amount, :points,
                 :type, :biz,
                 :before, :after)
            """), {
                "uid": user_id,
                "amount": amount,
                "points": points,
                "type": change_type,
                "biz": biz_id,
                "before": before_balance,
                "after": new_balance
            })

            db.commit()

            return {
                "status": "success",
                "balance": float(new_balance),
                "points": new_points
            }

        except Exception as e:
            db.rollback()
            raise e
