# 使用官方 Python 3.11 精简版镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY webhook_server.py config.py ./

# 创建日志目录并设置权限
RUN mkdir -p /app/logs && \
    chmod 755 /app/logs

# 暴露服务端口
EXPOSE 8899

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8899/')" || exit 1

# 启动服务
CMD ["python", "webhook_server.py"]
