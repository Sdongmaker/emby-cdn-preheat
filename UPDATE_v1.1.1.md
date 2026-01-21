# v1.1.1 更新说明

## 🎯 本次更新内容

### 1. ✅ Telegram 批量推送消息显示完整 CDN URL

**问题**：之前批量推送消息中只显示了媒体名称和 ID，没有显示最终要预热的 CDN URL。

**修改前**：
```
🎬 CDN 预热审核请求（共 1 项）

1. 🎬 风之谷 (ID: 1)

💡 使用下方按钮批准或拒绝每个项目
```

**修改后**：
```
🎬 CDN 预热审核请求（共 1 项）

1. 🎬 哈尔的移动城堡
   📹 文件类型: MP4
   📂 文件: 哈尔的移动城堡.Howl's Moving Castle.2004.2160p.mp4
   🔗 预热URL: https://your-cdn-domain.com/media/近期添加/动画电影/哈尔的移动城堡 (2004) {tmdbid=4935}/哈尔的移动城堡.Howl's Moving Castle.2004.2160p.mp4
   🆔 ID: 1

💡 使用下方按钮批准或拒绝每个项目
📝 批准后将立即提交 CDN 预热
ℹ️ 使用 /detail ID 查看完整路径信息
```

✅ **改进**：
- 显示完整的 CDN URL，可直接复制
- 显示文件类型（MP4、MKV 等）
- 显示实际文件名
- 更容易判断路径是否正确
- 提升审核体验
- 明确提示"批准后将立即提交 CDN 预热"

**修改文件**：
- `telegram_bot.py` (批量推送消息格式)

---

### 2. 🐛 修复 STRM 文件 CDN URL 错误

**问题**：处理 STRM 文件时，智能匹配使用了 `.strm` 文件路径而不是实际的媒体文件路径，导致生成的 CDN URL 是 `.strm` 而不是 `.mp4/.mkv` 等实际文件。

**示例**：
- Emby 路径：`/media/近期添加/哈尔的移动城堡.strm`
- 实际文件：`/mnt/media/近期添加/哈尔的移动城堡.mp4`
- **错误的 CDN URL**：`https://cdn.com/.../哈尔的移动城堡.strm` ❌
- **正确的 CDN URL**：`https://cdn.com/.../哈尔的移动城堡.mp4` ✅

**修复**：智能匹配现在使用 STRM 解析后的实际文件路径，而不是 STRM 文件本身的路径。

**修改文件**：
- `webhook_server.py` (第 295 行，智能匹配逻辑)

---

### 3. ✅ 新增路径黑名单功能

**需求**：某些路径不需要进行 CDN 预热，需要一个黑名单机制跳过这些路径。

**功能说明**：
- 配置黑名单路径列表
- 匹配到黑名单路径的媒体将被跳过，不会创建预热请求
- 支持环境变量配置或代码配置

**配置方式 1：通过环境变量**

在 `.env` 文件中配置：
```bash
# 多个路径用逗号分隔
PREHEAT_BLACKLIST_PATHS=/media/近期添加/,/media/test/,/media/temp/
```

在 `docker-compose.yml` 中配置：
```yaml
environment:
  - PREHEAT_BLACKLIST_PATHS=/media/近期添加/,/media/test/
```

**配置方式 2：通过代码配置**

编辑 `config.py`：
```python
PREHEAT_BLACKLIST_PATHS = [
    "/media/近期添加/",      # 跳过"近期添加"目录
    "/media/test/",          # 跳过测试目录
    "/media/temp/",          # 跳过临时目录
]
```

**日志示例**：
```
收到新媒体: 风之谷 (Movie)
Emby 路径: /media/近期添加/动画电影/风之谷 (1984) {tmdbid=81}/风之谷.mkv
⛔ 路径在黑名单中，跳过预热: /media/近期添加/
媒体项目处理完成: 风之谷 (已跳过)
```

**修改文件**：
- `config.py` (新增 `PREHEAT_BLACKLIST_PATHS` 配置)
- `webhook_server.py` (第 344-359 行，添加黑名单检查逻辑)
- `.env.example` (添加配置示例)

---

## 📦 升级步骤

### 方式 1：拉取最新代码（推荐）

```bash
cd /opt/emby-cdn-preheat

# 停止服务
docker compose down

# 备份数据（可选）
cp -r data data.backup.$(date +%Y%m%d_%H%M%S)
cp -r logs logs.backup.$(date +%Y%m%d_%H%M%S)

# 拉取最新代码
git pull origin main

# 重新构建镜像
docker compose build

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f
```

### 方式 2：使用 Docker Hub 镜像

```bash
cd /opt/emby-cdn-preheat

# 停止服务
docker compose down

# 拉取最新镜像
docker compose pull

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f
```

---

## ⚙️ 配置黑名单（可选）

如果你需要跳过某些路径的预热，可以配置黑名单：

### 1. 编辑 `.env` 文件

```bash
vim .env
```

### 2. 添加或修改黑名单配置

```bash
# 添加这一行，多个路径用逗号分隔
PREHEAT_BLACKLIST_PATHS=/media/近期添加/,/media/test/
```

### 3. 重启服务

```bash
docker compose restart
```

### 4. 测试黑名单

向 Emby 添加一个黑名单路径中的媒体，检查日志：

```bash
docker compose logs -f | grep "路径在黑名单中"
```

应该看到类似输出：
```
⛔ 路径在黑名单中，跳过预热: /media/近期添加/
```

---

## 🧪 测试建议

### 测试 URL 显示

1. 使用测试脚本发送几个媒体：
   ```bash
   python3 test_emby_webhook.py http://104.36.21.247:8899/emby
   ```

2. 检查 Telegram 消息是否显示完整 URL

### 测试黑名单功能

1. 配置黑名单路径（如 `/media/test/`）

2. 使用测试脚本修改生成路径：
   ```python
   # 修改 generate_random_movie 函数
   "Path": f"/media/test/{movie_name} ({year})/{movie_name}{ext}",
   ```

3. 发送测试请求，检查是否被跳过

4. 查看日志确认：
   ```bash
   docker compose logs | grep "黑名单"
   ```

---

## 🔍 常见问题

### Q: 升级后 Telegram 消息还是不显示 URL？

A: 检查以下几点：
1. 确认服务已重启：`docker compose ps`
2. 检查容器版本：`docker compose logs | grep "服务启动"`
3. 清除旧数据测试：发送新的媒体请求

### Q: 黑名单不生效？

A: 检查：
1. 环境变量是否正确配置：`docker compose config | grep BLACKLIST`
2. 路径格式是否正确（需要完整路径，以 `/` 开头和结尾）
3. 查看日志确认黑名单已加载：`docker compose logs | grep "PREHEAT_BLACKLIST_PATHS"`

### Q: 如何查看当前黑名单配置？

A: 在容器中执行：
```bash
docker compose exec emby-cdn-preheat python -c "import config; print(config.PREHEAT_BLACKLIST_PATHS)"
```

---

## 📝 更新日志

- `2026-01-22` - v1.1.1 发布
  - ✅ Telegram 批量推送显示完整 CDN URL
  - ✅ 新增路径黑名单功能
  - ✅ 改进日志输出

---

## 🔗 相关文档

- [README.md](./README.md) - 项目文档
- [CHANGELOG.md](./CHANGELOG.md) - 完整更新日志
- [TELEGRAM_COMMANDS.md](./TELEGRAM_COMMANDS.md) - Telegram Bot 命令
- [OPTIMIZATION_SUMMARY.md](./OPTIMIZATION_SUMMARY.md) - v1.1.0 优化总结

---

**问题反馈**: https://github.com/Sdongmaker/emby-cdn-preheat/issues
