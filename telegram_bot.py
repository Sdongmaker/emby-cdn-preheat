"""
Telegram Bot 审核模块
处理 CDN 预热的人工审核流程
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.error import TelegramError
import config
from database import db
from cdn_preheat import cdn_service

logger = logging.getLogger(__name__)


class TelegramReviewBot:
    """Telegram 审核 Bot"""

    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.admin_chat_ids = config.TELEGRAM_ADMIN_CHAT_IDS
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None

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

            logger.info("Telegram Bot 启动成功")
            logger.info(f"管理员 Chat IDs: {self.admin_chat_ids}")
            return True

        except Exception as e:
            logger.error(f"Telegram Bot 初始化失败: {str(e)}")
            return False

    async def shutdown(self):
        """关闭 Bot"""
        if self.application:
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram Bot 已关闭")
            except Exception as e:
                logger.error(f"关闭 Telegram Bot 失败: {str(e)}")

    async def send_review_request(
        self,
        request_id: int,
        media_name: str,
        media_type: str,
        cdn_url: str,
        emby_path: str = "",
        host_path: str = "",
        media_info: Dict[str, Any] = None
    ) -> bool:
        """
        发送审核请求到 Telegram

        Args:
            request_id: 请求 ID
            media_name: 媒体名称
            media_type: 媒体类型
            cdn_url: CDN URL
            emby_path: Emby 路径
            host_path: 宿主机路径
            media_info: 媒体详细信息

        Returns:
            是否发送成功
        """
        if not self.bot:
            logger.error("Telegram Bot 未初始化")
            return False

        try:
            # 构建消息文本
            message_text = self._build_review_message(
                request_id, media_name, media_type, cdn_url,
                emby_path, host_path, media_info
            )

            # 创建按钮
            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ 同意预热",
                        callback_data=f"approve_{request_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ 拒绝",
                        callback_data=f"reject_{request_id}"
                    )
                ]
            ]
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

                    # 更新数据库中的消息 ID
                    db.update_telegram_message_id(request_id, message.message_id)

                    logger.info(f"发送审核请求到 Telegram 成功: chat_id={chat_id}, request_id={request_id}")

                except TelegramError as e:
                    logger.error(f"发送消息到 {chat_id} 失败: {str(e)}")
                    continue

            return True

        except Exception as e:
            logger.error(f"发送审核请求失败: {str(e)}")
            return False

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
