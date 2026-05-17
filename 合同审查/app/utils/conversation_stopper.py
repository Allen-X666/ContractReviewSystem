"""
对话中断管理器

用于管理对话的中断状态，支持用户随时中断 AI 的思考和输出。
"""

import asyncio
import logging
from typing import Dict, Optional, Set
from datetime import datetime, timedelta

from 合同审查.app.core.config import settings

logger = logging.getLogger(__name__)


class ConversationStopper:
    """
    对话中断管理器
    
    使用内存存储中断状态，支持：
    - 标记对话为中断状态
    - 检查对话是否被中断
    - 清理过期的中断标记
    """
    
    def __init__(self):
        # 存储被标记为中断的对话ID及其过期时间
        self._stopped_conversations: Dict[str, datetime] = {}
        # 存储正在进行的对话任务
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
    
    async def stop_conversation(self, conversation_id: str) -> bool:
        """
        标记对话为中断状态
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            是否成功标记
        """
        async with self._lock:
            # 设置中断标记，5分钟后过期
            self._stopped_conversations[conversation_id] = datetime.now() + timedelta(minutes=5)
            
            # 如果有正在进行的任务，取消它
            if conversation_id in self._active_tasks:
                task = self._active_tasks[conversation_id]
                if not task.done():
                    task.cancel()
                    logger.info(f"已取消对话 {conversation_id} 的任务")
            
            logger.info(f"对话 {conversation_id} 已被标记为中断")
            return True
    
    async def is_stopped(self, conversation_id: str) -> bool:
        """
        检查对话是否被中断
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            是否被中断
        """
        async with self._lock:
            if conversation_id not in self._stopped_conversations:
                return False
            
            expire_time = self._stopped_conversations[conversation_id]
            if datetime.now() > expire_time:
                # 已过期，清理
                del self._stopped_conversations[conversation_id]
                return False
            
            return True
    
    async def register_task(self, conversation_id: str, task: asyncio.Task):
        """
        注册正在进行的任务
        
        Args:
            conversation_id: 对话ID
            task: 异步任务
        """
        async with self._lock:
            self._active_tasks[conversation_id] = task
    
    async def unregister_task(self, conversation_id: str):
        """
        注销任务
        
        Args:
            conversation_id: 对话ID
        """
        async with self._lock:
            if conversation_id in self._active_tasks:
                del self._active_tasks[conversation_id]
    
    async def clear_stop_flag(self, conversation_id: str):
        """
        清除中断标记
        
        Args:
            conversation_id: 对话ID
        """
        async with self._lock:
            if conversation_id in self._stopped_conversations:
                del self._stopped_conversations[conversation_id]
                logger.info(f"已清除对话 {conversation_id} 的中断标记")
    
    async def cleanup_expired(self):
        """清理过期的中断标记"""
        async with self._lock:
            now = datetime.now()
            expired = [
                cid for cid, expire_time in self._stopped_conversations.items()
                if now > expire_time
            ]
            for cid in expired:
                del self._stopped_conversations[cid]
            if expired:
                logger.debug(f"清理了 {len(expired)} 个过期的中断标记")


# 全局中断管理器实例
_conversation_stopper: Optional[ConversationStopper] = None


def get_conversation_stopper() -> ConversationStopper:
    """获取全局中断管理器实例"""
    global _conversation_stopper
    if _conversation_stopper is None:
        _conversation_stopper = ConversationStopper()
    return _conversation_stopper


async def stop_conversation(conversation_id: str) -> bool:
    """
    中断指定对话
    
    Args:
        conversation_id: 对话ID
        
    Returns:
        是否成功中断
    """
    stopper = get_conversation_stopper()
    return await stopper.stop_conversation(conversation_id)


async def is_conversation_stopped(conversation_id: str) -> bool:
    """
    检查对话是否被中断
    
    Args:
        conversation_id: 对话ID
        
    Returns:
        是否被中断
    """
    stopper = get_conversation_stopper()
    return await stopper.is_stopped(conversation_id)


async def clear_stop_flag(conversation_id: str):
    """
    清除对话的中断标记
    
    Args:
        conversation_id: 对话ID
    """
    stopper = get_conversation_stopper()
    await stopper.clear_stop_flag(conversation_id)
