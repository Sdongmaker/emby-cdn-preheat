# Emby CDN 预热服务

自动监听 Emby 媒体库新增内容，并提交到腾讯云 CDN 进行预热。

## 功能特性

- ✅ 接收 Emby Webhook 事件
- ✅ 自动识别新入库的电影和剧集
- ✅ 记录媒体文件路径和元数据
- ✅ 支持 Emby 容器路径到宿主机路径的映射
- ✅ 自动识别和处理 STRM 文件
- ✅ 自动转换路径为 CDN URL
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

编辑 `config.py`，配置三层路径映射关系。路径映射支持**最长匹配优先**原则，确保更具体的路径优先匹配。

#### 3.1 Emby 容器路径映射 (EMBY_CONTAINER_MAPPINGS)

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

#### 3.2 STRM 文件路径映射 (STRM_MOUNT_MAPPINGS)

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

#### 3.3 CDN URL 映射 (CDN_URL_MAPPINGS)

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

#### 路径映射工作流程

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

#### 配置示例

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

- [x] 实现本地路径到 CDN URL 的自动转换
- [x] 支持容器路径映射
- [x] 支持 STRM 文件解析
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

A: 查看 `webhook.log` 日志文件，每次处理媒体时会详细记录：
- 原始 Emby 路径
- 容器映射后的路径
- 是否为 STRM 文件及其内容
- STRM 路径映射结果
- 最终的 CDN URL

## 许可

MIT License
