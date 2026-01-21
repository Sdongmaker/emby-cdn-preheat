#!/usr/bin/env python3
"""
Emby Webhook 模拟测试脚本
用于测试云服务器上的 Emby CDN 预热服务
"""

import requests
import json
import time
import sys
from typing import Dict, Any, List

# 配置
WEBHOOK_URL = "http://104.36.21.247:8899/emby"  # 云服务器地址

# 模拟的媒体数据
TEST_MEDIA = [
    # 电影
    {
        "Name": "复仇者联盟4：终局之战",
        "Type": "Movie",
        "Path": "/media/电影/复仇者联盟4：终局之战 (2019)/复仇者联盟4：终局之战.mkv",
        "Id": "movie_001",
        "ProductionYear": 2019
    },
    {
        "Name": "流浪地球2",
        "Type": "Movie",
        "Path": "/media/电影/流浪地球2 (2023)/流浪地球2.mp4",
        "Id": "movie_002",
        "ProductionYear": 2023
    },
    {
        "Name": "教父",
        "Type": "Movie",
        "Path": "/media/电影/教父 (1972)/教父.mkv",
        "Id": "movie_003",
        "ProductionYear": 1972
    },

    # 剧集
    {
        "Name": "权力的游戏 S01E01",
        "Type": "Episode",
        "Path": "/media/剧集/权力的游戏/Season 01/权力的游戏 - S01E01 - 凛冬将至.mkv",
        "Id": "episode_001",
        "ProductionYear": 2011,
        "SeriesName": "权力的游戏",
        "Season": 1,
        "Episode": 1
    },
    {
        "Name": "绝命毒师 S01E01",
        "Type": "Episode",
        "Path": "/media/剧集/绝命毒师/Season 01/绝命毒师 - S01E01.mkv",
        "Id": "episode_002",
        "ProductionYear": 2008,
        "SeriesName": "绝命毒师",
        "Season": 1,
        "Episode": 1
    },
    {
        "Name": "瑞克和莫蒂 S01E01",
        "Type": "Episode",
        "Path": "/media/剧集/瑞克和莫蒂/Season 01/瑞克和莫蒂 - S01E01.mp4",
        "Id": "episode_003",
        "ProductionYear": 2013,
        "SeriesName": "瑞克和莫蒂",
        "Season": 1,
        "Episode": 1
    },

    # STRM 文件测试
    {
        "Name": "星际穿越 (STRM)",
        "Type": "Movie",
        "Path": "/media/电影/星际穿越 (2014)/星际穿越.strm",
        "Id": "movie_strm_001",
        "ProductionYear": 2014
    },
    {
        "Name": "黑镜 S01E01 (STRM)",
        "Type": "Episode",
        "Path": "/media/剧集/黑镜/Season 01/黑镜 - S01E01.strm",
        "Id": "episode_strm_001",
        "ProductionYear": 2011,
        "SeriesName": "黑镜",
        "Season": 1,
        "Episode": 1
    },
]


def build_emby_webhook_payload(media_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    构建 Emby Webhook 数据格式

    Args:
        media_item: 媒体信息

    Returns:
        完整的 Webhook payload
    """
    payload = {
        "Event": "library.new",
        "Item": {
            "Name": media_item["Name"],
            "Id": media_item["Id"],
            "Type": media_item["Type"],
            "Path": media_item["Path"],
            "ProductionYear": media_item.get("ProductionYear", ""),
        },
        "Server": {
            "Name": "Test Emby Server",
            "Id": "test_server_001",
            "Version": "4.7.0.0"
        },
        "User": {
            "Name": "TestUser",
            "Id": "test_user_001"
        },
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # 如果是剧集，添加剧集信息
    if media_item["Type"] == "Episode":
        payload["Item"]["SeriesName"] = media_item.get("SeriesName", "")
        payload["Item"]["Season"] = media_item.get("Season", 0)
        payload["Item"]["Episode"] = media_item.get("Episode", 0)

    return payload


def send_webhook(media_item: Dict[str, Any], server_url: str = WEBHOOK_URL) -> Dict[str, Any]:
    """
    发送 Webhook 请求

    Args:
        media_item: 媒体信息
        server_url: 服务器 URL

    Returns:
        包含状态和响应的字典
    """
    payload = build_emby_webhook_payload(media_item)

    try:
        response = requests.post(
            server_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Emby-Webhook/1.0"
            },
            timeout=10
        )

        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response": response.text if response.status_code != 200 else "OK",
            "media_name": media_item["Name"]
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "status_code": None,
            "response": "请求超时",
            "media_name": media_item["Name"]
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "status_code": None,
            "response": f"无法连接到服务器 {server_url}",
            "media_name": media_item["Name"]
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "response": str(e),
            "media_name": media_item["Name"]
        }


def print_banner():
    """打印横幅"""
    print("=" * 70)
    print("  Emby CDN 预热服务 - Webhook 测试工具")
    print("=" * 70)
    print()


def print_test_info(server_url: str, test_count: int):
    """打印测试信息"""
    print(f"📡 服务器地址: {server_url}")
    print(f"📊 测试媒体数量: {test_count}")
    print()


def test_server_health(server_url: str) -> bool:
    """
    测试服务器健康状态

    Args:
        server_url: 服务器 URL

    Returns:
        服务器是否健康
    """
    health_url = server_url.rsplit('/', 1)[0] + '/'

    print("🏥 检查服务器健康状态...")
    print(f"   URL: {health_url}")

    try:
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 服务器状态: {data.get('status', 'unknown')}")
            print(f"   ℹ️  服务名称: {data.get('service', 'unknown')}")
            return True
        else:
            print(f"   ⚠️  服务器响应异常: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 服务器无法访问: {str(e)}")
        return False


def test_single(media_item: Dict[str, Any], server_url: str = WEBHOOK_URL):
    """
    单个媒体测试

    Args:
        media_item: 媒体信息
        server_url: 服务器 URL
    """
    print_banner()
    print("🧪 单项测试模式")
    print()

    # 健康检查
    if not test_server_health(server_url):
        print()
        print("⚠️  警告: 服务器健康检查失败，但仍将继续测试...")
        print()

    print()
    print("-" * 70)
    print(f"📺 测试媒体: {media_item['Name']}")
    print(f"   类型: {media_item['Type']}")
    print(f"   路径: {media_item['Path']}")
    print("-" * 70)
    print()

    print("📤 发送 Webhook 请求...")
    result = send_webhook(media_item, server_url)

    print()
    if result["success"]:
        print("✅ 请求成功！")
        print(f"   HTTP 状态码: {result['status_code']}")
    else:
        print("❌ 请求失败！")
        print(f"   HTTP 状态码: {result['status_code']}")
        print(f"   错误信息: {result['response']}")

    print()
    print("=" * 70)
    print("💬 查看 Telegram Bot 是否收到审核通知")
    print("📝 查看服务器日志: docker compose logs -f")
    print("=" * 70)


def test_batch(media_list: List[Dict[str, Any]], server_url: str = WEBHOOK_URL, delay: float = 0.5):
    """
    批量测试

    Args:
        media_list: 媒体列表
        server_url: 服务器 URL
        delay: 每次请求之间的延迟（秒）
    """
    print_banner()
    print("🚀 批量测试模式")
    print()

    # 健康检查
    if not test_server_health(server_url):
        print()
        print("❌ 服务器健康检查失败，终止测试")
        return

    print()
    print_test_info(server_url, len(media_list))
    print("-" * 70)
    print("开始发送测试请求...")
    print("-" * 70)
    print()

    results = []
    success_count = 0

    for i, media_item in enumerate(media_list, 1):
        print(f"[{i}/{len(media_list)}] 📤 {media_item['Name']}")

        result = send_webhook(media_item, server_url)
        results.append(result)

        if result["success"]:
            print(f"        ✅ 成功 (HTTP {result['status_code']})")
            success_count += 1
        else:
            print(f"        ❌ 失败: {result['response']}")

        # 延迟以避免过快
        if i < len(media_list):
            time.sleep(delay)

        print()

    # 打印总结
    print("=" * 70)
    print("📊 测试完成")
    print("=" * 70)
    print(f"✅ 成功: {success_count}/{len(media_list)}")
    print(f"❌ 失败: {len(media_list) - success_count}/{len(media_list)}")
    print()

    # 打印失败的请求
    failed = [r for r in results if not r["success"]]
    if failed:
        print("失败的请求:")
        for r in failed:
            print(f"  - {r['media_name']}: {r['response']}")
        print()

    print("💬 预期行为:")
    print(f"   - 队列会收集这 {len(media_list)} 个请求")
    print(f"   - 达到批量阈值后会合并推送到 Telegram")
    print(f"   - 在 Telegram 中应该看到 1-2 条批量审核消息")
    print()
    print("📝 查看服务器日志:")
    print("   docker compose logs -f | grep '批量\\|队列'")
    print("=" * 70)


def test_custom():
    """自定义测试"""
    print_banner()
    print("🛠️  自定义测试")
    print()

    print("请输入测试信息:")
    print()

    name = input("媒体名称 [测试电影]: ").strip() or "测试电影"

    print("\n媒体类型:")
    print("  1. Movie (电影)")
    print("  2. Episode (剧集)")
    media_type = input("选择 (1/2) [1]: ").strip() or "1"
    media_type = "Movie" if media_type == "1" else "Episode"

    path = input(f"\n文件路径 [/media/电影/{name}.mkv]: ").strip() or f"/media/电影/{name}.mkv"

    year = input("\n年份 [2024]: ").strip() or "2024"
    try:
        year = int(year)
    except:
        year = 2024

    media_item = {
        "Name": name,
        "Type": media_type,
        "Path": path,
        "Id": f"custom_{int(time.time())}",
        "ProductionYear": year
    }

    print()
    print("-" * 70)
    print("自定义媒体信息:")
    print(json.dumps(media_item, indent=2, ensure_ascii=False))
    print("-" * 70)
    print()

    confirm = input("确认发送? (y/n) [y]: ").strip().lower() or "y"
    if confirm == "y":
        test_single(media_item, WEBHOOK_URL)
    else:
        print("已取消")


def show_menu():
    """显示主菜单"""
    print_banner()
    print("选择测试模式:")
    print()
    print("  1. 单项测试 - 测试单个媒体（电影）")
    print("  2. 批量测试 - 测试所有预设媒体（触发批量推送）")
    print("  3. 快速测试 - 测试 3 个媒体")
    print("  4. 电影测试 - 只测试电影")
    print("  5. 剧集测试 - 只测试剧集")
    print("  6. STRM 测试 - 只测试 STRM 文件")
    print("  7. 自定义测试 - 手动输入媒体信息")
    print("  8. 健康检查 - 只检查服务器状态")
    print("  9. 修改服务器地址")
    print("  0. 退出")
    print()


def main():
    """主函数"""
    global WEBHOOK_URL

    # 如果命令行指定了服务器地址
    if len(sys.argv) > 1:
        WEBHOOK_URL = sys.argv[1]
        if not WEBHOOK_URL.startswith("http"):
            WEBHOOK_URL = f"http://{WEBHOOK_URL}"
        if not WEBHOOK_URL.endswith("/emby"):
            WEBHOOK_URL = f"{WEBHOOK_URL}/emby"

    while True:
        show_menu()
        choice = input("请选择 (0-9): ").strip()
        print()

        if choice == "1":
            # 单项测试 - 电影
            test_single(TEST_MEDIA[0], WEBHOOK_URL)

        elif choice == "2":
            # 批量测试 - 所有媒体
            test_batch(TEST_MEDIA, WEBHOOK_URL, delay=0.5)

        elif choice == "3":
            # 快速测试 - 3个媒体
            test_batch(TEST_MEDIA[:3], WEBHOOK_URL, delay=0.5)

        elif choice == "4":
            # 电影测试
            movies = [m for m in TEST_MEDIA if m["Type"] == "Movie"]
            test_batch(movies, WEBHOOK_URL, delay=0.5)

        elif choice == "5":
            # 剧集测试
            episodes = [m for m in TEST_MEDIA if m["Type"] == "Episode"]
            test_batch(episodes, WEBHOOK_URL, delay=0.5)

        elif choice == "6":
            # STRM 测试
            strm_files = [m for m in TEST_MEDIA if ".strm" in m["Path"]]
            test_batch(strm_files, WEBHOOK_URL, delay=0.5)

        elif choice == "7":
            # 自定义测试
            test_custom()

        elif choice == "8":
            # 健康检查
            print_banner()
            test_server_health(WEBHOOK_URL)
            print()

        elif choice == "9":
            # 修改服务器地址
            print("当前服务器地址:", WEBHOOK_URL)
            new_url = input("输入新地址 (如 http://104.36.21.247:8899/emby): ").strip()
            if new_url:
                if not new_url.startswith("http"):
                    new_url = f"http://{new_url}"
                if not new_url.endswith("/emby"):
                    new_url = f"{new_url}/emby"
                WEBHOOK_URL = new_url
                print(f"✅ 已更新为: {WEBHOOK_URL}")
            print()

        elif choice == "0":
            # 退出
            print("👋 再见！")
            break

        else:
            print("❌ 无效选择，请重新输入")
            print()

        # 询问是否继续
        if choice != "0":
            print()
            continue_test = input("按 Enter 继续测试，输入 q 退出: ").strip().lower()
            if continue_test == "q":
                print("👋 再见！")
                break
            print("\n" * 2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试已中断")
        sys.exit(0)
