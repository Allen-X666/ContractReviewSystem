"""
降级与熔断策略模块

提供 LLM 调用失败降级、RAG 检索失败降级等容错机制
"""

import logging
from typing import Optional, List, Dict, Any, Callable
from functools import wraps
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """降级策略枚举"""
    RETRY = "retry"                    # 重试
    FALLBACK_MODEL = "fallback_model"  # 降级到备用模型
    KEYWORD_MATCH = "keyword_match"    # 关键词匹配
    EMPTY_RESULT = "empty_result"      # 返回空结果
    RAISE_ERROR = "raise_error"        # 抛出异常


@dataclass
class FallbackResult:
    """降级结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    strategy_used: Optional[FallbackStrategy] = None
    original_error: Optional[Exception] = None


class LLMFallbackManager:
    """
    LLM 调用降级管理器

    当主模型调用失败时，自动降级到备用模型
    """

    # 备用模型配置（按优先级排序）
    FALLBACK_MODELS = [
        "qwen3.6-plus",      # 首选备用模型
        "qwen3.6-35b-a3b",        # 次选备用模型
        "qwen3.5-35b-a3b",         # 最后备用模型
    ]

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        self._failure_count: Dict[str, int] = {}
        self._circuit_breaker_threshold = 5  # 熔断阈值

    def _get_fallback_model(self, current_model: str) -> Optional[str]:
        """
        获取备用模型

        Args:
            current_model: 当前失败的模型名称

        Returns:
            备用模型名称，如果没有可用备用模型则返回 None
        """
        try:
            current_idx = self.FALLBACK_MODELS.index(current_model)
            # 返回列表中下一个模型
            if current_idx + 1 < len(self.FALLBACK_MODELS):
                return self.FALLBACK_MODELS[current_idx + 1]
        except ValueError:
            # 当前模型不在备用列表中，使用第一个备用模型
            return self.FALLBACK_MODELS[0] if self.FALLBACK_MODELS else None

        return None

    def _is_circuit_breaker_open(self, model: str) -> bool:
        """
        检查熔断器是否打开

        Args:
            model: 模型名称

        Returns:
            如果熔断器打开返回 True
        """
        return self._failure_count.get(model, 0) >= self._circuit_breaker_threshold

    def _record_failure(self, model: str):
        """记录模型调用失败"""
        self._failure_count[model] = self._failure_count.get(model, 0) + 1
        logger.warning(f"模型 {model} 失败次数: {self._failure_count[model]}")

    def _record_success(self, model: str):
        """记录模型调用成功，重置失败计数"""
        if model in self._failure_count:
            del self._failure_count[model]

    async def call_with_fallback(
        self,
        call_func: Callable,
        model: str,
        *args,
        **kwargs
    ) -> FallbackResult:
        """
        带降级策略的 LLM 调用

        Args:
            call_func: LLM 调用函数
            model: 主模型名称
            *args, **kwargs: 传递给 call_func 的参数

        Returns:
            FallbackResult: 包含调用结果或降级结果
        """
        # 检查熔断器
        if self._is_circuit_breaker_open(model):
            logger.warning(f"模型 {model} 熔断器已打开，直接尝试备用模型")
            fallback_model = self._get_fallback_model(model)
            if fallback_model:
                return await self._try_fallback_model(call_func, fallback_model, *args, **kwargs)
            else:
                return FallbackResult(
                    success=False,
                    error=f"模型 {model} 熔断器已打开，且无可用备用模型",
                    strategy_used=FallbackStrategy.RAISE_ERROR
                )

        # 尝试主模型
        try:
            result = await call_func(*args, **kwargs)
            self._record_success(model)
            return FallbackResult(
                success=True,
                data=result,
                strategy_used=None  # 主模型成功，未使用降级
            )
        except Exception as e:
            logger.error(f"主模型 {model} 调用失败: {e}")
            self._record_failure(model)

            # 尝试备用模型
            fallback_model = self._get_fallback_model(model)
            if fallback_model:
                logger.info(f"尝试降级到备用模型: {fallback_model}")
                return await self._try_fallback_model(call_func, fallback_model, *args, **kwargs)

            # 没有可用备用模型
            return FallbackResult(
                success=False,
                error=f"主模型 {model} 调用失败，且无可用备用模型",
                original_error=e,
                strategy_used=FallbackStrategy.RAISE_ERROR
            )

    async def _try_fallback_model(
        self,
        call_func: Callable,
        fallback_model: str,
        *args,
        **kwargs
    ) -> FallbackResult:
        """尝试使用备用模型"""
        try:
            # 修改 kwargs 中的 model 参数
            kwargs_with_fallback = kwargs.copy()
            kwargs_with_fallback['model'] = fallback_model

            result = await call_func(*args, **kwargs_with_fallback)
            logger.info(f"备用模型 {fallback_model} 调用成功")
            self._record_success(fallback_model)

            return FallbackResult(
                success=True,
                data=result,
                strategy_used=FallbackStrategy.FALLBACK_MODEL
            )
        except Exception as e:
            logger.error(f"备用模型 {fallback_model} 调用失败: {e}")
            self._record_failure(fallback_model)

            # 递归尝试下一个备用模型
            next_fallback = self._get_fallback_model(fallback_model)
            if next_fallback:
                return await self._try_fallback_model(call_func, next_fallback, *args, **kwargs)

            return FallbackResult(
                success=False,
                error=f"所有模型（包括备用模型）均调用失败",
                original_error=e,
                strategy_used=FallbackStrategy.RAISE_ERROR
            )


class RAGFallbackManager:
    """
    RAG 检索降级管理器

    当向量检索失败时，降级到关键词匹配
    """

    def __init__(self):
        self._keyword_cache: Dict[str, List[Dict]] = {}

    def keyword_fallback_search(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        关键词匹配降级搜索

        当向量检索失败时，使用简单的关键词匹配作为降级方案

        Args:
            query: 查询文本
            documents: 待搜索的文档列表
            top_k: 返回结果数量

        Returns:
            匹配的关键词结果列表
        """
        logger.info(f"使用关键词匹配降级搜索: '{query[:50]}...'")

        # 简单的关键词匹配算法
        query_keywords = set(query.lower().split())
        scored_results = []

        for doc in documents:
            content = doc.get("content", "").lower()
            title = doc.get("title", "").lower()

            # 计算匹配分数
            content_matches = sum(1 for kw in query_keywords if kw in content)
            title_matches = sum(1 for kw in query_keywords if kw in title)

            # 标题匹配权重更高
            score = content_matches + title_matches * 2

            if score > 0:
                scored_results.append({
                    "doc": doc,
                    "score": score
                })

        # 按分数排序
        scored_results.sort(key=lambda x: x["score"], reverse=True)

        # 返回前 top_k 个结果
        results = [item["doc"] for item in scored_results[:top_k]]

        logger.info(f"关键词匹配找到 {len(results)} 个结果")
        return results

    async def retrieve_with_fallback(
        self,
        retrieve_func: Callable,
        query: str,
        documents: Optional[List[Dict]] = None,
        *args,
        **kwargs
    ) -> FallbackResult:
        """
        带降级策略的 RAG 检索

        Args:
            retrieve_func: 检索函数
            query: 查询文本
            documents: 用于关键词匹配的文档列表（降级时使用）
            *args, **kwargs: 传递给 retrieve_func 的参数

        Returns:
            FallbackResult: 包含检索结果或降级结果
        """
        # 尝试向量检索
        try:
            result = await retrieve_func(*args, **kwargs)
            if result:
                return FallbackResult(
                    success=True,
                    data=result,
                    strategy_used=None  # 向量检索成功
                )
            else:
                logger.warning("向量检索返回空结果，尝试关键词匹配")
        except Exception as e:
            logger.error(f"向量检索失败: {e}，尝试关键词匹配")

        # 降级到关键词匹配
        if documents:
            fallback_results = self.keyword_fallback_search(query, documents, kwargs.get("top_k", 5))
            return FallbackResult(
                success=True,
                data=fallback_results,
                strategy_used=FallbackStrategy.KEYWORD_MATCH
            )

        # 无法降级，返回空结果
        return FallbackResult(
            success=False,
            data=[],
            error="向量检索失败且无法降级到关键词匹配",
            strategy_used=FallbackStrategy.EMPTY_RESULT
        )


# 全局降级管理器实例
_llm_fallback_manager: Optional[LLMFallbackManager] = None
_rag_fallback_manager: Optional[RAGFallbackManager] = None


def get_llm_fallback_manager() -> LLMFallbackManager:
    """获取全局 LLM 降级管理器"""
    global _llm_fallback_manager
    if _llm_fallback_manager is None:
        _llm_fallback_manager = LLMFallbackManager()
    return _llm_fallback_manager


def get_rag_fallback_manager() -> RAGFallbackManager:
    """获取全局 RAG 降级管理器"""
    global _rag_fallback_manager
    if _rag_fallback_manager is None:
        _rag_fallback_manager = RAGFallbackManager()
    return _rag_fallback_manager


def with_llm_fallback(model: str = None):
    """
    LLM 调用降级装饰器

    使用示例:
        @with_llm_fallback(model="qwen3.6-flash")
        async def my_llm_call(prompt: str):
            # LLM 调用逻辑
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            manager = get_llm_fallback_manager()
            use_model = model or kwargs.get("model", "qwen3.6-flash")

            result = await manager.call_with_fallback(
                func,
                use_model,
                *args,
                **kwargs
            )

            if result.success:
                return result.data
            else:
                raise Exception(result.error) from result.original_error

        return wrapper
    return decorator
