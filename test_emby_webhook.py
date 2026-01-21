#!/usr/bin/env python3
"""
Emby Webhook 模拟测试脚本
用于测试云服务器上的 Emby CDN 预热服务
"""

import requests
import json
import time
import sys
import random
import string
from typing import Dict, Any, List

# 配置
WEBHOOK_URL = "http://104.36.21.247:8899/emby"  # 云服务器地址

# 随机数据生成配置
MOVIE_NAMES = [
    "复仇者联盟", "流浪地球", "教父", "肖申克的救赎", "霸王别姬",
    "这个杀手不太冷", "阿甘正传", "泰坦尼克号", "盗梦空间", "星际穿越",
    "蝙蝠侠", "蜘蛛侠", "钢铁侠", "美国队长", "黑客帝国",
    "指环王", "哈利波特", "速度与激情", "变形金刚", "侏罗纪公园",
    "沉默的羔羊", "辛德勒的名单", "低俗小说", "楚门的世界", "海上钢琴师"
]

TV_NAMES = [
    "权力的游戏", "绝命毒师", "瑞克和莫蒂", "黑镜", "西部世界",
    "怪奇物语", "纸牌屋", "行尸走肉", "真探", "冰与火之歌",
    "生活大爆炸", "老友记", "越狱", "24小时", "迷失",
    "美国恐怖故事", "汉尼拔", "神盾局特工", "闪电侠", "绿箭侠"
]

FILE_EXTENSIONS = [".mkv", ".mp4", ".avi", ".mov", ".m4v"]

def generate_random_id():
    """生成随机 ID"""
    timestamp = int(time.time() * 1000)
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{timestamp}_{random_str}"

def generate_random_movie(use_strm=False):
    """
    生成随机电影数据

    Args:
        use_strm: 是否生成 STRM 文件

    Returns:
        电影数据字典
    """
    movie_name = random.choice(MOVIE_NAMES)
    year = random.randint(2000, 2024)
    sequence = random.randint(1, 5)

    # 添加序号避免名称完全重复
    if sequence > 1:
        movie_name = f"{movie_name}{sequence}"

    ext = ".strm" if use_strm else random.choice(FILE_EXTENSIONS)

    movie_data = {
        "Name": f"{movie_name} ({year})",
        "Type": "Movie",
        "Path": f"/media/电影/{movie_name} ({year})/{movie_name}{ext}",
        "Id": generate_random_id(),
        "ProductionYear": year
    }

    return movie_data


def generate_random_episode(use_strm=False):
    """
    生成随机剧集数据

    Args:
        use_strm: 是否生成 STRM 文件

    Returns:
        剧集数据字典
    """
    tv_name = random.choice(TV_NAMES)
    season = random.randint(1, 5)
    episode = random.randint(1, 10)
    year = random.randint(2010, 2024)

    # 添加随机后缀避免名称完全重复
    suffix = random.choice(['', 'Plus', 'Special', 'Director Cut', ''])
    if suffix:
        tv_name = f"{tv_name} {suffix}"

    ext = ".strm" if use_strm else random.choice(FILE_EXTENSIONS)

    episode_data = {
        "Name": f"{tv_name} S{season:02d}E{episode:02d}",
        "Type": "Episode",
        "Path": f"/media/剧集/{tv_name}/Season {season:02d}/{tv_name} - S{season:02d}E{episode:02d}{ext}",
        "Id": generate_random_id(),
        "ProductionYear": year,
        "SeriesName": tv_name,
        "Season": season,
        "Episode": episode
    }

    return episode_data


def generate_test_media(count=8, movie_ratio=0.5, strm_ratio=0.25):
    """
    生成测试媒体列表

    Args:
        count: 生成数量
        movie_ratio: 电影占比（0-1）
        strm_ratio: STRM 文件占比（0-1）

    Returns:
        媒体列表
    """
    media_list = []

    movie_count = int(count * movie_ratio)
    episode_count = count - movie_count

    # 生成电影
    for _ in range(movie_count):
        use_strm = random.random() < strm_ratio
        media_list.append(generate_random_movie(use_strm))

    # 生成剧集
    for _ in range(episode_count):
        use_strm = random.random() < strm_ratio
        media_list.append(generate_random_episode(use_strm))

    # 打乱顺序
    random.shuffle(media_list)

    return media_list


# 生成默认测试数据（每次运行都不同）
TEST_MEDIA = generate_test_media(count=8, movie_ratio=0.5, strm_ratio=0.2)


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
    print("  1. 单项测试 - 随机生成1个媒体")
    print("  2. 批量测试 - 随机生成8个媒体（触发批量推送）")
    print("  3. 快速测试 - 随机生成3个媒体")
    print("  4. 电影测试 - 随机生成5个电影")
    print("  5. 剧集测试 - 随机生成5个剧集")
    print("  6. STRM 测试 - 随机生成5个STRM文件")
    print("  7. 自定义数量 - 指定生成数量")
    print("  8. 自定义测试 - 手动输入媒体信息")
    print("  9. 健康检查 - 只检查服务器状态")
    print("  s. 修改服务器地址")
    print("  0. 退出")
    print()
    print("💡 提示: 每次测试都会生成全新的随机数据，避免重复")


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
        choice = input("请选择: ").strip().lower()
        print()

        if choice == "1":
            # 单项测试 - 随机生成1个
            media = generate_random_movie() if random.random() > 0.5 else generate_random_episode()
            test_single(media, WEBHOOK_URL)

        elif choice == "2":
            # 批量测试 - 随机生成8个（不使用 STRM）
            print("🎲 正在生成8个随机媒体（不使用 STRM）...")
            test_media = generate_test_media(count=8, movie_ratio=0.5, strm_ratio=0.0)
            print(f"✅ 已生成: {sum(1 for m in test_media if m['Type']=='Movie')} 电影, "
                  f"{sum(1 for m in test_media if m['Type']=='Episode')} 剧集\n")
            test_batch(test_media, WEBHOOK_URL, delay=0.5)

        elif choice == "3":
            # 快速测试 - 随机生成3个（不使用 STRM）
            print("🎲 正在生成3个随机媒体（不使用 STRM）...")
            test_media = generate_test_media(count=3, movie_ratio=0.5, strm_ratio=0.0)
            print(f"✅ 已生成: {sum(1 for m in test_media if m['Type']=='Movie')} 电影, "
                  f"{sum(1 for m in test_media if m['Type']=='Episode')} 剧集\n")
            test_batch(test_media, WEBHOOK_URL, delay=0.5)

        elif choice == "4":
            # 电影测试 - 随机生成5个电影
            print("🎲 正在生成5个随机电影...")
            movies = [generate_random_movie(use_strm=random.random() < 0.2) for _ in range(5)]
            print(f"✅ 已生成: {sum(1 for m in movies if '.strm' in m['Path'])} 个STRM文件\n")
            test_batch(movies, WEBHOOK_URL, delay=0.5)

        elif choice == "5":
            # 剧集测试 - 随机生成5个剧集
            print("🎲 正在生成5个随机剧集...")
            episodes = [generate_random_episode(use_strm=random.random() < 0.2) for _ in range(5)]
            print(f"✅ 已生成: {sum(1 for e in episodes if '.strm' in e['Path'])} 个STRM文件\n")
            test_batch(episodes, WEBHOOK_URL, delay=0.5)

        elif choice == "6":
            # STRM 测试 - 随机生成5个STRM文件
            print("🎲 正在生成5个随机STRM文件...")
            strm_files = []
            for _ in range(5):
                if random.random() > 0.5:
                    strm_files.append(generate_random_movie(use_strm=True))
                else:
                    strm_files.append(generate_random_episode(use_strm=True))
            print(f"✅ 已生成: {sum(1 for m in strm_files if m['Type']=='Movie')} 电影, "
                  f"{sum(1 for m in strm_files if m['Type']=='Episode')} 剧集\n")
            test_batch(strm_files, WEBHOOK_URL, delay=0.5)

        elif choice == "7":
            # 自定义数量
            try:
                count = int(input("输入要生成的媒体数量 [8]: ").strip() or "8")
                if count <= 0 or count > 100:
                    print("❌ 数量必须在 1-100 之间")
                    continue

                print(f"\n🎲 正在生成{count}个随机媒体...")
                test_media = generate_test_media(count=count, movie_ratio=0.5, strm_ratio=0.2)
                print(f"✅ 已生成: {sum(1 for m in test_media if m['Type']=='Movie')} 电影, "
                      f"{sum(1 for m in test_media if m['Type']=='Episode')} 剧集, "
                      f"{sum(1 for m in test_media if '.strm' in m['Path'])} STRM文件\n")
                test_batch(test_media, WEBHOOK_URL, delay=0.5)
            except ValueError:
                print("❌ 无效的数量")

        elif choice == "8":
            # 自定义测试
            test_custom()

        elif choice == "9":
            # 健康检查
            print_banner()
            test_server_health(WEBHOOK_URL)
            print()

        elif choice == "s":
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
