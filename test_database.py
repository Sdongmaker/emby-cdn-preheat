"""
测试数据库连接和初始化
"""
import sys
import os
from pathlib import Path

def test_database():
    """测试数据库初始化"""
    print("=" * 60)
    print("🧪 数据库初始化测试")
    print("=" * 60)

    # 设置数据库路径
    db_file = os.getenv("DB_FILE", "data/preheat_review.db")
    print(f"\n📁 数据库文件路径: {db_file}")
    print(f"📂 当前工作目录: {Path.cwd()}")
    print(f"📍 数据库绝对路径: {Path(db_file).absolute()}")

    # 检查目录
    db_path = Path(db_file)
    db_dir = db_path.parent

    print(f"\n📂 数据库目录: {db_dir}")
    print(f"   - 目录存在: {db_dir.exists()}")
    if db_dir.exists():
        print(f"   - 可读: {os.access(db_dir, os.R_OK)}")
        print(f"   - 可写: {os.access(db_dir, os.W_OK)}")
        print(f"   - 可执行: {os.access(db_dir, os.X_OK)}")

    print(f"\n📄 数据库文件: {db_path}")
    print(f"   - 文件存在: {db_path.exists()}")

    # 尝试导入数据库模块
    try:
        print("\n🔧 尝试导入数据库模块...")
        from database import db
        print("✅ 数据库模块导入成功！")

        # 测试添加请求
        print("\n🧪 测试添加审核请求...")
        request_id = db.add_review_request(
            cdn_url="https://test.com/test.mp4",
            media_name="测试电影",
            media_type="Movie",
            emby_path="/media/test.mp4",
            host_path="/media/test.mp4"
        )

        if request_id:
            print(f"✅ 添加审核请求成功！ID: {request_id}")

            # 测试查询
            print("\n🧪 测试查询请求...")
            request = db.get_request_by_id(request_id)
            if request:
                print(f"✅ 查询请求成功！")
                print(f"   - 媒体名称: {request['media_name']}")
                print(f"   - CDN URL: {request['cdn_url']}")
                print(f"   - 状态: {request['status']}")
            else:
                print("❌ 查询请求失败")
        else:
            print("❌ 添加审核请求失败（可能已存在）")

        # 获取统计信息
        print("\n📊 数据库统计:")
        stats = db.get_statistics()
        print(f"   - 待审核: {stats['pending']}")
        print(f"   - 已批准: {stats['approved']}")
        print(f"   - 已拒绝: {stats['rejected']}")
        print(f"   - 总计: {stats['total']}")

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

        print("\n" + "=" * 60)
        print("❌ 测试失败！")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)
