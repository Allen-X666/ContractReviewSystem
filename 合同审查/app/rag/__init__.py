"""
RAG (Retrieval-Augmented Generation) 模块

提供文档加载、向量嵌入、向量存储、检索和 RAG 链的完整功能。
适配合同条款审查场景。
"""

# 合同数据结构
from .contract_schema import (
    ContractClause,
    ContractDocument,
    ClauseChunk,
    ContractReviewResult,
)

# 文档加载
from .document_loader import (
    DocumentLoader,
    load_document,
    load_documents,
    BaseLoader,
    PDFLoader,
    TXTLoader,
    DOCXLoader,
    MarkdownLoader,
    JSONLoaderWrapper,
    CSVLoaderWrapper,
    ContractLoader,
)

# 向量嵌入
from .embeddings import Embeddings, get_embeddings

# 向量存储
from .vector_store import (
    VectorStore,
    get_vector_store,
    ClauseVectorRecord,
    ChromaVectorStore,
    FAISSVectorStore,
)

# 检索器
from .retriever import (
    Retriever,
    get_retriever,
    get_law_retriever,
    RetrievedClause,
    VectorRetriever,
    KeywordRetriever,
    HybridRetriever,
    LawDocumentRetriever,
)

# 系统操作文档检索器
from .system_retriever import (
    SystemDocumentRetriever,
    CachedSystemDocumentRetriever,
    get_system_retriever,
    get_cached_system_retriever,
)

# RAG 链
from .rag_chain import (
    RAGChain,
    get_rag_chain,
    RAGResponse,
    BaseLLM,
    OpenAILLM,
    DashScopeLLM,
    OllamaLLM,
    ContractReviewRAGChain,
)

__all__ = [
    # 合同数据结构
    "ContractClause",
    "ContractDocument",
    "ClauseChunk",
    "ContractReviewResult",
    
    # 文档加载
    "DocumentLoader",
    "load_document",
    "load_documents",
    "BaseLoader",
    "PDFLoader",
    "TXTLoader",
    "DOCXLoader",
    "MarkdownLoader",
    "JSONLoaderWrapper",
    "CSVLoaderWrapper",
    "ContractLoader",
    
    # 向量嵌入
    "Embeddings",
    "get_embeddings",
    
    # 向量存储
    "VectorStore",
    "get_vector_store",
    "ClauseVectorRecord",
    "ChromaVectorStore",
    "FAISSVectorStore",
    
    # 检索器
    "Retriever",
    "get_retriever",
    "get_law_retriever",
    "RetrievedClause",
    "VectorRetriever",
    "KeywordRetriever",
    "HybridRetriever",
    "LawDocumentRetriever",

    # 系统操作文档检索器
    "SystemDocumentRetriever",
    "CachedSystemDocumentRetriever",
    "get_system_retriever",
    "get_cached_system_retriever",

    # RAG 链
    "RAGChain",
    "get_rag_chain",
    "RAGResponse",
    "BaseLLM",
    "OpenAILLM",
    "DashScopeLLM",
    "OllamaLLM",
    "ContractReviewRAGChain",
]
