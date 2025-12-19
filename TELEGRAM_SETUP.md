# Telegram Bot 审核功能使用指南

## 功能说明

Telegram Bot 审核功能允许你在 CDN 预热前，通过 Telegram 机器人进行人工审核。每当 Emby 添加新媒体时，系统会：

1. 解析媒体路径，生成 CDN URL
2. 将审核请求发送到 Telegram
3. 你可以点击按钮选择"✅ 同意预热"或"❌ 拒绝"
4. 只有被批准的 URL 才会进行 CDN 预热

## 设置步骤

### 第一步：创建 Telegram Bot

1. 在 Telegram 中搜索并打开 [@BotFather](https://t.me/BotFather)

2. 发送命令 `/newbot` 创建新机器人

3. 按提示输入机器人名称和用户名：
   ```
   BotFather: Alright, a new bot. How are we going to call it?
   You: CDN Preheat Review Bot

   BotFather: Good. Now let's choose a username for your bot.
   You: cdn_preheat_review_bot
   ```

4. 创建成功后，Bot Father 会返回你的 **Bot Token**，类似：
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

   ⚠️ **重要**: 请妥善保管这个 Token，不要泄露给他人！

### 第二步：获取你的 Chat ID

1. 在 Telegram 中搜索并打开 [@userinfobot](https://t.me/userinfobot)

2. 给它发送任意消息

3. Bot 会回复你的 Chat ID，类似：
   ```
   Id: 123456789
   ```

4. 如果需要多个管理员审核，重复此步骤获取所有管理员的 Chat ID

### 第三步：配置环境变量

在项目根目录创建 `.env` 文件（如果不存在），添加以下配置：

```bash
# Telegram Bot 配置
TELEGRAM_REVIEW_ENABLED=true
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ADMIN_CHAT_IDS=123456789,987654321

# 审核超时时间（秒），默认 24 小时
REVIEW_TIMEOUT_SECONDS=86400

# 如果未启用 Telegram 审核，是否自动批准
AUTO_APPROVE_IF_NO_REVIEW=false
```

**配置说明**：
- `TELEGRAM_REVIEW_ENABLED`: 是否启用 Telegram 审核（true/false）
- `TELEGRAM_BOT_TOKEN`: 从 BotFather 获取的 Token
- `TELEGRAM_ADMIN_CHAT_IDS`: 管理员 Chat ID，多个用逗号分隔
- `REVIEW_TIMEOUT_SECONDS`: 审核超时时间
- `AUTO_APPROVE_IF_NO_REVIEW`: 未启用审核时是否自动批准

### 第四步：安装依赖

```bash
pip install -r requirements.txt
```

### 第五步：启动服务

```bash
python webhook_server.py
```

启动成功后，你会看到：
```
================================================================================
启动 Emby CDN 预热服务
================================================================================
Telegram 审核已启用，正在初始化 Bot...
✅ Telegram Bot 初始化成功
管理员 Chat IDs: [123456789, 987654321]
================================================================================
```

### 第六步：测试

给你的 Bot 发送消息 `/start`，确认 Bot 可以正常工作。

然后在 Emby 中添加一个新媒体，或使用测试脚本：

```bash
python test_real_case.py
```

你应该会在 Telegram 中收到审核请求。

## 使用方式

### 审核请求消息格式

当有新的 CDN 预热请求时，你会收到如下消息：

```
🎬 CDN 预热审核请求

📝 请求 ID: 1
🎞 媒体名称: 圣诞礼物
📂 类型: Movie
📅 年份: 1952

📍 Emby 路径:
/media/软链接/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}/圣诞礼物.Gift Wrapped.1952.strm

💾 宿主机路径:
/mnt/media/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}/圣诞礼物.Gift Wrapped.1952.mp4

🔗 CDN 预热 URL:
https://qiufeng.huaijiufu.com/电影/动画电影/圣诞礼物 (1952) {tmdbid=48875}/圣诞礼物.Gift Wrapped.1952.mp4

⏰ 请选择操作：
```

下方有两个按钮：
- **✅ 同意预热**: 批准该 URL 进行 CDN 预热
- **❌ 拒绝**: 拒绝预热请求

### 点击按钮后

点击按钮后，消息会更新为：

**同意预热**：
```
✅ 已同意预热

🎞 媒体: 圣诞礼物
🔗 URL: https://qiufeng.huaijiufu.com/...

👤 审核人: 张三 (@zhangsan)
📝 结果: 将开始 CDN 预热
```

**拒绝**：
```
❌ 已拒绝

🎞 媒体: 圣诞礼物
🔗 URL: https://qiufeng.huaijiufu.com/...

👤 审核人: 张三 (@zhangsan)
📝 结果: 不会进行预热
```

### 可用命令

向 Bot 发送以下命令：

- `/stats` - 查看审核统计信息
  ```
  📊 CDN 预热审核统计

  ⏳ 待审核: 5
  ✅ 已批准: 123
  ❌ 已拒绝: 12
  📝 总计: 140
  ```

- `/pending` - 查看待审核列表
  ```
  ⏳ 待审核列表（最近 10 条）

  🆔 ID: 5
  🎞 电影名称 (Movie)
  🔗 https://qiufeng.huaijiufu.com/...
  ⏰ 2025-12-19 10:30:00

  ...
  ```

## 数据存储

审核记录存储在 SQLite 数据库中：`preheat_review.db`

数据库包含：
- 所有审核请求记录
- 审核状态（pending/approved/rejected）
- 审核时间和审核人
- 媒体信息和 URL

## 常见问题

### Q: Bot 没有响应？

A: 检查：
1. Bot Token 是否正确配置
2. Chat ID 是否正确
3. 服务器是否能访问 Telegram API（某些地区可能需要代理）
4. 查看日志中的错误信息

### Q: 收不到审核消息？

A: 检查：
1. 确认已给 Bot 发送过消息（点击 Start）
2. Chat ID 是否正确（使用 @userinfobot 确认）
3. TELEGRAM_ADMIN_CHAT_IDS 配置是否正确
4. 查看日志确认消息是否发送成功

### Q: 可以添加多个管理员吗？

A: 可以！在 TELEGRAM_ADMIN_CHAT_IDS 中用逗号分隔多个 Chat ID：
```
TELEGRAM_ADMIN_CHAT_IDS=123456789,987654321,555666777
```

所有管理员都会收到审核请求，任何一个管理员点击按钮都会触发审核。

### Q: 审核请求会过期吗？

A: 可以配置 `REVIEW_TIMEOUT_SECONDS`（默认 24 小时）。超时后的请求可以标记为过期（需要实现定时任务）。

### Q: 如何查看历史审核记录？

A: 可以使用 `/stats` 和 `/pending` 命令查看统计信息和待审核列表。

更详细的历史记录可以直接查询数据库：
```bash
sqlite3 preheat_review.db "SELECT * FROM review_requests ORDER BY created_at DESC LIMIT 20;"
```

### Q: 如果不小心点错了怎么办？

A: 目前一旦审核完成就无法撤销。未来可以添加撤销功能。

### Q: 是否支持设置代理？

A: 如果服务器无法直接访问 Telegram API，可以通过环境变量设置代理：

```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

或在代码中配置（需要修改 telegram_bot.py）。

## 安全建议

1. **保护 Bot Token**：不要将 Token 提交到 Git 仓库
2. **限制管理员**：只添加信任的人员的 Chat ID
3. **定期备份**：定期备份 preheat_review.db 数据库
4. **监控日志**：定期查看日志，确认系统正常运行

## 下一步开发

- [ ] 添加审核超时自动处理
- [ ] 实现审核撤销功能
- [ ] 添加批量审核功能
- [ ] 支持在 Telegram 中查看媒体缩略图
- [ ] 添加审核报表统计功能
