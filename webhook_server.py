"""
Emby Webhook 接收服务
监听 Emby 媒体库新增事件，并记录媒体文件路径
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import logging
import json
from pathlib import Path
import uvicorn
import os

# 导入配置
import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Emby CDN Preheat Webhook Service")


def apply_path_mapping(path: str, mappings: Dict[str, str]) -> Optional[str]:
    """
    应用路径映射，按最长匹配优先

    Args:
        path: 原始路径
        mappings: 路径映射字典

    Returns:
        映射后的路径，如果没有匹配则返回 None
    """
    if not path or not mappings:
        return None

    # 按键长度降序排序，实现最长匹配优先
    sorted_mappings = sorted(mappings.items(), key=lambda x: len(x[0]), reverse=True)

    for source_prefix, target_prefix in sorted_mappings:
        if path.startswith(source_prefix):
            mapped_path = path.replace(source_prefix, target_prefix, 1)
            logger.info(f"路径映射: {source_prefix} → {target_prefix}")
            logger.info(f"  原始路径: {path}")
            logger.info(f"  映射后: {mapped_path}")
            return mapped_path

    return None


def read_strm_file(strm_path: str) -> Optional[str]:
    """
    读取 strm 文件内容，获取真实的媒体文件路径

    Args:
        strm_path: strm 文件的宿主机路径

    Returns:
        strm 文件中的真实媒体路径，失败返回 None
    """
    try:
        # 确保文件存在
        if not os.path.exists(strm_path):
            logger.warning(f"STRM 文件不存在: {strm_path}")
            return None

        # 读取 strm 文件内容（通常是一行 URL 或路径）
        with open(strm_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            logger.warning(f"STRM 文件内容为空: {strm_path}")
            return None

        logger.info(f"STRM 文件内容: {content}")
        return content

    except Exception as e:
        logger.error(f"读取 STRM 文件失败 {strm_path}: {str(e)}")
        return None


def resolve_media_path(emby_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    解析媒体文件路径，处理容器映射和 strm 文件

    工作流程：
    1. Emby 容器路径 → 宿主机路径
    2. 如果是 .strm 文件，读取内容获取真实路径
    3. 应用 strm 路径映射（如果需要）
    4. 宿主机路径 → CDN URL

    Args:
        emby_path: Emby 中看到的文件路径

    Returns:
        (宿主机路径, CDN URL) 元组，失败返回 (None, None)
    """
    logger.info("=" * 60)
    logger.info(f"开始解析路径: {emby_path}")

    # 步骤 1: Emby 容器路径 → 宿主机路径
    host_path = apply_path_mapping(emby_path, config.EMBY_CONTAINER_MAPPINGS)
    if not host_path:
        logger.warning(f"无法映射 Emby 容器路径，请检查 EMBY_CONTAINER_MAPPINGS 配置")
        host_path = emby_path  # 使用原始路径

    # 步骤 2: 检查是否为 strm 文件
    if host_path.lower().endswith('.strm'):
        logger.info(f"检测到 STRM 文件: {host_path}")

        # 读取 strm 文件内容
        real_path = read_strm_file(host_path)
        if not real_path:
            logger.error(f"无法读取 STRM 文件内容")
            return (None, None)

        # 步骤 3: 应用 strm 路径映射
        mapped_real_path = apply_path_mapping(real_path, config.STRM_MOUNT_MAPPINGS)
        if mapped_real_path:
            real_path = mapped_real_path
        else:
            logger.info(f"STRM 内容路径未映射，使用原始路径: {real_path}")

        host_path = real_path

    # 步骤 4: 宿主机路径 → CDN URL
    cdn_url = apply_path_mapping(host_path, config.CDN_URL_MAPPINGS)
    if not cdn_url:
        logger.warning(f"无法生成 CDN URL，请检查 CDN_URL_MAPPINGS 配置")

    logger.info(f"最终解析结果:")
    logger.info(f"  宿主机路径: {host_path}")
    logger.info(f"  CDN URL: {cdn_url or '未生成'}")
    logger.info("=" * 60)

    return (host_path, cdn_url)


def process_media_item(item_data: Dict[str, Any]) -> Dict[str, str]:
    """
    处理媒体项目数据，提取关键信息

    Args:
        item_data: Emby webhook 传来的媒体项目数据

    Returns:
        包含处理后信息的字典
    """
    try:
        # 提取媒体信息
        item_name = item_data.get('Name', 'Unknown')
        item_type = item_data.get('Type', 'Unknown')
        emby_path = item_data.get('Path', '')
        item_id = item_data.get('Id', '')

        logger.info(f"收到新媒体: {item_name} ({item_type})")
        logger.info(f"Emby 路径: {emby_path}")

        # 解析路径，处理容器映射和 strm 文件
        host_path, cdn_url = resolve_media_path(emby_path)

        # 这里可以添加 CDN 预热逻辑
        # if cdn_url:
        #     preheat_cdn(cdn_url)

        return {
            'name': item_name,
            'type': item_type,
            'emby_path': emby_path,
            'host_path': host_path,
            'cdn_url': cdn_url,
            'id': item_id,
            'processed_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"处理媒体项目时出错: {str(e)}")
        raise


@app.get("/")
async def root():
    """健康检查端点"""
    return {
        "status": "running",
        "service": "Emby CDN Preheat Webhook",
        "timestamp": datetime.now().isoformat()
    }


async def handle_emby_webhook(request: Request):
    """
    处理 Emby Webhook 事件的核心逻辑

    Emby Webhook 数据格式:
    {
        "Title": "ROC 上新建 惊天魔盗团3",
        "Event": "library.new",
        "Item": {
            "Name": "惊天魔盗团3",
            "Path": "/strm/data5/Movie/...",
            "Type": "Movie",
            "Id": "751181"
        },
        "Server": {...}
    }
    """
    # 先获取原始请求体，用于调试
    raw_body = await request.body()

    # 输出请求详细信息（开发调试用）
    logger.info("=" * 80)
    logger.info("收到 Webhook 请求")
    logger.info(f"请求来源: {request.client.host}:{request.client.port}")
    logger.info(f"Content-Type: {request.headers.get('content-type', 'Not Set')}")
    logger.info(f"请求头: {dict(request.headers)}")
    logger.info(f"原始请求体长度: {len(raw_body)} bytes")
    logger.info(f"原始请求体内容:\n{raw_body.decode('utf-8', errors='replace')}")
    logger.info("=" * 80)

    try:
        # 解析 JSON 数据
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {str(e)}")
            logger.error(f"无法解析的内容: {raw_body.decode('utf-8', errors='replace')[:500]}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON data: {str(e)}"
            )

        # 记录解析后的数据（用于调试）
        logger.info(f"解析后的 JSON 数据:\n{json.dumps(data, ensure_ascii=False, indent=2)}")

        # 检查是否是包装的数据格式（包含 body_json 字段）
        if 'body_json' in data:
            logger.info("检测到包装格式，提取 body_json 字段")
            data = data['body_json']
            logger.info(f"提取后的 Emby 数据:\n{json.dumps(data, ensure_ascii=False, indent=2)}")

        # 获取事件类型
        event_type = data.get('Event', '')

        # 只处理媒体新增事件
        if event_type in ['item.added', 'library.new']:
            item_data = data.get('Item', {})

            # 只处理视频文件（电影和剧集）
            item_type = item_data.get('Type', '')
            if item_type in ['Movie', 'Episode']:
                # 处理媒体项目
                result = process_media_item(item_data)

                # TODO: 这里将来会添加 CDN 预热逻辑
                logger.info(f"媒体项目处理完成: {result['name']}")

                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "message": "Webhook received and processed",
                        "data": result
                    }
                )
            else:
                logger.info(f"忽略非视频类型: {item_type}")
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "skipped",
                        "message": f"Item type {item_type} is not a video"
                    }
                )
        else:
            logger.info(f"忽略事件类型: {event_type}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "skipped",
                    "message": f"Event type {event_type} is not monitored"
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理 Webhook 时出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/emby")
async def emby_webhook_legacy(request: Request):
    """接收 Emby Webhook 事件 - 传统路径"""
    return await handle_emby_webhook(request)


@app.post("/emby")
async def emby_webhook(request: Request):
    """接收 Emby Webhook 事件 - 简短路径"""
    return await handle_emby_webhook(request)


if __name__ == "__main__":
    # 启动服务
    logger.info("启动 Emby Webhook 服务...")
    uvicorn.run(
        app,
        host="0.0.0.0",  # 监听所有网络接口
        port=8899,        # 端口号，可以在配置文件中修改
        log_level="info"
    )
