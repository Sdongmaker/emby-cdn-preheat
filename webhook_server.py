"""
Emby Webhook 接收服务
监听 Emby 媒体库新增事件，并记录媒体文件路径
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict, Any
import logging
import json
from pathlib import Path
import uvicorn

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
        item_path = item_data.get('Path', '')
        item_id = item_data.get('Id', '')

        logger.info(f"收到新媒体: {item_name} ({item_type})")
        logger.info(f"文件路径: {item_path}")

        # 这里可以添加路径转换逻辑
        # 将本地路径转换为 CDN URL
        # 例如: /media/电影/... -> https://nginx.example.com/电影/...

        return {
            'name': item_name,
            'type': item_type,
            'path': item_path,
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


@app.post("/webhook/emby")
async def emby_webhook(request: Request):
    """
    接收 Emby Webhook 事件

    Emby Webhook 数据格式:
    {
        "Event": "item.added",
        "Item": {
            "Name": "电影名称",
            "Path": "/media/电影/...",
            "Type": "Movie",
            "Id": "xxx"
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


if __name__ == "__main__":
    # 启动服务
    logger.info("启动 Emby Webhook 服务...")
    uvicorn.run(
        app,
        host="0.0.0.0",  # 监听所有网络接口
        port=8899,        # 端口号，可以在配置文件中修改
        log_level="info"
    )
