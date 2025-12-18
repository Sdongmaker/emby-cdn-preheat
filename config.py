"""
配置文件
"""
import os
from pathlib import Path

# 服务器配置
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8899"))

# 路径映射配置
# 将 Emby 本地路径映射到 Nginx CDN URL
PATH_MAPPINGS = {
    "/media/电影/": "https://nginx.example.com/电影/",
    "/media/剧集/": "https://nginx.example.com/剧集/",
    "/media/动漫/": "https://nginx.example.com/动漫/",
}

# 日志配置
LOG_FILE = "webhook.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 腾讯云 CDN 配置（暂未使用，后续添加预热功能时使用）
TENCENT_SECRET_ID = os.getenv("TENCENT_SECRET_ID", "")
TENCENT_SECRET_KEY = os.getenv("TENCENT_SECRET_KEY", "")
CDN_DOMAIN = os.getenv("CDN_DOMAIN", "nginx.example.com")

# 预热配置
PREHEAT_ENABLED = os.getenv("PREHEAT_ENABLED", "false").lower() == "true"
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50000"))  # 最大预热文件大小（MB）
PREHEAT_BATCH_SIZE = int(os.getenv("PREHEAT_BATCH_SIZE", "10"))  # 每批预热的URL数量
