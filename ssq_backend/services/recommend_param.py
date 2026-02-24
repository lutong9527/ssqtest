# services/recommend_param.py
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
from datetime import datetime

from models.params_snapshot import ParamsSnapshot  # 假设你有这个模型
from schemas.recommend import RecommendRequest

DEFAULT_PARAMS = {
    "heat_weight": 0.4,
    "miss_weight": 0.4,
    "active_weight": 0.2,
    "top_n": 12,
    "min_odd_even_ratio": "3:3",
    "description": "默认参数"
}

def save_param_snapshot(
    db: Session,
    user_id: int,
    params: Dict[str, Any],
    description: str = "自定义参数版本"
):
    """
    保存一次参数快照（用于回测或版本管理）
    """
    snapshot = ParamsSnapshot(
        user_id=user_id,
        params_json=json.dumps(params),
        description=description,
        created_at=datetime.utcnow()
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot

def get_latest_params(db: Session, user_id: int) -> Dict:
    """
    获取用户最近一次保存的参数（没有则返回默认）
    """
    snapshot = db.query(ParamsSnapshot).filter(
        ParamsSnapshot.user_id == user_id
    ).order_by(ParamsSnapshot.created_at.desc()).first()

    if snapshot:
        return json.loads(snapshot.params_json)
    return DEFAULT_PARAMS.copy()

def apply_custom_params(request: RecommendRequest, params: Dict) -> RecommendRequest:
    """
    根据自定义参数调整请求（示例：修改组数限制）
    """
    if request.count > params.get("max_groups", 5):
        request.count = params["max_groups"]
    return request