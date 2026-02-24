from sqlalchemy.orm import Session
from sqlalchemy import select
from decimal import Decimal
from datetime import datetime
from typing import Optional, List

# 模型导入
from models.user import User
from models.proxy import Proxy
from models.commission import CommissionRules, Commission
from models.commission_log import CommissionLog
from models.commission_config import CommissionConfig


class CommissionService:
    """
    佣金计算与分发服务
    
    功能：
    1. 多级代理佣金分发（基于代理体系）
    2. 多级分销佣金分发（基于用户推荐关系）
    3. 佣金结算
    4. 佣金规则管理
    
    支持两种分佣体系：
    - 代理体系：用户→代理→上级代理→...（最多10级）
    - 分销体系：用户→推荐人→推荐人的推荐人→...（最多3级）
    """

    def __init__(self, db: Session):
        """
        初始化佣金服务
        
        参数：
            db: 数据库会话对象
        """
        self.db = db

    # =========================================================================
    # 代理体系分佣方法（支持多级代理，最多10级）
    # =========================================================================
    def create_commission_records(
        self,
        user_id: int,
        source_type: str,
        source_id: int,
        order_amount: Decimal
    ) -> bool:
        """
        生成代理体系的多级分佣记录
        
        参数：
            user_id: 产生消费的用户ID
            source_type: 佣金来源类型（如：order, recharge, subscription等）
            source_id: 来源ID（如订单ID、充值记录ID等）
            order_amount: 订单金额
            
        返回：
            bool: 是否成功创建分佣记录
            
        流程：
            1. 查找用户绑定的代理
            2. 从代理开始，逐级向上查找上级代理（最多10级）
            3. 根据每级的分佣规则计算佣金
            4. 创建佣金记录（状态为待结算）
        """
        try:
            # 1️⃣ 查询用户和绑定代理
            user = self.db.execute(
                select(User).where(User.id == user_id)
            ).scalar_one_or_none()

            if not user or not user.proxy_id:
                return False  # 用户不存在或未绑定代理，无需分佣

            # 获取当前代理
            current_proxy = self.db.execute(
                select(Proxy).where(Proxy.id == user.proxy_id)
            ).scalar_one_or_none()

            if not current_proxy:
                return False  # 代理不存在

            # 2️⃣ 开始分佣（最多10级）
            level = 1
            MAX_LEVEL = 10
            records_created = 0

            while current_proxy and level <= MAX_LEVEL:
                # 查询该级别的分佣规则
                rule = self.db.execute(
                    select(CommissionRules).where(
                        CommissionRules.level == level,
                        CommissionRules.source_type == source_type
                    )
                ).scalar_one_or_none()

                if rule:
                    # 计算佣金金额（基于百分比例）
                    commission_amount = (
                        order_amount * rule.commission_rate / Decimal(100)
                    ).quantize(Decimal("0.01"))

                    # 创建佣金记录
                    commission_record = Commission(
                        proxy_id=current_proxy.id,
                        from_user_id=user_id,
                        source_type=source_type,
                        source_id=source_id,
                        amount=commission_amount,
                        commission_rate=rule.commission_rate,
                        level=level,
                        status=0  # 0=待结算，1=已结算
                    )

                    self.db.add(commission_record)
                    records_created += 1

                # 查找上级代理
                if current_proxy.parent_id:
                    current_proxy = self.db.execute(
                        select(Proxy).where(Proxy.id == current_proxy.parent_id)
                    ).scalar_one_or_none()
                    level += 1
                else:
                    break  # 没有上级代理，结束循环

            if records_created > 0:
                self.db.commit()
                return True
            return False

        except Exception as e:
            self.db.rollback()
            raise e

    # =========================================================================
    # 分销体系分佣方法（支持多级分销，最多3级）
    # =========================================================================
    def distribute_commission(
        self,
        buyer_id: int,
        amount: float,
        source_type: str = "order"
    ) -> bool:
        """
        基于用户推荐关系的分销佣金分发
        
        参数：
            buyer_id: 产生消费的用户ID
            amount: 分佣金额
            source_type: 分佣来源类型
            
        返回：
            bool: 是否成功分发佣金
            
        流程：
            1. 查找买家用户
            2. 沿着推荐关系链向上查找（最多3级）
            3. 根据各级分佣配置计算佣金
            4. 创建分佣日志记录
        """
        try:
            # 查找买家用户
            buyer = self.db.query(User).filter(User.id == buyer_id).first()
            if not buyer:
                return False

            current_user = buyer
            level = 1
            MAX_LEVEL = 3  # 分销最多3级
            records_created = 0

            # 沿着推荐关系链向上分佣
            while current_user.parent_id and level <= MAX_LEVEL:
                # 查找推荐人
                parent = self.db.query(User).filter(
                    User.id == current_user.parent_id
                ).first()

                if not parent:
                    break

                # 获取该级别的分佣配置
                config = self.db.query(CommissionConfig).filter(
                    CommissionConfig.level == level
                ).first()

                if not config:
                    break

                # 计算佣金金额
                commission_amount = round(
                    amount * (config.commission_rate / 100),
                    2
                )

                # 创建分佣日志记录
                log = CommissionLog(
                    user_id=parent.id,
                    from_user_id=buyer.id,
                    amount=commission_amount,
                    level=level,
                    source_type=source_type,
                    status="pending"  # 待处理状态
                )

                self.db.add(log)
                records_created += 1

                # 继续向上查找
                current_user = parent
                level += 1

            if records_created > 0:
                self.db.commit()
                return True
            return False

        except Exception as e:
            self.db.rollback()
            raise e

    # =========================================================================
    # 佣金结算方法
    # =========================================================================
    def settle_commission(self, commission_id: int) -> bool:
        """
        手动结算单个佣金记录
        
        参数：
            commission_id: 佣金记录ID
            
        返回：
            bool: 是否成功结算
        """
        try:
            # 使用行级锁查询佣金记录，防止并发问题
            commission = self.db.execute(
                select(Commission).where(
                    Commission.id == commission_id,
                    Commission.status == 0  # 只结算待结算的记录
                ).with_for_update()
            ).scalar_one_or_none()

            if not commission:
                return False  # 记录不存在或已结算

            # 查找关联的代理
            proxy = self.db.execute(
                select(Proxy).where(Proxy.id == commission.proxy_id)
            ).scalar_one_or_none()

            if not proxy:
                return False  # 代理不存在

            # 更新代理佣金总额
            proxy.total_commission += commission.amount
            proxy.available_commission += commission.amount  # 增加可提现佣金

            # 更新佣金记录状态
            commission.status = 1  # 已结算
            commission.settled_at = datetime.utcnow()

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise e

    # =========================================================================
    # 批量佣金结算
    # =========================================================================
    def batch_settle_commissions(self, commission_ids: List[int]) -> dict:
        """
        批量结算佣金记录
        
        参数：
            commission_ids: 佣金记录ID列表
            
        返回：
            dict: 结算结果统计
        """
        result = {
            "total": len(commission_ids),
            "success": 0,
            "failed": 0,
            "failed_ids": []
        }

        try:
            for commission_id in commission_ids:
                try:
                    if self.settle_commission(commission_id):
                        result["success"] += 1
                    else:
                        result["failed"] += 1
                        result["failed_ids"].append(commission_id)
                except Exception:
                    result["failed"] += 1
                    result["failed_ids"].append(commission_id)

            return result

        except Exception as e:
            raise e

    # =========================================================================
    # 佣金查询方法
    # =========================================================================
    def get_user_commissions(
        self,
        user_id: int,
        status: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[dict]:
        """
        获取用户的分佣记录
        
        参数：
            user_id: 用户ID
            status: 佣金状态（0=待结算，1=已结算）
            start_date: 开始日期
            end_date: 结束日期
            
        返回：
            List[dict]: 佣金记录列表
        """
        try:
            query = self.db.query(Commission).filter(
                Commission.from_user_id == user_id
            )

            # 状态筛选
            if status is not None:
                query = query.filter(Commission.status == status)

            # 时间范围筛选
            if start_date:
                query = query.filter(Commission.created_at >= start_date)
            if end_date:
                query = query.filter(Commission.created_at <= end_date)

            # 排序：按创建时间倒序
            records = query.order_by(Commission.created_at.desc()).all()

            return [{
                "id": record.id,
                "proxy_id": record.proxy_id,
                "amount": float(record.amount),
                "commission_rate": float(record.commission_rate),
                "level": record.level,
                "source_type": record.source_type,
                "source_id": record.source_id,
                "status": record.status,
                "created_at": record.created_at,
                "settled_at": record.settled_at
            } for record in records]

        except Exception as e:
            raise e

    # =========================================================================
    # 佣金统计方法
    # =========================================================================
    def get_commission_stats(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """
        获取用户佣金统计
        
        参数：
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            
        返回：
            dict: 佣金统计数据
        """
        try:
            # 查询所有佣金记录
            query = self.db.query(Commission).filter(
                Commission.from_user_id == user_id
            )

            if start_date:
                query = query.filter(Commission.created_at >= start_date)
            if end_date:
                query = query.filter(Commission.created_at <= end_date)

            records = query.all()

            # 计算统计数据
            total_amount = sum(float(r.amount) for r in records)
            pending_amount = sum(
                float(r.amount) for r in records if r.status == 0
            )
            settled_amount = sum(
                float(r.amount) for r in records if r.status == 1
            )

            # 按级别统计
            level_stats = {}
            for record in records:
                level = record.level
                if level not in level_stats:
                    level_stats[level] = {
                        "count": 0,
                        "amount": Decimal("0"),
                        "pending_amount": Decimal("0"),
                        "settled_amount": Decimal("0")
                    }
                
                level_stats[level]["count"] += 1
                level_stats[level]["amount"] += record.amount
                
                if record.status == 0:
                    level_stats[level]["pending_amount"] += record.amount
                else:
                    level_stats[level]["settled_amount"] += record.amount

            return {
                "user_id": user_id,
                "total_count": len(records),
                "total_amount": float(total_amount),
                "pending_amount": float(pending_amount),
                "settled_amount": float(settled_amount),
                "level_stats": {
                    level: {
                        "count": stats["count"],
                        "amount": float(stats["amount"]),
                        "pending_amount": float(stats["pending_amount"]),
                        "settled_amount": float(stats["settled_amount"])
                    }
                    for level, stats in level_stats.items()
                },
                "start_date": start_date,
                "end_date": end_date
            }

        except Exception as e:
            raise e

    # =========================================================================
    # 静态方法（兼容旧代码调用方式）
    # =========================================================================
    @staticmethod
    def static_create_commission_records(
        db: Session,
        user_id: int,
        source_type: str,
        source_id: int,
        order_amount: Decimal
    ) -> bool:
        """
        静态方法：创建佣金记录（兼容旧代码）
        
        参数：
            db: 数据库会话
            user_id: 用户ID
            source_type: 来源类型
            source_id: 来源ID
            order_amount: 订单金额
            
        返回：
            bool: 是否成功创建
        """
        service = CommissionService(db)
        return service.create_commission_records(
            user_id, source_type, source_id, order_amount
        )

    @staticmethod
    def static_settle_commission(db: Session, commission_id: int) -> bool:
        """
        静态方法：结算佣金（兼容旧代码）
        
        参数：
            db: 数据库会话
            commission_id: 佣金ID
            
        返回：
            bool: 是否成功结算
        """
        service = CommissionService(db)
        return service.settle_commission(commission_id)


# 使用示例
if __name__ == "__main__":
    from database import SessionLocal
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 创建佣金服务实例
        service = CommissionService(db)
        
        # 示例1：代理体系分佣
        print("=== 代理体系分佣示例 ===")
        success = service.create_commission_records(
            user_id=1001,
            source_type="order",
            source_id=12345,
            order_amount=Decimal("1000.00")
        )
        print(f"代理分佣结果: {'成功' if success else '失败'}")
        
        # 示例2：分销体系分佣
        print("\n=== 分销体系分佣示例 ===")
        success = service.distribute_commission(
            buyer_id=1001,
            amount=1000.00,
            source_type="order"
        )
        print(f"分销分佣结果: {'成功' if success else '失败'}")
        
        # 示例3：获取佣金统计
        print("\n=== 用户佣金统计示例 ===")
        stats = service.get_commission_stats(user_id=1001)
        print(f"总佣金: {stats['total_amount']}")
        print(f"待结算: {stats['pending_amount']}")
        print(f"已结算: {stats['settled_amount']}")
        
        # 示例4：静态方法调用（兼容旧代码）
        print("\n=== 静态方法调用示例 ===")
        success = CommissionService.static_create_commission_records(
            db=db,
            user_id=1002,
            source_type="recharge",
            source_id=67890,
            order_amount=Decimal("500.00")
        )
        print(f"静态方法分佣结果: {'成功' if success else '失败'}")
        
    finally:
        db.close()
