"""
向量存储模块

支持 Chroma 和 FAISS 两种向量数据库。
适配合同条款数据结构。
"""

import logging
import os
import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

from .contract_schema import ClauseChunk

logger = logging.getLogger(__name__)


class ClauseVectorRecord:
    """条款向量记录"""

    def __init__(
        self,
        id: str,
        vector: List[float],
        clause_id: str,
        clause_no: str,
        clause_content: str,
        clause_title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.vector = vector
        self.clause_id = clause_id
        self.clause_no = clause_no
        self.clause_content = clause_content
        self.clause_title = clause_title
        self.metadata = metadata or {}

    @classmethod
    def from_clause_chunk(
        cls,
        chunk: ClauseChunk,
        vector: List[float],
        record_id: Optional[str] = None,
    ) -> "ClauseVectorRecord":
        """从 ClauseChunk 创建记录"""
        return cls(
            id=record_id or chunk.clause_id,
            vector=vector,
            clause_id=chunk.clause_id,
            clause_no=chunk.clause_no,
            clause_content=chunk.clause_content,
            clause_title=chunk.clause_title,
            metadata=chunk.metadata,
        )

    def to_clause_chunk(self) -> ClauseChunk:
        """转换为 ClauseChunk"""
        return ClauseChunk(
            clause_id=self.clause_id,
            clause_no=self.clause_no,
            clause_content=self.clause_content,
            clause_title=self.clause_title,
            metadata=self.metadata,
        )


class BaseVectorStore(ABC):
    """向量存储基类"""

    @abstractmethod
    def add_clauses(
        self,
        chunks: List[ClauseChunk],
        embeddings: List[List[float]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """添加条款向量到存储"""
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[ClauseVectorRecord, float]]:
        """搜索相似向量"""
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """删除指定 ID 的向量"""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """清空存储"""
        pass

    @abstractmethod
    def count(self) -> int:
        """返回存储的向量数量"""
        pass


class ChromaVectorStore(BaseVectorStore):
    """
    Chroma 向量存储

    使用 Chroma 数据库存储和检索条款向量。
    """

    def __init__(
        self,
        collection_name: str = "contract_clauses",
        persist_directory: Optional[str] = None,
        embedding_function=None,
    ):
        """
        初始化 Chroma 向量存储

        Args:
            collection_name: 集合名称
            persist_directory: 持久化目录
            embedding_function: 可选的嵌入函数
        """
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise ImportError("请安装 chromadb: pip install chromadb")

        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # 创建客户端
        if persist_directory:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False),
            )
        else:
            self.client = chromadb.EphemeralClient()

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )

    def add_clauses(
        self,
        chunks: List[ClauseChunk],
        embeddings: List[List[float]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        添加条款向量到存储

        Args:
            chunks: 条款块列表
            embeddings: 嵌入向量列表
            ids: 自定义 ID 列表

        Returns:
            List[str]: 添加的 ID 列表
        """
        if ids is None:
            ids = [chunk.clause_id for chunk in chunks]

        # 提取条款内容
        texts = [chunk.clause_content for chunk in chunks]
        
        # 构建元数据
        metadatas = []
        for chunk in chunks:
            metadata = {
                "clause_id": chunk.clause_id,
                "clause_no": chunk.clause_no,
                "clause_title": chunk.clause_title,
                **chunk.metadata,
            }
            # 确保元数据值可序列化
            serializable_metadata = {}
            for key, value in metadata.items():
                if value is None:
                    serializable_metadata[key] = ""
                elif isinstance(value, (str, int, float, bool)):
                    serializable_metadata[key] = value
                else:
                    serializable_metadata[key] = str(value)
            metadatas.append(serializable_metadata)

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        return ids

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[ClauseVectorRecord, float]]:
        """
        搜索相似向量

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            List[Tuple[ClauseVectorRecord, float]]: 记录和相似度分数列表
        """
        logger.info(f"【Chroma向量库】执行相似性搜索 | top_k={top_k} | 向量维度={len(query_embedding)}")
        if filter_dict:
            logger.info(f"【Chroma向量库】过滤条件: {filter_dict}")

        logger.debug(f"【Chroma向量库】查询向量前5维: {query_embedding[:5]}...")

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_dict,
            include=["metadatas", "documents", "distances"],
        )

        records = []
        result_count = len(results["ids"][0]) if results["ids"] else 0
        logger.info(f"【Chroma向量库】原始返回结果数: {result_count}")

        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}

                record = ClauseVectorRecord(
                    id=results["ids"][0][i],
                    vector=[],  # Chroma 不返回向量
                    clause_id=metadata.get("clause_id", ""),
                    clause_no=metadata.get("clause_no", ""),
                    clause_content=results["documents"][0][i] if results["documents"] else "",
                    clause_title=metadata.get("clause_title") or None,
                    metadata={k: v for k, v in metadata.items()
                             if k not in ["clause_id", "clause_no", "clause_title"]},
                )
                # 距离转换为相似度分数 (Chroma 使用余弦距离，范围[0, 2])
                distance = results["distances"][0][i] if results["distances"] else 0
                # 正确的余弦距离转相似度：cosine_similarity = 1 - cosine_distance
                # 但Chroma的余弦距离已经是 1 - cosine_similarity，所以需要转换
                score = max(0.0, 1.0 - distance / 2.0)  # 归一化到[0, 1]
                records.append((record, score))

                logger.info(f"【Chroma向量库】结果 {i+1}: "
                           f"ID={record.id} | "
                           f"条款号={record.clause_no} | "
                           f"距离={distance:.4f} | "
                           f"相似度={score:.4f} | "
                           f"内容: {record.clause_content[:80]}...")

        logger.info(f"【Chroma向量库】搜索完成，共找到 {len(records)} 条记录")
        return records

    def delete(self, ids: List[str]) -> bool:
        """删除指定 ID 的向量"""
        try:
            self.collection.delete(ids=ids)
            return True
        except Exception:
            return False

    def clear(self) -> bool:
        """清空存储"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(name=self.collection_name)
            return True
        except Exception:
            return False

    def count(self) -> int:
        """返回存储的向量数量"""
        return self.collection.count()

    def get_all_documents(self) -> List[ClauseVectorRecord]:
        """
        获取所有文档记录

        Returns:
            List[ClauseVectorRecord]: 所有文档记录列表
        """
        try:
            # 获取集合中的所有文档
            result = self.collection.get(
                include=["metadatas", "documents"]
            )

            records = []
            if result["ids"]:
                for i, doc_id in enumerate(result["ids"]):
                    metadata = result["metadatas"][i] if result["metadatas"] else {}

                    record = ClauseVectorRecord(
                        id=doc_id,
                        vector=[],  # 不返回向量以节省内存
                        clause_id=metadata.get("clause_id", ""),
                        clause_no=metadata.get("clause_no", ""),
                        clause_content=result["documents"][i] if result["documents"] else "",
                        clause_title=metadata.get("clause_title") or None,
                        metadata={k: v for k, v in metadata.items()
                                 if k not in ["clause_id", "clause_no", "clause_title"]},
                    )
                    records.append(record)

            logger.info(f"【Chroma向量库】获取所有文档: {len(records)} 条记录")
            return records

        except Exception as e:
            logger.error(f"【Chroma向量库】获取所有文档失败: {e}")
            return []


class FAISSVectorStore(BaseVectorStore):
    """
    FAISS 向量存储

    使用 FAISS 库进行高效的向量相似度搜索。
    """

    def __init__(
        self,
        dimension: int = 768,
        index_type: str = "Flat",
        persist_path: Optional[str] = None,
    ):
        """
        初始化 FAISS 向量存储

        Args:
            dimension: 向量维度
            index_type: 索引类型 (Flat, IVF, HNSW 等)
            persist_path: 持久化路径
        """
        try:
            import faiss
        except ImportError:
            raise ImportError("请安装 faiss: pip install faiss-cpu 或 faiss-gpu")

        self.dimension = dimension
        self.index_type = index_type
        self.persist_path = persist_path
        self.faiss = faiss

        # 存储元数据
        self.id_to_index: Dict[str, int] = {}
        self.index_to_id: Dict[int, str] = {}
        self.clause_data: Dict[str, Dict[str, Any]] = {}
        self.current_index = 0

        # 创建索引
        if index_type == "Flat":
            self.index = faiss.IndexFlatIP(dimension)
        elif index_type == "IVF":
            quantizer = faiss.IndexFlatIP(dimension)
            nlist = 100
            self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
        elif index_type == "HNSW":
            self.index = faiss.IndexHNSWFlat(dimension, 32)
        else:
            raise ValueError(f"不支持的索引类型: {index_type}")

        # 加载已有数据
        if persist_path and os.path.exists(persist_path):
            self._load()

    def _load(self):
        """从磁盘加载数据"""
        if not self.persist_path:
            return

        index_path = os.path.join(self.persist_path, "index.faiss")
        if os.path.exists(index_path):
            self.index = self.faiss.read_index(index_path)

        metadata_path = os.path.join(self.persist_path, "metadata.pkl")
        if os.path.exists(metadata_path):
            with open(metadata_path, "rb") as f:
                data = pickle.load(f)
                self.id_to_index = data["id_to_index"]
                self.index_to_id = data["index_to_id"]
                self.clause_data = data["clause_data"]
                self.current_index = data["current_index"]

    def _save(self):
        """保存数据到磁盘"""
        if not self.persist_path:
            return

        os.makedirs(self.persist_path, exist_ok=True)

        index_path = os.path.join(self.persist_path, "index.faiss")
        self.faiss.write_index(self.index, index_path)

        metadata_path = os.path.join(self.persist_path, "metadata.pkl")
        with open(metadata_path, "wb") as f:
            pickle.dump({
                "id_to_index": self.id_to_index,
                "index_to_id": self.index_to_id,
                "clause_data": self.clause_data,
                "current_index": self.current_index,
            }, f)

    def add_clauses(
        self,
        chunks: List[ClauseChunk],
        embeddings: List[List[float]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        添加条款向量到存储

        Args:
            chunks: 条款块列表
            embeddings: 嵌入向量列表
            ids: 自定义 ID 列表

        Returns:
            List[str]: 添加的 ID 列表
        """
        if ids is None:
            ids = [chunk.clause_id for chunk in chunks]

        # 存储条款数据
        for i, chunk in enumerate(chunks):
            self.clause_data[ids[i]] = {
                "clause_id": chunk.clause_id,
                "clause_no": chunk.clause_no,
                "clause_content": chunk.clause_content,
                "clause_title": chunk.clause_title,
                "metadata": chunk.metadata,
            }

        # 归一化向量
        vectors = np.array(embeddings, dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        vectors = vectors / norms

        # 添加索引映射
        start_idx = self.current_index
        for i, id in enumerate(ids):
            idx = start_idx + i
            self.id_to_index[id] = idx
            self.index_to_id[idx] = id

        self.current_index += len(ids)

        # 添加到 FAISS 索引
        if self.index_type == "IVF" and not self.index.is_trained:
            self.index.train(vectors)
        self.index.add(vectors)

        self._save()
        return ids

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[ClauseVectorRecord, float]]:
        """
        搜索相似向量
        """
        # 归一化查询向量
        query_vector = np.array([query_embedding], dtype=np.float32)
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm

        # 搜索
        scores, indices = self.index.search(query_vector, top_k * 2)

        records = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:
                continue

            id = self.index_to_id.get(int(idx))
            if not id:
                continue

            data = self.clause_data.get(id, {})
            
            # 过滤
            if filter_dict:
                metadata = data.get("metadata", {})
                if not all(metadata.get(k) == v for k, v in filter_dict.items()):
                    continue

            record = ClauseVectorRecord(
                id=id,
                vector=[],
                clause_id=data.get("clause_id", ""),
                clause_no=data.get("clause_no", ""),
                clause_content=data.get("clause_content", ""),
                clause_title=data.get("clause_title"),
                metadata=data.get("metadata", {}),
            )
            records.append((record, float(scores[0][i])))

            if len(records) >= top_k:
                break

        return records

    def delete(self, ids: List[str]) -> bool:
        """删除指定 ID 的向量"""
        for id in ids:
            if id in self.clause_data:
                del self.clause_data[id]
                if id in self.id_to_index:
                    idx = self.id_to_index[id]
                    del self.id_to_index[id]
                    del self.index_to_id[idx]

        self._save()
        return True

    def clear(self) -> bool:
        """清空存储"""
        if self.index_type == "Flat":
            self.index = self.faiss.IndexFlatIP(self.dimension)
        elif self.index_type == "IVF":
            quantizer = self.faiss.IndexFlatIP(self.dimension)
            self.index = self.faiss.IndexIVFFlat(quantizer, self.dimension, 100)
        elif self.index_type == "HNSW":
            self.index = self.faiss.IndexHNSWFlat(self.dimension, 32)

        self.id_to_index.clear()
        self.index_to_id.clear()
        self.clause_data.clear()
        self.current_index = 0

        self._save()
        return True

    def count(self) -> int:
        """返回存储的向量数量"""
        return len(self.clause_data)


class VectorStore:
    """
    通用向量存储接口

    提供统一的接口，支持多种向量数据库。
    """

    STORE_TYPES = {
        "chroma": ChromaVectorStore,
        "faiss": FAISSVectorStore,
    }

    def __init__(
        self,
        store_type: str = "chroma",
        **kwargs,
    ):
        """
        初始化向量存储

        Args:
            store_type: 存储类型
            **kwargs: 传递给具体存储的参数
        """
        store_class = self.STORE_TYPES.get(store_type)
        if not store_class:
            raise ValueError(f"未知的存储类型: {store_type}")

        self.store = store_class(**kwargs)

    def add_clauses(
        self,
        chunks: List[ClauseChunk],
        embeddings: List[List[float]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        添加条款向量到存储

        Args:
            chunks: 条款块列表
            embeddings: 嵌入向量列表
            ids: 自定义 ID 列表

        Returns:
            List[str]: 添加的 ID 列表
        """
        return self.store.add_clauses(chunks, embeddings, ids)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[ClauseVectorRecord, float]]:
        """
        搜索相似向量

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            List[Tuple[ClauseVectorRecord, float]]: 记录和相似度分数列表
        """
        return self.store.search(query_embedding, top_k, filter_dict)

    def delete(self, ids: List[str]) -> bool:
        """删除指定 ID 的向量"""
        return self.store.delete(ids)

    def clear(self) -> bool:
        """清空存储"""
        return self.store.clear()

    def count(self) -> int:
        """返回存储的向量数量"""
        return self.store.count()


_vector_store_cache = {}

LAW_VECTOR_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "vector_db", "law_documents")


def get_vector_store(
    store_type: str = "chroma",
    **kwargs,
) -> VectorStore:
    """
    便捷函数：获取向量存储实例（单例缓存）

    Args:
        store_type: 存储类型
        **kwargs: 传递给具体存储的参数

    Returns:
        VectorStore: 向量存储实例
    """
    global _vector_store_cache
    cache_key = store_type
    if cache_key not in _vector_store_cache:
        _vector_store_cache[cache_key] = VectorStore(store_type=store_type, **kwargs)
    return _vector_store_cache[cache_key]


_law_stores_cache: Optional[List[ChromaVectorStore]] = None


def get_law_vector_stores() -> List[ChromaVectorStore]:
    """
    获取所有法律文档向量存储实例

    扫描 law_documents 持久化目录下的所有 Chroma 集合，
    返回可用的 ChromaVectorStore 列表。

    Returns:
        List[ChromaVectorStore]: 法律文档向量存储列表
    """
    global _law_stores_cache
    if _law_stores_cache is not None:
        return _law_stores_cache

    stores = []
    persist_dir = LAW_VECTOR_DB_DIR

    if not os.path.exists(persist_dir):
        logger.warning(f"法律文档向量库目录不存在: {persist_dir}")
        return stores

    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        collections = client.list_collections()
        logger.info(f"发现 {len(collections)} 个 Chroma 集合")

        for collection in collections:
            name = collection.name
            count = collection.count()
            if count > 0:
                store = ChromaVectorStore(
                    collection_name=name,
                    persist_directory=persist_dir,
                )
                stores.append(store)
                logger.info(f"  加载集合: {name} ({count} 条记录)")
            else:
                logger.debug(f"  跳过空集合: {name}")

    except Exception as e:
        logger.error(f"扫描法律文档向量库失败: {e}")

    _law_stores_cache = stores
    return stores


def search_law_documents(
    query_embedding: List[float],
    top_k: int = 5,
) -> List[Tuple[ClauseVectorRecord, float]]:
    """
    在所有法律文档集合中搜索，合并结果按相似度排序返回

    Args:
        query_embedding: 查询向量
        top_k: 返回结果数量

    Returns:
        List[Tuple[ClauseVectorRecord, float]]: 记录和相似度分数列表
    """
    stores = get_law_vector_stores()
    if not stores:
        logger.warning("没有可用的法律文档向量库")
        return []

    all_results = []
    for store in stores:
        try:
            results = store.search(query_embedding, top_k=top_k)
            all_results.extend(results)
        except Exception as e:
            logger.error(f"搜索集合 {store.collection_name} 失败: {e}")

    all_results.sort(key=lambda x: x[1], reverse=True)
    return all_results[:top_k]


# ==================== 系统操作知识库 ====================

SYSTEM_VECTOR_DB_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "vector_db", "system_operations"
)

_system_stores_cache: Optional[List[ChromaVectorStore]] = None


def get_system_vector_stores() -> List[ChromaVectorStore]:
    """
    获取所有系统操作文档向量存储实例

    扫描 system_operations 持久化目录下的所有 Chroma 集合，
    返回可用的 ChromaVectorStore 列表。

    Returns:
        List[ChromaVectorStore]: 系统操作文档向量存储列表
    """
    global _system_stores_cache
    if _system_stores_cache is not None:
        return _system_stores_cache

    stores = []
    persist_dir = SYSTEM_VECTOR_DB_DIR

    if not os.path.exists(persist_dir):
        logger.warning(f"系统操作向量库目录不存在: {persist_dir}")
        return stores

    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        collections = client.list_collections()
        logger.info(f"发现 {len(collections)} 个系统操作 Chroma 集合")

        for collection in collections:
            name = collection.name
            count = collection.count()
            if count > 0:
                store = ChromaVectorStore(
                    collection_name=name,
                    persist_directory=persist_dir,
                )
                stores.append(store)
                logger.info(f"  加载系统操作集合: {name} ({count} 条记录)")
            else:
                logger.debug(f"  跳过空集合: {name}")

    except Exception as e:
        logger.error(f"扫描系统操作向量库失败: {e}")

    _system_stores_cache = stores
    return stores


def search_system_documents(
    query_embedding: List[float],
    top_k: int = 5,
) -> List[Tuple[ClauseVectorRecord, float]]:
    """
    在所有系统操作文档集合中搜索，合并结果按相似度排序返回

    Args:
        query_embedding: 查询向量
        top_k: 返回结果数量

    Returns:
        List[Tuple[ClauseVectorRecord, float]]: 记录和相似度分数列表
    """
    stores = get_system_vector_stores()
    if not stores:
        logger.warning("没有可用的系统操作文档向量库")
        return []

    all_results = []
    for store in stores:
        try:
            results = store.search(query_embedding, top_k=top_k)
            all_results.extend(results)
        except Exception as e:
            logger.error(f"搜索系统操作集合 {store.collection_name} 失败: {e}")

    all_results.sort(key=lambda x: x[1], reverse=True)
    return all_results[:top_k]


def invalidate_system_stores_cache():
    """使系统操作向量存储缓存失效"""
    global _system_stores_cache
    _system_stores_cache = None
    logger.info("系统操作向量存储缓存已清除")
