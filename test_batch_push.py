"""
测试批量推送功能
模拟多个媒体快速添加的场景
"""
import asyncio
import requests
import time
import json

# 配置
WEBHOOK_URL = "http://localhost:8899/emby"

# 模拟的媒体数据
test_media_items = [
    {
        "Name": "测试电影 1",
        "Type": "Movie",
        "Path": "/media/电影/测试电影1.mp4",
        "Id": "test_movie_1",
        "ProductionYear": 2024
    },
    {
        "Name": "测试电影 2",
        "Type": "Movie",
        "Path": "/media/电影/测试电影2.mp4",
        "Id": "test_movie_2",
        "ProductionYear": 2024
    },
    {
        "Name": "测试剧集 S01E01",
        "Type": "Episode",
        "Path": "/media/剧集/测试剧集/S01E01.mp4",
        "Id": "test_episode_1",
        "ProductionYear": 2024
    },
    {
        "Name": "测试剧集 S01E02",
        "Type": "Episode",
        "Path": "/media/剧集/测试剧集/S01E02.mp4",
        "Id": "test_episode_2",
        "ProductionYear": 2024
    },
    {
        "Name": "测试电影 3",
        "Type": "Movie",
        "Path": "/media/电影/测试电影3.mp4",
        "Id": "test_movie_3",
        "ProductionYear": 2024
    },
    {
        "Name": "测试电影 4",
        "Type": "Movie",
        "Path": "/media/电影/测试电影4.mp4",
        "Id": "test_movie_4",
        "ProductionYear": 2024
    },
    {
        "Name": "测试剧集 S01E03",
        "Type": "Episode",
        "Path": "/media/剧集/测试剧集/S01E03.mp4",
        "Id": "test_episode_3",
        "ProductionYear": 2024
    },
    {
        "Name": "测试电影 5",
        "Type": "Movie",
        "Path": "/media/电影/测试电影5.mp4",
        "Id": "test_movie_5",
        "ProductionYear": 2024
    },
]


def send_webhook_event(item_data):
    """发送 Webhook 事件"""
    webhook_data = {
        "Event": "library.new",
        "Item": item_data,
        "Server": {
            "Name": "Test Emby Server",
            "Id": "test_server_id"
        }
    }

    try:
        response = requests.post(
            WEBHOOK_URL,
            json=webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        if response.status_code == 200:
            print(f"✅ 发送成功: {item_data['Name']}")
            return True
        else:
            print(f"❌ 发送失败: {item_data['Name']}, 状态码: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 发送异常: {item_data['Name']}, 错误: {str(e)}")
        return False


def test_batch_push():
    """测试批量推送"""
    print("=" * 60)
    print("🧪 开始批量推送测试")
    print("=" * 60)
    print(f"\n📊 测试配置:")
    print(f"  - Webhook URL: {WEBHOOK_URL}")
    print(f"  - 测试媒体数量: {len(test_media_items)}")
    print(f"\n💡 预期行为:")
    print(f"  - 所有请求会加入队列")
    print(f"  - 当队列达到 BATCH_PUSH_SIZE 或经过 BATCH_PUSH_INTERVAL 秒后")
    print(f"  - Telegram Bot 会批量推送消息\n")

    print("-" * 60)
    print("🚀 开始快速发送媒体 Webhook 事件...")
    print("-" * 60)

    success_count = 0
    start_time = time.time()

    # 快速连续发送
    for idx, item in enumerate(test_media_items, 1):
        print(f"\n[{idx}/{len(test_media_items)}] 发送: {item['Name']}")
        if send_webhook_event(item):
            success_count += 1

        # 短暂延迟，模拟真实场景
        time.sleep(0.5)

    elapsed_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("📊 测试完成")
    print("=" * 60)
    print(f"✅ 成功发送: {success_count}/{len(test_media_items)}")
    print(f"⏱️  总耗时: {elapsed_time:.2f} 秒")
    print(f"\n💬 请查看 Telegram Bot 是否收到批量推送消息")
    print(f"📝 查看日志: tail -f webhook.log")
    print("=" * 60)


def test_single_item():
    """测试单个项目（用于快速验证）"""
    print("=" * 60)
    print("🧪 单项测试")
    print("=" * 60)

    item = test_media_items[0]
    print(f"\n发送测试媒体: {item['Name']}")

    if send_webhook_event(item):
        print(f"\n✅ 测试成功！")
        print(f"💬 请检查 Telegram Bot 是否收到通知")
    else:
        print(f"\n❌ 测试失败！")
        print(f"请检查:")
        print(f"  1. Webhook 服务是否运行: {WEBHOOK_URL}")
        print(f"  2. 查看日志: tail -f webhook.log")

    print("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "single":
        # 单项测试
        test_single_item()
    else:
        # 批量测试
        test_batch_push()
