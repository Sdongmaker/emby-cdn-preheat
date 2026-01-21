# 常见问题排查指南

快速解决常见部署和运行问题。

---

## ❌ `docker-compose: command not found`

### 问题原因

新版 Docker 将 `docker-compose` 改为 `docker compose`（带空格），旧命令不再可用。

### 解决方案

**方案 1: 使用新命令（推荐）**
```bash
docker compose up -d       # 而不是 docker-compose up -d
docker compose logs -f
docker compose ps
```

**方案 2: 使用快捷命令**
```bash
chmod +x dc
./dc up -d        # 自动兼容新旧版本
./dc logs -f
```

**方案 3: 修改脚本已自动兼容**
```bash
# 所有项目提供的脚本已自动检测并使用正确命令
./init.sh         # 自动处理
./backup.sh       # 自动处理
```

---

## ❌ `sqlite3.OperationalError: unable to open database file`

### 问题原因

数据库目录不存在或权限不足。

### 解决方案

**方案 1: 运行修复脚本**
```bash
./fix-permissions.sh
docker compose restart
```

**方案 2: 手动修复**
```bash
# 创建目录
mkdir -p data logs

# 设置权限
chmod 755 data logs

# 重启服务
docker compose restart
```

**方案 3: 重新初始化**
```bash
docker compose down
./init.sh
```

---

## ❌ 容器无法启动

### 检查步骤

1. **查看详细日志**
```bash
docker compose logs
# 或查看特定服务
docker compose logs emby-cdn-preheat
```

2. **检查端口占用**
```bash
# 检查 8899 端口
netstat -tlnp | grep 8899
# 或使用 ss
ss -tlnp | grep 8899
```

如果端口被占用，修改 `docker-compose.yml`:
```yaml
ports:
  - "8900:8899"  # 改为其他端口
```

3. **检查 Docker 状态**
```bash
docker ps -a
docker info
```

4. **重建容器**
```bash
docker compose down
docker compose up -d --force-recreate
```

---

## ❌ Telegram Bot 无响应

### 检查配置

```bash
# 查看环境变量
grep TELEGRAM .env

# 确认必填项
# TELEGRAM_BOT_TOKEN 不能为空或默认值
# TELEGRAM_ADMIN_CHAT_IDS 不能为空或默认值
```

### 测试 Bot Token

```bash
# 使用 curl 测试
BOT_TOKEN="你的Token"
curl "https://api.telegram.org/bot${BOT_TOKEN}/getMe"

# 应该返回 Bot 信息，如果返回错误说明 Token 无效
```

### 查看日志

```bash
docker compose logs | grep -i telegram
# 或
tail -f logs/webhook.log | grep -i telegram
```

### 常见错误

| 错误信息 | 原因 | 解决方法 |
|---------|------|---------|
| `401 Unauthorized` | Token 错误 | 检查 .env 中的 TELEGRAM_BOT_TOKEN |
| `Bad Request: chat not found` | Chat ID 错误 | 检查 TELEGRAM_ADMIN_CHAT_IDS |
| `未配置 TELEGRAM_BOT_TOKEN` | 未设置环境变量 | 编辑 .env 文件 |

---

## ❌ Webhook 接收不到数据

### 检查 Emby 配置

1. **Webhook 插件已安装且启用**
   - Emby 控制台 → 插件 → Webhook

2. **Webhook URL 正确**
   - 格式: `http://服务器IP:8899/emby`
   - 确认 IP 地址和端口正确

3. **事件类型已选择**
   - 必须选择 `Item Added` 或 `Library New`

4. **媒体类型已选择**
   - 选择 `Movies` 和 `Episodes`

### 网络测试

```bash
# 从 Emby 服务器测试连接
curl http://服务器IP:8899/

# 应该返回 {"status": "running", ...}
```

### 防火墙检查

```bash
# CentOS/RHEL
firewall-cmd --list-ports
firewall-cmd --permanent --add-port=8899/tcp
firewall-cmd --reload

# Ubuntu/Debian
ufw status
ufw allow 8899/tcp
```

### 查看日志

```bash
# 查看是否收到请求
tail -f logs/webhook.log

# 或查看容器日志
docker compose logs -f
```

---

## ❌ 路径映射不工作

### 检查映射配置

编辑 `config.py`:

```python
# 检查三层映射是否正确
EMBY_CONTAINER_MAPPINGS = {
    "/media/": "/media/",  # Emby 容器路径 → 宿主机路径
}

CDN_URL_MAPPINGS = {
    "/media/": "https://your-cdn.com/",  # 宿主机路径 → CDN URL
}
```

### 查看详细日志

日志会显示路径转换的每一步：

```bash
tail -f logs/webhook.log | grep -A 10 "步骤"
```

应该看到：
```
步骤 1: Emby 容器路径映射
步骤 2: 检查文件类型
步骤 3: STRM 路径映射
步骤 4: CDN URL 映射
```

### 验证路径

```bash
# 进入容器检查路径
docker compose exec emby-cdn-preheat bash
ls -la /media/  # 检查媒体目录是否正确挂载
```

---

## ❌ Docker 网络错误

### 错误信息
```
ERROR: Network 1panel-network declared as external, but could not be found
```

### 解决方案

**方案 1: 创建网络**
```bash
docker network create 1panel-network
```

**方案 2: 修改配置**

编辑 `docker-compose.yml`，删除或注释外部网络：

```yaml
networks:
  1panel-network:
    # external: true  # 注释掉这行
```

---

## ❌ 健康检查失败

### 错误信息
```
Unhealthy
```

### 检查步骤

1. **查看详细日志**
```bash
docker compose logs emby-cdn-preheat
```

2. **手动测试**
```bash
curl http://localhost:8899/
# 应该返回 JSON 响应
```

3. **进入容器检查**
```bash
docker compose exec emby-cdn-preheat bash
python -c "import requests; print(requests.get('http://localhost:8899/').text)"
```

4. **检查 requests 库**

如果报错 `No module named 'requests'`，说明镜像有问题，重新拉取：

```bash
docker compose pull
docker compose up -d --force-recreate
```

---

## ❌ 权限被拒绝

### 脚本权限

```bash
# 赋予所有脚本执行权限
chmod +x *.sh dc

# 单独赋予
chmod +x init.sh
chmod +x backup.sh
chmod +x fix-permissions.sh
```

### 目录权限

```bash
# 检查权限
ls -la data/ logs/

# 修复权限
chmod 755 data/ logs/
```

---

## 📝 调试技巧

### 1. 启用详细日志

编辑 `.env`:
```bash
LOG_LEVEL=DEBUG
```

重启服务:
```bash
docker compose restart
```

### 2. 实时监控日志

```bash
# 终端 1: 容器日志
docker compose logs -f

# 终端 2: 应用日志
tail -f logs/webhook.log

# 终端 3: 过滤关键信息
tail -f logs/webhook.log | grep -E "ERROR|WARNING|批量|队列"
```

### 3. 测试各个组件

```bash
# 测试数据库
python test_database.py

# 测试 Webhook
python test_batch_push.py single

# 测试路径映射
python test_path_mapping.py
```

### 4. 进入容器调试

```bash
# 进入容器
docker compose exec emby-cdn-preheat bash

# 检查环境
env | grep -E "TELEGRAM|DB_FILE|CDN"

# 检查文件
ls -la /app/
ls -la /app/data/
ls -la /app/logs/

# 手动运行 Python
python -c "from database import db; print(db.get_statistics())"
```

---

## 🆘 仍然无法解决？

### 收集信息

```bash
# 系统信息
uname -a
docker --version
docker compose version

# 服务状态
docker compose ps
docker compose logs > debug.log

# 目录状态
ls -la
ls -la data/
ls -la logs/

# 配置信息（删除敏感信息后）
cat .env | grep -v "TOKEN\|SECRET\|KEY"
```

### 提交 Issue

访问: https://github.com/Sdongmaker/emby-cdn-preheat/issues

提供以下信息：
1. 问题描述
2. 错误信息
3. 上述收集的系统信息
4. 相关日志（删除敏感信息）

---

## ✅ 预防措施

1. **定期备份**
```bash
# 添加定时任务
crontab -e
# 每天凌晨 2 点备份
0 2 * * * /opt/emby-cdn-preheat/backup.sh
```

2. **监控服务**
```bash
# 健康检查脚本（见 DEPLOY.md）
*/5 * * * * /opt/emby-cdn-preheat/health-check.sh
```

3. **定期更新**
```bash
# 每周检查更新
cd /opt/emby-cdn-preheat
git pull
docker compose pull
docker compose up -d
```

4. **日志清理**
```bash
# 定期清理旧日志
0 2 * * * /opt/emby-cdn-preheat/clean-logs.sh
```
