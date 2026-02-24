# config/pay.py
import os
from dotenv import load_dotenv

load_dotenv()

# 支付宝配置（保持不变）
ALIPAY_APPID = os.getenv("ALIPAY_APPID")
ALIPAY_APP_PRIVATE_KEY = os.getenv("ALIPAY_APP_PRIVATE_KEY")
ALIPAY_ALIPAY_PUBLIC_KEY = os.getenv("ALIPAY_ALIPAY_PUBLIC_KEY")
ALIPAY_NOTIFY_URL = os.getenv("ALIPAY_NOTIFY_URL")
ALIPAY_RETURN_URL = os.getenv("ALIPAY_RETURN_URL")
ALIPAY_GATEWAY = "https://openapi.alipaydev.com/gateway.do"  # 沙箱

# 微信支付证书管理（推荐使用环境变量 + 文件路径）
WECHAT_MCH_ID = os.getenv("WECHAT_MCH_ID")
WECHAT_APP_ID = os.getenv("WECHAT_APP_ID")
WECHAT_API_V3_KEY = os.getenv("WECHAT_API_V3_KEY")
WECHAT_CERT_SERIAL_NO = os.getenv("WECHAT_CERT_SERIAL_NO")

# 证书文件路径（推荐放在项目根目录的 cert/ 文件夹）
WECHAT_CERT_PATH = os.getenv("WECHAT_CERT_PATH", "cert/apiclient_cert.pem")
WECHAT_KEY_PATH = os.getenv("WECHAT_KEY_PATH", "cert/apiclient_key.pem")

WECHAT_NOTIFY_URL = os.getenv("WECHAT_NOTIFY_URL", "http://你的域名/api/order/wechat/notify")