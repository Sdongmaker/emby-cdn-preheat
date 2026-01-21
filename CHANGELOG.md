# 更新日志

## v1.1.1 (2026-01-22) - URL 显示优化 & 黑名单功能

### ✨ 新增功能

- **路径黑名单**: 支持配置不需要预热的路径列表
  - 通过环境变量 `PREHEAT_BLACKLIST_PATHS` 配置
  - 匹配到黑名单路径的媒体将被跳过
  - 支持多个路径（逗号分隔）

### 🎨 改进

- **批量推送消息优化**: 显示完整的 CDN URL 而不是截断版本
  - 旧版本：`📎 .../文件名.mkv`
  - 新版本：`🔗 https://cdn.example.com/完整/路径/文件名.mkv`
  - 便于直接复制和验证 URL

### 📚 文档

- 新增 [UPDATE_v1.1.1.md](./UPDATE_v1.1.1.md) - 详细更新说明
- 更新 `.env.example` - 添加黑名单配置示例

---

## v1.1.0 (2026-01-22) - 批量推送优化

### ✨ 新增功能

- **批量推送消息优化**: 现在显示每个媒体的 CDN URL（文件名部分）
- **新增 `/detail` 命令**: 查看指定请求的完整详细信息
  - 完整的 CDN URL
  - Emby 路径
  - 宿主机路径
  - 审核状态和时间
  - 如果待审核，可直接在详情中批准/拒绝

### 🎨 改进

- **批量推送消息格式优化**:
  ```
  旧格式:
  1. 🎬 流浪地球2 (ID: 2)

  新格式:
  1. 🎬 流浪地球2
     📎 .../流浪地球2.mp4
     🆔 ID: 2
  ```

- **`/pending` 命令优化**: 显示 URL 预览（截断）
- **智能 URL 显示**:
  - 批量消息中显示文件名部分
  - 使用 `<code>` 标签便于复制
  - 可点击查看完整链接

### 🐛 修复

- 修复 `docker-compose` 命令兼容性问题
- 修复数据库权限问题
- 优化错误日志输出

### 📚 文档

- 新增完整的测试文档 ([TESTING.md](./TESTING.md))
- 新增故障排查指南 ([TROUBLESHOOTING.md](./TROUBLESHOOTING.md))
- 新增快速开始指南 ([QUICKSTART.md](./QUICKSTART.md))
- 新增完整部署指南 ([DEPLOY.md](./DEPLOY.md))

---

## v1.0.0 (2026-01-22) - 首个稳定版本

### ✨ 核心功能

- ✅ Emby Webhook 事件接收和处理
- ✅ 智能路径映射（三层转换）
- ✅ STRM 文件完整支持
- ✅ Telegram Bot 人工审核机制
- ✅ 批量推送功能（避免速率限制）
- ✅ 腾讯云 CDN 预热集成
- ✅ SQLite 数据库存储审核记录
- ✅ Docker 容器化部署
- ✅ 多架构支持 (amd64/arm64)

### 🎯 批量推送机制

- 时间阈值: 30 秒
- 数量阈值: 10 条
- 单条消息最多: 5 个媒体
- 自动合并推送到 Telegram

### 📝 Bot 命令

- `/stats` - 查看审核统计
- `/pending` - 查看待审核列表

### 🛠️ 部署工具

- `init.sh` - 一键初始化脚本
- `backup.sh` - 备份脚本
- `fix-permissions.sh` - 权限修复
- `dc` - Docker Compose 快捷命令

---

## 使用说明

### 查看详细信息

在 Telegram 中使用 `/detail` 命令查看完整信息：

```
/detail 123
```

**输出示例**:
```
⏳ 请求详情

🆔 请求 ID: 123
🎞 媒体名称: 流浪地球2
📂 类型: Movie
📊 状态: pending

📍 Emby 路径:
/media/电影/流浪地球2 (2023)/流浪地球2.mp4

💾 宿主机路径:
/media/电影/流浪地球2 (2023)/流浪地球2.mp4

🔗 CDN 预热 URL:
https://qiufeng.huaijiufu.com/电影/流浪地球2 (2023)/流浪地球2.mp4

⏰ 创建时间: 2026-01-22 10:30:00

[✅ 同意预热] [❌ 拒绝]
```

### 批量推送新格式

**旧版本**（v1.0.0）:
```
🎬 CDN 预热审核请求（共 5 项）

1. 🎬 流浪地球2 (ID: 2)
2. 🎬 教父 (ID: 3)
3. 📺 权力的游戏 S01E01 (ID: 4)
...

[✅ 流浪地球2] [❌]
[✅ 教父] [❌]
...
```

**新版本**（v1.1.0）:
```
🎬 CDN 预热审核请求（共 5 项）

1. 🎬 流浪地球2
   📎 .../流浪地球2.mp4
   🆔 ID: 2

2. 🎬 教父
   📎 .../教父.mkv
   🆔 ID: 3

3. 📺 权力的游戏 S01E01
   📎 .../权力的游戏 - S01E01 - 凛冬将至.mkv
   🆔 ID: 4

...

💡 使用下方按钮批准或拒绝每个项目
📝 点击 URL 可查看完整链接

[✅ 流浪地球2] [❌]
[✅ 教父] [❌]
...
```

---

## 升级指南

### 从 v1.0.0 升级到 v1.1.0

```bash
# 1. 停止服务
cd /opt/emby-cdn-preheat
docker compose down

# 2. 拉取最新代码
git pull origin main

# 3. 拉取最新镜像
docker compose pull

# 4. 启动服务
docker compose up -d

# 5. 查看日志
docker compose logs -f
```

**注意**:
- 数据库结构未变更，无需迁移
- 配置文件兼容，无需修改
- 旧的审核记录仍然可用

---

## 反馈

如有问题或建议，请访问:
- GitHub Issues: https://github.com/Sdongmaker/emby-cdn-preheat/issues
- 项目文档: https://github.com/Sdongmaker/emby-cdn-preheat
