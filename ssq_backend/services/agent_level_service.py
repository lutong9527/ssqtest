class AgentLevelService:

    def __init__(self, db):
        self.db = db

    def check_upgrade(self, user_id):

        user = self.db.query(User).filter(User.id == user_id).first()

        direct_users = self.db.query(User).filter(
            User.parent_id == user_id
        ).count()

        team_users = self.get_team_count(user_id)

        team_recharge = self.get_team_recharge(user_id)

        levels = self.db.query(AgentLevel).all()

        for level in sorted(levels, key=lambda x: x.min_team_recharge, reverse=True):

            if (
                direct_users >= level.min_direct_users and
                team_users >= level.min_team_users and
                team_recharge >= level.min_team_recharge
            ):
                user.agent_level = level.level_code
                self.db.commit()
                break
