# Emby CDN 预热服务

[![Docker Build](https://github.com/Sdongmaker/emby-cdn-preheat/actions/workflows/docker-build.yml/badge.svg)](https://github.com/Sdongmaker/emby-cdn-preheat/actions/workflows/docker-build.yml)
[![Docker Hub](https://img.shields.io/docker/v/tdck/emby-cdn-preheat?label=Docker%20Hub)](https://hub.docker.com/r/tdck/emby-cdn-preheat)
[![Docker Pulls](https://img.shields.io/docker/pulls/tdck/emby-cdn-preheat)](https://hub.docker.com/r/tdck/emby-cdn-preheat)

自动监听 Emby 媒体库新增内容，通过 Telegram 人工审核后提交到腾讯云 CDN 进行预热。

---

## 🚀 快速开始

```bash
cd /opt
git clone https://github.com/Sdongmaker/emby-cdn-preheat.git
cd emby-cdn-preheat
chmod +x init.sh && ./init.sh
```

详细说明: [QUICKSTART.md](./QUICKSTART.md) | [完整部署指南](./DEPLOY.md)

---

## 功能特性

- ✅ 接收 Emby Webhook 事件
- ✅ 自动识别新入库的电影和剧集
- ✅ 支持 Emby 容器路径到宿主机路径的映射
- ✅ 自动识别和处理 STRM 文件
- ✅ 自动转换路径为 CDN URL
- ✅ Telegram Bot 人工审核机制
- ✅ 提交到腾讯云 CDN 预热
- ✅ 审核记录和统计功能

## 快速开始（推荐 Docker 部署）

> 💡 **生产环境部署**: 完整的部署指南请参考 [DEPLOY.md](./DEPLOY.md)

### 方式一：使用 Docker Hub 预构建镜像（推荐）

#### 1. 克隆项目并初始化

```bash
# 克隆到服务器（推荐路径：/opt）
cd /opt
git clone https://github.com/Sdongmaker/emby-cdn-preheat.git
cd emby-cdn-preheat

# 运行初始化脚本
chmod +x init.sh
./init.sh
```

#### 2. 配置环境变量

编辑 `.env` 文件配置必要参数：

```bash
vim .env
```

**必填参数**:
- `TELEGRAM_BOT_TOKEN` - Telegram Bot Token
- `TELEGRAM_ADMIN_CHAT_IDS` - 管理员 Chat IDs

#### 3. 启动服务

```bash
docker-compose up -d
```

---

### 方式二：手动配置（自定义部署）

#### 1. 准备配置文件

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  emby-cdn-preheat:
    # 使用 Docker Hub 镜像
    image: tdck/emby-cdn-preheat:latest
    container_name: emby-cdn-preheat
    restart: unless-stopped
    ports:
      - "8899:8899"
    volumes:
      # 日志目录
      - ./logs:/app/logs
      # 数据库文件
      - ./preheat_review.db:/app/preheat_review.db
      # 媒体文件目录（只读，用于读取 STRM 文件）
      - /your/media/path:/media:ro
    environment:
      # 服务器配置
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8899
      - LOG_LEVEL=INFO

      # 腾讯云 CDN API 配置
      - TENCENT_SECRET_ID=your_secret_id
      - TENCENT_SECRET_KEY=your_secret_key
      - CDN_DOMAIN=your-cdn-domain.com
      - PREHEAT_ENABLED=false
      - PREHEAT_BATCH_SIZE=10

      # Telegram Bot 配置（必填）
      - TELEGRAM_REVIEW_ENABLED=true
      - TELEGRAM_BOT_TOKEN=your_telegram_bot_token
      - TELEGRAM_ADMIN_CHAT_IDS=123456789,987654321
      - REVIEW_TIMEOUT_SECONDS=86400
      - AUTO_APPROVE_IF_NO_REVIEW=false

      # 智能 URL 匹配（可选）
      - ENABLE_SMART_URL_MATCHING=false
      - SMART_MATCH_KEYWORDS=剧集,电影
      - SMART_MATCH_CDN_BASE=https://your-cdn-domain.com/
    networks:
      - emby-network

networks:
  emby-network:
    external: true
    # 如果没有外部网络，删除 external: true 行
```

> **重要提示**:
> - 请根据实际情况修改 `volumes` 中的媒体目录路径
> - 需要配置 Telegram Bot Token 和管理员 Chat IDs，参考 [Telegram Bot 设置指南](./TELEGRAM_SETUP.md)
> - 如需启用 CDN 预热，请设置 `PREHEAT_ENABLED=true` 并配置腾讯云凭证

#### 2. 配置路径映射

创建自定义配置文件 `config.py`（或使用默认配置）：

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

如果需要自定义路径映射，将 `config.py` 挂载到容器：

```yaml
volumes:
  - ./config.py:/app/config.py
```

#### 3. 启动服务

```bash
docker-compose up -d
```

#### 4. 查看日志

```bash
docker-compose logs -f
```

#### 5. 查看运行状态

访问 `http://localhost:8899/` 进行健康检查。

---

### 方式三：本地源码运行

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置服务器端口、腾讯云凭证等。

#### 3. 配置路径映射

编辑 `config.py`，配置三层路径映射关系。路径映射支持**最长匹配优先**原则，确保更具体的路径优先匹配。

##### 3.1 Emby 容器路径映射 (EMBY_CONTAINER_MAPPINGS)

将 Emby 容器内的路径映射到宿主机实际路径：

```python
EMBY_CONTAINER_MAPPINGS = {
    # Emby 容器路径 → 宿主机路径
    "/media/剧集/": "/mnt/storage/series/",
    "/media/电影/": "/mnt/storage/movies/",
    "/strm/data5/": "/mnt/strm/data5/",
}
```

> 如果 Emby 运行在 Docker 容器中，容器内看到的路径与宿主机不同，需要配置此映射。
> 如果 Emby 直接运行在宿主机，此映射可以为空或配置为相同路径。

##### 3.2 STRM 文件路径映射 (STRM_MOUNT_MAPPINGS)

如果 STRM 文件内容中的路径与宿主机路径不同，需要配置此映射：

```python
STRM_MOUNT_MAPPINGS = {
    # STRM 文件内容路径 → 宿主机路径
    "smb://nas/media/": "/mnt/nas/media/",
    "nfs://storage/": "/mnt/nfs/",
    "/remote/path/": "/mnt/local/path/",
}
```

> STRM 文件通常包含网络路径（如 SMB、NFS）或远程路径。
> 如果你的宿主机已经挂载了这些网络位置，配置此映射来指向本地挂载点。
> 如果 STRM 文件内容已经是正确的宿主机路径，此映射可以为空。

##### 3.3 CDN URL 映射 (CDN_URL_MAPPINGS)

将宿主机路径转换为 CDN 访问 URL：

```python
CDN_URL_MAPPINGS = {
    # 宿主机路径 → CDN URL
    "/mnt/storage/series/": "https://cdn.example.com/series/",
    "/mnt/storage/movies/": "https://cdn.example.com/movies/",
    "/mnt/nas/media/": "https://cdn.example.com/nas/",
}
```

> 配置你的 CDN 域名和路径前缀，用于后续 CDN 预热。

##### 路径映射工作流程

```
Emby 容器路径
    ↓ (EMBY_CONTAINER_MAPPINGS)
宿主机路径
    ↓ (如果是 .strm 文件)
读取 STRM 文件内容
    ↓ (STRM_MOUNT_MAPPINGS)
真实媒体文件路径
    ↓ (CDN_URL_MAPPINGS)
CDN URL
```

##### 配置示例

假设你的环境配置如下：

1. Emby 运行在 Docker 中，容器内路径 `/media/剧集/` 挂载到宿主机 `/data/media/series/`
2. 有些视频是 STRM 文件，内容指向 `smb://192.168.1.100/share/videos/xxx.mkv`
3. SMB 共享已挂载到宿主机 `/mnt/smb/videos/`
4. CDN 域名是 `https://cdn.example.com`，路径前缀是 `/videos/`

配置如下：

```python
EMBY_CONTAINER_MAPPINGS = {
    "/media/剧集/": "/data/media/series/",
}

STRM_MOUNT_MAPPINGS = {
    "smb://192.168.1.100/share/videos/": "/mnt/smb/videos/",
}

CDN_URL_MAPPINGS = {
    "/data/media/series/": "https://cdn.example.com/series/",
    "/mnt/smb/videos/": "https://cdn.example.com/videos/",
}
```

处理流程：
- Emby 报告路径：`/media/剧集/美剧/show.strm`
- 映射到宿主机：`/data/media/series/美剧/show.strm`
- 读取 STRM 内容：`smb://192.168.1.100/share/videos/show.mkv`
- 映射 STRM 路径：`/mnt/smb/videos/show.mkv`
- 生成 CDN URL：`https://cdn.example.com/videos/show.mkv`

#### 4. 启动服务

```bash
python webhook_server.py
```

服务将在 `http://0.0.0.0:8899` 启动。

---

### 方式四：本地构建 Docker 镜像

如果你需要修改代码或自定义构建：

#### 1. 克隆仓库

```bash
git clone https://github.com/Sdongmaker/emby-cdn-preheat.git
cd emby-cdn-preheat
```

#### 2. 修改 docker-compose.yml

将 `image: tdck/emby-cdn-preheat:latest` 改为：

```yaml
build:
  context: .
  dockerfile: Dockerfile
```

#### 3. 构建并启动

```bash
docker-compose up -d --build
```

---

## Docker 镜像版本说明

| 标签 | 说明 | 推荐场景 |
|------|------|---------|
| `latest` | 最新稳定版本 | 生产环境 |
| `v1.0.0` | 特定版本号 | 需要版本锁定 |
| `main-abc1234` | 最新提交的开发版 | 测试新功能 |

**支持的架构**:
- `linux/amd64` (x86_64 服务器)
- `linux/arm64` (ARM 服务器、树莓派等)

---

## Telegram Bot 配置

本项目使用 Telegram Bot 进行人工审核，管理员可以批准或拒绝 CDN 预热请求。

详细配置步骤请参考: [Telegram Bot 设置指南](./TELEGRAM_SETUP.md)

**Bot 命令**:
- `/stats` - 查看审核统计信息
- `/pending` - 查看待审核列表

### 批量推送功能

为避免触发 Telegram API 速率限制，本项目实现了**批量推送机制**：将短时间内的多个审核请求合并成一条消息发送。

**特性**:
- ✅ 避免触发 Telegram 速率限制（每秒 30 条，每分钟 20 条/群组）
- ✅ 提升批量导入场景的用户体验
- ✅ 智能触发：时间阈值（30秒）或数量阈值（10条）
- ✅ 自动分批发送（单条消息最多 5 个媒体）

**配置参数**:
```bash
BATCH_PUSH_INTERVAL=30      # 批量推送时间间隔（秒）
BATCH_PUSH_SIZE=10          # 队列达到此数量立即推送
MAX_ITEMS_PER_MESSAGE=5     # 单条消息最多包含的媒体数量
```

详细说明请参考: [批量推送功能文档](./BATCH_PUSH.md)

## Emby Webhook 配置

### 1. 安装 Emby Webhook 插件

在 Emby 控制台中：
1. 进入 **插件** -> **目录**
2. 搜索并安装 **Webhook** 插件
3. 重启 Emby 服务器

### 2. 配置 Webhook

1. 进入 **插件** -> **Webhook**
2. 添加新的 Webhook
3. 设置：
   - **Webhook URL**: `http://你的服务器IP:8899/emby` 或 `http://你的服务器IP:8899/webhook/emby`
   - **事件**: 选择 `Item Added` 或 `Library New`
   - **媒体类型**: 选择 `Movies` 和 `Episodes`
   - **请求内容类型**: 选择 `application/json`

### 测试

在 Emby 中添加一个新视频，检查服务日志：

```bash
tail -f webhook.log
```

应该能看到类似以下的日志：

```
2025-12-18 10:00:00 - __main__ - INFO - 收到新媒体: 电影名称 (Movie)
2025-12-18 10:00:00 - __main__ - INFO - 文件路径: /media/电影/...
```

## API 端点

### GET /

健康检查端点，返回服务状态。

### POST /emby

接收 Emby Webhook 事件的端点（推荐使用）。

### POST /webhook/emby

接收 Emby Webhook 事件的端点（兼容旧版配置）。

## 日志

日志文件：`webhook.log`

日志包含：
- 接收到的 Webhook 事件
- 媒体项目信息
- 处理结果和错误信息

## 开发路线图

- [x] 实现本地路径到 CDN URL 的自动转换
- [x] 支持容器路径映射
- [x] 支持 STRM 文件解析
- [x] 集成腾讯云 CDN API
- [x] Telegram Bot 人工审核机制
- [x] 实现预热队列和批量提交
- [x] 审核记录和统计功能
- [x] Docker Hub 自动构建和发布
- [x] 多架构支持 (amd64/arm64)
- [ ] 添加文件大小过滤
- [ ] 添加预热状态实时跟踪
- [ ] Web 管理界面
- [ ] 支持更多 CDN 服务商

## 更新日志

### v1.0.0 (2026-01-22)
- 🎉 首个稳定版本发布
- ✅ 完整的 Telegram Bot 审核机制
- ✅ 腾讯云 CDN 预热集成
- ✅ STRM 文件完整支持
- ✅ Docker Hub 自动构建
- ✅ 多架构支持 (amd64/arm64)

---

## 故障排查

遇到问题？查看 [故障排查指南](./TROUBLESHOOTING.md)

**快速链接**:
- [`docker-compose: command not found`](./TROUBLESHOOTING.md#-docker-compose-command-not-found)
- [数据库权限错误](./TROUBLESHOOTING.md#-sqlite3operationalerror-unable-to-open-database-file)
- [Telegram Bot 无响应](./TROUBLESHOOTING.md#-telegram-bot-无响应)
- [容器无法启动](./TROUBLESHOOTING.md#-容器无法启动)

---

## 常见问题

**Q: 报错 `docker-compose: command not found`？**

A: 新版 Docker 使用 `docker compose`（带空格）而不是 `docker-compose`。

```bash
# 使用新命令
docker compose up -d

# 或使用项目提供的快捷命令
chmod +x dc && ./dc up -d
```

详细说明: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#-docker-compose-command-not-found)

**Q: 如何获取 Docker 镜像？**

A: 使用 Docker Hub 预构建镜像：
```bash
docker pull tdck/emby-cdn-preheat:latest
```

**Q: 如何更新到最新版本？**

A:
```bash
docker-compose pull
docker-compose up -d
```

**Q: Webhook 无法接收到数据？**

A: 检查：
1. 防火墙是否开放 8899 端口
2. Emby Webhook 配置的 URL 是否正确
3. 网络是否可达

**Q: 如何修改监听端口？**

A: 修改 `.env` 文件中的 `SERVER_PORT` 或直接修改 `webhook_server.py` 中的端口号。

**Q: 路径映射不工作？**

A: 检查：
1. `config.py` 中的路径映射配置是否正确
2. 路径前缀必须完全匹配（包括开头的 `/` 和结尾的 `/`）
3. 查看日志中的路径映射详细信息
4. 映射按最长匹配优先，更具体的路径应该配置更长的前缀

**Q: STRM 文件无法读取？**

A: 检查：
1. webhook_server.py 运行的用户是否有读取 STRM 文件的权限
2. EMBY_CONTAINER_MAPPINGS 是否正确映射到宿主机路径
3. 宿主机路径是否确实存在该文件
4. 查看日志中的详细错误信息

**Q: 如何知道路径映射是否正确？**

A: 查看日志文件（Docker 部署：`./logs/webhook.log`），每次处理媒体时会详细记录：
- 原始 Emby 路径
- 容器映射后的路径
- 是否为 STRM 文件及其内容
- STRM 路径映射结果
- 最终的 CDN URL

**Q: 如何在 Docker 中查看日志？**

A:
```bash
# 查看实时日志
docker-compose logs -f

# 查看日志文件
tail -f ./logs/webhook.log
```

**Q: 遇到数据库权限错误怎么办？**

A: 如果看到 `sqlite3.OperationalError: unable to open database file` 错误：

```bash
# 1. 停止服务
docker-compose down

# 2. 创建必要的目录
mkdir -p data logs

# 3. 设置权限
chmod 755 data logs

# 4. 重启服务
docker-compose up -d
```

详细说明请参考: [数据库权限问题修复文档](./DATABASE_FIX.md)

**Q: 为什么需要 Telegram Bot？**

A: Telegram Bot 提供人工审核机制，可以：
- 在预热前人工检查媒体内容
- 避免错误的预热请求
- 提供审核历史记录
- 实时通知和反馈

**Q: 可以跳过 Telegram 审核吗？**

A: 可以，设置环境变量：
```yaml
- TELEGRAM_REVIEW_ENABLED=false
- AUTO_APPROVE_IF_NO_REVIEW=true
```
但不推荐，建议至少保留审核机制以防止错误预热。

---

## 相关链接

- [GitHub 仓库](https://github.com/Sdongmaker/emby-cdn-preheat)
- [Docker Hub](https://hub.docker.com/r/tdck/emby-cdn-preheat)
- [问题反馈](https://github.com/Sdongmaker/emby-cdn-preheat/issues)
- [Telegram Bot 设置指南](./TELEGRAM_SETUP.md)

---

## 许可

MIT License
