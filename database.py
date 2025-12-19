"""
数据库模型 - 存储待审核的 CDN 预热请求
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

# 数据库文件路径
DB_FILE = "preheat_review.db"


class ReviewDatabase:
    """CDN 预热审核数据库"""

    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()

            # 创建审核请求表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS review_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cdn_url TEXT NOT NULL,
                    media_name TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    emby_path TEXT,
                    host_path TEXT,
                    media_info TEXT,
                    status TEXT DEFAULT 'pending',
                    telegram_message_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    reviewed_by TEXT,
                    review_action TEXT,
                    UNIQUE(cdn_url)
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status
                ON review_requests(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON review_requests(created_at)
            """)

            conn.commit()
            logger.info("数据库初始化完成")

    def add_review_request(
        self,
        cdn_url: str,
        media_name: str,
        media_type: str,
        emby_path: str = "",
        host_path: str = "",
        media_info: Dict[str, Any] = None
    ) -> Optional[int]:
        """
        添加审核请求

        Args:
            cdn_url: CDN URL
            media_name: 媒体名称
            media_type: 媒体类型
            emby_path: Emby 路径
            host_path: 宿主机路径
            media_info: 媒体详细信息

        Returns:
            请求 ID，如果失败返回 None
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()

                media_info_json = json.dumps(media_info or {}, ensure_ascii=False)

                cursor.execute("""
                    INSERT INTO review_requests
                    (cdn_url, media_name, media_type, emby_path, host_path, media_info)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (cdn_url, media_name, media_type, emby_path, host_path, media_info_json))

                conn.commit()
                request_id = cursor.lastrowid
                logger.info(f"添加审核请求成功: ID={request_id}, URL={cdn_url}")
                return request_id

        except sqlite3.IntegrityError:
            logger.warning(f"审核请求已存在: {cdn_url}")
            return None
        except Exception as e:
            logger.error(f"添加审核请求失败: {str(e)}")
            return None

    def update_telegram_message_id(self, request_id: int, message_id: int):
        """更新 Telegram 消息 ID"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE review_requests
                    SET telegram_message_id = ?
                    WHERE id = ?
                """, (message_id, request_id))
                conn.commit()
                logger.info(f"更新消息 ID: request_id={request_id}, message_id={message_id}")
        except Exception as e:
            logger.error(f"更新消息 ID 失败: {str(e)}")

    def approve_request(self, request_id: int, reviewed_by: str = "unknown"):
        """批准预热请求"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE review_requests
                    SET status = 'approved',
                        reviewed_at = ?,
                        reviewed_by = ?,
                        review_action = 'approve'
                    WHERE id = ?
                """, (datetime.now().isoformat(), reviewed_by, request_id))
                conn.commit()
                logger.info(f"审核请求已批准: ID={request_id}, 审核人={reviewed_by}")
        except Exception as e:
            logger.error(f"批准请求失败: {str(e)}")

    def reject_request(self, request_id: int, reviewed_by: str = "unknown"):
        """拒绝预热请求"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE review_requests
                    SET status = 'rejected',
                        reviewed_at = ?,
                        reviewed_by = ?,
                        review_action = 'reject'
                    WHERE id = ?
                """, (datetime.now().isoformat(), reviewed_by, request_id))
                conn.commit()
                logger.info(f"审核请求已拒绝: ID={request_id}, 审核人={reviewed_by}")
        except Exception as e:
            logger.error(f"拒绝请求失败: {str(e)}")

    def get_request_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        """根据 ID 获取请求"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM review_requests WHERE id = ?
                """, (request_id,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"获取请求失败: {str(e)}")
            return None

    def get_pending_requests(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取待审核的请求"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM review_requests
                    WHERE status = 'pending'
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取待审核请求失败: {str(e)}")
            return []

    def get_approved_requests(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取已批准的请求"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM review_requests
                    WHERE status = 'approved'
                    ORDER BY reviewed_at DESC
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取已批准请求失败: {str(e)}")
            return []

    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM review_requests WHERE status = 'pending'")
                pending_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM review_requests WHERE status = 'approved'")
                approved_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM review_requests WHERE status = 'rejected'")
                rejected_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM review_requests")
                total_count = cursor.fetchone()[0]

                return {
                    "pending": pending_count,
                    "approved": approved_count,
                    "rejected": rejected_count,
                    "total": total_count
                }
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {"pending": 0, "approved": 0, "rejected": 0, "total": 0}


# 全局数据库实例
db = ReviewDatabase()
