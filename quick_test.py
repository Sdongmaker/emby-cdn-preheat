#!/usr/bin/env python3
"""
快速测试脚本 - 简化版
"""

import requests
import time

# 修改为你的服务器地址
SERVER_URL = "http://104.36.21.247:8899/emby"

# 测试数据
TEST_MOVIE = {
    "Event": "library.new",
    "Item": {
        "Name": "复仇者联盟4：终局之战",
        "Type": "Movie",
        "Path": "/media/电影/复仇者联盟4：终局之战 (2019)/复仇者联盟4：终局之战.mkv",
        "Id": "test_001",
        "ProductionYear": 2019
    },
    "Server": {"Name": "Test Server", "Id": "test_001"}
}

print("🧪 快速测试 Emby CDN 预热服务")
print(f"📡 服务器: {SERVER_URL}")
print()

# 1. 健康检查
print("1️⃣ 健康检查...")
try:
    health_url = SERVER_URL.rsplit('/', 1)[0] + '/'
    r = requests.get(health_url, timeout=5)
    print(f"   ✅ 服务器状态: {r.json()['status']}")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    exit(1)

print()

# 2. 发送 Webhook
print("2️⃣ 发送测试 Webhook...")
try:
    r = requests.post(SERVER_URL, json=TEST_MOVIE, timeout=10)
    if r.status_code == 200:
        print(f"   ✅ 请求成功！")
    else:
        print(f"   ❌ 请求失败: HTTP {r.status_code}")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    exit(1)

print()
print("=" * 60)
print("✅ 测试完成！")
print()
print("💬 检查 Telegram Bot 是否收到审核通知")
print("📝 查看日志: docker compose logs -f")
print("=" * 60)
