"""
路径映射测试脚本 - 针对你的实际案例

测试案例：
- Emby 容器路径: /media/软链接/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}/圣诞礼物.Gift Wrapped.1952.strm
- 宿主机路径: /mnt/media/软链接/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}/圣诞礼物.Gift Wrapped.1952.strm
- STRM 文件内容: /mnt/media/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}/圣诞礼物.Gift Wrapped.1952.mp4
- 预期 CDN URL: https://qiufeng.huaijiufu.com/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}/圣诞礼物.Gift Wrapped.1952.mp4
"""
import json
import requests
from typing import Dict, Any
import sys


def send_test_webhook(url: str, test_data: Dict[str, Any], test_name: str):
    """
    发送测试 webhook 请求

    Args:
        url: webhook 服务器地址
        test_data: 测试数据
        test_name: 测试名称
    """
    print("\n" + "=" * 100)
    print(f"🧪 测试案例: {test_name}")
    print("=" * 100)
    print(f"📤 发送请求到: {url}")
    print(f"📝 测试媒体: {test_data['Item']['Name']}")
    print(f"📂 Emby 路径: {test_data['Item']['Path']}")
    print("-" * 100)

    try:
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        print(f"\n📡 HTTP 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功\n")

            if 'data' in result:
                data = result['data']
                print("📊 解析结果:")
                print("-" * 100)
                print(f"  1️⃣  Emby 容器路径: {data.get('emby_path', 'N/A')}")
                print(f"  2️⃣  宿主机实际路径: {data.get('host_path', 'N/A')}")
                print(f"  3️⃣  CDN 预热 URL: {data.get('cdn_url', 'N/A')}")
                print("-" * 100)

                # 验证结果
                cdn_url = data.get('cdn_url')
                if cdn_url:
                    print(f"\n✅ CDN URL 生成成功！")
                    print(f"🔗 完整 URL: {cdn_url}")
                else:
                    print(f"\n⚠️  警告: CDN URL 未生成")
                    print(f"💡 请检查 config.py 中的 CDN_URL_MAPPINGS 配置")
            else:
                print(f"\n⚠️  响应中没有数据字段")
                print(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 请求失败")
            print(f"响应内容: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"❌ 连接错误: 无法连接到 webhook 服务器")
        print(f"💡 请确保:")
        print(f"   1. webhook_server.py 正在运行")
        print(f"   2. 服务器地址正确: {url}")
        print(f"   3. 端口未被防火墙阻止")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求错误: {str(e)}")
        sys.exit(1)

    print("=" * 100)


def main():
    # Webhook 服务器地址
    webhook_url = "http://localhost:8899/emby"

    print("\n" + "🎬" * 50)
    print("Emby CDN 预热服务 - 实际案例测试")
    print("🎬" * 50)
    print("\n💡 提示:")
    print("  - 请确保 webhook_server.py 已启动")
    print("  - 查看详细日志: tail -f webhook.log")
    print("  - 每一步的映射过程都会在日志中显示\n")

    # 测试用例: 你的实际 STRM 文件案例
    test_case_strm = {
        "Event": "library.new",
        "Title": "ROC 上新建 圣诞礼物",
        "Item": {
            "Name": "圣诞礼物",
            "OriginalTitle": "Gift Wrapped",
            "Type": "Movie",
            "Path": "/media/软链接/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}/圣诞礼物.Gift Wrapped.1952.strm",
            "Id": "48875",
            "ProductionYear": 1952
        },
        "Server": {
            "Name": "ROC",
            "Id": "test-server-001",
            "Version": "4.9.1.90"
        }
    }

    # 执行测试
    send_test_webhook(webhook_url, test_case_strm, "STRM 文件路径解析")

    print("\n" + "🎯" * 50)
    print("测试完成！")
    print("🎯" * 50)
    print("\n📋 验证清单:")
    print("  ✓ 检查上面的输出，确认 CDN URL 是否生成")
    print("  ✓ 查看 webhook.log 文件，确认每一步的映射过程")
    print("  ✓ 预期的 CDN URL 应该是:")
    print("    https://qiufeng.huaijiufu.com/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}/圣诞礼物.Gift Wrapped.1952.mp4")
    print("\n📝 注意事项:")
    print("  1. 如果 STRM 文件实际存在于系统中，URL 才能正确生成")
    print("  2. STRM 文件路径: /mnt/media/软链接/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}/圣诞礼物.Gift Wrapped.1952.strm")
    print("  3. STRM 文件内容应该是: /mnt/media/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}/圣诞礼物.Gift Wrapped.1952.mp4")
    print("  4. 如果 STRM 文件不存在，可以手动创建用于测试")
    print("\n💡 创建测试 STRM 文件的命令:")
    print('  mkdir -p "/mnt/media/软链接/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}"')
    print('  echo "/mnt/media/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}/圣诞礼物.Gift Wrapped.1952.mp4" > "/mnt/media/软链接/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}/圣诞礼物.Gift Wrapped.1952.strm"')
    print()


if __name__ == "__main__":
    main()
