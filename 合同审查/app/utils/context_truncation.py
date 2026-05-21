"""
对话上下文截断工具模块

提供滑动窗口截断功能，保留最近 N 条对话消息
"""

import logging
from typing import List, Any

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    BaseMessage,
)

from 合同审查.app.core.config import settings

logger = logging.getLogger(__name__)


def trim_messages_sliding_window(
    messages: List[BaseMessage],
    max_messages: int = None,
    preserve_system: bool = True
) -> List[BaseMessage]:
    """
    使用滑动窗口截断对话消息，保留最近 N 条

    Args:
        messages: 原始消息列表
        max_messages: 最大保留消息数，默认使用配置值
        preserve_system: 是否保留系统提示消息

    Returns:
        截断后的消息列表
    """
    if max_messages is None:
        max_messages = settings.MAX_HISTORY_MESSAGES

    if not messages or len(messages) <= max_messages:
        return messages

    if not settings.CONTEXT_TRUNCATION_ENABLED:
        logger.debug(f"上下文截断已禁用，保留全部 {len(messages)} 条消息")
        return messages

    # 分离系统消息和其他消息
    system_messages = []
    other_messages = []

    for msg in messages:
        if isinstance(msg, SystemMessage):
            system_messages.append(msg)
        else:
            other_messages.append(msg)

    # 计算需要保留的非系统消息数量
    if preserve_system:
        available_slots = max(0, max_messages - len(system_messages))
    else:
        available_slots = max_messages

    # 保留最近的消息
    kept_messages = other_messages[-available_slots:] if available_slots > 0 else []

    # 组装结果：系统消息 + 保留的最近消息
    result = system_messages + kept_messages

    trimmed_count = len(messages) - len(result)
    logger.info(
        f"上下文截断: 原始 {len(messages)} 条消息 -> 保留 {len(result)} 条, "
        f"截断 {trimmed_count} 条早期消息"
    )

    return result


def trim_messages_by_checkpoint(
    checkpoint: dict,
    max_messages: int = None
) -> dict:
    """
    对 checkpoint 中的消息进行截断

    Args:
        checkpoint: LangGraph checkpoint 字典
        max_messages: 最大保留消息数

    Returns:
        修改后的 checkpoint
    """
    if max_messages is None:
        max_messages = settings.MAX_HISTORY_MESSAGES

    if not checkpoint or 'channel_values' not in checkpoint:
        return checkpoint

    channel_values = checkpoint.get('channel_values', {})
    if 'messages' not in channel_values:
        return checkpoint

    messages = channel_values['messages']
    if not isinstance(messages, list) or len(messages) <= max_messages:
        return checkpoint

    # 截断消息
    trimmed_messages = trim_messages_sliding_window(messages, max_messages)

    # 更新 checkpoint
    checkpoint['channel_values']['messages'] = trimmed_messages

    return checkpoint


def get_message_summary(messages: List[BaseMessage]) -> str:
    """
    获取消息列表的摘要信息（用于日志记录）

    Args:
        messages: 消息列表

    Returns:
        摘要字符串
    """
    human_count = sum(1 for m in messages if isinstance(m, HumanMessage))
    ai_count = sum(1 for m in messages if isinstance(m, AIMessage))
    tool_count = sum(1 for m in messages if isinstance(m, ToolMessage))
    system_count = sum(1 for m in messages if isinstance(m, SystemMessage))

    return (
        f"总计:{len(messages)} 条 "
        f"(用户:{human_count} AI:{ai_count} 工具:{tool_count} 系统:{system_count})"
    )
