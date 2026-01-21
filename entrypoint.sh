#!/bin/bash
set -e

# 创建必要的目录
echo "Creating required directories..."
mkdir -p /app/logs
mkdir -p /app/data

# 设置权限
chmod 755 /app/logs
chmod 755 /app/data

echo "Directories created successfully"
echo "Working directory: $(pwd)"
echo "Directory contents:"
ls -la /app

# 启动应用
echo "Starting application..."
exec python webhook_server.py
