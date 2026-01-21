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
    # Emby 容器挂载: /media:/media (容器内外路径一致)
    # 容器内路径 /media/xxx → 宿主机路径 /media/xxx
    "/media/": "/media/",
}

# 2. STRM 文件内容路径 → 宿主机路径映射（可选）
# 如果 strm 文件内容中的路径与实际宿主机路径不同，需要配置此映射
# 本例中 STRM 文件内容已经是正确的宿主机路径，所以留空
STRM_MOUNT_MAPPINGS = {
    # 示例：如果 STRM 内容是网络路径，需要映射到本地挂载点
    # "smb://nas/media/": "/mnt/nas/media/",
    # "nfs://storage/": "/mnt/nfs/",
}

# 3. 宿主机路径 → CDN URL 映射
# 将宿主机实际路径映射到 CDN 访问 URL，用于预热
CDN_URL_MAPPINGS = {
    # 宿主机路径 /media/xxx → CDN URL https://qiufeng.huaijiufu.com/xxx
    "/media/": "https://qiufeng.huaijiufu.com/",
}

# 4. 不预热路径黑名单
# 包含这些路径的媒体将不会提交预热请求
# 注意：这些是 Emby 容器路径，在路径映射之前进行检查
# 可以通过环境变量 PREHEAT_BLACKLIST_PATHS 配置（用逗号分隔）
PREHEAT_BLACKLIST_PATHS = [
    path.strip()
    for path in os.getenv("PREHEAT_BLACKLIST_PATHS", "").split(",")
    if path.strip()
] or [
    # 默认黑名单（如果环境变量未设置）
    # 示例：跳过某些特定目录
    # "/media/近期添加/",      # 跳过"近期添加"目录
    # "/media/test/",          # 跳过测试目录
    # "/media/temp/",          # 跳过临时目录
]

# ==================== 智能 URL 匹配配置 ====================
# 用于单体 Emby 部署，当标准路径映射失败时启用

# 是否启用智能 URL 匹配
ENABLE_SMART_URL_MATCHING = os.getenv("ENABLE_SMART_URL_MATCHING", "true").lower() == "true"

# 智能匹配的关键目录列表（按优先级排序，逗号分隔）
SMART_MATCH_KEYWORDS = [k.strip() for k in os.getenv("SMART_MATCH_KEYWORDS", "剧集,电影").split(",") if k.strip()]

# 智能匹配的 CDN 基础 URL
SMART_MATCH_CDN_BASE = os.getenv("SMART_MATCH_CDN_BASE", "https://your-cdn-domain.com/")

# 日志配置
LOG_FILE = "webhook.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 腾讯云 CDN 配置（暂未使用，后续添加预热功能时使用）
TENCENT_SECRET_ID = os.getenv("TENCENT_SECRET_ID", "")
TENCENT_SECRET_KEY = os.getenv("TENCENT_SECRET_KEY", "")
CDN_DOMAIN = os.getenv("CDN_DOMAIN", "nginx.example.com")

# 预热配置
PREHEAT_ENABLED = os.getenv("PREHEAT_ENABLED", "false").lower() == "true"
PREHEAT_BATCH_SIZE = int(os.getenv("PREHEAT_BATCH_SIZE", "10"))  # 每批预热的URL数量

# ==================== Telegram Bot 审核配置 ====================
# 是否启用 Telegram 人工审核
TELEGRAM_REVIEW_ENABLED = os.getenv("TELEGRAM_REVIEW_ENABLED", "true").lower() == "true"

# Telegram Bot Token (从 @BotFather 获取)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Telegram 管理员 Chat ID (可以是多个，用逗号分隔)
# 获取方式：给 @userinfobot 发消息，它会返回你的 Chat ID
TELEGRAM_ADMIN_CHAT_IDS = [
    int(chat_id.strip())
    for chat_id in os.getenv("TELEGRAM_ADMIN_CHAT_IDS", "").split(",")
    if chat_id.strip()
]

# 审核超时时间（秒），超时后自动拒绝
REVIEW_TIMEOUT_SECONDS = int(os.getenv("REVIEW_TIMEOUT_SECONDS", "86400"))  # 默认 24 小时

# 如果未启用 Telegram 审核，是否自动批准所有预热请求
AUTO_APPROVE_IF_NO_REVIEW = os.getenv("AUTO_APPROVE_IF_NO_REVIEW", "false").lower() == "true"

# ==================== Telegram 批量推送配置 ====================
# 批量推送时间间隔（秒）- 收集这么长时间的请求后批量发送
BATCH_PUSH_INTERVAL = int(os.getenv("BATCH_PUSH_INTERVAL", "30"))

# 批量推送最大数量 - 队列达到这个数量时立即推送（不等待时间间隔）
BATCH_PUSH_SIZE = int(os.getenv("BATCH_PUSH_SIZE", "10"))

# 单条消息最多包含的媒体数量（Telegram 消息长度限制）
MAX_ITEMS_PER_MESSAGE = int(os.getenv("MAX_ITEMS_PER_MESSAGE", "5"))
