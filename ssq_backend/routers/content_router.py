"""
内容管理API路由
提供横幅和公告的获取接口
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from typing import List, Optional

from database import get_db
from models.banner import Banner
from models.announcement import Announcement
#from models.user_segment import UserSegment
from auth import get_current_user
from models.user import User

router = APIRouter(prefix="/content", tags=["内容管理"])


# =========================================================================
# 横幅管理API
# =========================================================================
@router.get("/banners/{position}", summary="获取横幅", description="根据位置获取有效的横幅列表")
def get_banners(
    position: str, 
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    获取指定位置的横幅
    
    参数：
        position: 横幅位置（如：home_top, home_middle, sidebar等）
    
    返回：
        横幅列表，按排序倒序排列
    """
    now = datetime.now()

    banners = db.query(Banner).filter(
        Banner.position == position,
        Banner.status == 1,  # 状态为启用
        (Banner.start_time == None) | (Banner.start_time <= now),
        (Banner.end_time == None) | (Banner.end_time >= now)
    ).order_by(Banner.sort_order.desc()).all()

    return [
        {
            "id": banner.id,
            "title": banner.title,
            "image_url": banner.image_url,
            "link_url": banner.link_url,
            "position": banner.position,
            "sort_order": banner.sort_order,
            "start_time": banner.start_time,
            "end_time": banner.end_time,
            "status": banner.status
        }
        for banner in banners
    ]


@router.get("/banners", summary="获取所有横幅", description="获取所有有效的横幅列表")
def get_all_banners(
    status: Optional[int] = None,
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    获取所有横幅（管理员或公开接口）
    
    参数：
        status: 横幅状态（可选，1=启用，0=禁用）
    
    返回：
        横幅列表
    """
    now = datetime.now()
    query = db.query(Banner)
    
    # 如果指定了状态，按状态筛选
    if status is not None:
        query = query.filter(Banner.status == status)
    
    # 对于公开访问，只返回当前有效的横幅
    if status is None:
        query = query.filter(
            Banner.status == 1,
            (Banner.start_time == None) | (Banner.start_time <= now),
            (Banner.end_time == None) | (Banner.end_time >= now)
        )
    
    banners = query.order_by(
        Banner.position.asc(),
        Banner.sort_order.desc()
    ).all()
    
    return [
        {
            "id": banner.id,
            "title": banner.title,
            "image_url": banner.image_url,
            "link_url": banner.link_url,
            "position": banner.position,
            "sort_order": banner.sort_order,
            "start_time": banner.start_time,
            "end_time": banner.end_time,
            "status": banner.status
        }
        for banner in banners
    ]


# =========================================================================
# 公告管理API
# =========================================================================
@router.get("/announcements", summary="获取公告列表", description="获取当前用户可见的公告列表")
def get_announcements(
    limit: int = 20,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> List[dict]:
    """
    获取公告列表
    
    参数：
        limit: 返回数量限制（默认20）
        category: 公告分类（可选）
        current_user: 当前用户（可选，用于个性化公告）
    
    返回：
        公告列表，按排序倒序排列
    """
    now = datetime.now()
    
    # 构建基础查询
    query = db.query(Announcement).filter(
        Announcement.status == 1,  # 状态为启用
        (Announcement.start_time == None) | (Announcement.start_time <= now),
        (Announcement.end_time == None) | (Announcement.end_time >= now)
    )
    
    # 如果用户已登录，获取用户分组的公告
    if current_user:
        # 获取用户所属的分组
        user_segments = db.query(UserSegment.segment).filter(
            UserSegment.user_id == current_user.id
        ).all()
        
        segments = [s[0] for s in user_segments] if user_segments else []
        segments.append("all")  # 总是包含"all"分组
        
        # 筛选目标分组
        query = query.filter(
            Announcement.target_group.in_(segments)
        )
    else:
        # 未登录用户只能看到"all"分组的公告
        query = query.filter(
            Announcement.target_group == "all"
        )
    
    # 按分类筛选
    if category:
        query = query.filter(Announcement.category == category)
    
    # 执行查询并限制数量
    announcements = query.order_by(
        Announcement.sort_order.desc(),
        Announcement.created_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": ann.id,
            "title": ann.title,
            "content": ann.content,
            "category": ann.category,
            "target_group": ann.target_group,
            "sort_order": ann.sort_order,
            "start_time": ann.start_time,
            "end_time": ann.end_time,
            "status": ann.status,
            "created_at": ann.created_at,
            "updated_at": ann.updated_at
        }
        for ann in announcements
    ]


@router.get("/announcements/{announcement_id}", summary="获取公告详情", description="根据ID获取公告详情")
def get_announcement_detail(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> dict:
    """
    获取指定公告的详情
    
    参数：
        announcement_id: 公告ID
        current_user: 当前用户（用于权限检查）
    
    返回：
        公告详情
    """
    now = datetime.now()
    
    # 获取公告
    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id,
        Announcement.status == 1,
        (Announcement.start_time == None) | (Announcement.start_time <= now),
        (Announcement.end_time == None) | (Announcement.end_time >= now)
    ).first()
    
    if not announcement:
        return {"error": "公告不存在或已失效"}
    
    # 检查用户是否有权限查看此公告
    if current_user:
        # 获取用户所属的分组
        user_segments = db.query(UserSegment.segment).filter(
            UserSegment.user_id == current_user.id
        ).all()
        segments = [s[0] for s in user_segments] if user_segments else []
        segments.append("all")
        
        # 检查公告是否在用户分组中
        if announcement.target_group not in segments:
            return {"error": "您没有权限查看此公告"}
    else:
        # 未登录用户只能查看"all"分组的公告
        if announcement.target_group != "all":
            return {"error": "请登录后查看此公告"}
    
    return {
        "id": announcement.id,
        "title": announcement.title,
        "content": announcement.content,
        "category": announcement.category,
        "target_group": announcement.target_group,
        "sort_order": announcement.sort_order,
        "start_time": announcement.start_time,
        "end_time": announcement.end_time,
        "status": announcement.status,
        "created_at": announcement.created_at,
        "updated_at": announcement.updated_at
    }


@router.get("/announcements/categories", summary="获取公告分类", description="获取所有公告分类")
def get_announcement_categories(db: Session = Depends(get_db)) -> List[str]:
    """
    获取所有公告分类
    
    返回：
        分类名称列表
    """
    now = datetime.now()
    
    # 获取所有启用的公告分类
    categories = db.query(Announcement.category).filter(
        Announcement.status == 1,
        (Announcement.start_time == None) | (Announcement.start_time <= now),
        (Announcement.end_time == None) | (Announcement.end_time >= now),
        Announcement.category.isnot(None)  # 排除没有分类的公告
    ).distinct().all()
    
    return [category[0] for category in categories if category[0]]


@router.get("/announcements/all", summary="获取所有公告（管理员）", description="获取所有公告（需要管理员权限）")
def get_all_announcements(
    status: Optional[int] = None,
    target_group: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[dict]:
    """
    获取所有公告（管理员接口）
    
    参数：
        status: 公告状态（可选）
        target_group: 目标分组（可选）
        category: 公告分类（可选）
        current_user: 当前用户（需要管理员权限）
    
    返回：
        公告列表
    """
    # 检查管理员权限
    if current_user.role != "admin":
        return {"error": "需要管理员权限"}
    
    query = db.query(Announcement)
    
    # 应用筛选条件
    if status is not None:
        query = query.filter(Announcement.status == status)
    
    if target_group:
        query = query.filter(Announcement.target_group == target_group)
    
    if category:
        query = query.filter(Announcement.category == category)
    
    # 执行查询
    announcements = query.order_by(
        Announcement.sort_order.desc(),
        Announcement.created_at.desc()
    ).all()
    
    return [
        {
            "id": ann.id,
            "title": ann.title,
            "content": ann.content,
            "category": ann.category,
            "target_group": ann.target_group,
            "sort_order": ann.sort_order,
            "start_time": ann.start_time,
            "end_time": ann.end_time,
            "status": ann.status,
            "created_at": ann.created_at,
            "updated_at": ann.updated_at
        }
        for ann in announcements
    ]


# =========================================================================
# 首页内容API（整合横幅和公告）
# =========================================================================
@router.get("/home", summary="获取首页内容", description="获取首页所需的横幅和公告")
def get_home_content(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> dict:
    """
    获取首页内容（整合横幅和公告）
    
    参数：
        current_user: 当前用户（可选）
    
    返回：
        包含横幅和公告的首页内容
    """
    now = datetime.now()
    
    # 获取首页横幅
    home_banners = db.query(Banner).filter(
        Banner.position == "home",
        Banner.status == 1,
        (Banner.start_time == None) | (Banner.start_time <= now),
        (Banner.end_time == None) | (Banner.end_time >= now)
    ).order_by(Banner.sort_order.desc()).all()
    
    # 获取公告
    query = db.query(Announcement).filter(
        Announcement.status == 1,
        (Announcement.start_time == None) | (Announcement.start_time <= now),
        (Announcement.end_time == None) | (Announcement.end_time >= now)
    )
    
    # 根据用户分组筛选公告
    if current_user:
        user_segments = db.query(UserSegment.segment).filter(
            UserSegment.user_id == current_user.id
        ).all()
        segments = [s[0] for s in user_segments] if user_segments else []
        segments.append("all")
        query = query.filter(Announcement.target_group.in_(segments))
    else:
        query = query.filter(Announcement.target_group == "all")
    
    announcements = query.order_by(
        Announcement.sort_order.desc(),
        Announcement.created_at.desc()
    ).limit(10).all()
    
    return {
        "banners": [
            {
                "id": banner.id,
                "title": banner.title,
                "image_url": banner.image_url,
                "link_url": banner.link_url,
                "sort_order": banner.sort_order
            }
            for banner in home_banners
        ],
        "announcements": [
            {
                "id": ann.id,
                "title": ann.title,
                "content": ann.content[:100] + "..." if ann.content and len(ann.content) > 100 else ann.content,
                "category": ann.category,
                "created_at": ann.created_at
            }
            for ann in announcements
        ],
        "timestamp": now.isoformat()
    }
