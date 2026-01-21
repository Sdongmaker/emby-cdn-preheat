# 快速开始指南

3 步完成部署！

## 📦 方式一：自动部署（推荐）

```bash
# 1. 克隆项目
cd /opt
git clone https://github.com/Sdongmaker/emby-cdn-preheat.git
cd emby-cdn-preheat

# 2. 运行初始化脚本（自动创建目录、检查环境、配置文件）
chmod +x init.sh
./init.sh

# 3. 完成！服务已启动
# 访问: http://localhost:8899/
```

---

## 🛠️ 方式二：手动部署

```bash
# 1. 克隆项目
cd /opt
git clone https://github.com/Sdongmaker/emby-cdn-preheat.git
cd emby-cdn-preheat

# 2. 创建配置
cp .env.example .env
vim .env  # 配置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_ADMIN_CHAT_IDS

# 3. 创建目录
mkdir -p data logs

# 4. 启动服务
docker-compose up -d

# 5. 查看日志
docker-compose logs -f
```

---

## ⚙️ 必要配置

编辑 `.env` 文件，配置以下参数：

```bash
# Telegram Bot 配置（必填）
TELEGRAM_BOT_TOKEN=你的_Bot_Token        # 从 @BotFather 获取
TELEGRAM_ADMIN_CHAT_IDS=你的_Chat_ID     # 从 @userinfobot 获取

# CDN 配置（可选）
TENCENT_SECRET_ID=你的_Secret_ID
TENCENT_SECRET_KEY=你的_Secret_Key
PREHEAT_ENABLED=true
```

### 如何获取 Telegram 配置？

1. **Bot Token**:
   - 给 [@BotFather](https://t.me/BotFather) 发送 `/newbot`
   - 按提示创建 Bot
   - 获得 Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

2. **Chat ID**:
   - 给 [@userinfobot](https://t.me/userinfobot) 发送任意消息
   - 获得 Chat ID（格式：`123456789`）

---

## 🔗 配置 Emby Webhook

在 Emby 控制台中：

1. **插件** → **Webhook** → **添加 Webhook**

2. 配置:
   - **URL**: `http://服务器IP:8899/emby`
   - **事件**: 选择 `Item Added`
   - **媒体类型**: `Movies` 和 `Episodes`
   - **请求内容类型**: `application/json`

3. 保存并测试

---

## 📊 验证部署

```bash
# 1. 检查容器状态
docker-compose ps
# 应显示: emby-cdn-preheat (Up, healthy)

# 2. 测试健康检查
curl http://localhost:8899/
# 应返回: {"status": "running", ...}

# 3. 查看日志
docker-compose logs -f
# 应看到: "Telegram Bot 启动成功"

# 4. 测试 Webhook
python test_batch_push.py single
```

---

## 🎯 目录结构

部署后的目录：

```
/opt/emby-cdn-preheat/
├── .env                    # 环境配置（你创建的）
├── docker-compose.yml      # Docker 配置
├── data/                   # 数据目录（自动创建）
│   └── preheat_review.db  # 审核记录数据库
└── logs/                   # 日志目录（自动创建）
    └── webhook.log        # 服务日志
```

**所有数据都在当前目录，备份只需备份这个文件夹！**

---

## 📝 常用命令

```bash
# 启动服务
docker compose up -d
# 或使用快捷命令: ./dc up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f

# 查看状态
docker compose ps

# 更新服务
git pull
docker compose pull
docker compose up -d

# 备份数据
./backup.sh
```

> **提示**: 如果报错 `docker-compose: command not found`，使用 `docker compose`（带空格）代替

---

## 🆘 常见问题

### 容器无法启动？

```bash
# 查看详细日志
docker compose logs

# 检查端口占用
netstat -tlnp | grep 8899

# 重建容器
docker compose down
docker compose up -d --force-recreate
```

### `docker-compose: command not found` 错误？

新版 Docker 使用 `docker compose`（带空格）而不是 `docker-compose`（带连字符）。

**解决方法**:
```bash
# 方式 1: 使用新命令（推荐）
docker compose up -d

# 方式 2: 使用项目提供的快捷命令
chmod +x dc
./dc up -d

# 方式 3: 安装旧版 docker-compose（不推荐）
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 数据库权限错误？

```bash
# 运行修复脚本
./fix-permissions.sh

# 或手动修复
chmod 755 data/ logs/
docker compose restart
```

### Telegram Bot 无响应？

```bash
# 检查配置
grep TELEGRAM .env

# 查看日志
docker compose logs | grep Telegram
```

---

## 📚 完整文档

- [完整部署指南](./DEPLOY.md) - 生产环境部署详细说明
- [项目文档](./README.md) - 功能说明和使用指南
- [Telegram Bot 配置](./TELEGRAM_SETUP.md) - Telegram 详细配置
- [批量推送说明](./BATCH_PUSH.md) - 批量推送功能介绍
- [数据库问题修复](./DATABASE_FIX.md) - 数据库权限问题

---

## 🎉 完成！

现在你可以：

1. ✅ 在 Emby 中添加新媒体
2. ✅ 在 Telegram 收到审核通知
3. ✅ 点击按钮批准或拒绝
4. ✅ 自动触发 CDN 预热

**项目地址**: https://github.com/Sdongmaker/emby-cdn-preheat

**问题反馈**: https://github.com/Sdongmaker/emby-cdn-preheat/issues
