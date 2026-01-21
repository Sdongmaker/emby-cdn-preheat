#!/bin/bash

# Emby CDN 预热服务 - 初始化脚本
# 用于快速部署和环境准备

set -e

# 检测 docker-compose 命令
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ 未找到 docker-compose 或 docker compose 命令"
    exit 1
fi

echo "=========================================="
echo "  Emby CDN 预热服务 - 初始化"
echo "=========================================="
echo ""

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    echo "   当前目录: $(pwd)"
    exit 1
fi

echo "📂 当前目录: $(pwd)"
echo ""

# 1. 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p data logs

echo "   ✅ data/ - 数据库目录"
echo "   ✅ logs/ - 日志目录"
echo ""

# 2. 设置权限
echo "🔧 设置目录权限..."
chmod 755 data logs

echo "   ✅ data/ 权限: 755"
echo "   ✅ logs/ 权限: 755"
echo ""

# 3. 检查 .env 文件
echo "⚙️  检查环境配置..."
if [ ! -f ".env" ]; then
    echo "   ⚠️  未找到 .env 文件"

    # 询问是否创建
    read -p "   是否从示例文件创建 .env? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo "   ✅ 已创建 .env 文件"
        echo ""
        echo "   ⚠️  重要: 请编辑 .env 文件配置以下参数:"
        echo "      - TELEGRAM_BOT_TOKEN (必填)"
        echo "      - TELEGRAM_ADMIN_CHAT_IDS (必填)"
        echo "      - TENCENT_SECRET_ID (可选)"
        echo "      - TENCENT_SECRET_KEY (可选)"
        echo ""

        read -p "   是否现在编辑 .env 文件? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-vim} .env
        fi
    else
        echo "   ℹ️  跳过创建 .env 文件"
        echo "   请手动创建并配置 .env 文件后再启动服务"
    fi
else
    echo "   ✅ .env 文件已存在"

    # 检查必填参数
    echo ""
    echo "   检查必填参数..."

    if grep -q "TELEGRAM_BOT_TOKEN=.*[^[:space:]]" .env 2>/dev/null && \
       ! grep -q "TELEGRAM_BOT_TOKEN=your_bot_token_here" .env 2>/dev/null; then
        echo "   ✅ TELEGRAM_BOT_TOKEN 已配置"
    else
        echo "   ⚠️  TELEGRAM_BOT_TOKEN 未配置或使用默认值"
    fi

    if grep -q "TELEGRAM_ADMIN_CHAT_IDS=.*[^[:space:]]" .env 2>/dev/null && \
       ! grep -q "TELEGRAM_ADMIN_CHAT_IDS=123456789" .env 2>/dev/null; then
        echo "   ✅ TELEGRAM_ADMIN_CHAT_IDS 已配置"
    else
        echo "   ⚠️  TELEGRAM_ADMIN_CHAT_IDS 未配置或使用默认值"
    fi
fi

echo ""

# 4. 检查 Docker
echo "🐳 检查 Docker 环境..."
if command -v docker &> /dev/null; then
    echo "   ✅ Docker: $(docker --version)"
else
    echo "   ❌ 未安装 Docker"
    echo "   请先安装 Docker: https://docs.docker.com/engine/install/"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo "   ✅ Docker Compose: $(docker-compose --version)"
elif docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
    echo "   ✅ Docker Compose: $(docker compose version)"
else
    echo "   ❌ 未安装 Docker Compose"
    echo "   请先安装 Docker Compose"
    exit 1
fi

echo ""

# 5. 检查网络
echo "🌐 检查 Docker 网络..."
NETWORK_NAME="1panel-network"

if docker network inspect $NETWORK_NAME &> /dev/null; then
    echo "   ✅ 外部网络 '$NETWORK_NAME' 已存在"
else
    echo "   ⚠️  外部网络 '$NETWORK_NAME' 不存在"
    read -p "   是否创建该网络? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker network create $NETWORK_NAME
        echo "   ✅ 网络创建成功"
    else
        echo "   ℹ️  跳过网络创建"
        echo "   提示: 如果不需要外部网络，请修改 docker-compose.yml:"
        echo "         删除 'external: true' 行"
    fi
fi

echo ""

# 6. 检查端口
echo "🔌 检查端口占用..."
PORT=8899

if command -v netstat &> /dev/null; then
    if netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
        echo "   ⚠️  端口 $PORT 已被占用"
        netstat -tlnp 2>/dev/null | grep ":$PORT "
        echo "   请修改 docker-compose.yml 中的端口配置"
    else
        echo "   ✅ 端口 $PORT 可用"
    fi
elif command -v ss &> /dev/null; then
    if ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
        echo "   ⚠️  端口 $PORT 已被占用"
        ss -tlnp 2>/dev/null | grep ":$PORT "
        echo "   请修改 docker-compose.yml 中的端口配置"
    else
        echo "   ✅ 端口 $PORT 可用"
    fi
else
    echo "   ℹ️  无法检查端口占用（缺少 netstat 或 ss 命令）"
fi

echo ""

# 7. 显示目录状态
echo "📊 目录状态:"
echo "   data/:"
if [ -d "data" ] && [ "$(ls -A data 2>/dev/null)" ]; then
    ls -lh data/ | tail -n +2 | awk '{print "      " $0}'
else
    echo "      (空目录)"
fi

echo ""
echo "   logs/:"
if [ -d "logs" ] && [ "$(ls -A logs 2>/dev/null)" ]; then
    ls -lh logs/ | tail -n +2 | awk '{print "      " $0}'
else
    echo "      (空目录)"
fi

echo ""

# 8. 完成提示
echo "=========================================="
echo "✅ 初始化完成！"
echo "=========================================="
echo ""
echo "📝 下一步操作:"
echo ""
echo "   1. 确认配置文件:"
echo "      vim .env"
echo ""
echo "   2. 启动服务:"
echo "      docker-compose up -d"
echo ""
echo "   3. 查看日志:"
echo "      docker-compose logs -f"
echo ""
echo "   4. 访问测试:"
echo "      curl http://localhost:8899/"
echo ""
echo "   5. 配置 Emby Webhook:"
echo "      URL: http://服务器IP:8899/emby"
echo ""
echo "=========================================="
echo ""

# 9. 询问是否立即启动
read -p "是否现在启动服务? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 启动服务..."

    # 检查是否已有运行的容器
    if $DOCKER_COMPOSE ps 2>/dev/null | grep -q "Up"; then
        echo "   ⚠️  检测到已运行的容器"
        read -p "   是否重启? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            $DOCKER_COMPOSE restart
            echo "   ✅ 服务已重启"
        else
            echo "   ℹ️  保持当前状态"
        fi
    else
        $DOCKER_COMPOSE up -d
        echo "   ✅ 服务已启动"
    fi

    echo ""
    echo "   查看日志:"
    echo "   $DOCKER_COMPOSE logs -f"
    echo ""

    # 等待服务启动
    echo "   等待服务启动..."
    sleep 5

    # 健康检查
    if curl -s http://localhost:8899/ > /dev/null 2>&1; then
        echo "   ✅ 服务健康检查通过"
    else
        echo "   ⚠️  服务可能未正常启动，请查看日志"
        echo "   使用命令查看: $DOCKER_COMPOSE logs -f"
    fi
else
    echo ""
    echo "ℹ️  稍后手动启动服务:"
    echo "   $DOCKER_COMPOSE up -d"
fi

echo ""
echo "🎉 完成！"
