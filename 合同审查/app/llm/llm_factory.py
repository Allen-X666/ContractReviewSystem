"""
统一LLM工厂

根据 settings.LLM_TYPE 配置自动选择通义千问、DeepSeek 或本地 Qwen/WebWorld-8B 后端。
"""

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel

from 合同审查.app.core.config import settings

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    统一LLM工厂

    根据 settings.LLM_TYPE 自动分发到对应的 LLM 后端：
    - "tongyi"      → TongyiLLMFactory (阿里云通义千问)
    - "deepseek"    → DeepSeekLLMFactory (DeepSeek)
    - "local_qwen"  → LocalQwenLLMFactory (本地 Qwen/WebWorld-8B)
    """

    @staticmethod
    def _get_factory():
        llm_type = settings.LLM_TYPE.lower()
        if llm_type == "deepseek":
            from .deepseek_llm import DeepSeekLLMFactory
            return DeepSeekLLMFactory
        elif llm_type == "tongyi":
            from .tongyi_llm import TongyiLLMFactory
            return TongyiLLMFactory
        elif llm_type == "local_qwen":
            from .local_qwen_llm import LocalQwenLLMFactory
            return LocalQwenLLMFactory
        else:
            raise ValueError(f"不支持的LLM类型: {llm_type}，可选值: tongyi, deepseek, local_qwen")

    @staticmethod
    def create_review_llm(**kwargs) -> BaseChatModel:
        """创建用于合同审查的LLM实例"""
        factory = LLMFactory._get_factory()
        logger.info(f"创建审查LLM，后端: {settings.LLM_TYPE}")
        return factory.create_review_llm(**kwargs)

    @staticmethod
    def create_summary_llm(**kwargs) -> BaseChatModel:
        """创建用于合同摘要的LLM实例"""
        factory = LLMFactory._get_factory()
        logger.info(f"创建摘要LLM，后端: {settings.LLM_TYPE}")
        return factory.create_summary_llm(**kwargs)

    @staticmethod
    def create_chat_llm(**kwargs) -> BaseChatModel:
        """创建用于对话的LLM实例"""
        factory = LLMFactory._get_factory()
        logger.info(f"创建对话LLM，后端: {settings.LLM_TYPE}")
        return factory.create_chat_llm(**kwargs)

    @staticmethod
    def create_streaming_llm(**kwargs) -> BaseChatModel:
        """创建用于流式对话的LLM实例"""
        factory = LLMFactory._get_factory()
        logger.info(f"创建流式LLM，后端: {settings.LLM_TYPE}")
        return factory.create_streaming_llm(**kwargs)
