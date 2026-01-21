# 数据库权限问题修复说明

## 问题描述

```
sqlite3.OperationalError: unable to open database file
```

容器启动时无法创建或打开 SQLite 数据库文件。

## 根本原因

1. **目录不存在**: 数据库文件所在目录未创建
2. **权限不足**: 容器内应用进程没有写权限
3. **挂载问题**: Docker 直接挂载文件可能创建目录而非文件

---

## 修复方案

### 1. 数据库目录结构调整

**修改前**:
```
preheat_review.db  # 直接在根目录
```

**修改后**:
```
data/
  └── preheat_review.db  # 在独立的 data 目录中
```

### 2. 自动创建目录

**database.py** - 添加目录检查和创建逻辑：

```python
def _ensure_db_directory(self):
    """确保数据库文件所在目录存在"""
    db_path = Path(self.db_file)
    db_dir = db_path.parent

    if db_dir.name == '.':
        return

    try:
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"数据库目录已确保存在: {db_dir}")
    except Exception as e:
        logger.error(f"创建数据库目录失败: {str(e)}")
        raise
```

### 3. 增强错误日志

添加详细的错误信息输出：

```python
except sqlite3.OperationalError as e:
    logger.error(f"数据库初始化失败: {str(e)}")
    logger.error(f"数据库文件路径: {self.db_file}")
    logger.error(f"当前工作目录: {Path.cwd()}")
    logger.error(f"文件绝对路径: {Path(self.db_file).absolute()}")
    raise
```

### 4. 启动脚本

**entrypoint.sh** - 在应用启动前创建目录：

```bash
#!/bin/bash
set -e

# 创建必要的目录
mkdir -p /app/logs
mkdir -p /app/data

# 设置权限
chmod 755 /app/logs
chmod 755 /app/data

# 启动应用
exec python webhook_server.py
```

### 5. Dockerfile 优化

```dockerfile
# 复制启动脚本
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 创建必要的目录
RUN mkdir -p /app/logs /app/data && \
    chmod 755 /app/logs /app/data /app

# 使用启动脚本
ENTRYPOINT ["/app/entrypoint.sh"]
```

### 6. Docker Compose 挂载调整

**修改前** - 直接挂载文件：
```yaml
volumes:
  - ./preheat_review.db:/app/preheat_review.db
```

**修改后** - 挂载目录：
```yaml
volumes:
  # 挂载数据目录（持久化审核记录）
  - ./data:/app/data
  # 挂载日志目录
  - ./logs:/app/logs
```

### 7. 环境变量配置

**.env.example**:
```bash
# 数据库文件路径（相对于工作目录）
DB_FILE=data/preheat_review.db
```

**docker-compose.yml**:
```yaml
environment:
  - DB_FILE=data/preheat_review.db
```

### 8. .dockerignore 更新

防止本地数据库文件打包进镜像：

```
# 数据库文件和数据目录
*.db
*.db-journal
data/
```

---

## 测试验证

### 1. 本地测试

```bash
# 创建数据目录
mkdir -p data

# 运行数据库测试
python test_database.py
```

**预期输出**:
```
🧪 数据库初始化测试
📁 数据库文件路径: data/preheat_review.db
✅ 数据库模块导入成功！
✅ 添加审核请求成功！ID: 1
✅ 所有测试通过！
```

### 2. Docker 测试

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

**预期日志**:
```
Creating required directories...
Directories created successfully
数据库目录已确保存在: data
数据库初始化完成: data/preheat_review.db
Telegram Bot 启动成功
```

### 3. 健康检查

```bash
# 检查容器状态
docker-compose ps

# 应该显示 healthy
```

访问 `http://localhost:8899/` 应该返回：
```json
{
  "status": "running",
  "service": "Emby CDN Preheat Webhook",
  "timestamp": "2026-01-22T..."
}
```

---

## 目录结构

修复后的目录结构：

```
emby-cdn-preheat/
├── data/                          # 数据目录（持久化）
│   └── preheat_review.db         # 数据库文件
├── logs/                          # 日志目录（持久化）
│   └── webhook.log               # 日志文件
├── webhook_server.py             # 应用主程序
├── database.py                   # 数据库模块
├── entrypoint.sh                 # 启动脚本
├── Dockerfile                    # Docker 镜像配置
├── docker-compose.yml            # Docker Compose 配置
└── .dockerignore                 # Docker 忽略文件
```

---

## 迁移指南

如果你之前已经部署并有数据库文件：

### 方案 1：移动现有数据库

```bash
# 停止服务
docker-compose down

# 创建 data 目录
mkdir -p data

# 移动数据库文件
mv preheat_review.db data/

# 重启服务
docker-compose up -d
```

### 方案 2：使用环境变量指定旧路径

在 `.env` 文件中：
```bash
DB_FILE=preheat_review.db
```

并在 docker-compose.yml 中挂载：
```yaml
volumes:
  - ./preheat_review.db:/app/preheat_review.db
```

---

## 常见问题

### Q: 数据库文件在哪里？

A: 在宿主机的 `./data/preheat_review.db`，映射到容器的 `/app/data/preheat_review.db`

### Q: 如何备份数据库？

A:
```bash
# 简单备份
cp data/preheat_review.db data/preheat_review.db.backup

# 带时间戳的备份
cp data/preheat_review.db data/preheat_review.db.$(date +%Y%m%d_%H%M%S)
```

### Q: 如何重置数据库？

A:
```bash
# 停止服务
docker-compose down

# 删除数据库
rm data/preheat_review.db

# 重启服务（会自动创建新数据库）
docker-compose up -d
```

### Q: 权限错误怎么办？

A:
```bash
# 检查目录权限
ls -la data/

# 修复权限
chmod 755 data/
chmod 644 data/preheat_review.db
```

---

## 验证清单

- [x] 数据库目录自动创建
- [x] 数据库文件权限正确
- [x] 启动脚本创建目录
- [x] Docker 挂载目录而非文件
- [x] 详细错误日志输出
- [x] 环境变量配置数据库路径
- [x] .dockerignore 排除数据文件
- [x] 测试脚本验证功能

---

## 相关文件

| 文件 | 修改内容 |
|------|---------|
| `database.py` | 添加目录检查、详细错误日志 |
| `entrypoint.sh` | 新增启动脚本 |
| `Dockerfile` | 使用启动脚本、创建目录 |
| `docker-compose.yml` | 挂载 data 目录、添加环境变量 |
| `.env.example` | 添加 DB_FILE 配置 |
| `.dockerignore` | 排除数据库文件 |
| `test_database.py` | 新增测试脚本 |

---

## 总结

通过以上修复，彻底解决了数据库文件权限问题：

1. ✅ 自动创建必要的目录
2. ✅ 使用启动脚本确保环境
3. ✅ 挂载目录而非文件，避免 Docker 问题
4. ✅ 环境变量灵活配置路径
5. ✅ 详细日志便于排查问题
6. ✅ 测试脚本验证功能

现在服务应该能正常启动和运行！
