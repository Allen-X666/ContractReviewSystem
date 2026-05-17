"""
文档加载器模块

支持加载 PDF、TXT、DOCX、JSON、Markdown 等格式的文档。
使用 LangChain 提供的加载器实现。
支持从文件路径或文件对象（BytesIO）加载文档。
"""

import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union, BinaryIO

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    JSONLoader,
    UnstructuredMarkdownLoader,
    CSVLoader,
)
from pypdf.errors import PdfStreamError

from .contract_schema import ContractClause, ClauseChunk


def _cleanup_temp_file(file_path: Path) -> None:
    """清理临时文件"""
    try:
        if file_path.exists():
            os.unlink(file_path)
    except Exception:
        pass


class BaseLoader(ABC):
    """文档加载器基类"""

    @abstractmethod
    def load(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> List[ClauseChunk]:
        """
        加载文档，返回条款块列表

        Args:
            file_path: 文件路径（与 file_obj 二选一）
            file_obj: 文件对象（BytesIO 等，与 file_path 二选一）
            file_name: 文件名（当使用 file_obj 时必需，用于确定文件类型）
        """
        pass

    def _get_file_info(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> tuple[Path, Optional[BinaryIO], str]:
        """
        统一处理文件路径和文件对象，返回临时文件路径（如有需要）、原始文件对象和文件名

        Returns:
            tuple: (处理后的文件路径, 原始文件对象, 文件名)
        """
        if file_path is not None:
            path = Path(file_path)
            return path, None, path.name

        if file_obj is not None:
            if file_name is None:
                raise ValueError("使用 file_obj 时必须提供 file_name 参数")
            # 创建临时文件
            suffix = Path(file_name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_obj.read())
                tmp_path = Path(tmp.name)
            # 重置文件对象指针
            file_obj.seek(0)
            return tmp_path, file_obj, file_name

        raise ValueError("必须提供 file_path 或 file_obj 之一")


class PDFLoader(BaseLoader):
    """PDF 文档加载器 - 使用 PyPDFLoader"""

    def __init__(self, extract_images: bool = False):
        self.extract_images = extract_images

    def load(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> List[ClauseChunk]:
        """
        加载 PDF 文档

        Args:
            file_path: PDF 文件路径
            file_obj: PDF 文件对象（BytesIO）
            file_name: 文件名（当使用 file_obj 时必需）

        Returns:
            List[ClauseChunk]: 条款块列表
        """
        path, original_obj, name = self._get_file_info(file_path, file_obj, file_name)
        is_temp = file_obj is not None

        try:
            loader = PyPDFLoader(
                str(path),
                extract_images=self.extract_images
            )

            docs = loader.load()

            result = []
            for i, doc in enumerate(docs):
                chunk = ClauseChunk(
                    clause_id=f"{Path(name).stem}_page_{i+1}",
                    clause_no=f"第{i+1}页",
                    clause_content=doc.page_content,
                    clause_title=None,
                    metadata={
                        "source": name if file_obj else str(file_path),
                        "file_type": "pdf",
                        "page_number": i + 1,
                        "file_name": name,
                    },
                )
                result.append(chunk)

            return result
        except PdfStreamError:
            raise ValueError(
                "PDF 文件已损坏或不完整，请检查文件是否上传完整后重试"
            )
        finally:
            if is_temp:
                _cleanup_temp_file(path)


class TXTLoader(BaseLoader):
    """TXT 文档加载器 - 使用 TextLoader"""

    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def load(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> List[ClauseChunk]:
        """
        加载 TXT 文档

        Args:
            file_path: TXT 文件路径
            file_obj: TXT 文件对象（BytesIO）
            file_name: 文件名（当使用 file_obj 时必需）

        Returns:
            List[ClauseChunk]: 条款块列表
        """
        path, original_obj, name = self._get_file_info(file_path, file_obj, file_name)
        is_temp = file_obj is not None

        try:
            loader = TextLoader(str(path), encoding=self.encoding)

            docs = loader.load()

            result = []
            for i, doc in enumerate(docs):
                chunk = ClauseChunk(
                    clause_id=f"{Path(name).stem}_chunk_{i}",
                    clause_no="",
                    clause_content=doc.page_content,
                    clause_title=None,
                    metadata={
                        "source": name if file_obj else str(file_path),
                        "file_type": "txt",
                        "file_name": name,
                    },
                )
                result.append(chunk)

            return result
        finally:
            if is_temp:
                _cleanup_temp_file(path)


class DOCXLoader(BaseLoader):
    """DOCX/DOC 文档加载器 - 使用 python-docx"""

    def load(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> List[ClauseChunk]:
        """
        加载 DOCX/DOC 文档

        Args:
            file_path: DOCX 文件路径
            file_obj: DOCX 文件对象（BytesIO）
            file_name: 文件名（当使用 file_obj 时必需）

        Returns:
            List[ClauseChunk]: 条款块列表
        """
        try:
            from docx import Document
        except ImportError:
            raise ImportError("请安装 python-docx: pip install python-docx")

        path, original_obj, name = self._get_file_info(file_path, file_obj, file_name)
        is_temp = file_obj is not None

        try:
            # 使用 python-docx 加载文档
            doc = Document(str(path))

            # 提取所有段落文本
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)

            # 合并为一个完整文本
            full_text = "\n".join(paragraphs)

            # 创建单个 ClauseChunk
            chunk = ClauseChunk(
                clause_id=f"{Path(name).stem}_doc",
                clause_no="",
                clause_content=full_text,
                clause_title=None,
                metadata={
                    "source": name if file_obj else str(file_path),
                    "file_type": "docx",
                    "file_name": name,
                    "paragraph_count": len(paragraphs),
                },
            )

            return [chunk]
        finally:
            if is_temp:
                _cleanup_temp_file(path)


class MarkdownLoader(BaseLoader):
    """Markdown 文档加载器 - 使用 UnstructuredMarkdownLoader"""

    def load(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> List[ClauseChunk]:
        """
        加载 Markdown 文档

        Args:
            file_path: Markdown 文件路径
            file_obj: Markdown 文件对象（BytesIO）
            file_name: 文件名（当使用 file_obj 时必需）

        Returns:
            List[ClauseChunk]: 条款块列表
        """
        path, original_obj, name = self._get_file_info(file_path, file_obj, file_name)
        is_temp = file_obj is not None

        try:
            loader = UnstructuredMarkdownLoader(str(path))

            docs = loader.load()

            result = []
            for i, doc in enumerate(docs):
                chunk = ClauseChunk(
                    clause_id=f"{Path(name).stem}_chunk_{i}",
                    clause_no="",
                    clause_content=doc.page_content,
                    clause_title=None,
                    metadata={
                        "source": name if file_obj else str(file_path),
                        "file_type": "markdown",
                        "file_name": name,
                    },
                )
                result.append(chunk)

            return result
        finally:
            if is_temp:
                _cleanup_temp_file(path)


class JSONLoaderWrapper(BaseLoader):
    """JSON 文档加载器 - 使用 JSONLoader"""

    def __init__(
        self,
        jq_schema: str = ".",
        content_key: Optional[str] = None,
        is_content_key_jq_parsable: bool = False,
    ):
        """
        初始化 JSON 加载器

        Args:
            jq_schema: jq 查询模式，用于提取内容
            content_key: 内容字段的键名
            is_content_key_jq_parsable: content_key 是否支持 jq 解析
        """
        self.jq_schema = jq_schema
        self.content_key = content_key
        self.is_content_key_jq_parsable = is_content_key_jq_parsable

    def load(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> List[ClauseChunk]:
        """
        加载 JSON 文档

        Args:
            file_path: JSON 文件路径
            file_obj: JSON 文件对象（BytesIO）
            file_name: 文件名（当使用 file_obj 时必需）

        Returns:
            List[ClauseChunk]: 条款块列表
        """
        path, original_obj, name = self._get_file_info(file_path, file_obj, file_name)
        is_temp = file_obj is not None

        try:
            loader = JSONLoader(
                file_path=str(path),
                jq_schema=self.jq_schema,
                content_key=self.content_key,
                is_content_key_jq_parsable=self.is_content_key_jq_parsable,
            )

            docs = loader.load()

            result = []
            for i, doc in enumerate(docs):
                chunk = ClauseChunk(
                    clause_id=f"{Path(name).stem}_chunk_{i}",
                    clause_no="",
                    clause_content=doc.page_content,
                    clause_title=None,
                    metadata={
                        "source": name if file_obj else str(file_path),
                        "file_type": "json",
                        "file_name": name,
                    },
                )
                result.append(chunk)

            return result
        finally:
            if is_temp:
                _cleanup_temp_file(path)


class CSVLoaderWrapper(BaseLoader):
    """CSV 文档加载器 - 使用 CSVLoader"""

    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def load(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> List[ClauseChunk]:
        """
        加载 CSV 文档

        Args:
            file_path: CSV 文件路径
            file_obj: CSV 文件对象（BytesIO）
            file_name: 文件名（当使用 file_obj 时必需）

        Returns:
            List[ClauseChunk]: 条款块列表
        """
        path, original_obj, name = self._get_file_info(file_path, file_obj, file_name)
        is_temp = file_obj is not None

        try:
            loader = CSVLoader(file_path=str(path), encoding=self.encoding)

            docs = loader.load()

            result = []
            for i, doc in enumerate(docs):
                chunk = ClauseChunk(
                    clause_id=f"{Path(name).stem}_row_{i}",
                    clause_no=f"第{i+1}行",
                    clause_content=doc.page_content,
                    clause_title=None,
                    metadata={
                        "source": name if file_obj else str(file_path),
                        "file_type": "csv",
                        "file_name": name,
                    },
                )
                result.append(chunk)

            return result
        finally:
            if is_temp:
                _cleanup_temp_file(path)


class ContractLoader(BaseLoader):
    """
    合同条款加载器

    专门用于加载结构化的合同条款数据。
    """

    def load(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> List[ClauseChunk]:
        """
        加载合同条款 JSON 文件

        Args:
            file_path: JSON 文件路径
            file_obj: JSON 文件对象（BytesIO）
            file_name: 文件名（当使用 file_obj 时必需）

        Returns:
            List[ClauseChunk]: 条款块列表
        """
        import json

        if file_obj is not None:
            if file_name is None:
                raise ValueError("使用 file_obj 时必须提供 file_name 参数")
            data = json.load(file_obj)
            source_name = file_name
            stem = Path(file_name).stem
        elif file_path is not None:
            file_path = Path(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            source_name = str(file_path)
            stem = file_path.stem
        else:
            raise ValueError("必须提供 file_path 或 file_obj 之一")

        result = []

        # 处理 ContractDocument 格式
        if isinstance(data, dict) and "clauses" in data:
            contract_id = data.get("contract_id", stem)
            for clause_data in data["clauses"]:
                clause = ContractClause(**clause_data)
                chunk = ClauseChunk.from_contract_clause(
                    clause,
                    extra_metadata={
                        "contract_id": contract_id,
                        "contract_name": data.get("contract_name"),
                        "contract_type": data.get("contract_type"),
                        "source": source_name,
                        "file_type": "contract_json",
                    }
                )
                result.append(chunk)

        # 处理 ContractClause 列表格式
        elif isinstance(data, list):
            for i, clause_data in enumerate(data):
                clause = ContractClause(**clause_data)
                chunk = ClauseChunk.from_contract_clause(
                    clause,
                    extra_metadata={
                        "source": source_name,
                        "file_type": "contract_json",
                        "index": i,
                    }
                )
                result.append(chunk)

        return result


class DocumentLoader:
    """
    通用文档加载器

    根据文件类型自动选择合适的加载器
    支持从文件路径或文件对象加载
    """

    LOADERS = {
        ".pdf": PDFLoader,
        ".txt": TXTLoader,
        ".docx": DOCXLoader,
        ".doc": DOCXLoader,  # .doc 格式也使用 DOCXLoader 处理
        ".md": MarkdownLoader,
        ".markdown": MarkdownLoader,
        ".json": JSONLoaderWrapper,
        ".csv": CSVLoaderWrapper,
        ".contract": ContractLoader,  # 合同专用格式
    }

    def __init__(self):
        self._loaders = {}

    def _get_loader(self, file_extension: str) -> BaseLoader:
        """获取对应文件类型的加载器"""
        file_extension = file_extension.lower()
        if file_extension not in self._loaders:
            loader_class = self.LOADERS.get(file_extension)
            if not loader_class:
                raise ValueError(f"不支持的文件类型: {file_extension}")
            self._loaders[file_extension] = loader_class()
        return self._loaders[file_extension]

    def load(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> List[ClauseChunk]:
        """
        加载单个文档

        Args:
            file_path: 文档文件路径（与 file_obj 二选一）
            file_obj: 文件对象（BytesIO 等，与 file_path 二选一）
            file_name: 文件名（当使用 file_obj 时必需，用于确定文件类型）

        Returns:
            List[ClauseChunk]: 条款块列表

        Examples:
            # 从文件路径加载
            chunks = loader.load(file_path="/path/to/contract.pdf")

            # 从文件对象加载
            with open("contract.pdf", "rb") as f:
                chunks = loader.load(file_obj=f, file_name="contract.pdf")

            # 从 BytesIO 加载
            import io
            file_bytes = io.BytesIO(pdf_bytes)
            chunks = loader.load(file_obj=file_bytes, file_name="contract.pdf")
        """
        if file_path is not None:
            file_path = Path(file_path)
            extension = file_path.suffix.lower()
            loader = self._get_loader(extension)
            return loader.load(file_path=file_path)

        if file_obj is not None:
            if file_name is None:
                raise ValueError("使用 file_obj 时必须提供 file_name 参数")
            extension = Path(file_name).suffix.lower()
            loader = self._get_loader(extension)
            return loader.load(file_obj=file_obj, file_name=file_name)

        raise ValueError("必须提供 file_path 或 file_obj 之一")

    def load_directory(
        self,
        directory: Union[str, Path],
        extensions: Optional[List[str]] = None,
        recursive: bool = True,
    ) -> List[ClauseChunk]:
        """
        加载目录中的所有文档

        Args:
            directory: 目录路径
            extensions: 要加载的文件扩展名列表，None 则加载所有支持的类型
            recursive: 是否递归加载子目录

        Returns:
            List[ClauseChunk]: 条款块列表
        """
        directory = Path(directory)
        chunks = []

        if extensions is None:
            extensions = list(self.LOADERS.keys())

        pattern = "**/*" if recursive else "*"

        for ext in extensions:
            for file_path in directory.glob(f"{pattern}{ext}"):
                try:
                    docs = self.load(file_path=file_path)
                    chunks.extend(docs)
                except Exception as e:
                    print(f"加载文件失败 {file_path}: {e}")

        return chunks

    def load_multiple(
        self,
        file_paths: Optional[List[Union[str, Path]]] = None,
        file_objects: Optional[List[tuple[BinaryIO, str]]] = None,
    ) -> List[ClauseChunk]:
        """
        加载多个文档

        Args:
            file_paths: 文档文件路径列表
            file_objects: 文件对象列表，每个元素为 (file_obj, file_name) 元组

        Returns:
            List[ClauseChunk]: 条款块列表
        """
        chunks = []

        if file_paths:
            for file_path in file_paths:
                try:
                    docs = self.load(file_path=file_path)
                    chunks.extend(docs)
                except Exception as e:
                    print(f"加载文件失败 {file_path}: {e}")

        if file_objects:
            for file_obj, file_name in file_objects:
                try:
                    docs = self.load(file_obj=file_obj, file_name=file_name)
                    chunks.extend(docs)
                except Exception as e:
                    print(f"加载文件对象失败 {file_name}: {e}")

        return chunks


def load_document(
    file_path: Optional[Union[str, Path]] = None,
    file_obj: Optional[BinaryIO] = None,
    file_name: Optional[str] = None,
) -> List[ClauseChunk]:
    """
    便捷函数：加载单个文档

    Args:
        file_path: 文档文件路径（与 file_obj 二选一）
        file_obj: 文件对象（BytesIO 等，与 file_path 二选一）
        file_name: 文件名（当使用 file_obj 时必需）

    Returns:
        List[ClauseChunk]: 条款块列表

    Examples:
        # 从文件路径加载
        chunks = load_document("/path/to/contract.pdf")

        # 从 BytesIO 加载
        import io
        file_bytes = io.BytesIO(pdf_bytes)
        chunks = load_document(file_obj=file_bytes, file_name="contract.pdf")
    """
    loader = DocumentLoader()
    return loader.load(file_path=file_path, file_obj=file_obj, file_name=file_name)


def load_documents(
    file_paths: Optional[List[Union[str, Path]]] = None,
    file_objects: Optional[List[tuple[BinaryIO, str]]] = None,
    directory: Optional[Union[str, Path]] = None,
    extensions: Optional[List[str]] = None,
    recursive: bool = True,
) -> List[ClauseChunk]:
    """
    便捷函数：加载多个文档或目录

    Args:
        file_paths: 文档文件路径列表
        file_objects: 文件对象列表，每个元素为 (file_obj, file_name) 元组
        directory: 目录路径
        extensions: 要加载的文件扩展名列表
        recursive: 是否递归加载子目录

    Returns:
        List[ClauseChunk]: 条款块列表

    Examples:
        # 加载多个文件路径
        chunks = load_documents(file_paths=["doc1.pdf", "doc2.txt"])

        # 加载多个文件对象
        files = [(io.BytesIO(pdf_bytes), "doc1.pdf"), (io.BytesIO(txt_bytes), "doc2.txt")]
        chunks = load_documents(file_objects=files)

        # 混合加载
        chunks = load_documents(
            file_paths=["doc1.pdf"],
            file_objects=[(io.BytesIO(txt_bytes), "doc2.txt")]
        )
    """
    loader = DocumentLoader()
    chunks = []

    if file_paths:
        chunks.extend(loader.load_multiple(file_paths=file_paths))

    if file_objects:
        chunks.extend(loader.load_multiple(file_objects=file_objects))

    if directory:
        chunks.extend(loader.load_directory(directory, extensions, recursive))

    return chunks
