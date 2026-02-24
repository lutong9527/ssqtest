from sqlalchemy.orm import Session
from models.user_account import UserAccount


class AccountService:

    def __init__(self, db: Session):
        self.db = db

    def get_account(self, user_id):
        account = self.db.query(UserAccount).filter(
            UserAccount.user_id == user_id
        ).first()

        if not account:
            account = UserAccount(user_id=user_id)
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)

        return account

    def change_points(self, user_id, amount):
        account = self.get_account(user_id)

        if account.points_balance + amount < 0:
            raise Exception("积分不足")

        account.points_balance += amount
        self.db.commit()

    def change_commission(self, user_id, amount):
        account = self.get_account(user_id)
        account.commission_balance += amount
        self.db.commit()
