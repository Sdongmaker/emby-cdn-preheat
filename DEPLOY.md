# 生产环境部署指南

本指南介绍如何在生产服务器上部署 Emby CDN 预热服务。

## 快速部署

### 1. 拉取代码到服务器

```bash
# 克隆仓库到 /opt 目录
cd /opt
git clone https://github.com/Sdongmaker/emby-cdn-preheat.git
cd emby-cdn-preheat
```

### 2. 创建环境配置

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑配置文件
vim .env
```

**必须配置的参数**:

```bash
# Telegram Bot 配置（必填）
TELEGRAM_BOT_TOKEN=你的_Bot_Token
TELEGRAM_ADMIN_CHAT_IDS=你的_Chat_ID

# 腾讯云 API 配置（可选，如需 CDN 预热）
TENCENT_SECRET_ID=你的_Secret_ID
TENCENT_SECRET_KEY=你的_Secret_Key
CDN_DOMAIN=你的_CDN_域名
PREHEAT_ENABLED=true
```

### 3. 运行初始化脚本

```bash
# 赋予执行权限
chmod +x init.sh

# 运行初始化（创建目录、设置权限）
./init.sh
```

### 4. 启动服务

```bash
# 启动服务（使用预构建镜像）
docker compose up -d
# 如果使用旧版 Docker，使用: docker-compose up -d

# 查看日志
docker compose logs -f
```

> **提示**: 本项目提供了 `./dc` 快捷命令，自动兼容新旧版本：
> ```bash
> chmod +x dc
> ./dc up -d      # 等同于 docker compose up -d
> ./dc logs -f    # 等同于 docker compose logs -f
> ```

---

## 目录结构

部署后的目录结构：

```
/opt/emby-cdn-preheat/
├── .env                    # 环境配置（需创建）
├── docker-compose.yml      # Docker 编排配置
├── config.py              # 路径映射配置（可选修改）
├── data/                  # 数据目录（自动创建）
│   └── preheat_review.db # 审核记录数据库
├── logs/                  # 日志目录（自动创建）
│   └── webhook.log       # 服务日志
└── ...                    # 其他源码文件
```

**持久化数据**:
- `./data/` - 审核记录数据库
- `./logs/` - 服务日志
- `.env` - 环境配置

**挂载说明**:
- 所有数据都在当前目录下
- 容器重启数据不会丢失
- 备份只需备份 `data/` 和 `.env`

---

## 路径映射配置

如果需要自定义路径映射，编辑 `config.py`：

```python
# 1. Emby 容器路径 → 宿主机路径映射
EMBY_CONTAINER_MAPPINGS = {
    "/media/": "/media/",
}

# 2. STRM 文件内容路径 → 宿主机路径映射（可选）
STRM_MOUNT_MAPPINGS = {
    # "smb://nas/media/": "/mnt/nas/media/",
}

# 3. 宿主机路径 → CDN URL 映射
CDN_URL_MAPPINGS = {
    "/media/": "https://your-cdn-domain.com/",
}
```

**注意**: 如果修改了 `config.py`，需要重建镜像：

```bash
# 方案 1: 本地构建镜像
docker-compose down
docker-compose build
docker-compose up -d

# 方案 2: 挂载配置文件（推荐）
# 在 docker-compose.yml 中添加:
# volumes:
#   - ./config.py:/app/config.py:ro
```

---

## 媒体目录挂载

根据你的 Emby 媒体文件位置，修改 `docker-compose.yml`：

```yaml
volumes:
  # 示例 1: 单个媒体目录
  - /media:/media:ro

  # 示例 2: 多个媒体目录
  - /mnt/movies:/mnt/movies:ro
  - /mnt/series:/mnt/series:ro

  # 示例 3: NAS 挂载目录
  - /mnt/nas/media:/mnt/nas/media:ro
```

**重要提示**:
- 容器内路径必须与 `config.py` 中的路径映射一致
- 使用 `:ro` 只读挂载，防止误操作
- 确保容器有读取 STRM 文件的权限

---

## 服务管理

### 启动服务

```bash
docker compose up -d
# 或使用快捷命令: ./dc up -d
```

### 停止服务

```bash
docker compose down
# 或: ./dc down
```

### 重启服务

```bash
docker compose restart
# 或: ./dc restart
```

### 查看日志

```bash
# 实时日志
docker compose logs -f
# 或: ./dc logs -f

# 最近 100 行
docker compose logs --tail=100

# 查看日志文件
tail -f logs/webhook.log
```

### 查看状态

```bash
# 容器状态
docker compose ps
# 或: ./dc ps

# 健康检查
curl http://localhost:8899/

# 进入容器
docker compose exec emby-cdn-preheat bash
```

### 更新服务

```bash
# 拉取最新代码
git pull origin main

# 拉取最新镜像
docker compose pull

# 重启服务
docker compose up -d
```

> **关于 docker-compose vs docker compose**:
> - 新版 Docker (>= 2020): 使用 `docker compose` (带空格)
> - 旧版 Docker: 使用 `docker-compose` (带连字符)
> - 本项目的脚本自动兼容两种方式

---

## Emby Webhook 配置

在 Emby 中配置 Webhook：

1. 进入 **插件** → **Webhook**
2. 添加新的 Webhook
3. 配置:
   - **URL**: `http://服务器IP:8899/emby`
   - **事件**: 选择 `Item Added` 或 `Library New`
   - **媒体类型**: `Movies` 和 `Episodes`
   - **请求内容类型**: `application/json`

---

## 网络配置

### 防火墙规则

```bash
# 开放 8899 端口（如需外部访问）
firewall-cmd --permanent --add-port=8899/tcp
firewall-cmd --reload

# 或使用 ufw
ufw allow 8899/tcp
```

### 反向代理（可选）

如果使用 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name emby-cdn-preheat.example.com;

    location / {
        proxy_pass http://localhost:8899;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 备份和恢复

### 备份

```bash
# 创建备份目录
mkdir -p /opt/backups/emby-cdn-preheat

# 备份数据和配置
tar -czf /opt/backups/emby-cdn-preheat/backup-$(date +%Y%m%d_%H%M%S).tar.gz \
    data/ .env

# 或使用脚本
./backup.sh
```

### 恢复

```bash
# 停止服务
docker-compose down

# 解压备份
tar -xzf /opt/backups/emby-cdn-preheat/backup-20260122_120000.tar.gz

# 启动服务
docker-compose up -d
```

---

## 监控和告警

### 日志监控

```bash
# 监控错误日志
tail -f logs/webhook.log | grep ERROR

# 监控批量推送
tail -f logs/webhook.log | grep "批量\|队列"

# 监控 CDN 预热
tail -f logs/webhook.log | grep "预热"
```

### 健康检查

```bash
# 创建健康检查脚本
cat > /opt/emby-cdn-preheat/health-check.sh << 'EOF'
#!/bin/bash
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8899/)
if [ "$RESPONSE" != "200" ]; then
    echo "Service is down! HTTP $RESPONSE"
    # 发送告警（可选）
    # curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
    #     -d "chat_id=$CHAT_ID" \
    #     -d "text=Emby CDN Preheat Service is down!"
    exit 1
fi
echo "Service is healthy"
EOF

chmod +x /opt/emby-cdn-preheat/health-check.sh

# 添加到 crontab（每 5 分钟检查一次）
# */5 * * * * /opt/emby-cdn-preheat/health-check.sh
```

---

## 性能优化

### 1. 调整批量推送参数

根据使用场景调整 `.env` 中的参数：

```bash
# 大量媒体导入场景
BATCH_PUSH_INTERVAL=60      # 更长间隔
BATCH_PUSH_SIZE=20          # 更大批次
MAX_ITEMS_PER_MESSAGE=10    # 更多条目

# 实时响应场景
BATCH_PUSH_INTERVAL=10      # 更短间隔
BATCH_PUSH_SIZE=5           # 更小批次
MAX_ITEMS_PER_MESSAGE=5     # 标准条目
```

### 2. 日志清理

```bash
# 创建日志清理脚本
cat > /opt/emby-cdn-preheat/clean-logs.sh << 'EOF'
#!/bin/bash
# 保留最近 7 天的日志
find /opt/emby-cdn-preheat/logs -name "*.log" -mtime +7 -delete
echo "Old logs cleaned"
EOF

chmod +x /opt/emby-cdn-preheat/clean-logs.sh

# 添加到 crontab（每天凌晨 2 点执行）
# 0 2 * * * /opt/emby-cdn-preheat/clean-logs.sh
```

---

## 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker-compose logs

# 检查端口占用
netstat -tlnp | grep 8899

# 检查目录权限
ls -la data/ logs/

# 重建容器
docker-compose down
docker-compose up -d --force-recreate
```

### 数据库权限错误

```bash
# 运行修复脚本
./fix-permissions.sh

# 手动修复
chmod 755 data/ logs/
docker-compose restart
```

### Telegram Bot 无响应

```bash
# 检查配置
grep TELEGRAM .env

# 测试网络
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe

# 查看日志
docker-compose logs | grep Telegram
```

---

## 安全建议

1. **保护环境变量**:
   ```bash
   chmod 600 .env
   ```

2. **限制网络访问**:
   - 只允许 Emby 服务器访问 8899 端口
   - 使用防火墙规则限制源 IP

3. **定期更新**:
   ```bash
   # 每周检查更新
   cd /opt/emby-cdn-preheat
   git pull
   docker-compose pull
   docker-compose up -d
   ```

4. **备份策略**:
   - 每天自动备份数据库
   - 保留最近 7 天的备份
   - 异地备份重要数据

---

## 常见问题

### Q: 如何修改端口？

A: 修改 `docker-compose.yml` 和 `.env`:

```yaml
ports:
  - "8899:8899"  # 改为 "新端口:8899"
```

```bash
SERVER_PORT=8899  # 保持不变（容器内部端口）
```

### Q: 如何查看 Telegram Chat ID？

A: 给 [@userinfobot](https://t.me/userinfobot) 发送任意消息，它会返回你的 Chat ID。

### Q: 如何测试配置是否正确？

A: 运行测试脚本:

```bash
python test_database.py  # 测试数据库
python test_batch_push.py single  # 测试 Webhook
```

---

## 完整部署示例

```bash
# 1. 克隆代码
cd /opt
git clone https://github.com/Sdongmaker/emby-cdn-preheat.git
cd emby-cdn-preheat

# 2. 配置环境
cp .env.example .env
vim .env  # 配置必要参数

# 3. 初始化
chmod +x init.sh
./init.sh

# 4. 启动服务
docker-compose up -d

# 5. 查看日志
docker-compose logs -f

# 6. 访问测试
curl http://localhost:8899/

# 7. 配置 Emby Webhook
# 在 Emby 中配置 Webhook URL: http://服务器IP:8899/emby

# 完成！
```

---

## 相关链接

- [项目文档](./README.md)
- [Telegram Bot 配置指南](./TELEGRAM_SETUP.md)
- [批量推送功能说明](./BATCH_PUSH.md)
- [数据库权限问题修复](./DATABASE_FIX.md)
- [GitHub 仓库](https://github.com/Sdongmaker/emby-cdn-preheat)
- [问题反馈](https://github.com/Sdongmaker/emby-cdn-preheat/issues)
