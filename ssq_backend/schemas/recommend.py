# schemas/recommend.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class RecommendRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=10, description="请求推荐组数")

class RedProbItem(BaseModel):
    number: int = Field(..., ge=1, le=33)
    prob: float = Field(..., ge=0.0, le=100.0)

class RecommendResponse(BaseModel):
    group_id: int
    red_balls: List[int]
    blue_ball: int
    strategy: str
    red_probs: List[RedProbItem]
    created_at: str

    class Config:
        from_attributes = True

# ==================== 新增：参数快照相关模型 ====================
class ParamSnapshotCreate(BaseModel):
    version: str = Field(..., description="参数版本号，例如 v2026.02.18.001")
    params: Dict[str, float] = Field(..., description="参数字典")
    description: Optional[str] = None
    coverage_rate: Optional[float] = None

class ParamSnapshotResponse(BaseModel):
    id: int
    version: str
    params: Dict[str, float]
    description: Optional[str]
    coverage_rate: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

# ==================== 新增：加载历史参数请求 ====================
class LoadParamsRequest(BaseModel):
    version: str = Field(..., description="要加载的参数版本号")