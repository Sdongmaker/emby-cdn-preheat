"""
配置文件
"""
import os
from pathlib import Path

# 服务器配置
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8899"))

# ==================== 路径映射配置 ====================
#
# 路径映射的工作流程：
# 1. Emby 容器内路径 → 宿主机路径（EMBY_CONTAINER_MAPPINGS）
# 2. 如果是 .strm 文件，读取内容获取真实路径
# 3. strm 内的路径 → 宿主机路径（STRM_MOUNT_MAPPINGS，可选）
# 4. 宿主机路径 → CDN URL（CDN_URL_MAPPINGS）

# 1. Emby 容器路径 → 宿主机路径映射
# 将 Emby 容器内看到的路径映射到宿主机实际路径
# 注意：映射会按照最长匹配优先的原则进行
EMBY_CONTAINER_MAPPINGS = {
    # 示例：Emby 容器内的 /media/剧集/ 映射到宿主机的 /mnt/storage/series/
    "/media/剧集/": "/mnt/storage/series/",
    "/media/电影/": "/mnt/storage/movies/",
    "/media/动漫/": "/mnt/storage/anime/",
    # strm 文件目录映射
    "/strm/data5/": "/mnt/strm/data5/",
}

# 2. STRM 文件内容路径 → 宿主机路径映射（可选）
# 如果 strm 文件内容中的路径与实际宿主机路径不同，需要配置此映射
# 例如：strm 文件内容是 smb://nas/media/xxx.mkv，需要映射到本地路径
STRM_MOUNT_MAPPINGS = {
    # 示例：strm 文件内的 smb 路径映射到宿主机挂载路径
    "smb://nas/media/": "/mnt/nas/media/",
    "nfs://storage/": "/mnt/nfs/",
    # 或者本地路径映射
    "/data/": "/mnt/storage/",
}

# 3. 宿主机路径 → CDN URL 映射
# 将宿主机实际路径映射到 CDN 访问 URL，用于预热
CDN_URL_MAPPINGS = {
    "/mnt/storage/series/": "https://cdn.example.com/series/",
    "/mnt/storage/movies/": "https://cdn.example.com/movies/",
    "/mnt/storage/anime/": "https://cdn.example.com/anime/",
    "/mnt/nas/media/": "https://cdn.example.com/nas/",
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
