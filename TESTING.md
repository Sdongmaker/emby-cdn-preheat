# 测试指南

如何测试 Emby CDN 预热服务是否正常工作。

---

## 🚀 快速测试

### 方式 1: 使用交互式测试工具（推荐）

```bash
python3 test_emby_webhook.py
```

**功能**:
- 🎯 交互式菜单选择
- 🧪 单项测试
- 📦 批量测试（触发批量推送）
- 🎬 按类型测试（电影/剧集/STRM）
- 🛠️ 自定义测试
- 🏥 健康检查

**使用截图**:
```
==================================================================
  Emby CDN 预热服务 - Webhook 测试工具
==================================================================

选择测试模式:

  1. 单项测试 - 测试单个媒体（电影）
  2. 批量测试 - 测试所有预设媒体（触发批量推送）
  3. 快速测试 - 测试 3 个媒体
  4. 电影测试 - 只测试电影
  5. 剧集测试 - 只测试剧集
  6. STRM 测试 - 只测试 STRM 文件
  7. 自定义测试 - 手动输入媒体信息
  8. 健康检查 - 只检查服务器状态
  9. 修改服务器地址
  0. 退出

请选择 (0-9):
```

### 方式 2: 使用快速测试脚本

```bash
# 编辑服务器地址
vim quick_test.py
# 修改 SERVER_URL = "http://你的服务器IP:8899/emby"

# 运行测试
python3 quick_test.py
```

**输出示例**:
```
🧪 快速测试 Emby CDN 预热服务
📡 服务器: http://104.36.21.247:8899/emby

1️⃣ 健康检查...
   ✅ 服务器状态: running

2️⃣ 发送测试 Webhook...
   ✅ 请求成功！

=============================================================
✅ 测试完成！

💬 检查 Telegram Bot 是否收到审核通知
📝 查看日志: docker compose logs -f
=============================================================
```

### 方式 3: 使用原有的测试脚本

```bash
python3 test_batch_push.py single
```

---

## 📊 测试场景

### 场景 1: 单个媒体测试

**目的**: 验证基本功能

```bash
python3 test_emby_webhook.py
# 选择 1 - 单项测试
```

**预期结果**:
- ✅ Webhook 请求成功（HTTP 200）
- ✅ 服务器日志显示收到请求
- ✅ Telegram Bot 收到审核通知（30 秒内或达到 10 条）

### 场景 2: 批量测试（推荐）

**目的**: 测试批量推送功能

```bash
python3 test_emby_webhook.py
# 选择 2 - 批量测试
```

**预期结果**:
- ✅ 所有请求成功
- ✅ 请求加入队列（查看日志: `grep "队列" logs/webhook.log`）
- ✅ 触发批量推送（查看日志: `grep "批量" logs/webhook.log`）
- ✅ Telegram 收到 1-2 条合并消息

### 场景 3: STRM 文件测试

**目的**: 验证 STRM 文件处理

```bash
python3 test_emby_webhook.py
# 选择 6 - STRM 测试
```

**预期结果**:
- ✅ 正确识别 .strm 文件
- ✅ 尝试读取 STRM 文件内容
- ✅ 应用 STRM 路径映射

### 场景 4: 自定义测试

**目的**: 测试特定路径

```bash
python3 test_emby_webhook.py
# 选择 7 - 自定义测试
# 按提示输入媒体信息
```

---

## 🔍 验证方法

### 1. 检查服务器日志

```bash
# 实时查看日志
docker compose logs -f

# 查看特定内容
docker compose logs | grep "收到新媒体"
docker compose logs | grep "队列"
docker compose logs | grep "批量"
docker compose logs | grep "审核请求"
```

**正常日志示例**:
```
收到新媒体: 复仇者联盟4：终局之战 (Movie)
Emby 路径: /media/电影/复仇者联盟4：终局之战 (2019)/...
✅ 审核请求已创建: ID=1
📥 审核请求已加入批量推送队列
```

### 2. 检查 Telegram Bot

在 Telegram 中应该看到：

**单项推送（旧版行为）**:
```
🎬 CDN 预热审核请求

📝 请求 ID: 1
🎞 媒体名称: 复仇者联盟4：终局之战
📂 类型: Movie
...

[✅ 同意预热] [❌ 拒绝]
```

**批量推送（新版行为）**:
```
🎬 CDN 预热审核请求（共 5 项）

1. 🎬 复仇者联盟4：终局之战 (ID: 1)
2. 🎬 流浪地球2 (ID: 2)
3. 📺 权力的游戏 S01E01 (ID: 3)
...

💡 使用下方按钮批准或拒绝每个项目

[✅ 复仇者联盟4] [❌]
[✅ 流浪地球2] [❌]
...
```

### 3. 检查数据库

```bash
# 进入容器
docker compose exec emby-cdn-preheat bash

# 查看数据库
python3 -c "
from database import db
print('待审核:', db.get_statistics()['pending'])
print('已批准:', db.get_statistics()['approved'])
print('已拒绝:', db.get_statistics()['rejected'])
"
```

### 4. 使用测试命令

```bash
# 运行数据库测试
python3 test_database.py

# 运行路径映射测试（如果存在）
python3 test_path_mapping.py
```

---

## 📝 测试数据

测试脚本包含以下预设媒体：

| 类型 | 名称 | 路径特点 |
|------|------|---------|
| 电影 | 复仇者联盟4 | 标准电影路径 |
| 电影 | 流浪地球2 | 中文路径 |
| 电影 | 教父 | 经典电影 |
| 剧集 | 权力的游戏 S01E01 | 剧集路径 |
| 剧集 | 绝命毒师 S01E01 | 剧集路径 |
| 剧集 | 瑞克和莫蒂 S01E01 | 剧集路径 |
| 电影 | 星际穿越 (STRM) | STRM 文件 |
| 剧集 | 黑镜 S01E01 (STRM) | STRM 文件 |

---

## 🐛 调试技巧

### 查看详细的路径解析过程

```bash
# 设置调试日志级别
# 编辑 .env
LOG_LEVEL=DEBUG

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f | grep "步骤"
```

**日志示例**:
```
步骤 1: Emby 容器路径映射
  原始路径: /media/电影/...
  映射后: /media/电影/...

步骤 2: 检查文件类型
  不是 STRM 文件

步骤 4: CDN URL 映射
  原始路径: /media/电影/...
  CDN URL: https://cdn.example.com/电影/...
```

### 测试特定路径

编辑 `test_emby_webhook.py`，添加自定义路径：

```python
TEST_MEDIA.append({
    "Name": "我的测试视频",
    "Type": "Movie",
    "Path": "/media/你的实际路径/视频.mkv",
    "Id": "custom_test",
    "ProductionYear": 2024
})
```

### 模拟网络问题

```bash
# 测试超时
python3 -c "
import requests
try:
    requests.post('http://104.36.21.247:8899/emby', json={}, timeout=0.001)
except requests.exceptions.Timeout:
    print('✅ 超时处理正常')
"
```

---

## 🎯 性能测试

### 批量推送压力测试

```bash
# 快速发送 20 个请求
python3 test_emby_webhook.py
# 选择 2 - 批量测试
# 运行 2 次

# 查看队列和批量推送日志
docker compose logs | grep -E "队列|批量"
```

**预期行为**:
- 第 1 批 8 个请求：加入队列
- 达到阈值（10 个）：触发批量推送
- 第 2 批请求：继续加入队列
- 等待 30 秒或达到 10 个：再次批量推送

---

## ✅ 测试清单

完整测试检查表：

- [ ] 服务器健康检查通过
- [ ] 单个媒体 Webhook 成功
- [ ] 批量媒体触发批量推送
- [ ] Telegram Bot 收到通知
- [ ] 点击批准按钮后触发 CDN 预热（如果启用）
- [ ] 数据库正确记录请求
- [ ] 日志输出正常
- [ ] 路径映射正确
- [ ] STRM 文件处理正确

---

## 🆘 常见问题

### Q: 请求成功但 Telegram 没收到通知？

A: 检查：
1. Telegram Bot Token 是否正确
2. Chat ID 是否正确
3. 是否达到批量推送阈值（默认 30 秒或 10 条）
4. 查看日志: `docker compose logs | grep Telegram`

### Q: 路径没有正确转换？

A: 检查：
1. `config.py` 中的路径映射配置
2. 路径前缀是否完全匹配（包括 `/`）
3. 查看日志中的详细路径转换过程

### Q: 测试脚本无法连接服务器？

A: 检查：
1. 服务器 IP 和端口是否正确
2. 防火墙是否开放 8899 端口
3. 服务是否正在运行: `docker compose ps`

---

## 📚 相关文档

- [快速开始](./QUICKSTART.md) - 部署指南
- [完整部署](./DEPLOY.md) - 详细部署说明
- [故障排查](./TROUBLESHOOTING.md) - 问题解决
- [批量推送](./BATCH_PUSH.md) - 批量推送机制

---

## 🎉 测试完成后

如果所有测试通过：

1. ✅ 在 Emby 中配置 Webhook
2. ✅ 添加真实媒体测试
3. ✅ 配置定时备份
4. ✅ 监控服务运行状态

恭喜！你的 Emby CDN 预热服务已经可以投入使用了。
