"""
管理员佣金管理API路由
提供佣金配置、统计和查询功能
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from database import get_db
from auth import get_current_user
from models.commission_config import CommissionConfig
from models.commission_log import CommissionLog
from models.user import User
from models.commission import Commissions

router = APIRouter(prefix="/admin/commission", tags=["admin-commission"])


def admin_required(current_user):
    """
    管理员权限检查
    
    参数：
        current_user: 当前用户对象
        
    异常：
        HTTPException: 当用户不是管理员时抛出403错误
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足，需要管理员权限")


# =========================================================================
# 佣金配置管理
# =========================================================================
@router.get("/config", summary="获取佣金配置", description="获取所有级别的佣金配置")
def get_commission_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[dict]:
    """
    查看当前所有分佣比例配置
    
    返回：
        佣金配置列表
    """
    admin_required(current_user)
    
    configs = db.query(CommissionConfig).order_by(CommissionConfig.level).all()
    
    return [
        {
            "id": config.id,
            "level": config.level,
            "commission_rate": float(config.commission_rate),
            "description": config.description,
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }
        for config in configs
    ]


@router.get("/config/{level}", summary="获取指定级别配置", description="获取指定级别的佣金配置")
def get_commission_config_by_level(
    level: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    查看指定级别的分佣比例配置
    
    参数：
        level: 分佣级别（1-10）
    
    返回：
        指定级别的佣金配置
    """
    admin_required(current_user)
    
    if level < 1 or level > 10:
        raise HTTPException(status_code=400, detail="级别必须在1-10之间")
    
    config = db.query(CommissionConfig).filter(
        CommissionConfig.level == level
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"级别 {level} 的配置不存在")
    
    return {
        "id": config.id,
        "level": config.level,
        "commission_rate": float(config.commission_rate),
        "description": config.description,
        "created_at": config.created_at,
        "updated_at": config.updated_at
    }


@router.post("/config", summary="更新佣金配置", description="创建或更新佣金配置")
def update_commission_config(
    level: int,
    commission_rate: float,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    修改或创建分佣比例配置
    
    参数：
        level: 分佣级别（1-10）
        commission_rate: 佣金比例（百分比，如5.5表示5.5%）
        description: 配置描述（可选）
    
    返回：
        操作结果
    """
    admin_required(current_user)
    
    # 参数验证
    if level < 1 or level > 10:
        raise HTTPException(status_code=400, detail="级别必须在1-10之间")
    
    if commission_rate < 0 or commission_rate > 100:
        raise HTTPException(status_code=400, detail="佣金比例必须在0-100之间")
    
    # 查找或创建配置
    config = db.query(CommissionConfig).filter(
        CommissionConfig.level == level
    ).first()

    if not config:
        # 创建新配置
        config = CommissionConfig(
            level=level,
            commission_rate=commission_rate,
            description=description
        )
        db.add(config)
        message = "创建成功"
    else:
        # 更新现有配置
        config.commission_rate = commission_rate
        if description is not None:
            config.description = description
        message = "更新成功"

    db.commit()
    
    return {
        "message": message,
        "data": {
            "level": level,
            "commission_rate": commission_rate,
            "description": description
        }
    }


@router.delete("/config/{level}", summary="删除佣金配置", description="删除指定级别的佣金配置")
def delete_commission_config(
    level: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    删除指定级别的分佣比例配置
    
    参数：
        level: 分佣级别（1-10）
    
    返回：
        操作结果
    """
    admin_required(current_user)
    
    if level < 1 or level > 10:
        raise HTTPException(status_code=400, detail="级别必须在1-10之间")
    
    config = db.query(CommissionConfig).filter(
        CommissionConfig.level == level
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail=f"级别 {level} 的配置不存在")
    
    db.delete(config)
    db.commit()
    
    return {"message": f"级别 {level} 的佣金配置已删除"}


# =========================================================================
# 佣金统计与查询
# =========================================================================
@router.get("/summary", summary="佣金汇总统计", description="获取全站佣金总额和记录统计")
def commission_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    查看全站佣金总额统计
    
    返回：
        佣金汇总信息
    """
    admin_required(current_user)
    
    # 计算总记录数和总金额
    total_logs = db.query(CommissionLog).all()
    total_commissions = db.query(Commission).all()
    
    # 计算日志总金额
    total_log_amount = sum(float(log.amount) for log in total_logs) if total_logs else 0
    
    # 计算佣金总金额
    total_commission_amount = sum(float(commission.amount) for commission in total_commissions) if total_commissions else 0
    
    return {
        "total_records": len(total_logs) + len(total_commissions),
        "commission_logs_count": len(total_logs),
        "commission_records_count": len(total_commissions),
        "total_log_amount": total_log_amount,
        "total_commission_amount": total_commission_amount,
        "total_combined_amount": total_log_amount + total_commission_amount
    }


@router.get("/summary/detailed", summary="详细佣金统计", description="获取详细的佣金统计数据")
def commission_detailed_summary(
    days: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    获取详细的佣金统计数据
    
    参数：
        days: 统计天数（可选，默认统计所有数据）
        status: 状态筛选（可选："pending" 或 "completed"）
    
    返回：
        详细的佣金统计信息
    """
    admin_required(current_user)
    
    # 构建基础查询
    log_query = db.query(CommissionLog)
    commission_query = db.query(Commission)
    
    # 时间范围筛选
    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        log_query = log_query.filter(CommissionLog.created_at >= start_date)
        commission_query = commission_query.filter(Commission.created_at >= start_date)
    
    # 状态筛选（仅对CommissionLog有效）
    if status:
        if status not in ["pending", "completed"]:
            raise HTTPException(status_code=400, detail="状态必须是 'pending' 或 'completed'")
        log_query = log_query.filter(CommissionLog.status == status)
    
    # 执行查询
    logs = log_query.all()
    commissions = commission_query.all()
    
    # 按级别统计
    log_level_stats = {}
    for log in logs:
        level = log.level
        if level not in log_level_stats:
            log_level_stats[level] = {
                "count": 0,
                "total_amount": 0.0,
                "pending_amount": 0.0,
                "completed_amount": 0.0
            }
        
        log_level_stats[level]["count"] += 1
        log_level_stats[level]["total_amount"] += float(log.amount)
        
        if log.status == "pending":
            log_level_stats[level]["pending_amount"] += float(log.amount)
        else:
            log_level_stats[level]["completed_amount"] += float(log.amount)
    
    # 按级别统计佣金
    commission_level_stats = {}
    for commission in commissions:
        level = commission.level
        if level not in commission_level_stats:
            commission_level_stats[level] = {
                "count": 0,
                "total_amount": 0.0,
                "pending_amount": 0.0,
                "completed_amount": 0.0
            }
        
        commission_level_stats[level]["count"] += 1
        commission_level_stats[level]["total_amount"] += float(commission.amount)
        
        if commission.status == 0:  # 0=待结算
            commission_level_stats[level]["pending_amount"] += float(commission.amount)
        else:  # 1=已结算
            commission_level_stats[level]["completed_amount"] += float(commission.amount)
    
    return {
        "time_range": {
            "days": days,
            "start_date": start_date if days else None
        },
        "commission_logs": {
            "total_count": len(logs),
            "total_amount": sum(float(log.amount) for log in logs) if logs else 0,
            "pending_count": sum(1 for log in logs if log.status == "pending"),
            "completed_count": sum(1 for log in logs if log.status == "completed"),
            "level_stats": log_level_stats
        },
        "commission_records": {
            "total_count": len(commissions),
            "total_amount": sum(float(c.amount) for c in commissions) if commissions else 0,
            "pending_count": sum(1 for c in commissions if c.status == 0),
            "completed_count": sum(1 for c in commissions if c.status == 1),
            "level_stats": commission_level_stats
        }
    }


@router.get("/logs", summary="佣金日志查询", description="查询佣金分发的日志记录")
def get_commission_logs(
    user_id: Optional[int] = None,
    from_user_id: Optional[int] = None,
    level: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    查询佣金日志记录
    
    参数：
        user_id: 用户ID（接收佣金者）
        from_user_id: 来源用户ID（产生佣金者）
        level: 分佣级别
        status: 状态筛选（"pending" 或 "completed"）
        start_date: 开始日期
        end_date: 结束日期
        page: 页码（默认1）
        page_size: 每页数量（默认20）
    
    返回：
        分页的佣金日志列表
    """
    admin_required(current_user)
    
    # 构建查询
    query = db.query(CommissionLog)
    
    # 应用筛选条件
    if user_id:
        query = query.filter(CommissionLog.user_id == user_id)
    if from_user_id:
        query = query.filter(CommissionLog.from_user_id == from_user_id)
    if level:
        query = query.filter(CommissionLog.level == level)
    if status:
        if status not in ["pending", "completed"]:
            raise HTTPException(status_code=400, detail="状态必须是 'pending' 或 'completed'")
        query = query.filter(CommissionLog.status == status)
    if start_date:
        query = query.filter(CommissionLog.created_at >= start_date)
    if end_date:
        query = query.filter(CommissionLog.created_at <= end_date)
    
    # 计算总数
    total = query.count()
    
    # 分页查询
    logs = query.order_by(CommissionLog.created_at.desc()) \
               .offset((page - 1) * page_size) \
               .limit(page_size) \
               .all()
    
    # 计算总金额
    total_amount = sum(float(log.amount) for log in logs) if logs else 0
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "total_amount": total_amount,
        "data": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "from_user_id": log.from_user_id,
                "amount": float(log.amount),
                "level": log.level,
                "status": log.status,
                "source_type": log.source_type,
                "created_at": log.created_at,
                "updated_at": log.updated_at
            }
            for log in logs
        ]
    }


@router.get("/records", summary="佣金记录查询", description="查询代理佣金记录")
def get_commission_records(
    proxy_id: Optional[int] = None,
    from_user_id: Optional[int] = None,
    level: Optional[int] = None,
    status: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    查询代理佣金记录
    
    参数：
        proxy_id: 代理ID
        from_user_id: 来源用户ID
        level: 分佣级别
        status: 状态筛选（0=待结算，1=已结算）
        start_date: 开始日期
        end_date: 结束日期
        page: 页码（默认1）
        page_size: 每页数量（默认20）
    
    返回：
        分页的佣金记录列表
    """
    admin_required(current_user)
    
    # 构建查询
    query = db.query(Commission)
    
    # 应用筛选条件
    if proxy_id:
        query = query.filter(Commission.proxy_id == proxy_id)
    if from_user_id:
        query = query.filter(Commission.from_user_id == from_user_id)
    if level:
        query = query.filter(Commission.level == level)
    if status is not None:
        query = query.filter(Commission.status == status)
    if start_date:
        query = query.filter(Commission.created_at >= start_date)
    if end_date:
        query = query.filter(Commission.created_at <= end_date)
    
    # 计算总数
    total = query.count()
    
    # 分页查询
    records = query.order_by(Commission.created_at.desc()) \
                   .offset((page - 1) * page_size) \
                   .limit(page_size) \
                   .all()
    
    # 计算总金额
    total_amount = sum(float(record.amount) for record in records) if records else 0
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "total_amount": total_amount,
        "data": [
            {
                "id": record.id,
                "proxy_id": record.proxy_id,
                "from_user_id": record.from_user_id,
                "amount": float(record.amount),
                "commission_rate": float(record.commission_rate),
                "level": record.level,
                "source_type": record.source_type,
                "source_id": record.source_id,
                "status": record.status,
                "created_at": record.created_at,
                "settled_at": record.settled_at
            }
            for record in records
        ]
    }


@router.get("/user/{user_id}", summary="用户佣金统计", description="获取指定用户的佣金统计信息")
def get_user_commission_stats(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    获取指定用户的佣金统计信息
    
    参数：
        user_id: 用户ID
    
    返回：
        用户佣金统计信息
    """
    admin_required(current_user)
    
    # 检查用户是否存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 查询用户的佣金日志
    logs = db.query(CommissionLog).filter(CommissionLog.user_id == user_id).all()
    
    # 查询用户的佣金记录（如果用户是代理）
    commissions = db.query(Commission).filter(Commission.proxy_id == user_id).all()
    
    # 计算统计信息
    log_stats = {
        "total_amount": sum(float(log.amount) for log in logs),
        "pending_amount": sum(float(log.amount) for log in logs if log.status == "pending"),
        "completed_amount": sum(float(log.amount) for log in logs if log.status == "completed"),
        "count": len(logs)
    }
    
    commission_stats = {
        "total_amount": sum(float(c.amount) for c in commissions),
        "pending_amount": sum(float(c.amount) for c in commissions if c.status == 0),
        "completed_amount": sum(float(c.amount) for c in commissions if c.status == 1),
        "count": len(commissions)
    }
    
    return {
        "user_info": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "proxy_id": user.proxy_id
        },
        "commission_logs": log_stats,
        "commission_records": commission_stats,
        "total_combined_amount": log_stats["total_amount"] + commission_stats["total_amount"]
    }
