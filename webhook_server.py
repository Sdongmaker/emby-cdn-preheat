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
import asyncio

# 导入配置
import config

# 导入数据库和 Telegram Bot
from database import db
from telegram_bot import telegram_bot

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


# ==================== 应用生命周期事件 ====================
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化 Telegram Bot"""
    logger.info("=" * 80)
    logger.info("启动 Emby CDN 预热服务")
    logger.info("=" * 80)

    if config.TELEGRAM_REVIEW_ENABLED:
        logger.info("Telegram 审核已启用，正在初始化 Bot...")
        success = await telegram_bot.initialize()
        if success:
            logger.info("✅ Telegram Bot 初始化成功")
        else:
            logger.error("❌ Telegram Bot 初始化失败，审核功能将不可用")
    else:
        logger.info("Telegram 审核未启用")
        if config.AUTO_APPROVE_IF_NO_REVIEW:
            logger.info("⚠️  自动批准模式已启用，所有请求将自动通过")
        else:
            logger.info("⚠️  自动批准模式未启用，所有请求将被忽略")

    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("正在关闭服务...")
    if config.TELEGRAM_REVIEW_ENABLED:
        await telegram_bot.shutdown()
    logger.info("服务已关闭")


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
            logger.info(f"  🔄 应用映射规则: {source_prefix} → {target_prefix}")
            return mapped_path

    return None


def smart_match_cdn_url(path: str) -> Optional[str]:
    """
    智能匹配 CDN URL（用于单体 Emby 部署）

    当标准路径映射失败时，尝试智能识别路径中的关键目录（如"剧集"、"电影"），
    截取从关键字开始到最后的部分，拼接到 CDN 基础 URL

    Args:
        path: 原始路径

    Returns:
        匹配的 CDN URL，失败返回 None
    """
    if not config.ENABLE_SMART_URL_MATCHING:
        return None

    if not path or not config.SMART_MATCH_KEYWORDS:
        return None

    try:
        logger.info("【智能 URL 匹配】")
        logger.info(f"  🔍 原始路径: {path}")
        logger.info(f"  🎯 搜索关键字: {config.SMART_MATCH_KEYWORDS}")

        # 规范化路径（确保使用正斜杠）
        normalized_path = path.replace('\\', '/')

        # 查找第一个匹配的关键字
        for keyword in config.SMART_MATCH_KEYWORDS:
            # 查找关键字在路径中的位置
            # 例如: /media/剧集/国产剧/... 中查找 "剧集"
            keyword_pattern = f"/{keyword}/"

            if keyword_pattern in normalized_path:
                # 找到关键字的起始位置
                start_index = normalized_path.index(keyword_pattern)

                # 截取从关键字开始到结尾的部分（包括关键字前的斜杠）
                path_suffix = normalized_path[start_index + 1:]  # +1 是为了跳过开头的 /

                # 拼接 CDN URL
                cdn_base = config.SMART_MATCH_CDN_BASE
                if not cdn_base.endswith('/'):
                    cdn_base += '/'

                cdn_url = cdn_base + path_suffix

                logger.info(f"  ✅ 匹配成功！")
                logger.info(f"  📍 匹配关键字: {keyword}")
                logger.info(f"  ✂️  截取部分: {path_suffix}")
                logger.info(f"  🔗 生成 CDN URL: {cdn_url}")

                return cdn_url

        logger.warning(f"  ⚠️  未找到匹配的关键字")
        return None

    except Exception as e:
        logger.error(f"  ❌ 智能匹配失败: {str(e)}")
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
            logger.error(f"  ❌ 文件不存在: {strm_path}")
            return None

        # 读取 strm 文件内容（通常是一行 URL 或路径）
        with open(strm_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            logger.error(f"  ❌ 文件内容为空")
            return None

        return content

    except PermissionError:
        logger.error(f"  ❌ 权限不足，无法读取文件")
        return None
    except Exception as e:
        logger.error(f"  ❌ 读取失败: {str(e)}")
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
    logger.info("=" * 80)
    logger.info("🎬 开始路径解析流程")
    logger.info("=" * 80)
    logger.info(f"📥 接收到的 Emby 路径: {emby_path}")
    logger.info("")

    # ========== 步骤 1: Emby 容器路径 → 宿主机路径 ==========
    logger.info("【步骤 1/4】Emby 容器路径 → 宿主机路径")
    logger.info("-" * 80)
    logger.info(f"  输入路径: {emby_path}")

    host_path = apply_path_mapping(emby_path, config.EMBY_CONTAINER_MAPPINGS)
    if not host_path:
        logger.warning(f"  ⚠️  未找到匹配的容器映射规则")
        logger.warning(f"  💡 提示：请检查 config.py 中的 EMBY_CONTAINER_MAPPINGS 配置")
        logger.warning(f"  使用原始路径继续: {emby_path}")
        host_path = emby_path
    else:
        logger.info(f"  ✅ 映射成功")
        logger.info(f"  输出路径: {host_path}")

    logger.info("")

    # ========== 步骤 2: 检查是否为 STRM 文件 ==========
    logger.info("【步骤 2/4】检查文件类型")
    logger.info("-" * 80)

    if host_path.lower().endswith('.strm'):
        logger.info(f"  🎯 检测到 STRM 文件: {os.path.basename(host_path)}")
        logger.info(f"  📂 STRM 文件完整路径: {host_path}")
        logger.info("")

        # ========== 步骤 2.1: 读取 STRM 文件内容 ==========
        logger.info("【步骤 2.1/4】读取 STRM 文件内容")
        logger.info("-" * 80)

        real_path = read_strm_file(host_path)
        if not real_path:
            logger.error(f"  ❌ 无法读取 STRM 文件内容")
            logger.error(f"  💡 可能的原因:")
            logger.error(f"     1. 文件不存在或路径错误")
            logger.error(f"     2. 没有读取权限")
            logger.error(f"     3. 文件内容为空")
            logger.info("=" * 80)
            return (None, None)

        logger.info(f"  ✅ 读取成功")
        logger.info(f"  📝 STRM 文件内容: {real_path}")
        logger.info("")

        # ========== 步骤 3: STRM 内容路径映射 ==========
        logger.info("【步骤 3/4】STRM 内容路径映射（如果需要）")
        logger.info("-" * 80)
        logger.info(f"  输入路径: {real_path}")

        mapped_real_path = apply_path_mapping(real_path, config.STRM_MOUNT_MAPPINGS)
        if mapped_real_path:
            logger.info(f"  ✅ 映射成功")
            logger.info(f"  输出路径: {mapped_real_path}")
            real_path = mapped_real_path
        else:
            logger.info(f"  ℹ️  未配置 STRM 路径映射或路径已是宿主机路径")
            logger.info(f"  使用原始路径: {real_path}")

        host_path = real_path
        logger.info("")
    else:
        logger.info(f"  📄 普通媒体文件: {os.path.basename(host_path)}")
        logger.info(f"  跳过 STRM 处理，直接使用宿主机路径")
        logger.info("")

    # ========== 步骤 4: 宿主机路径 → CDN URL ==========
    logger.info("【步骤 4/4】宿主机路径 → CDN URL")
    logger.info("-" * 80)
    logger.info(f"  输入路径: {host_path}")

    cdn_url = apply_path_mapping(host_path, config.CDN_URL_MAPPINGS)
    if not cdn_url:
        logger.warning(f"  ⚠️  未找到匹配的 CDN 映射规则")
        logger.warning(f"  💡 提示：请检查 config.py 中的 CDN_URL_MAPPINGS 配置")

        # 尝试智能匹配（使用实际的宿主机文件路径）
        if config.ENABLE_SMART_URL_MATCHING:
            logger.info("")
            logger.info("  🔄 尝试智能 URL 匹配...")
            logger.info("")
            cdn_url = smart_match_cdn_url(host_path)

            if cdn_url:
                logger.info(f"  ✅ 智能匹配成功")
                logger.info(f"  📡 CDN URL: {cdn_url}")
            else:
                logger.warning(f"  ⚠️  智能匹配也失败了")
                logger.info(f"  CDN URL: 未生成")
        else:
            logger.info(f"  ℹ️  智能匹配未启用")
            logger.info(f"  CDN URL: 未生成")
    else:
        logger.info(f"  ✅ 映射成功")
        logger.info(f"  📡 CDN URL: {cdn_url}")

    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 最终解析结果汇总")
    logger.info("=" * 80)
    logger.info(f"  1️⃣  Emby 容器路径: {emby_path}")
    logger.info(f"  2️⃣  宿主机实际路径: {host_path}")
    logger.info(f"  3️⃣  CDN 预热 URL: {cdn_url or '未生成'}")
    logger.info("=" * 80)
    logger.info("")

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
        production_year = item_data.get('ProductionYear', '')

        logger.info(f"收到新媒体: {item_name} ({item_type})")
        logger.info(f"Emby 路径: {emby_path}")

        # 检查路径是否在黑名单中
        if config.PREHEAT_BLACKLIST_PATHS:
            for blacklist_path in config.PREHEAT_BLACKLIST_PATHS:
                if emby_path.startswith(blacklist_path):
                    logger.warning(f"⛔ 路径在黑名单中，跳过预热: {blacklist_path}")
                    logger.info(f"媒体项目处理完成: {item_name} (已跳过)")
                    return {
                        'name': item_name,
                        'type': item_type,
                        'emby_path': emby_path,
                        'host_path': None,
                        'cdn_url': None,
                        'id': item_id,
                        'skipped': True,
                        'reason': f'路径在黑名单中: {blacklist_path}',
                        'processed_at': datetime.now().isoformat()
                    }

        # 解析路径，处理容器映射和 strm 文件
        host_path, cdn_url = resolve_media_path(emby_path)

        # 如果生成了 CDN URL，发送审核请求
        if cdn_url:
            if config.TELEGRAM_REVIEW_ENABLED:
                # 添加到数据库
                request_id = db.add_review_request(
                    cdn_url=cdn_url,
                    media_name=item_name,
                    media_type=item_type,
                    emby_path=emby_path,
                    host_path=host_path,
                    media_info={
                        'production_year': production_year,
                        'id': item_id
                    }
                )

                if request_id:
                    logger.info(f"✅ 审核请求已创建: ID={request_id}")

                    # 添加到批量推送队列（不阻塞响应）
                    asyncio.create_task(
                        telegram_bot.add_to_queue(
                            request_id=request_id,
                            media_name=item_name,
                            media_type=item_type,
                            cdn_url=cdn_url,
                            emby_path=emby_path,
                            host_path=host_path,
                            media_info={'production_year': production_year}
                        )
                    )
                    logger.info(f"📥 审核请求已加入批量推送队列")
                else:
                    logger.warning(f"⚠️  审核请求创建失败或已存在")

            elif config.AUTO_APPROVE_IF_NO_REVIEW:
                logger.info(f"✅ 自动批准模式：CDN URL 将自动预热")
                # TODO: 直接调用 CDN 预热
            else:
                logger.info(f"ℹ️  未启用审核或自动批准，CDN URL 已生成但不会预热")
        else:
            logger.warning(f"⚠️  未生成 CDN URL，跳过审核流程")

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
