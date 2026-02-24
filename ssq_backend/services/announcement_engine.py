from models.announcement import Announcement


class AnnouncementEngine:

    def __init__(self, db):
        self.db = db

    def create_win_announcement(self, user, amount):

        content = f"恭喜用户{user.id}中奖 {amount} 元 🎉"

        ann = Announcement(
            content=content,
            type="user_feed",
            is_auto=1,
            target_group="all"
        )

        self.db.add(ann)
        self.db.commit()

    def create_recharge_announcement(self, user, amount):

        content = f"用户{user.id}成功充值 {amount} 元"

        ann = Announcement(
            content=content,
            type="promotion",
            is_auto=1,
            target_group="all"
        )

        self.db.add(ann)
        self.db.commit()
