"""
路径映射测试脚本

用于测试 Emby 容器路径、STRM 文件和 CDN URL 的映射是否正确配置
"""
import json
import requests
from typing import Dict, Any


def send_test_webhook(url: str, test_data: Dict[str, Any]):
    """
    发送测试 webhook 请求

    Args:
        url: webhook 服务器地址
        test_data: 测试数据
    """
    print("=" * 80)
    print(f"发送测试请求到: {url}")
    print(f"测试媒体: {test_data['Item']['Name']}")
    print(f"测试路径: {test_data['Item']['Path']}")
    print("-" * 80)

    try:
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        print(f"响应状态码: {response.status_code}")
        print(f"响应内容:")
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))

        if response.status_code == 200:
            result = response.json()
            if 'data' in result:
                data = result['data']
                print("\n✅ 路径映射结果:")
                print(f"  Emby 路径: {data.get('emby_path', 'N/A')}")
                print(f"  宿主机路径: {data.get('host_path', 'N/A')}")
                print(f"  CDN URL: {data.get('cdn_url', 'N/A')}")
        else:
            print(f"\n❌ 请求失败")

    except requests.exceptions.RequestException as e:
        print(f"❌ 请求错误: {str(e)}")

    print("=" * 80)
    print()


def main():
    # Webhook 服务器地址
    webhook_url = "http://localhost:8899/emby"

    print("Emby CDN 预热服务 - 路径映射测试")
    print("=" * 80)
    print()

    # 测试用例 1: 普通媒体文件
    test_case_1 = {
        "Event": "library.new",
        "Title": "测试 - 普通媒体文件",
        "Item": {
            "Name": "测试电影",
            "Type": "Movie",
            "Path": "/media/电影/测试电影 (2025)/movie.mkv",
            "Id": "test001"
        },
        "Server": {
            "Name": "Test Server",
            "Id": "test-server-001"
        }
    }

    # 测试用例 2: STRM 文件
    test_case_2 = {
        "Event": "library.new",
        "Title": "测试 - STRM 文件",
        "Item": {
            "Name": "测试剧集",
            "Type": "Episode",
            "Path": "/strm/data5/剧集/测试剧集/S01E01.strm",
            "Id": "test002"
        },
        "Server": {
            "Name": "Test Server",
            "Id": "test-server-001"
        }
    }

    # 测试用例 3: 剧集文件
    test_case_3 = {
        "Event": "library.new",
        "Title": "测试 - 剧集文件",
        "Item": {
            "Name": "测试剧集第一集",
            "Type": "Episode",
            "Path": "/media/剧集/测试剧集 (2025)/Season 01/S01E01.mkv",
            "Id": "test003"
        },
        "Server": {
            "Name": "Test Server",
            "Id": "test-server-001"
        }
    }

    # 执行测试
    print("开始测试路径映射...\n")

    send_test_webhook(webhook_url, test_case_1)
    send_test_webhook(webhook_url, test_case_2)
    send_test_webhook(webhook_url, test_case_3)

    print("\n测试完成！")
    print("\n提示:")
    print("1. 检查上面的输出，确认路径映射是否正确")
    print("2. 查看 webhook.log 文件获取详细的映射过程")
    print("3. 如果映射不正确，请检查 config.py 中的配置")
    print("4. 对于 STRM 文件测试，需要确保:")
    print("   - STRM 文件在宿主机上确实存在")
    print("   - webhook_server.py 运行用户有读取权限")
    print("   - EMBY_CONTAINER_MAPPINGS 正确映射到 STRM 文件所在的宿主机目录")


if __name__ == "__main__":
    main()
