# services/role_permission_service.py
from sqlalchemy.orm import Session
from models.role_limit import RoleLimit  # ← 假设权限表是 role_limit，根据实际情况替换
# 或 from models.permission import Permission

def get_permissions_by_role(db: Session, role: str):
    """
    根据角色查询可使用的模型权限列表
    """
    # 根据你的数据库表结构调整查询
    # 假设表名为 role_limit，且有 role 和 model_code 字段
    return (
        db.query(RoleLimit)
        .filter(RoleLimit.role == role)
        .all()
    )

    # 如果表结构不同，例如：
    # return db.query(Permission).filter(Permission.role == role).all()
