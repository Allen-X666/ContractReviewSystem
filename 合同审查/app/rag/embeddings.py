"""
向量嵌入模块

提供文本向量嵌入功能，支持多种嵌入模型。
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
import numpy as np

from 合同审查.app.core.config import settings

logger = logging.getLogger(__name__)


class BaseEmbeddings(ABC):
    """嵌入模型基类"""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档列表"""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """嵌入查询文本"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """返回嵌入向量维度"""
        pass


class OpenAIEmbeddings(BaseEmbeddings):
    """
    OpenAI 嵌入模型

    使用 OpenAI API 生成文本嵌入。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = settings.OPENAI_EMBEDDING_MODEL,
    ):
        """
        初始化 OpenAI 嵌入模型

        Args:
            api_key: OpenAI API 密钥
            base_url: 自定义 API 基础 URL
            model: 模型名称
        """
        try:
            import openai
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model

        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

        # 不同模型的维度
        self._dimension_map = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文档列表

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        # 批量处理，每次最多 100 条
        all_embeddings = []
        batch_size = 100

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.embeddings.create(
                model=self.model,
                input=batch,
            )
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入查询文本

        Args:
            text: 查询文本

        Returns:
            List[float]: 嵌入向量
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=[text],
        )
        return response.data[0].embedding

    @property
    def dimension(self) -> int:
        """返回嵌入向量维度"""
        return self._dimension_map.get(self.model, 1536)


class HuggingFaceEmbeddings(BaseEmbeddings):
    """
    HuggingFace 嵌入模型

    使用本地 HuggingFace 模型生成文本嵌入。
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        model: Optional[str] = None,
        device: Optional[str] = None,
        normalize_embeddings: bool = True,
    ):
        """
        初始化 HuggingFace 嵌入模型

        Args:
            model_name: 模型名称
            model: 模型名称（与model_name兼容）
            device: 计算设备 (cpu/cuda)
            normalize_embeddings: 是否归一化嵌入向量
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("请安装 sentence-transformers: pip install sentence-transformers")

        # 兼容 model 和 model_name 参数
        self.model_name = model_name or model or settings.EMBEDDING_MODEL
        self.device = device or ("cuda" if self._check_cuda() else "cpu")
        self.normalize_embeddings = normalize_embeddings

        # 对于多模态模型，使用不同的初始化方式
        # 先尝试使用本地缓存，如果失败则联网下载
        if "vl" in self.model_name.lower():
            try:
                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    trust_remote_code=True,
                    local_files_only=True
                )
                logger.info(f"Embedding 模型从本地缓存加载成功: {self.model_name}")
            except Exception as e:
                logger.warning(f"本地缓存加载失败，尝试联网下载: {e}")
                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    trust_remote_code=True
                )
        else:
            try:
                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    local_files_only=True
                )
                logger.info(f"Embedding 模型从本地缓存加载成功: {self.model_name}")
            except Exception as e:
                logger.warning(f"本地缓存加载失败，尝试联网下载: {e}")
                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device
                )

    def _check_cuda(self) -> bool:
        """检查 CUDA 是否可用"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文档列表

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入查询文本

        Args:
            text: 查询文本

        Returns:
            List[float]: 嵌入向量
        """
        embedding = self.model.encode(
            [text],
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )
        return embedding[0].tolist()

    @property
    def dimension(self) -> int:
        """返回嵌入向量维度"""
        return self.model.get_sentence_embedding_dimension()


class ModelScopeEmbeddings(BaseEmbeddings):
    """
    ModelScope 嵌入模型

    使用阿里ModelScope平台的中文嵌入模型，国内高速下载。
    """

    def __init__(
        self,
        model: str = settings.MODELSCOPE_EMBEDDING_MODEL,
    ):
        """
        初始化 ModelScope 嵌入模型

        Args:
            model: 模型名称
        """
        try:
            from modelscope.pipelines import pipeline
            from modelscope.utils.constant import Tasks
        except ImportError:
            raise ImportError("请安装 modelscope: pip install modelscope")

        self.model_name = model
        self._pipeline = pipeline(
            task=Tasks.text_embedding,
            model=model,
        )
        self._dimension = None

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文档列表

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        results = self._pipeline(texts)
        return [result["embedding"] for result in results]

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入查询文本

        Args:
            text: 查询文本

        Returns:
            List[float]: 嵌入向量
        """
        result = self._pipeline(text)
        return result[0]["embedding"]

    @property
    def dimension(self) -> int:
        """返回嵌入向量维度"""
        if self._dimension is None:
            sample = self.embed_query("sample")
            self._dimension = len(sample)
        return self._dimension


class OllamaEmbeddings(BaseEmbeddings):
    """
    Ollama 嵌入模型

    使用本地 Ollama 服务生成文本嵌入。
    """

    def __init__(
        self,
        model: str = settings.OLLAMA_EMBEDDING_MODEL,
        base_url: str = "http://localhost:11434",
    ):
        """
        初始化 Ollama 嵌入模型

        Args:
            model: 模型名称
            base_url: Ollama 服务地址
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._dimension = None

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """调用 Ollama API 生成嵌入"""
        import requests

        embeddings = []
        for text in texts:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            data = response.json()
            embeddings.append(data["embedding"])

        return embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文档列表

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入查询文本

        Args:
            text: 查询文本

        Returns:
            List[float]: 嵌入向量
        """
        embeddings = self._embed([text])
        return embeddings[0]

    @property
    def dimension(self) -> int:
        """返回嵌入向量维度"""
        if self._dimension is None:
            # 通过实际调用来获取维度
            sample_embedding = self.embed_query("sample")
            self._dimension = len(sample_embedding)
        return self._dimension


class DashScopeEmbeddings(BaseEmbeddings):
    """
    阿里云 DashScope 嵌入模型

    使用阿里云 DashScope API 生成文本嵌入。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = settings.EMBEDDING_MODEL,
    ):
        """
        初始化 DashScope 嵌入模型

        Args:
            api_key: DashScope API 密钥
            model: 模型名称
        """
        try:
            import dashscope
        except ImportError:
            raise ImportError("请安装 dashscope: pip install dashscope")

        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.model = model

        dashscope.api_key = self.api_key

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文档列表

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        # 根据模型选择调用方式
        if "vl" in self.model.lower() and "embedding" not in self.model.lower():
            # 多模态嵌入模型使用 DashScope 原生 API
            return self._embed_multimodal(texts)
        else:
            # 纯文本嵌入模型使用 TextEmbedding
            from dashscope import TextEmbedding

            all_embeddings = []
            batch_size = 25

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = TextEmbedding.call(
                    model=self.model,
                    input=batch,
                )

                if response.status_code == 200:
                    embeddings = [item["embedding"] for item in response.output["embeddings"]]
                    all_embeddings.extend(embeddings)
                else:
                    raise RuntimeError(f"Embedding API 调用失败: {response.message}")

            return all_embeddings

    def _embed_multimodal(self, texts: List[str]) -> List[List[float]]:
        """使用 DashScope 多模态嵌入 API"""
        from dashscope import MultiModalEmbedding

        all_embeddings = []
        for text in texts:
            response = MultiModalEmbedding.call(
                model=self.model,
                input=[{"text": text}],
            )

            if response.status_code == 200:
                embedding = response.output["embeddings"][0]["embedding"]
                all_embeddings.append(embedding)
            else:
                raise RuntimeError(f"Embedding API 调用失败: {response.message}")

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入查询文本

        Args:
            text: 查询文本

        Returns:
            List[float]: 嵌入向量
        """
        embeddings = self.embed_documents([text])
        return embeddings[0]

    @property
    def dimension(self) -> int:
        """返回嵌入向量维度"""
        return 2560


class TransformersPipelineEmbeddings(BaseEmbeddings):
    """
    Transformers Pipeline 嵌入模型

    使用 HuggingFace transformers 的 pipeline('feature-extraction') 接口生成文本嵌入。
    通过对 token 级别输出进行均值池化（mean pooling）得到句子级向量。
    """

    def __init__(
        self,
        model: str = settings.EMBEDDING_MODEL,
        device: Optional[str] = None,
        normalize_embeddings: bool = True,
        trust_remote_code: bool = True,
        batch_size: int = 8,
    ):
        try:
            from transformers import pipeline as hf_pipeline
        except ImportError:
            raise ImportError("请安装 transformers: pip install transformers")

        self.model_name = model
        self.normalize_embeddings = normalize_embeddings
        self.trust_remote_code = trust_remote_code
        self.batch_size = batch_size

        if device is None:
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        self.device = device

        self._pipe = hf_pipeline(
            task="feature-extraction",
            model=self.model_name,
            device=self.device,
            trust_remote_code=self.trust_remote_code,
        )
        self._dimension = None

    def _mean_pooling(self, output) -> np.ndarray:
        """对 token 级别输出进行均值池化，得到句子级向量"""
        if hasattr(output, "numpy"):
            arr = output.numpy()
        elif isinstance(output, np.ndarray):
            arr = output
        else:
            arr = np.array(output)

        if arr.ndim == 3:
            arr = arr[0]

        if arr.ndim == 1:
            return arr

        return arr.mean(axis=0)

    def _normalize(self, vec: np.ndarray) -> np.ndarray:
        """归一化向量"""
        norm = np.linalg.norm(vec)
        if norm > 0:
            return vec / norm
        return vec

    def _process_output(self, output) -> np.ndarray:
        vec = self._mean_pooling(output)
        if self.normalize_embeddings:
            vec = self._normalize(vec)
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            outputs = self._pipe(batch)
            for output in outputs:
                vec = self._process_output(output)
                all_embeddings.append(vec.tolist())
        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        output = self._pipe(text)
        if isinstance(output, list) and len(output) > 0 and isinstance(output[0], list):
            output = output[0]
        vec = self._process_output(output)
        return vec.tolist()

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            sample = self.embed_query("sample")
            self._dimension = len(sample)
        return self._dimension


class Embeddings:
    """
    通用嵌入模型接口

    提供统一的接口，支持多种嵌入模型。
    """

    EMBEDDING_TYPES = {
        "openai": OpenAIEmbeddings,
        "huggingface": HuggingFaceEmbeddings,
        "modelscope": ModelScopeEmbeddings,
        "ollama": OllamaEmbeddings,
        "dashscope": DashScopeEmbeddings,
        "transformers_pipeline": TransformersPipelineEmbeddings,
    }

    def __init__(
        self,
        embedding_type: Optional[str] = None,
        **kwargs,
    ):
        """
        初始化嵌入模型

        Args:
            embedding_type: 嵌入模型类型，默认从 settings.EMBEDDING_TYPE 读取
            **kwargs: 传递给具体嵌入模型的参数
        """
        embedding_type = embedding_type or settings.EMBEDDING_TYPE
        embedding_class = self.EMBEDDING_TYPES.get(embedding_type)
        if not embedding_class:
            raise ValueError(f"未知的嵌入模型类型: {embedding_type}")

        self.embeddings = embedding_class(**kwargs)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文档列表

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入查询文本

        Args:
            text: 查询文本

        Returns:
            List[float]: 嵌入向量
        """
        return self.embeddings.embed_query(text)

    @property
    def dimension(self) -> int:
        """返回嵌入向量维度"""
        return self.embeddings.dimension

    def similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """
        计算两个嵌入向量的余弦相似度

        Args:
            embedding1: 第一个嵌入向量
            embedding2: 第二个嵌入向量

        Returns:
            float: 余弦相似度 (-1 到 1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))


_embeddings_cache: Dict[str, "Embeddings"] = {}


def get_embeddings(
    embedding_type: Optional[str] = None,
    **kwargs,
) -> "Embeddings":
    """
    便捷函数：获取嵌入模型实例（单例缓存）

    相同配置的嵌入模型只会初始化一次，后续调用直接返回缓存实例。

    Args:
        embedding_type: 嵌入模型类型，默认从 settings.EMBEDDING_TYPE 读取
        **kwargs: 传递给具体嵌入模型的参数

    Returns:
        Embeddings: 嵌入模型实例
    """
    global _embeddings_cache
    resolved_type = embedding_type or settings.EMBEDDING_TYPE
    cache_key = f"{resolved_type}:{kwargs.get('model', settings.EMBEDDING_MODEL)}"
    if cache_key not in _embeddings_cache:
        _embeddings_cache[cache_key] = Embeddings(embedding_type=embedding_type, **kwargs)
    return _embeddings_cache[cache_key]
