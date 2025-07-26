# config.py
import os

# ———————— 机器人 & API 基本配置 ————————
BOT_TOKEN = os.getenv("BOT_TOKEN", "7618735913:AAHUoI8uAcDOfV9G9uXEY6_wzCfuYDEZr9I")
API_URL   = os.getenv("API_URL", "http://api.eomsg.com/zc/data.php")

# ———————— Redis 缓存配置 ————————
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB   = int(os.getenv("REDIS_DB", 0))

# ———————— 取号/短信轮询策略 ————————
SMS_KEYWORD        = os.getenv("SMS_KEYWORD", "码")
SMS_POLL_INTERVAL  = float(os.getenv("SMS_POLL_INTERVAL", 5))    # 秒
SMS_POLL_TIMEOUT   = float(os.getenv("SMS_POLL_TIMEOUT", 60))    # 秒
