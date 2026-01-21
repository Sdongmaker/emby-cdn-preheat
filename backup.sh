#!/bin/bash

# Emby CDN 预热服务 - 备份脚本
# 备份数据库和配置文件

set -e

# 检测 docker-compose 命令
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker compose"  # 默认使用新版命令
fi

BACKUP_DIR="/opt/backups/emby-cdn-preheat"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup-${TIMESTAMP}.tar.gz"

echo "=========================================="
echo "  Emby CDN 预热服务 - 备份"
echo "=========================================="
echo ""

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 创建备份目录
echo "📁 创建备份目录..."
mkdir -p "$BACKUP_DIR"
echo "   目录: $BACKUP_DIR"
echo ""

# 检查需要备份的内容
echo "📊 检查备份内容..."

BACKUP_ITEMS=""

if [ -d "data" ] && [ "$(ls -A data 2>/dev/null)" ]; then
    echo "   ✅ data/ ($(du -sh data | cut -f1))"
    BACKUP_ITEMS="$BACKUP_ITEMS data/"
else
    echo "   ⚠️  data/ 目录为空，跳过"
fi

if [ -f ".env" ]; then
    echo "   ✅ .env"
    BACKUP_ITEMS="$BACKUP_ITEMS .env"
else
    echo "   ⚠️  .env 文件不存在，跳过"
fi

if [ -f "config.py" ]; then
    echo "   ℹ️  config.py (可选)"
    read -p "   是否包含 config.py? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        BACKUP_ITEMS="$BACKUP_ITEMS config.py"
    fi
fi

if [ -z "$BACKUP_ITEMS" ]; then
    echo ""
    echo "❌ 没有需要备份的内容"
    exit 1
fi

echo ""

# 创建备份
echo "📦 创建备份..."
tar -czf "$BACKUP_DIR/$BACKUP_FILE" $BACKUP_ITEMS

if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -sh "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    echo "   ✅ 备份成功"
    echo "   文件: $BACKUP_DIR/$BACKUP_FILE"
    echo "   大小: $BACKUP_SIZE"
else
    echo "   ❌ 备份失败"
    exit 1
fi

echo ""

# 列出所有备份
echo "📋 备份历史:"
ls -lh "$BACKUP_DIR" | tail -n +2 | awk '{print "   " $9 " (" $5 ")"}'

echo ""

# 清理旧备份
KEEP_DAYS=7
echo "🧹 清理旧备份 (保留 ${KEEP_DAYS} 天)..."

DELETED_COUNT=$(find "$BACKUP_DIR" -name "backup-*.tar.gz" -mtime +${KEEP_DAYS} -delete -print | wc -l)

if [ "$DELETED_COUNT" -gt 0 ]; then
    echo "   ✅ 已删除 $DELETED_COUNT 个旧备份"
else
    echo "   ℹ️  无需清理"
fi

echo ""
echo "=========================================="
echo "✅ 备份完成！"
echo "=========================================="
echo ""
echo "📝 恢复方法:"
echo "   1. 停止服务:"
echo "      $DOCKER_COMPOSE down"
echo ""
echo "   2. 解压备份:"
echo "      tar -xzf $BACKUP_DIR/$BACKUP_FILE"
echo ""
echo "   3. 启动服务:"
echo "      $DOCKER_COMPOSE up -d"
echo ""
echo "=========================================="
