"""
RAG 链模块

整合文档加载、嵌入、存储、检索和生成的完整 RAG 流程。
适配合同条款数据结构。
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable, Union

from 合同审查.app.core.config import settings
from .document_loader import DocumentLoader, load_document, load_documents
from .embeddings import Embeddings, get_embeddings
from .vector_store import VectorStore, get_vector_store
from .retriever import Retriever, RetrievedClause, get_retriever
from .contract_schema import ClauseChunk, ContractClause, ContractReviewResult


@dataclass
class RAGResponse:
    """RAG 响应结果"""
    answer: str
    sources: List[RetrievedClause]
    query: str
    context: str


class BaseLLM(ABC):
    """大语言模型基类"""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        **kwargs,
    ) -> str:
        """生成文本"""
        pass


class OpenAILLM(BaseLLM):
    """OpenAI 大语言模型"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = settings.LLM_MODEL_DEFAULT,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """
        初始化 OpenAI LLM

        Args:
            api_key: API 密钥
            base_url: 自定义 API 基础 URL
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
        """
        try:
            import openai
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )
        return response.choices[0].message.content


class DashScopeLLM(BaseLLM):
    """阿里云 DashScope 大语言模型"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = settings.LLM_MODEL_DEFAULT,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """初始化 DashScope LLM"""
        try:
            import dashscope
        except ImportError:
            raise ImportError("请安装 dashscope: pip install dashscope")

        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        dashscope.api_key = self.api_key

    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        from dashscope import Generation

        response = Generation.call(
            model=kwargs.get("model", self.model),
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            result_format="message",
        )

        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            raise RuntimeError(f"API 调用失败: {response.message}")


class OllamaLLM(BaseLLM):
    """Ollama 本地大语言模型"""

    def __init__(
        self,
        model: str = settings.OLLAMA_LLM_MODEL,
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
    ):
        """初始化 Ollama LLM"""
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature

    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        import requests

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": kwargs.get("model", self.model),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", self.temperature),
                },
            },
        )
        response.raise_for_status()
        return response.json()["response"]


class RAGChain:
    """
    RAG 链

    整合完整的 RAG 流程：
    1. 文档加载（条款级别）
    2. 向量嵌入
    3. 向量存储
    4. 文档检索
    5. 答案生成
    """

    DEFAULT_PROMPT_TEMPLATE = """基于以下参考信息回答问题。

参考信息：
{context}

问题：{question}

请基于参考信息回答问题。如果参考信息不足以回答问题，请明确说明。
回答："""

    CONTRACT_REVIEW_PROMPT_TEMPLATE = """你是一位专业的合同审查专家。请基于以下合同条款和相关法律知识，回答关于合同的问题。

相关合同条款：
{context}

用户问题：{question}

请从专业角度分析并回答上述问题。注意：
1. 引用具体的合同条款编号作为依据
2. 指出潜在的风险点
3. 提供专业的建议

回答："""

    def __init__(
        self,
        document_loader: Optional[DocumentLoader] = None,
        embeddings: Optional[Embeddings] = None,
        vector_store: Optional[VectorStore] = None,
        retriever: Optional[Retriever] = None,
        llm: Optional[BaseLLM] = None,
        prompt_template: Optional[str] = None,
    ):
        """
        初始化 RAG 链

        Args:
            document_loader: 文档加载器
            embeddings: 嵌入模型
            vector_store: 向量存储
            retriever: 检索器
            llm: 大语言模型
            prompt_template: 提示词模板
        """
        self.document_loader = document_loader or DocumentLoader()
        self.embeddings = embeddings or get_embeddings(model=settings.EMBEDDING_MODEL)
        self.vector_store = vector_store or get_vector_store()
        self.retriever = retriever
        self.llm = llm
        self.prompt_template = prompt_template or self.DEFAULT_PROMPT_TEMPLATE

        # 如果没有提供检索器，创建默认的向量检索器
        if self.retriever is None:
            self.retriever = get_retriever(
                retriever_type="vector",
                vector_store=self.vector_store,
                embeddings=self.embeddings,
            )

    def load_and_index(
        self,
        file_path: Union[str, Path, List[Union[str, Path]]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        加载文档并建立索引

        Args:
            file_path: 文件路径或路径列表
            metadata: 附加元数据

        Returns:
            List[str]: 添加的条款 ID 列表
        """
        # 加载文档
        if isinstance(file_path, list):
            chunks = self.document_loader.load_multiple(file_path)
        else:
            chunks = self.document_loader.load(file_path)

        if not chunks:
            return []

        # 合并元数据
        if metadata:
            for chunk in chunks:
                chunk.metadata.update(metadata)

        # 生成嵌入（使用条款内容）
        texts = [chunk.clause_content for chunk in chunks]
        embeddings = self.embeddings.embed_documents(texts)

        # 存储到向量库
        ids = self.vector_store.add_clauses(chunks, embeddings)

        return ids

    def load_directory(
        self,
        directory: Union[str, Path],
        extensions: Optional[List[str]] = None,
        recursive: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        加载目录中的所有文档并建立索引

        Args:
            directory: 目录路径
            extensions: 文件扩展名列表
            recursive: 是否递归
            metadata: 附加元数据

        Returns:
            List[str]: 添加的条款 ID 列表
        """
        chunks = self.document_loader.load_directory(
            directory, extensions, recursive
        )

        if not chunks:
            return []

        # 合并元数据
        if metadata:
            for chunk in chunks:
                chunk.metadata.update(metadata)

        # 生成嵌入
        texts = [chunk.clause_content for chunk in chunks]
        embeddings = self.embeddings.embed_documents(texts)

        # 存储到向量库
        ids = self.vector_store.add_clauses(chunks, embeddings)

        return ids

    def query(
        self,
        question: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> RAGResponse:
        """
        查询 RAG 系统

        Args:
            question: 问题
            top_k: 检索条款数量
            filter_dict: 过滤条件

        Returns:
            RAGResponse: 响应结果
        """
        # 检索相关条款
        clauses = self.retriever.retrieve(
            query=question,
            top_k=top_k,
            filter_dict=filter_dict,
        )

        # 构建上下文（使用条款结构）
        context_parts = []
        for i, clause in enumerate(clauses, 1):
            part = f"[{i}]"
            if clause.clause_no:
                part += f" {clause.clause_no}"
            if clause.clause_title:
                part += f" {clause.clause_title}"
            part += f"\n{clause.clause_content}"
            context_parts.append(part)
        
        context = "\n\n".join(context_parts)

        # 构建提示词
        prompt = self.prompt_template.format(
            context=context,
            question=question,
        )

        # 生成答案
        if self.llm:
            answer = self.llm.generate(prompt)
        else:
            # 如果没有 LLM，只返回检索结果
            answer = "（未配置语言模型，仅返回检索结果）"

        return RAGResponse(
            answer=answer,
            sources=clauses,
            query=question,
            context=context,
        )

    def set_prompt_template(self, template: str) -> "RAGChain":
        """
        设置提示词模板

        Args:
            template: 提示词模板，需要包含 {context} 和 {question} 占位符

        Returns:
            RAGChain: 自身，支持链式调用
        """
        self.prompt_template = template
        return self

    def set_llm(self, llm: BaseLLM) -> "RAGChain":
        """
        设置语言模型

        Args:
            llm: 语言模型实例

        Returns:
            RAGChain: 自身，支持链式调用
        """
        self.llm = llm
        return self

    def clear_index(self) -> bool:
        """
        清空索引

        Returns:
            bool: 是否成功
        """
        return self.vector_store.clear()

    def get_index_count(self) -> int:
        """
        获取索引条款数量

        Returns:
            int: 条款数量
        """
        return self.vector_store.count()


class ContractReviewRAGChain(RAGChain):
    """
    合同审查专用 RAG 链

    针对合同审查场景优化的 RAG 流程。
    """

    def __init__(
        self,
        document_loader: Optional[DocumentLoader] = None,
        embeddings: Optional[Embeddings] = None,
        vector_store: Optional[VectorStore] = None,
        retriever: Optional[Retriever] = None,
        llm: Optional[BaseLLM] = None,
    ):
        """
        初始化合同审查 RAG 链

        Args:
            document_loader: 文档加载器
            embeddings: 嵌入模型
            vector_store: 向量存储
            retriever: 检索器
            llm: 大语言模型
        """
        super().__init__(
            document_loader=document_loader,
            embeddings=embeddings,
            vector_store=vector_store,
            retriever=retriever,
            llm=llm,
            prompt_template=self.CONTRACT_REVIEW_PROMPT_TEMPLATE,
        )

    def review_contract(
        self,
        contract_path: Union[str, Path],
        review_points: Optional[List[str]] = None,
    ) -> Dict[str, RAGResponse]:
        """
        审查合同

        Args:
            contract_path: 合同文件路径
            review_points: 审查要点列表，None 则使用默认要点

        Returns:
            Dict[str, RAGResponse]: 各审查要点的结果
        """
        # 加载并索引合同
        self.load_and_index(contract_path, metadata={"type": "contract"})

        # 默认审查要点
        if review_points is None:
            review_points = [
                "合同主体是否明确合法",
                "合同标的描述是否清晰",
                "价款及支付方式条款",
                "违约责任条款",
                "争议解决条款",
                "合同生效及终止条件",
                "保密条款",
                "知识产权条款",
            ]

        results = {}
        for point in review_points:
            response = self.query(point)
            results[point] = response

        return results

    def analyze_clause(
        self,
        clause_no: str,
    ) -> RAGResponse:
        """
        分析特定条款

        Args:
            clause_no: 条款编号

        Returns:
            RAGResponse: 分析结果
        """
        query = f"请详细分析 {clause_no} 条款的内容、潜在风险和建议"
        return self.query(query, filter_dict={"clause_no": clause_no})


def get_rag_chain(
    chain_type: str = "default",
    **kwargs,
) -> RAGChain:
    """
    便捷函数：获取 RAG 链实例

    Args:
        chain_type: 链类型 (default/contract)
        **kwargs: 传递给 RAG 链的参数

    Returns:
        RAGChain: RAG 链实例
    """
    if chain_type == "contract":
        return ContractReviewRAGChain(**kwargs)
    return RAGChain(**kwargs)
