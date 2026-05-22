"""
系统操作文档检索器模块

提供系统操作知识库的检索功能，与法律文档检索器分离。
支持混合检索（向量检索 + 关键词检索）。
"""

import logging
import hashlib
import asyncio
from typing import List, Optional, Dict, Any, Set

from 合同审查.app.core.config import settings
from 合同审查.app.rag.embeddings import Embeddings, get_embeddings
from 合同审查.app.rag.vector_store import (
    ClauseVectorRecord,
    search_system_documents,
    get_system_vector_stores,
)
from 合同审查.app.rag.retriever import BaseRetriever, RetrievedClause, SimpleTTLCache

logger = logging.getLogger(__name__)


def _calculate_keyword_score(query: str, content: str) -> float:
    """计算关键词匹配分数（Jaccard 相似度）"""
    query_words: Set[str] = set(query.lower().split())
    content_words: Set[str] = set(content.lower().split())

    if not query_words:
        return 0.0

    intersection = len(query_words & content_words)
    union = len(query_words | content_words)

    return intersection / union if union > 0 else 0.0


def _hybrid_merge_results(
    query: str,
    vector_results: List[RetrievedClause],
    top_k: int,
    vector_weight: float,
    keyword_weight: float,
) -> List[RetrievedClause]:
    """
    混合检索融合

    结合向量检索和关键词检索的结果，按加权分数排序。
    """
    if not vector_results:
        return []

    clause_scores: Dict[str, tuple] = {}

    # 添加向量检索结果
    for clause in vector_results:
        clause_scores[clause.clause_id] = (clause, vector_weight * clause.score)

    # 关键词检索并融合
    for clause in vector_results:
        keyword_score = _calculate_keyword_score(query, clause.clause_content)
        if keyword_score > 0:
            existing_clause, existing_score = clause_scores[clause.clause_id]
            clause_scores[clause.clause_id] = (
                existing_clause,
                existing_score + keyword_weight * keyword_score
            )

    # 按融合分数排序
    sorted_results = sorted(
        clause_scores.values(),
        key=lambda x: x[1],
        reverse=True,
    )

    # 返回前 top_k 个结果
    results = []
    for clause, score in sorted_results[:top_k]:
        clause.score = score
        clause.metadata["hybrid_score"] = score
        results.append(clause)

    return results


class SystemDocumentRetriever(BaseRetriever):
    """
    系统操作文档检索器（支持混合检索）

    在所有已上传的系统操作文档向量库中进行相似度搜索，
    跨多个 collection 检索并合并结果。

    混合检索模式：
    - 启用时：向量检索 + 关键词检索融合
    - 禁用时：仅向量检索
    """

    def __init__(
        self,
        embeddings: Embeddings,
        enable_hybrid: bool = None,
        vector_weight: float = None,
        keyword_weight: float = None,
    ):
        self.embeddings = embeddings
        # 使用配置默认值
        self.enable_hybrid = enable_hybrid if enable_hybrid is not None else settings.HYBRID_RETRIEVAL_ENABLED
        self.vector_weight = vector_weight if vector_weight is not None else settings.HYBRID_VECTOR_WEIGHT
        self.keyword_weight = keyword_weight if keyword_weight is not None else settings.HYBRID_KEYWORD_WEIGHT

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        检索系统操作文档

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            List[str]: 检索结果内容列表
        """
        mode = "混合检索" if self.enable_hybrid else "向量检索"
        logger.info(f"【系统操作检索】查询: '{query[:100]}...' | top_k={top_k} | 模式={mode}")

        # 生成查询向量
        query_embedding = self.embeddings.embed_query(query)
        vector_norm = sum(x**2 for x in query_embedding) ** 0.5
        logger.info(f"【系统操作检索】查询向量维度: {len(query_embedding)} | 模长: {vector_norm:.6f}")

        if vector_norm < 1e-6:
            logger.error("【系统操作检索】查询向量为零向量")
            return []

        # 扩大召回数量用于混合检索
        recall_top_k = settings.HYBRID_RECALL_TOP_K if self.enable_hybrid else top_k
        results = search_system_documents(query_embedding, top_k=recall_top_k)

        if not results:
            logger.warning("【系统操作检索】未找到任何结果")
            return []

        # 转换为 RetrievedClause
        clauses = []
        for i, (record, score) in enumerate(results):
            clause = RetrievedClause.from_record(record, score)
            clause.metadata["vector_score"] = score
            clauses.append(clause)

        logger.info(f"【系统操作检索】向量召回: {len(clauses)} 条")

        # 混合检索融合
        if self.enable_hybrid and len(clauses) > 1:
            clauses = _hybrid_merge_results(
                query, clauses, top_k,
                self.vector_weight, self.keyword_weight
            )
            logger.info(
                f"【系统操作检索】混合融合完成: "
                f"返回前 {len(clauses)} 条 | "
                f"最高分={clauses[0].score:.4f}"
            )
        else:
            clauses = clauses[:top_k]

        # 返回内容列表
        contents = [clause.clause_content for clause in clauses]

        for i, content in enumerate(contents):
            logger.info(f"【系统操作检索】结果 {i+1}: 内容: {content[:80]}...")

        logger.info(f"【系统操作检索】共返回 {len(contents)} 条结果")
        return contents


class CachedSystemDocumentRetriever(BaseRetriever):
    """
    带缓存的系统操作文档检索器（支持混合检索）

    优化点：
    1. 嵌入模型延迟初始化，避免重复创建
    2. 检索结果TTL缓存，减少重复查询
    3. 异步缓存操作，不阻塞主流程
    4. 支持缓存统计和手动清理
    5. 支持混合检索（向量 + 关键词）
    """

    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        cache_size: int = 1000,
        cache_ttl: int = 3600,  # 1小时
        enable_hybrid: bool = None,
        vector_weight: float = None,
        keyword_weight: float = None,
    ):
        self._embeddings = embeddings
        self._cache = SimpleTTLCache(maxsize=cache_size, ttl=cache_ttl)
        self._embedding_lock = asyncio.Lock()
        self._stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        # 混合检索配置
        self.enable_hybrid = enable_hybrid if enable_hybrid is not None else settings.HYBRID_RETRIEVAL_ENABLED
        self.vector_weight = vector_weight if vector_weight is not None else settings.HYBRID_VECTOR_WEIGHT
        self.keyword_weight = keyword_weight if keyword_weight is not None else settings.HYBRID_KEYWORD_WEIGHT

    async def _get_embeddings(self) -> Embeddings:
        """延迟初始化嵌入模型（线程安全）"""
        if self._embeddings is None:
            async with self._embedding_lock:
                if self._embeddings is None:
                    logger.info("【CachedSystemRetriever】初始化嵌入模型...")
                    self._embeddings = get_embeddings(
                        embedding_type=settings.EMBEDDING_TYPE,
                        model=settings.EMBEDDING_MODEL,
                    )
                    logger.info("【CachedSystemRetriever】嵌入模型初始化完成")
        return self._embeddings

    def _generate_cache_key(self, query: str, top_k: int) -> str:
        """生成缓存key（基于查询内容和top_k的哈希）"""
        key_content = f"system:{query.strip().lower()}:{top_k}"
        return hashlib.md5(key_content.encode()).hexdigest()

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> List[RetrievedClause]:
        """
        检索系统操作文档（带缓存）

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件（暂不支持缓存）
            use_cache: 是否使用缓存

        Returns:
            List[RetrievedClause]: 检索结果列表
        """
        self._stats["total_queries"] += 1

        # 如果有过滤条件，跳过缓存
        if filter_dict:
            use_cache = False
            logger.debug("【CachedSystemRetriever】存在过滤条件，跳过缓存")

        cache_key = self._generate_cache_key(query, top_k)

        # 尝试从缓存获取
        if use_cache:
            cached_result = await self._cache.get(cache_key)
            if cached_result is not None:
                self._stats["cache_hits"] += 1
                logger.info(f"【CachedSystemRetriever】缓存命中 | key={cache_key[:8]}... | "
                           f"命中率: {self.cache_hit_rate:.1%}")
                return cached_result
            self._stats["cache_misses"] += 1
            logger.debug(f"【CachedSystemRetriever】缓存未命中 | key={cache_key[:8]}...")

        # 执行检索
        mode = "混合检索" if self.enable_hybrid else "向量检索"
        logger.info(f"【CachedSystemRetriever】执行检索 | query='{query[:100]}...' | top_k={top_k} | 模式={mode}")

        # 获取嵌入模型（延迟初始化）
        embeddings = await self._get_embeddings()

        # 生成查询向量
        query_embedding = embeddings.embed_query(query)
        vector_norm = sum(x**2 for x in query_embedding) ** 0.5

        if vector_norm < 1e-6:
            logger.error("【CachedSystemRetriever】查询向量为零向量")
            return []

        # 扩大召回数量用于混合检索
        recall_top_k = settings.HYBRID_RECALL_TOP_K if self.enable_hybrid else top_k
        results = search_system_documents(query_embedding, top_k=recall_top_k)

        if not results:
            logger.warning("【CachedSystemRetriever】未找到任何结果")
            return []

        # 转换为 RetrievedClause
        clauses = []
        for i, (record, score) in enumerate(results):
            clause = RetrievedClause.from_record(record, score)
            clause.metadata["vector_score"] = score
            clauses.append(clause)

        logger.info(f"【CachedSystemRetriever】向量召回: {len(clauses)} 条")

        # 混合检索融合
        if self.enable_hybrid and len(clauses) > 1:
            clauses = _hybrid_merge_results(
                query, clauses, top_k,
                self.vector_weight, self.keyword_weight
            )
            logger.info(
                f"【CachedSystemRetriever】混合融合完成: "
                f"返回前 {len(clauses)} 条 | "
                f"最高分={clauses[0].score:.4f}"
            )
        else:
            clauses = clauses[:top_k]

        logger.info(f"【CachedSystemRetriever】检索完成 | 共 {len(clauses)} 条结果")

        # 存入缓存
        if use_cache:
            await self._cache.set(cache_key, clauses)
            cache_stats = await self._cache.stats()
            logger.debug(f"【CachedSystemRetriever】结果已缓存 | 缓存大小: {cache_stats['size']}/{cache_stats['maxsize']}")

        return clauses

    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        total = self._stats["cache_hits"] + self._stats["cache_misses"]
        if total == 0:
            return 0.0
        return self._stats["cache_hits"] / total

    async def clear_cache(self):
        """清空缓存"""
        await self._cache.clear()
        self._stats["cache_hits"] = 0
        self._stats["cache_misses"] = 0
        logger.info("【CachedSystemRetriever】缓存已清空")

    async def get_stats(self) -> Dict[str, Any]:
        """获取检索器统计信息"""
        cache_stats = await self._cache.stats()
        return {
            "cache": cache_stats,
            "hits": self._stats["cache_hits"],
            "misses": self._stats["cache_misses"],
            "hit_rate": self.cache_hit_rate,
            "total_queries": self._stats["total_queries"],
        }


# ==================== 检索器单例缓存 ====================

_system_retriever_cache: Optional["SystemDocumentRetriever"] = None
_cached_system_retriever: Optional[CachedSystemDocumentRetriever] = None


async def get_system_retriever() -> SystemDocumentRetriever:
    """
    获取系统操作文档检索器实例（单例缓存）- 异步版本

    连接到已上传的系统操作文档向量库，用于在回答系统使用问题时
    检索相关操作指南。

    优先使用预热服务中已加载的 Embedding 模型，避免重复加载。
    支持混合检索（向量检索 + 关键词检索）。

    Returns:
        SystemDocumentRetriever: 系统操作文档检索器实例
    """
    global _system_retriever_cache
    if _system_retriever_cache is not None:
        return _system_retriever_cache

    # 优先使用预热服务中已加载的模型
    try:
        from 合同审查.app.services.warmup_service import get_warmup_service
        warmup_service = get_warmup_service()
        embeddings = await warmup_service.get_embedding_model()
        if embeddings is not None:
            logger.info("使用预热服务中的 Embedding 模型")
        else:
            logger.info("预热服务中无 Embedding 模型，创建新实例")
            embeddings = get_embeddings(
                embedding_type=settings.EMBEDDING_TYPE,
                model=settings.EMBEDDING_MODEL,
            )
    except Exception as e:
        logger.warning(f"获取预热模型失败: {e}，创建新实例")
        embeddings = get_embeddings(
            embedding_type=settings.EMBEDDING_TYPE,
            model=settings.EMBEDDING_MODEL,
        )

    # 创建系统文档检索器（已内置混合检索支持）
    _system_retriever_cache = SystemDocumentRetriever(embeddings=embeddings)

    mode = "混合检索" if settings.HYBRID_RETRIEVAL_ENABLED else "向量检索"
    logger.info(f"系统操作文档检索器初始化完成 | 模式: {mode} | 向量权重: {settings.HYBRID_VECTOR_WEIGHT} | 关键词权重: {settings.HYBRID_KEYWORD_WEIGHT}")
    return _system_retriever_cache


def get_cached_system_retriever(
    cache_size: int = 1000,
    cache_ttl: int = 3600,
    force_new: bool = False,
) -> CachedSystemDocumentRetriever:
    """
    获取带缓存的系统操作文档检索器实例（单例缓存）

    优化版本，支持：
    - 嵌入模型延迟初始化
    - 检索结果TTL缓存
    - 缓存统计和清理

    Args:
        cache_size: 缓存最大条目数
        cache_ttl: 缓存过期时间（秒）
        force_new: 强制创建新实例

    Returns:
        CachedSystemDocumentRetriever: 带缓存的系统操作文档检索器
    """
    global _cached_system_retriever

    if _cached_system_retriever is not None and not force_new:
        return _cached_system_retriever

    _cached_system_retriever = CachedSystemDocumentRetriever(
        embeddings=None,  # 延迟初始化
        cache_size=cache_size,
        cache_ttl=cache_ttl,
    )

    logger.info(f"带缓存的系统操作文档检索器初始化完成 | 缓存大小: {cache_size} | TTL: {cache_ttl}s")
    return _cached_system_retriever


async def clear_system_retriever_cache():
    """清空系统操作文档检索器缓存"""
    global _cached_system_retriever
    if _cached_system_retriever is not None:
        await _cached_system_retriever.clear_cache()
        logger.info("系统操作文档检索器缓存已清空")


async def get_system_retriever_stats() -> Optional[Dict[str, Any]]:
    """获取系统操作文档检索器统计信息"""
    global _cached_system_retriever
    if _cached_system_retriever is not None:
        return await _cached_system_retriever.get_stats()
    return None
