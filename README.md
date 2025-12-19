# Emby CDN 预热服务

自动监听 Emby 媒体库新增内容，并提交到腾讯云 CDN 进行预热。

## 功能特性

- ✅ 接收 Emby Webhook 事件
- ✅ 自动识别新入库的电影和剧集
- ✅ 记录媒体文件路径和元数据
- 🔄 自动转换本地路径为 CDN URL（待实现）
- 🔄 提交到腾讯云 CDN 预热（待实现）

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置服务器端口、腾讯云凭证等。

### 3. 配置路径映射

编辑 `config.py` 中的 `PATH_MAPPINGS`，设置本地路径到 CDN URL 的映射关系：

```python
PATH_MAPPINGS = {
    "/media/电影/": "https://nginx.example.com/电影/",
    "/media/剧集/": "https://nginx.example.com/剧集/",
}
```

## 运行服务

### 启动 Webhook 服务器

```bash
python webhook_server.py
```

服务将在 `http://0.0.0.0:8899` 启动。

### 健康检查

访问 `http://localhost:8899/` 查看服务状态。

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

## 下一步开发

- [ ] 实现本地路径到 CDN URL 的自动转换
- [ ] 集成腾讯云 CDN API
- [ ] 实现预热队列和批量提交
- [ ] 添加文件大小过滤
- [ ] 添加预热状态跟踪

## 常见问题

**Q: Webhook 无法接收到数据？**

A: 检查：
1. 防火墙是否开放 8899 端口
2. Emby Webhook 配置的 URL 是否正确
3. 网络是否可达

**Q: 如何修改监听端口？**

A: 修改 `.env` 文件中的 `SERVER_PORT` 或直接修改 `webhook_server.py` 中的端口号。

## 许可

MIT License
