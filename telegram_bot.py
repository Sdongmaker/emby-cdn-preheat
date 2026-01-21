"""
Telegram Bot 审核模块
处理 CDN 预热的人工审核流程
支持批量推送以避免触发 Telegram 速率限制
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.error import TelegramError
import config
from database import db
from cdn_preheat import cdn_service

logger = logging.getLogger(__name__)


class TelegramReviewBot:
    """Telegram 审核 Bot - 支持批量推送"""

    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.admin_chat_ids = config.TELEGRAM_ADMIN_CHAT_IDS
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None

        # 批量推送相关
        self.review_queue: asyncio.Queue = asyncio.Queue()
        self.batch_worker_task: Optional[asyncio.Task] = None
        self.last_push_time: float = 0

    async def initialize(self):
        """初始化 Bot"""
        if not self.bot_token:
            logger.error("未配置 TELEGRAM_BOT_TOKEN，无法启动 Telegram Bot")
            return False

        if not self.admin_chat_ids:
            logger.error("未配置 TELEGRAM_ADMIN_CHAT_IDS，无法启动 Telegram Bot")
            return False

        try:
            # 创建 Application
            self.application = Application.builder().token(self.bot_token).build()
            self.bot = self.application.bot

            # 注册回调处理器
            self.application.add_handler(
                CallbackQueryHandler(self._handle_button_callback)
            )

            # 注册命令处理器
            self.application.add_handler(
                CommandHandler("stats", self._handle_stats_command)
            )
            self.application.add_handler(
                CommandHandler("pending", self._handle_pending_command)
            )

            # 启动 Bot（非阻塞）
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

            # 启动批量推送后台任务
            self.batch_worker_task = asyncio.create_task(self._batch_push_worker())

            logger.info("Telegram Bot 启动成功")
            logger.info(f"管理员 Chat IDs: {self.admin_chat_ids}")
            logger.info(f"批量推送配置: 间隔={config.BATCH_PUSH_INTERVAL}秒, 最大数量={config.BATCH_PUSH_SIZE}")
            return True

        except Exception as e:
            logger.error(f"Telegram Bot 初始化失败: {str(e)}")
            return False

    async def shutdown(self):
        """关闭 Bot"""
        # 停止批量推送任务
        if self.batch_worker_task:
            self.batch_worker_task.cancel()
            try:
                await self.batch_worker_task
            except asyncio.CancelledError:
                pass

        if self.application:
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram Bot 已关闭")
            except Exception as e:
                logger.error(f"关闭 Telegram Bot 失败: {str(e)}")

    async def add_to_queue(
        self,
        request_id: int,
        media_name: str,
        media_type: str,
        cdn_url: str,
        emby_path: str = "",
        host_path: str = "",
        media_info: Dict[str, Any] = None
    ):
        """
        添加审核请求到队列（批量推送）

        Args:
            request_id: 请求 ID
            media_name: 媒体名称
            media_type: 媒体类型
            cdn_url: CDN URL
            emby_path: Emby 路径
            host_path: 宿主机路径
            media_info: 媒体详细信息
        """
        if not self.bot:
            logger.error("Telegram Bot 未初始化")
            return

        request_data = {
            'request_id': request_id,
            'media_name': media_name,
            'media_type': media_type,
            'cdn_url': cdn_url,
            'emby_path': emby_path,
            'host_path': host_path,
            'media_info': media_info or {}
        }

        await self.review_queue.put(request_data)
        queue_size = self.review_queue.qsize()
        logger.info(f"📥 审核请求已加入队列: ID={request_id}, 队列大小={queue_size}")

        # 如果队列达到最大数量，立即触发推送
        if queue_size >= config.BATCH_PUSH_SIZE:
            logger.info(f"🚀 队列达到最大数量 ({config.BATCH_PUSH_SIZE})，触发立即推送")
            # 通过设置时间戳来触发推送
            self.last_push_time = 0

    async def _batch_push_worker(self):
        """
        后台任务：定期检查队列并批量推送
        触发条件：
        1. 距离上次推送超过 BATCH_PUSH_INTERVAL 秒
        2. 队列大小达到 BATCH_PUSH_SIZE
        """
        logger.info("📡 批量推送后台任务已启动")
        self.last_push_time = time.time()

        while True:
            try:
                await asyncio.sleep(5)  # 每 5 秒检查一次

                queue_size = self.review_queue.qsize()
                if queue_size == 0:
                    continue

                current_time = time.time()
                time_elapsed = current_time - self.last_push_time

                # 判断是否需要推送
                should_push = False
                reason = ""

                if queue_size >= config.BATCH_PUSH_SIZE:
                    should_push = True
                    reason = f"队列大小达到 {config.BATCH_PUSH_SIZE}"
                elif time_elapsed >= config.BATCH_PUSH_INTERVAL:
                    should_push = True
                    reason = f"距上次推送已 {int(time_elapsed)} 秒"

                if should_push:
                    logger.info(f"🔔 触发批量推送: {reason}, 队列大小={queue_size}")
                    await self._push_batch_from_queue()
                    self.last_push_time = time.time()

            except asyncio.CancelledError:
                logger.info("批量推送任务已取消")
                break
            except Exception as e:
                logger.error(f"批量推送任务出错: {str(e)}", exc_info=True)
                await asyncio.sleep(10)  # 出错后等待 10 秒再继续

    async def _push_batch_from_queue(self):
        """从队列中取出请求并批量推送"""
        try:
            # 从队列中取出所有待推送的请求
            requests = []
            while not self.review_queue.empty() and len(requests) < config.BATCH_PUSH_SIZE:
                try:
                    request_data = await asyncio.wait_for(
                        self.review_queue.get(),
                        timeout=0.1
                    )
                    requests.append(request_data)
                except asyncio.TimeoutError:
                    break

            if not requests:
                return

            logger.info(f"📤 准备推送 {len(requests)} 个审核请求")

            # 分组发送（避免单条消息太长）
            max_per_message = config.MAX_ITEMS_PER_MESSAGE
            for i in range(0, len(requests), max_per_message):
                batch = requests[i:i + max_per_message]
                await self._send_batch_reviews(batch)

                # 批次间短暂延迟，避免速率限制
                if i + max_per_message < len(requests):
                    await asyncio.sleep(1)

            logger.info(f"✅ 批量推送完成，共 {len(requests)} 个请求")

        except Exception as e:
            logger.error(f"批量推送失败: {str(e)}", exc_info=True)

    async def _send_batch_reviews(self, requests: List[Dict[str, Any]]):
        """
        发送一批审核请求（合并成一条消息）

        Args:
            requests: 请求列表
        """
        if not requests:
            return

        try:
            # 构建批量消息文本
            message_text = f"🎬 <b>CDN 预热审核请求</b>（共 {len(requests)} 项）\n\n"

            # 为每个请求创建一行摘要
            for idx, req in enumerate(requests, 1):
                media_name = req['media_name']
                media_type = req['media_type']
                request_id = req['request_id']

                # 简化显示
                type_emoji = "🎬" if media_type == "Movie" else "📺"
                message_text += f"{idx}. {type_emoji} <b>{media_name}</b> (ID: {request_id})\n"

            message_text += f"\n💡 使用下方按钮批准或拒绝每个项目"

            # 创建按钮（每个请求一行，最多显示配置的数量）
            keyboard = []
            for req in requests:
                request_id = req['request_id']
                media_name = req['media_name']
                # 截断名称以适应按钮宽度
                short_name = media_name[:15] + "..." if len(media_name) > 15 else media_name

                keyboard.append([
                    InlineKeyboardButton(
                        f"✅ {short_name}",
                        callback_data=f"approve_{request_id}"
                    ),
                    InlineKeyboardButton(
                        f"❌",
                        callback_data=f"reject_{request_id}"
                    )
                ])

            reply_markup = InlineKeyboardMarkup(keyboard)

            # 发送消息给所有管理员
            for chat_id in self.admin_chat_ids:
                try:
                    message = await self.bot.send_message(
                        chat_id=chat_id,
                        text=message_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )

                    # 更新数据库中的消息 ID（使用第一个请求的 ID）
                    if requests:
                        first_request_id = requests[0]['request_id']
                        db.update_telegram_message_id(first_request_id, message.message_id)

                    logger.info(f"✅ 批量消息发送成功: chat_id={chat_id}, 包含 {len(requests)} 个请求")

                except TelegramError as e:
                    logger.error(f"发送批量消息到 {chat_id} 失败: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"发送批量审核请求失败: {str(e)}", exc_info=True)

    def _build_review_message(
        self,
        request_id: int,
        media_name: str,
        media_type: str,
        cdn_url: str,
        emby_path: str = "",
        host_path: str = "",
        media_info: Dict[str, Any] = None
    ) -> str:
        """构建审核消息文本"""
        media_info = media_info or {}

        # 基本信息
        message = f"🎬 <b>CDN 预热审核请求</b>\n\n"
        message += f"📝 <b>请求 ID:</b> {request_id}\n"
        message += f"🎞 <b>媒体名称:</b> {media_name}\n"
        message += f"📂 <b>类型:</b> {media_type}\n"

        # 年份信息
        if media_info.get('production_year'):
            message += f"📅 <b>年份:</b> {media_info['production_year']}\n"

        # 路径信息
        if emby_path:
            message += f"\n📍 <b>Emby 路径:</b>\n<code>{emby_path}</code>\n"
        if host_path:
            message += f"\n💾 <b>宿主机路径:</b>\n<code>{host_path}</code>\n"

        # CDN URL
        message += f"\n🔗 <b>CDN 预热 URL:</b>\n<code>{cdn_url}</code>\n"

        message += f"\n⏰ 请选择操作："

        return message

    async def _handle_button_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """处理按钮点击回调"""
        query = update.callback_query
        await query.answer()

        # 解析回调数据
        callback_data = query.data
        action, request_id = callback_data.split("_")
        request_id = int(request_id)

        # 获取用户信息
        user = query.from_user
        reviewed_by = f"{user.first_name} (@{user.username})" if user.username else user.first_name

        # 获取请求信息
        request = db.get_request_by_id(request_id)
        if not request:
            await query.edit_message_text(
                text=f"❌ 请求不存在: ID={request_id}"
            )
            return

        # 检查是否已经审核过
        if request['status'] != 'pending':
            await query.edit_message_text(
                text=f"⚠️ 该请求已经被处理过\n"
                     f"状态: {request['status']}\n"
                     f"审核人: {request['reviewed_by']}"
            )
            return

        # 执行操作
        if action == "approve":
            db.approve_request(request_id, reviewed_by)
            result_emoji = "✅"
            result_text = "已同意预热"

            # 触发 CDN 预热
            cdn_url = request['cdn_url']
            logger.info(f"开始 CDN 预热: {cdn_url}")

            try:
                preheat_result = await cdn_service.preheat_url(cdn_url)

                if preheat_result['success']:
                    result_action = f"CDN 预热已提交\n任务 ID: {preheat_result['task_id']}"
                    logger.info(f"✅ CDN 预热成功: task_id={preheat_result['task_id']}")
                else:
                    result_action = f"CDN 预热失败: {preheat_result['message']}"
                    logger.error(f"❌ CDN 预热失败: {preheat_result['message']}")
            except Exception as e:
                result_action = f"CDN 预热出错: {str(e)}"
                logger.error(f"❌ CDN 预热异常: {str(e)}", exc_info=True)

        elif action == "reject":
            db.reject_request(request_id, reviewed_by)
            result_emoji = "❌"
            result_text = "已拒绝"
            result_action = "不会进行预热"

        else:
            await query.edit_message_text(text="❌ 未知操作")
            return

        # 更新消息
        updated_message = (
            f"{result_emoji} <b>{result_text}</b>\n\n"
            f"🎞 <b>媒体:</b> {request['media_name']}\n"
            f"🔗 <b>URL:</b> <code>{request['cdn_url']}</code>\n\n"
            f"👤 <b>审核人:</b> {reviewed_by}\n"
            f"📝 <b>结果:</b> {result_action}"
        )

        await query.edit_message_text(
            text=updated_message,
            parse_mode='HTML'
        )

    async def _handle_stats_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """处理 /stats 命令 - 显示统计信息"""
        stats = db.get_statistics()

        message = (
            f"📊 <b>CDN 预热审核统计</b>\n\n"
            f"⏳ 待审核: {stats['pending']}\n"
            f"✅ 已批准: {stats['approved']}\n"
            f"❌ 已拒绝: {stats['rejected']}\n"
            f"📝 总计: {stats['total']}\n"
        )

        await update.message.reply_text(message, parse_mode='HTML')

    async def _handle_pending_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """处理 /pending 命令 - 显示待审核列表"""
        pending_requests = db.get_pending_requests(limit=10)

        if not pending_requests:
            await update.message.reply_text("✅ 当前没有待审核的请求")
            return

        message = f"⏳ <b>待审核列表</b>（最近 {len(pending_requests)} 条）\n\n"

        for req in pending_requests:
            message += (
                f"🆔 ID: {req['id']}\n"
                f"🎞 {req['media_name']} ({req['media_type']})\n"
                f"🔗 {req['cdn_url']}\n"
                f"⏰ {req['created_at']}\n\n"
            )

        await update.message.reply_text(message, parse_mode='HTML')


# 全局 Bot 实例
telegram_bot = TelegramReviewBot()
