class SegmentService:

    def __init__(self, db):
        self.db = db

    def update_user_segment(self, user):

        segments = []

        if user.membership == "vip":
            segments.append("vip")

        if user.total_recharge > 1000:
            segments.append("high_value")

        if user.parent_id:
            segments.append("agent")

        # 删除旧分群
        self.db.query(UserSegment).filter(
            UserSegment.user_id == user.id
        ).delete()

        for s in segments:
            self.db.add(UserSegment(
                user_id=user.id,
                segment=s
            ))

        self.db.commit()
