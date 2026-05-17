"""
检索器模块

提供文档检索功能，支持多种检索策略。
适配合同条款数据结构。
"""

import logging
import hashlib
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Callable
from functools import lru_cache

from 合同审查.app.core.config import settings
from 合同审查.app.schemas.models import RelatedLaw
from .embeddings import Embeddings, get_embeddings
from .vector_store import VectorStore, get_vector_store, ClauseVectorRecord, search_law_documents, get_law_vector_stores
from .contract_schema import ClauseChunk

logger = logging.getLogger(__name__)


# ==================== 缓存实现 ====================

def _get_current_time() -> float:
    import time
    return time.time()


class SimpleTTLCache:
    """简单的TTL缓存实现（无需额外依赖）"""
    
    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._access_order: List[str] = []
        self._lock = asyncio.Lock()

    def _is_expired(self, key: str) -> bool:
        if key not in self._timestamps:
            return True
        return _get_current_time() - self._timestamps[key] > self.ttl
    
    def _evict_if_needed(self):
        while len(self._cache) >= self.maxsize and self._access_order:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                del self._timestamps[oldest_key]
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self._cache:
                if self._is_expired(key):
                    del self._cache[key]
                    del self._timestamps[key]
                    if key in self._access_order:
                        self._access_order.remove(key)
                    return None
                # 更新访问顺序（LRU）
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
                return self._cache[key]
            return None
    
    async def set(self, key: str, value: Any):
        async with self._lock:
            if key in self._cache:
                # 更新现有key
                if key in self._access_order:
                    self._access_order.remove(key)
            else:
                # 新key，可能需要淘汰
                self._evict_if_needed()
            
            self._cache[key] = value
            self._timestamps[key] = _get_current_time()
            self._access_order.append(key)
    
    async def clear(self):
        async with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._access_order.clear()
    
    async def stats(self) -> Dict[str, Any]:
        async with self._lock:
            return {
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "ttl": self.ttl,
            }


@dataclass
class RetrievedClause:
    """检索结果条款"""
    clause_id: str
    clause_no: str
    clause_content: str
    clause_title: Optional[str]
    metadata: Dict[str, Any]
    score: float

    @classmethod
    def from_record(
        cls,
        record: ClauseVectorRecord,
        score: float,
    ) -> "RetrievedClause":
        """从 ClauseVectorRecord 创建"""
        return cls(
            clause_id=record.clause_id,
            clause_no=record.clause_no,
            clause_content=record.clause_content,
            clause_title=record.clause_title,
            metadata=record.metadata,
            score=score,
        )

    @classmethod
    def from_chunk(
        cls,
        chunk: ClauseChunk,
        score: float,
    ) -> "RetrievedClause":
        """从 ClauseChunk 创建"""
        return cls(
            clause_id=chunk.clause_id,
            clause_no=chunk.clause_no,
            clause_content=chunk.clause_content,
            clause_title=chunk.clause_title,
            metadata=chunk.metadata,
            score=score,
        )


class BaseRetriever(ABC):
    """检索器基类"""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedClause]:
        """检索相关条款"""
        pass


class VectorRetriever(BaseRetriever):
    """
    向量检索器

    使用向量相似度进行条款检索。
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embeddings: Embeddings,
    ):
        """
        初始化向量检索器

        Args:
            vector_store: 向量存储实例
            embeddings: 嵌入模型实例
        """
        self.vector_store = vector_store
        self.embeddings = embeddings

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0,  # 相似度阈值，低于此值的结果将被过滤
    ) -> List[RetrievedClause]:
        """
        检索相关条款

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件
            score_threshold: 相似度阈值（0-1），低于此值的结果将被过滤

        Returns:
            List[RetrievedClause]: 检索结果列表
        """
        logger.info(f"【向量检索】查询: '{query[:100]}...' | top_k={top_k} | 阈值={score_threshold}")
        if filter_dict:
            logger.info(f"【向量检索】过滤条件: {filter_dict}")

        # 生成查询向量
        logger.debug("【向量检索】生成查询向量...")
        query_embedding = self.embeddings.embed_query(query)
        logger.debug(f"【向量检索】查询向量维度: {len(query_embedding)}")
        
        # 检查向量是否有效（非零向量）
        vector_norm = sum(x**2 for x in query_embedding) ** 0.5
        logger.info(f"【向量检索】查询向量模长: {vector_norm:.6f}")
        if vector_norm < 1e-6:
            logger.error("【向量检索】查询向量为零向量，请检查嵌入模型！")
            return []

        # 搜索相似向量
        logger.info("【向量检索】开始相似性搜索...")
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # 检索更多结果，以便过滤后仍有足够数量
            filter_dict=filter_dict,
        )
        
        # 检查向量库是否为空
        if not results:
            logger.warning("【向量检索】向量库为空或未找到任何结果")
            return []

        # 转换为 RetrievedClause 并过滤低相似度结果
        clauses = []
        logger.info(f"【向量检索】搜索完成，原始返回 {len(results)} 条结果")

        for i, (record, score) in enumerate(results):
            # 过滤低于阈值的結果
            if score < score_threshold:
                logger.debug(f"【向量检索】结果 {i+1} 相似度 {score:.4f} 低于阈值 {score_threshold}，已过滤")
                continue
                
            clause = RetrievedClause.from_record(record, score)
            clauses.append(clause)
            logger.info(f"【向量检索】结果 {i+1}/{len(results)}: "
                       f"条款[{clause.clause_no}] "
                       f"相似度={score:.4f} | "
                       f"内容: {clause.clause_content[:100]}...")
            
            # 达到top_k数量时停止
            if len(clauses) >= top_k:
                break

        logger.info(f"【向量检索】过滤后返回 {len(clauses)} 条结果（阈值: {score_threshold}）")
        return clauses


class KeywordRetriever(BaseRetriever):
    """
    关键词检索器

    使用关键词匹配进行条款检索。
    """

    def __init__(
        self,
        clauses: List[ClauseChunk],
    ):
        """
        初始化关键词检索器

        Args:
            clauses: 条款块列表
        """
        self.clauses = clauses

    def _calculate_keyword_score(self, query: str, clause_content: str) -> float:
        """计算关键词匹配分数"""
        query_words = set(query.lower().split())
        content_words = set(clause_content.lower().split())

        if not query_words:
            return 0.0

        # 计算 Jaccard 相似度
        intersection = len(query_words & content_words)
        union = len(query_words | content_words)

        return intersection / union if union > 0 else 0.0

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedClause]:
        """
        检索相关条款

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            List[RetrievedClause]: 检索结果列表
        """
        scored_clauses = []

        for clause in self.clauses:
            # 过滤
            if filter_dict:
                if not all(clause.metadata.get(k) == v for k, v in filter_dict.items()):
                    continue

            score = self._calculate_keyword_score(query, clause.clause_content)
            if score > 0:
                scored_clauses.append((clause, score))

        # 按分数排序
        scored_clauses.sort(key=lambda x: x[1], reverse=True)

        # 返回前 top_k 个结果
        results = []
        for clause, score in scored_clauses[:top_k]:
            results.append(RetrievedClause.from_chunk(clause, score))

        return results


class HybridRetriever(BaseRetriever):
    """
    混合检索器

    结合向量检索和关键词检索的优势。
    """

    def __init__(
        self,
        vector_retriever: VectorRetriever,
        keyword_retriever: Optional[KeywordRetriever] = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ):
        """
        初始化混合检索器

        Args:
            vector_retriever: 向量检索器
            keyword_retriever: 关键词检索器
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
        """
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedClause]:
        """
        检索相关条款

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            List[RetrievedClause]: 检索结果列表
        """
        # 向量检索
        vector_results = self.vector_retriever.retrieve(
            query=query,
            top_k=top_k * 2,
            filter_dict=filter_dict,
        )

        # 关键词检索
        keyword_results = []
        if self.keyword_retriever:
            keyword_results = self.keyword_retriever.retrieve(
                query=query,
                top_k=top_k * 2,
                filter_dict=filter_dict,
            )

        # 合并结果
        clause_scores: Dict[str, tuple] = {}

        # 添加向量检索结果
        for clause in vector_results:
            clause_scores[clause.clause_id] = (
                clause,
                self.vector_weight * clause.score,
            )

        # 添加关键词检索结果
        for clause in keyword_results:
            if clause.clause_id in clause_scores:
                existing_clause, existing_score = clause_scores[clause.clause_id]
                clause_scores[clause.clause_id] = (
                    existing_clause,
                    existing_score + self.keyword_weight * clause.score,
                )
            else:
                clause_scores[clause.clause_id] = (
                    clause,
                    self.keyword_weight * clause.score,
                )

        # 按分数排序
        sorted_results = sorted(
            clause_scores.values(),
            key=lambda x: x[1],
            reverse=True,
        )

        # 返回前 top_k 个结果
        results = []
        for clause, score in sorted_results[:top_k]:
            # 更新分数
            clause.score = score
            results.append(clause)

        return results


class LawDocumentRetriever(BaseRetriever):
    """
    法律文档检索器

    在所有已上传的法律文档向量库中进行相似度搜索，
    跨多个 collection 检索并合并结果。
    """

    def __init__(self, embeddings: Embeddings):
        self.embeddings = embeddings

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedClause]:
        logger.info(f"【法律文档检索】查询: '{query[:100]}...' | top_k={top_k}")

        query_embedding = self.embeddings.embed_query(query)
        vector_norm = sum(x**2 for x in query_embedding) ** 0.5
        logger.info(f"【法律文档检索】查询向量维度: {len(query_embedding)} | 模长: {vector_norm:.6f}")

        if vector_norm < 1e-6:
            logger.error("【法律文档检索】查询向量为零向量")
            return []

        results = search_law_documents(query_embedding, top_k=top_k)

        if not results:
            logger.warning("【法律文档检索】未找到任何结果")
            return []

        clauses = []
        for i, (record, score) in enumerate(results):
            clause = RetrievedClause.from_record(record, score)
            clauses.append(clause)
            logger.info(f"【法律文档检索】结果 {i+1}: "
                       f"条款[{clause.clause_no}] "
                       f"相似度={score:.4f} | "
                       f"来源={clause.metadata.get('source', '未知')} | "
                       f"内容: {clause.clause_content[:80]}...")

        logger.info(f"【法律文档检索】共返回 {len(clauses)} 条结果")
        return clauses


def _generate_cache_key(query: str, top_k: int) -> str:
    """生成缓存key（基于查询内容和top_k的哈希）"""
    key_content = f"{query.strip().lower()}:{top_k}"
    return hashlib.md5(key_content.encode()).hexdigest()


class CachedLawDocumentRetriever(BaseRetriever):
    """
    带缓存的法律文档检索器

    优化点：
    1. 嵌入模型延迟初始化，避免重复创建
    2. 检索结果TTL缓存，减少重复查询
    3. 异步缓存操作，不阻塞主流程
    4. 支持缓存统计和手动清理
    """

    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        cache_size: int = 1000,
        cache_ttl: int = 3600,  # 1小时
    ):
        self._embeddings = embeddings
        self._cache = SimpleTTLCache(maxsize=cache_size, ttl=cache_ttl)
        self._embedding_lock = asyncio.Lock()
        self._stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    async def _get_embeddings(self) -> Embeddings:
        """延迟初始化嵌入模型（线程安全）"""
        if self._embeddings is None:
            async with self._embedding_lock:
                if self._embeddings is None:
                    logger.info("【CachedLawRetriever】初始化嵌入模型...")
                    self._embeddings = get_embeddings(
                        embedding_type=settings.EMBEDDING_TYPE,
                        model=settings.EMBEDDING_MODEL,
                    )
                    logger.info("【CachedLawRetriever】嵌入模型初始化完成")
        return self._embeddings

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> List[RetrievedClause]:
        """
        检索关联法条（带缓存）

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
            logger.debug("【CachedLawRetriever】存在过滤条件，跳过缓存")

        cache_key = _generate_cache_key(query, top_k)
        
        # 尝试从缓存获取
        if use_cache:
            cached_result = await self._cache.get(cache_key)
            if cached_result is not None:
                self._stats["cache_hits"] += 1
                logger.info(f"【CachedLawRetriever】缓存命中 | key={cache_key[:8]}... | "
                           f"命中率: {self.cache_hit_rate:.1%}")
                return cached_result
            self._stats["cache_misses"] += 1
            logger.debug(f"【CachedLawRetriever】缓存未命中 | key={cache_key[:8]}...")

        # 执行检索
        logger.info(f"【CachedLawRetriever】执行检索 | query='{query[:100]}...' | top_k={top_k}")
        
        # 获取嵌入模型（延迟初始化）
        embeddings = await self._get_embeddings()
        
        # 生成查询向量
        query_embedding = embeddings.embed_query(query)
        vector_norm = sum(x**2 for x in query_embedding) ** 0.5
        
        if vector_norm < 1e-6:
            logger.error("【CachedLawRetriever】查询向量为零向量")
            return []

        # 搜索向量库
        results = search_law_documents(query_embedding, top_k=top_k)
        
        if not results:
            logger.warning("【CachedLawRetriever】未找到任何结果")
            return []

        # 转换为 RetrievedClause
        clauses = []
        for i, (record, score) in enumerate(results):
            clause = RetrievedClause.from_record(record, score)
            clauses.append(clause)
            logger.debug(f"【CachedLawRetriever】结果 {i+1}: "
                        f"条款[{clause.clause_no}] 相似度={score:.4f}")

        logger.info(f"【CachedLawRetriever】检索完成 | 共 {len(clauses)} 条结果")

        # 存入缓存
        if use_cache:
            await self._cache.set(cache_key, clauses)
            cache_stats = await self._cache.stats()
            logger.debug(f"【CachedLawRetriever】结果已缓存 | 缓存大小: {cache_stats['size']}/{cache_stats['maxsize']}")

        return clauses

    async def retrieve_as_related_laws(
        self,
        query: str,
        top_k: int = 5,
        use_cache: bool = True,
    ) -> List[RelatedLaw]:
        """
        检索并转换为 RelatedLaw 格式（供LLM使用）

        Args:
            query: 查询文本
            top_k: 返回结果数量
            use_cache: 是否使用缓存

        Returns:
            List[RelatedLaw]: 关联法条列表
        """
        clauses = await self.retrieve(query, top_k, use_cache=use_cache)
        
        related_laws = []
        for clause in clauses:
            related_law = RelatedLaw(
                law_id=0,  # 向量库中的记录可能没有law_id
                law_name=clause.metadata.get("law_name", clause.metadata.get("source", "未知法规")),
                article_no=clause.clause_no or "相关条款",
                content=clause.clause_content or "",
            )
            related_laws.append(related_law)
        
        return related_laws

    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        total = self._stats["cache_hits"] + self._stats["cache_misses"]
        if total == 0:
            return 0.0
        return self._stats["cache_hits"] / total

    async def get_stats(self) -> Dict[str, Any]:
        """获取检索器统计信息"""
        cache_stats = await self._cache.stats()
        return {
            "total_queries": self._stats["total_queries"],
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "cache_hit_rate": self.cache_hit_rate,
            "cache": cache_stats,
        }

    async def clear_cache(self):
        """清空缓存"""
        await self._cache.clear()
        logger.info("【CachedLawRetriever】缓存已清空")


class Retriever:
    """
    通用检索器接口

    提供统一的检索接口，支持多种检索策略。
    """

    RETRIEVER_TYPES = {
        "vector": VectorRetriever,
        "keyword": KeywordRetriever,
        "hybrid": HybridRetriever,
    }

    def __init__(
        self,
        retriever_type: str = "vector",
        **kwargs,
    ):
        """
        初始化检索器

        Args:
            retriever_type: 检索器类型
            **kwargs: 传递给具体检索器的参数
        """
        self.retriever_type = retriever_type
        self.retriever = None
        self.kwargs = kwargs

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedClause]:
        """
        检索相关条款

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            List[RetrievedClause]: 检索结果列表
        """
        if self.retriever is None:
            raise ValueError("检索器未初始化")
        return self.retriever.retrieve(query, top_k, filter_dict)


def get_retriever(
    retriever_type: str = "vector",
    vector_store: Optional[VectorStore] = None,
    embeddings: Optional[Embeddings] = None,
    **kwargs,
) -> Retriever:
    """
    便捷函数：获取检索器实例

    Args:
        retriever_type: 检索器类型
        vector_store: 向量存储实例
        embeddings: 嵌入模型实例
        **kwargs: 额外参数

    Returns:
        Retriever: 检索器实例
    """
    retriever = Retriever(retriever_type=retriever_type)

    if retriever_type == "vector":
        if vector_store is None:
            vector_store = get_vector_store()
        if embeddings is None:
            embeddings = get_embeddings(
                embedding_type=settings.EMBEDDING_TYPE,
                model=settings.EMBEDDING_MODEL,
            )
        retriever.retriever = VectorRetriever(
            vector_store=vector_store,
            embeddings=embeddings,
        )
    elif retriever_type == "hybrid":
        if vector_store is None:
            vector_store = get_vector_store()
        if embeddings is None:
            embeddings = get_embeddings(
                embedding_type=settings.EMBEDDING_TYPE,
                model=settings.EMBEDDING_MODEL,
            )
        vector_retriever = VectorRetriever(
            vector_store=vector_store,
            embeddings=embeddings,
        )
        retriever.retriever = HybridRetriever(
            vector_retriever=vector_retriever,
            **kwargs,
        )

    return retriever


# ==================== 检索器单例缓存 ====================

_law_retriever_cache: Optional["Retriever"] = None
_cached_law_retriever: Optional[CachedLawDocumentRetriever] = None


def get_law_retriever() -> "Retriever":
    """
    获取法律文档检索器实例（单例缓存）- 兼容旧版本

    连接到已上传的法律文档向量库，用于在合同审查时
    检索相关法律条款。

    Returns:
        Retriever: 法律文档检索器实例
    """
    global _law_retriever_cache
    if _law_retriever_cache is not None:
        return _law_retriever_cache

    embeddings = get_embeddings(
        embedding_type=settings.EMBEDDING_TYPE,
        model=settings.EMBEDDING_MODEL,
    )

    retriever = Retriever(retriever_type="vector")
    retriever.retriever = LawDocumentRetriever(embeddings=embeddings)

    _law_retriever_cache = retriever
    logger.info("法律文档检索器初始化完成")
    return _law_retriever_cache


def get_cached_law_retriever(
    cache_size: int = 1000,
    cache_ttl: int = 3600,
    force_new: bool = False,
) -> CachedLawDocumentRetriever:
    """
    获取带缓存的法律文档检索器实例（单例缓存）

    优化版本，支持：
    - 嵌入模型延迟初始化
    - 检索结果TTL缓存
    - 缓存统计和清理

    Args:
        cache_size: 缓存最大条目数
        cache_ttl: 缓存过期时间（秒）
        force_new: 强制创建新实例

    Returns:
        CachedLawDocumentRetriever: 带缓存的法律文档检索器
    """
    global _cached_law_retriever
    
    if _cached_law_retriever is not None and not force_new:
        return _cached_law_retriever
    
    _cached_law_retriever = CachedLawDocumentRetriever(
        embeddings=None,  # 延迟初始化
        cache_size=cache_size,
        cache_ttl=cache_ttl,
    )
    
    logger.info(f"带缓存的法律文档检索器初始化完成 | 缓存大小: {cache_size} | TTL: {cache_ttl}s")
    return _cached_law_retriever


async def clear_law_retriever_cache():
    """清空法律文档检索器缓存"""
    global _cached_law_retriever
    if _cached_law_retriever is not None:
        await _cached_law_retriever.clear_cache()
        logger.info("法律文档检索器缓存已清空")


async def get_law_retriever_stats() -> Optional[Dict[str, Any]]:
    """获取法律文档检索器统计信息"""
    global _cached_law_retriever
    if _cached_law_retriever is not None:
        return await _cached_law_retriever.get_stats()
    return None
