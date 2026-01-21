#!/bin/bash

# Docker Compose 命令包装器
# 自动检测并使用正确的 docker-compose 命令

# 检测 docker-compose 命令
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ 错误: 未找到 docker-compose 或 docker compose 命令"
    echo ""
    echo "请安装 Docker Compose:"
    echo "  方式 1 (推荐): 使用 Docker Desktop 或最新版 Docker Engine"
    echo "  方式 2: 安装独立的 docker-compose:"
    echo "    sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose"
    echo "    sudo chmod +x /usr/local/bin/docker-compose"
    exit 1
fi

# 执行命令
$DOCKER_COMPOSE "$@"
