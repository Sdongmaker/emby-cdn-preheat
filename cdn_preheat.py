"""
CDN 预热模块
支持腾讯云 CDN URL 预热，包括 URL 编码和批量提交
"""
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote, urlparse
import asyncio
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.cdn.v20180606 import cdn_client, models
import config

logger = logging.getLogger(__name__)


class CDNPreheatService:
    """CDN 预热服务"""

    def __init__(self):
        self.secret_id = config.TENCENT_SECRET_ID
        self.secret_key = config.TENCENT_SECRET_KEY
        self.batch_size = config.PREHEAT_BATCH_SIZE
        self.enabled = config.PREHEAT_ENABLED
        self.client = None

        # 初始化腾讯云客户端
        if self.enabled:
            self._init_client()

    def _init_client(self):
        """初始化腾讯云 CDN 客户端"""
        try:
            if not self.secret_id or not self.secret_key:
                logger.error("未配置腾讯云 API 凭证，无法初始化 CDN 客户端")
                self.enabled = False
                return

            if self.secret_id == "your_secret_id_here":
                logger.warning("腾讯云 API 凭证未设置，CDN 预热功能将不可用")
                self.enabled = False
                return

            cred = credential.Credential(self.secret_id, self.secret_key)
            self.client = cdn_client.CdnClient(cred, "")
            logger.info("✅ 腾讯云 CDN 客户端初始化成功")

        except Exception as e:
            logger.error(f"初始化腾讯云 CDN 客户端失败: {str(e)}")
            self.enabled = False

    def encode_url(self, url: str) -> str:
        """
        对 URL 进行编码

        Args:
            url: 原始 URL

        Returns:
            编码后的 URL
        """
        try:
            # 解析 URL
            parsed = urlparse(url)

            # 对路径部分进行编码（保留 /）
            # safe 参数指定不需要编码的字符
            encoded_path = quote(parsed.path, safe='/:')

            # 重新组装 URL
            encoded_url = f"{parsed.scheme}://{parsed.netloc}{encoded_path}"

            if parsed.query:
                encoded_query = quote(parsed.query, safe='=&')
                encoded_url += f"?{encoded_query}"

            logger.debug(f"URL 编码: {url} -> {encoded_url}")
            return encoded_url

        except Exception as e:
            logger.error(f"URL 编码失败: {str(e)}")
            return url

    async def preheat_url(self, url: str) -> Dict[str, Any]:
        """
        预热单个 URL

        Args:
            url: 要预热的 URL

        Returns:
            预热结果字典
        """
        return await self.preheat_urls([url])

    async def preheat_urls(self, urls: List[str]) -> Dict[str, Any]:
        """
        批量预热 URL

        Args:
            urls: URL 列表

        Returns:
            预热结果字典
        """
        if not self.enabled:
            logger.warning("CDN 预热功能未启用")
            return {
                "success": False,
                "message": "CDN 预热功能未启用",
                "urls": urls,
                "task_id": None
            }

        if not urls:
            return {
                "success": False,
                "message": "URL 列表为空",
                "urls": [],
                "task_id": None
            }

        try:
            logger.info("=" * 80)
            logger.info(f"🚀 开始 CDN 预热")
            logger.info(f"📊 预热 URL 数量: {len(urls)}")
            logger.info("=" * 80)

            # 对所有 URL 进行编码
            encoded_urls = [self.encode_url(url) for url in urls]

            # 显示编码前后对比
            for i, (original, encoded) in enumerate(zip(urls, encoded_urls), 1):
                logger.info(f"\n【URL {i}】")
                logger.info(f"  📝 原始 URL:")
                logger.info(f"     {original}")
                logger.info(f"  🔐 编码后 URL (将提交到 CDN):")
                logger.info(f"     {encoded}")

            logger.info("\n" + "=" * 80)
            logger.info(f"📤 准备提交 {len(encoded_urls)} 个编码后的 URL 到腾讯云 CDN")
            logger.info("=" * 80)

            # 调用腾讯云 CDN API
            result = await self._call_tencent_api(encoded_urls)

            logger.info("\n" + "=" * 80)
            if result["success"]:
                logger.info(f"✅ CDN 预热提交成功！")
                logger.info(f"📝 任务 ID: {result['task_id']}")
                logger.info(f"📊 已提交 URL 数量: {len(encoded_urls)}")
                logger.info(f"🔗 提交的编码 URL:")
                for i, url in enumerate(encoded_urls, 1):
                    logger.info(f"   {i}. {url}")
            else:
                logger.error(f"❌ CDN 预热提交失败")
                logger.error(f"💬 错误信息: {result['message']}")
                if 'error_code' in result:
                    logger.error(f"🔢 错误代码: {result['error_code']}")
            logger.info("=" * 80 + "\n")

            return result

        except Exception as e:
            logger.error(f"CDN 预热失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": str(e),
                "urls": urls,
                "task_id": None
            }

    async def _call_tencent_api(self, urls: List[str]) -> Dict[str, Any]:
        """
        调用腾讯云 CDN API 进行预热

        Args:
            urls: 已编码的 URL 列表

        Returns:
            API 调用结果
        """
        try:
            # 创建预热请求
            req = models.PushUrlsCacheRequest()
            req.Urls = urls

            # 异步调用 API（在线程池中执行）
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                self.client.PushUrlsCache,
                req
            )

            # 解析响应
            task_id = resp.TaskId if hasattr(resp, 'TaskId') else None

            return {
                "success": True,
                "message": "预热任务已提交",
                "urls": urls,
                "task_id": task_id
            }

        except TencentCloudSDKException as e:
            error_msg = f"腾讯云 API 错误: {e.get_message()}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "urls": urls,
                "task_id": None,
                "error_code": e.get_code()
            }

        except Exception as e:
            error_msg = f"调用 API 失败: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "urls": urls,
                "task_id": None
            }

    async def preheat_batch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        批量预热（自动分批）

        Args:
            urls: URL 列表

        Returns:
            每批的预热结果列表
        """
        if not urls:
            return []

        results = []

        # 按批次大小分割 URL
        for i in range(0, len(urls), self.batch_size):
            batch = urls[i:i + self.batch_size]
            logger.info(f"处理第 {i // self.batch_size + 1} 批，共 {len(batch)} 个 URL")

            result = await self.preheat_urls(batch)
            results.append(result)

            # 批次之间稍作延迟，避免触发 API 限流
            if i + self.batch_size < len(urls):
                await asyncio.sleep(1)

        return results

    def get_preheat_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询预热任务状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态信息
        """
        if not self.enabled or not self.client:
            return {
                "success": False,
                "message": "CDN 客户端未初始化"
            }

        try:
            req = models.DescribePushTasksRequest()
            req.TaskId = task_id

            resp = self.client.DescribePushTasks(req)

            # 解析任务状态
            if hasattr(resp, 'PushLogs') and resp.PushLogs:
                log = resp.PushLogs[0]
                return {
                    "success": True,
                    "task_id": task_id,
                    "status": log.Status,
                    "percent": log.Percent,
                    "create_time": log.CreateTime,
                    "update_time": log.UpdateTime
                }

            return {
                "success": False,
                "message": "未找到任务信息"
            }

        except TencentCloudSDKException as e:
            return {
                "success": False,
                "message": f"查询失败: {e.get_message()}",
                "error_code": e.get_code()
            }


# 全局 CDN 预热服务实例
cdn_service = CDNPreheatService()
