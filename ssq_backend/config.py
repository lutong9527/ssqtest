# config.py（项目根目录 /)

# JWT 配置
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # 生产必须从 .env 读取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

# 支付宝配置（示例）
ALIPAY_APPID = "your_alipay_appid"
ALIPAY_NOTIFY_URL = "https://your-domain.com/api/order/alipay/notify"

# 微信支付配置（示例）
WECHAT_MCH_ID = "your_mch_id"
WECHAT_NOTIFY_URL = "https://your-domain.com/api/order/wechat/notify"