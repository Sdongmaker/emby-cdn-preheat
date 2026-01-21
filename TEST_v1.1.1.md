# v1.1.1 测试指南

本文档帮助你验证 v1.1.1 的所有修复和新功能。

---

## 🧪 测试 1：STRM 文件 CDN URL 修复

### 测试目的
验证 STRM 文件生成的 CDN URL 是否正确（应该是实际媒体文件 URL，而不是 .strm 文件 URL）

### 测试步骤

1. **准备测试环境**

确保你的 Emby 中有 STRM 文件，例如：
```
/media/近期添加/动画电影/哈尔的移动城堡.strm
```

STRM 文件内容指向实际媒体文件：
```
/mnt/media/近期添加/动画电影/哈尔的移动城堡.mp4
```

2. **触发测试**

在 Emby 中添加这个 STRM 媒体，或使用测试脚本：
```bash
python3 test_emby_webhook.py http://104.36.21.247:8899/emby
# 选择 6. STRM 测试
```

3. **检查日志**

查看服务日志：
```bash
docker compose logs -f | grep "CDN 预热 URL"
```

**期望结果**：
```
宿主机实际路径: /mnt/media/.../哈尔的移动城堡.mp4
CDN 预热 URL: https://your-cdn-domain.com/.../哈尔的移动城堡.mp4
```

**错误结果**（已修复）：
```
CDN 预热 URL: https://your-cdn-domain.com/.../哈尔的移动城堡.strm  ❌
```

4. **检查 Telegram 消息**

查看 Telegram Bot 发送的批量推送消息，应该显示：
```
1. 🎬 哈尔的移动城堡
   📹 文件类型: MP4
   📂 文件: 哈尔的移动城堡.Howl's Moving Castle.2004.2160p.mp4
   🔗 预热URL: https://.../.../哈尔的移动城堡.mp4
   🆔 ID: 1
```

**验证点**：
- ✅ 文件类型显示 `MP4`（不是 STRM）
- ✅ 文件名是 `.mp4`（不是 `.strm`）
- ✅ CDN URL 是 `.mp4`（不是 `.strm`）

---

## 🧪 测试 2：批量推送消息信息完整性

### 测试目的
验证批量推送消息是否显示完整的审核信息

### 测试步骤

1. **发送批量测试**

```bash
python3 test_emby_webhook.py http://104.36.21.247:8899/emby
# 选择 2. 批量测试
```

2. **检查 Telegram 消息格式**

消息应该包含以下信息：
- ✅ 媒体名称
- ✅ 文件类型（MP4、MKV 等）
- ✅ 文件名
- ✅ 完整的 CDN URL
- ✅ 请求 ID
- ✅ 提示信息："批准后将立即提交 CDN 预热"

**期望格式**：
```
🎬 CDN 预热审核请求（共 5 项）

1. 🎬 流浪地球2
   📹 文件类型: MP4
   📂 文件: 流浪地球2.mp4
   🔗 预热URL: https://cdn.com/.../流浪地球2.mp4
   🆔 ID: 1

2. 📺 权力的游戏 S01E01
   📹 文件类型: MKV
   📂 文件: 权力的游戏 - S01E01.mkv
   🔗 预热URL: https://cdn.com/.../权力的游戏 - S01E01.mkv
   🆔 ID: 2

...

💡 使用下方按钮批准或拒绝每个项目
📝 批准后将立即提交 CDN 预热
ℹ️ 使用 /detail ID 查看完整路径信息
```

3. **验证 URL 可复制**

在 Telegram 中：
- 长按 URL
- 应该能够复制完整 URL
- 粘贴到浏览器或文本编辑器验证格式

---

## 🧪 测试 3：路径黑名单功能

### 测试目的
验证黑名单路径的媒体是否被正确跳过

### 测试步骤

1. **配置黑名单**

编辑 `.env` 文件：
```bash
vim .env
```

添加黑名单路径：
```bash
PREHEAT_BLACKLIST_PATHS=/media/近期添加/,/media/test/
```

2. **重启服务**

```bash
docker compose restart
```

3. **验证配置已加载**

```bash
docker compose logs | grep -i "blacklist"
```

或在容器中执行：
```bash
docker compose exec emby-cdn-preheat python -c "import config; print('黑名单路径:', config.PREHEAT_BLACKLIST_PATHS)"
```

**期望输出**：
```
黑名单路径: ['/media/近期添加/', '/media/test/']
```

4. **测试黑名单匹配**

方式 1：在 Emby 中添加黑名单路径中的媒体

方式 2：使用测试脚本（需要修改生成路径）

5. **检查日志**

```bash
docker compose logs -f | grep "黑名单"
```

**期望输出**：
```
收到新媒体: 某电影 (Movie)
Emby 路径: /media/近期添加/某电影/某电影.mp4
⛔ 路径在黑名单中，跳过预热: /media/近期添加/
媒体项目处理完成: 某电影 (已跳过)
```

**验证点**：
- ✅ 日志显示"路径在黑名单中"
- ✅ 媒体被跳过，不创建审核请求
- ✅ Telegram 不会收到该媒体的推送

6. **测试非黑名单路径**

添加一个不在黑名单中的媒体，确保正常流程：
```
Emby 路径: /media/电影/某电影.mp4
✅ 审核请求已创建
📥 审核请求已加入批量推送队列
```

---

## 🧪 测试 4：端到端完整流程

### 测试目的
验证从 Webhook 到 Telegram 审核的完整流程

### 测试步骤

1. **清空数据库（可选）**

```bash
docker compose down
rm data/preheat_review.db
docker compose up -d
```

2. **配置黑名单**

```bash
echo "PREHEAT_BLACKLIST_PATHS=/media/近期添加/" >> .env
docker compose restart
```

3. **发送混合测试**

```bash
python3 test_emby_webhook.py
# 选择 2. 批量测试 - 随机生成8个媒体
```

4. **验证处理流程**

**日志检查清单**：
```bash
# 1. 检查是否收到 Webhook
docker compose logs | grep "收到新媒体"

# 2. 检查黑名单过滤（如果有）
docker compose logs | grep "黑名单"

# 3. 检查路径解析
docker compose logs | grep "最终解析结果汇总"

# 4. 检查 CDN URL 生成
docker compose logs | grep "CDN 预热 URL"

# 5. 检查批量推送触发
docker compose logs | grep "批量推送"
```

5. **Telegram 验证清单**

- ✅ 收到批量推送消息
- ✅ 显示文件类型
- ✅ 显示文件名
- ✅ 显示完整 CDN URL
- ✅ URL 格式正确（实际文件扩展名，不是 .strm）
- ✅ 按钮可点击
- ✅ 批准/拒绝功能正常

6. **批准测试**

- 点击 ✅ 按钮批准一个请求
- 检查消息更新
- 检查数据库状态：
  ```bash
  docker compose exec emby-cdn-preheat sqlite3 data/preheat_review.db "SELECT id, media_name, status FROM review_requests;"
  ```

---

## 📊 测试结果记录

### STRM 文件测试

- [ ] CDN URL 使用实际文件扩展名（.mp4/.mkv 等）
- [ ] 不使用 .strm 扩展名
- [ ] 日志显示正确的文件路径

### 批量推送消息测试

- [ ] 显示文件类型
- [ ] 显示文件名
- [ ] 显示完整 CDN URL
- [ ] URL 可复制
- [ ] 提示信息完整

### 黑名单测试

- [ ] 配置正确加载
- [ ] 黑名单路径被跳过
- [ ] 非黑名单路径正常处理
- [ ] 日志输出正确

### 端到端测试

- [ ] Webhook 接收正常
- [ ] 路径解析正确
- [ ] 批量推送正常
- [ ] 审核功能正常
- [ ] 数据库记录正确

---

## 🐛 常见问题

### Q: 测试后 CDN URL 还是 .strm？

A: 检查：
1. 是否重新构建了镜像：`docker compose build`
2. 是否重启了服务：`docker compose restart`
3. 查看代码版本：`docker compose logs | grep "智能 URL 匹配"`

### Q: 黑名单不生效？

A: 检查：
1. 环境变量格式：路径必须以 `/` 开头
2. 路径必须完全匹配开头部分
3. 查看加载的配置：`docker compose exec emby-cdn-preheat python -c "import config; print(config.PREHEAT_BLACKLIST_PATHS)"`

### Q: Telegram 消息格式没变？

A: 确保：
1. 已重新构建：`docker compose build`
2. 已重启服务：`docker compose restart`
3. 发送新的测试请求（不是查看旧消息）

---

## 📝 测试完成检查表

完成所有测试后，确认：

- [ ] STRM 文件生成正确的 CDN URL
- [ ] 批量推送显示完整信息
- [ ] 黑名单功能正常工作
- [ ] 端到端流程无错误
- [ ] 日志输出清晰准确
- [ ] Telegram Bot 响应正常

---

**问题反馈**: https://github.com/Sdongmaker/emby-cdn-preheat/issues
