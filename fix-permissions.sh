#!/bin/bash

# 数据库权限快速修复脚本

echo "=========================================="
echo "  数据库权限快速修复工具"
echo "=========================================="
echo ""

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

echo "📂 创建必要的目录..."
mkdir -p data logs

echo "🔧 设置目录权限..."
chmod 755 data logs

echo "📊 检查目录状态..."
echo ""
echo "  data/ 目录:"
ls -la data/ 2>/dev/null || echo "    (空目录)"
echo ""
echo "  logs/ 目录:"
ls -la logs/ 2>/dev/null || echo "    (空目录)"
echo ""

echo "✅ 权限修复完成！"
echo ""
echo "📝 下一步操作:"
echo "   1. 如果容器正在运行，请重启:"
echo "      docker-compose restart"
echo ""
echo "   2. 如果容器未运行，请启动:"
echo "      docker-compose up -d"
echo ""
echo "   3. 查看日志确认正常运行:"
echo "      docker-compose logs -f"
echo ""
echo "=========================================="
