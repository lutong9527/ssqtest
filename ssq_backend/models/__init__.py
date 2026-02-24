# models/__init__.py

# 原有导入保持不变
from .user import User
from .proxy import Proxy
from .kaijiang import Kaijiang
from .order import Order
from .recommend_result import RecommendResult
from .withdraw import Withdraw
from .role_limit import RoleLimit
from .call_log import CallLog
from .commission import CommissionRules, Commissions

# 新增的回测记录模型
from .backtest_records import BacktestRecord

# 如果你还有其他新模型，也可以继续加在这里
# from .xxx import XxxModel

__all__ = [
    "User",
    "Proxy",
    "Kaijiang",
    "Order",
    "RecommendResult",
    "Withdraw",
    "RoleLimit",
    "CallLog",
    "CommissionRules",
    "Commissions",
    "BacktestRecord",          # 新增这一行
    # 其他原有导出项...
]
from .backtest_records import BacktestRecord

