"""
文档拆分器工厂模块

根据文件后缀自动选择合适的拆分器：
- .md, .markdown -> MarkdownSplitter
- .doc, .docx -> DocSplitter

提供统一的拆分接口，返回标准化的 DocumentChunk 列表。
"""

import io
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union, BinaryIO, Dict, Any

try:
    from 合同审查.app.rag.markdown_splitter import MarkdownSplitter, MarkdownSection
    from 合同审查.app.rag.doc_splitter import DocSplitter, DocSection
except ImportError:
    # 直接导入（用于测试）
    from markdown_splitter import MarkdownSplitter, MarkdownSection
    from doc_splitter import DocSplitter, DocSection


@dataclass
class DocumentChunk:
    """
    统一的文档分块数据结构

    所有拆分器都返回此格式的数据，便于后续处理。
    """
    id: str
    title: str
    content: str
    chunk_type: str  # 'heading', 'paragraph', 'section', 'page'
    level: int = 0  # 标题级别（如果有）
    source_file: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseDocumentSplitter(ABC):
    """文档拆分器基类"""

    @abstractmethod
    def split(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
        content: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """
        拆分文档

        Args:
            file_path: 文件路径
            file_obj: 文件对象
            file_name: 文件名
            content: 文本内容（直接传入内容时）

        Returns:
            List[DocumentChunk]: 拆分后的文档块列表
        """
        pass


class MarkdownDocumentSplitter(BaseDocumentSplitter):
    """Markdown 文档拆分器包装类"""

    def __init__(
        self,
        max_depth: int = 3,
        min_content_length: int = 50,
        preserve_hierarchy: bool = True,
    ):
        self.splitter = MarkdownSplitter(
            max_depth=max_depth,
            min_content_length=min_content_length,
            preserve_hierarchy=preserve_hierarchy,
        )

    def split(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
        content: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """拆分 Markdown 文档"""
        # 获取内容
        if content is None:
            content = self._load_content(file_path, file_obj, file_name)

        if not content or not content.strip():
            return []

        # 使用 MarkdownSplitter 拆分
        sections = self.splitter.split_with_context(content)

        # 转换为 DocumentChunk
        chunks = []
        for section in sections:
            chunk = DocumentChunk(
                id=section.id,
                title=section.metadata.get('full_title', section.title),
                content=section.content,
                chunk_type='heading',
                level=section.level,
                source_file=str(file_path) if file_path else (file_name or ""),
                metadata={
                    'original_title': section.title,
                    'heading': section.heading,
                    **section.metadata,
                },
            )
            chunks.append(chunk)

        return chunks

    def _load_content(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> str:
        """加载文件内容"""
        if content := self._read_file(file_path, file_obj, file_name):
            return content
        raise ValueError("必须提供 file_path、file_obj 或 content 之一")

    def _read_file(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> Optional[str]:
        """读取文件内容"""
        if file_path is not None:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        if file_obj is not None:
            content = file_obj.read().decode('utf-8')
            file_obj.seek(0)  # 重置文件指针，以便后续读取
            return content

        return None


class WordDocumentSplitter(BaseDocumentSplitter):
    """Word 文档拆分器包装类

    支持 .docx 和 .doc 格式：
    - .docx: 使用 python-docx 直接读取并按标题样式拆分
    - .doc: 使用 system_manual_loader 转换为文本后按段落拆分
    """

    def __init__(
        self,
        split_by: str = "heading",  # 'heading', 'paragraph', 'page'
        max_depth: int = 3,
        min_content_length: int = 50,
    ):
        self.split_by = split_by
        self.max_depth = max_depth
        self.min_content_length = min_content_length

    def split(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
        content: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """拆分 Word 文档"""
        # 确定文件扩展名
        if file_name:
            ext = Path(file_name).suffix.lower()
        elif file_path:
            ext = Path(file_path).suffix.lower()
        else:
            raise ValueError("必须提供 file_path 或 file_name")

        # 根据文件类型选择拆分方式
        if ext == '.docx':
            return self._split_docx(file_path, file_obj, file_name)
        elif ext == '.doc':
            return self._split_doc(file_path, file_obj, file_name)
        else:
            raise ValueError(f"不支持的 Word 文档格式: {ext}")

    def _split_docx(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """拆分 DOCX 文件"""
        temp_path = None
        try:
            actual_path = self._get_file_path(file_path, file_obj, file_name)

            # 使用 DocSplitter 拆分
            splitter = DocSplitter(
                split_by=self.split_by,
                max_depth=self.max_depth,
                min_content_length=self.min_content_length,
            )
            sections = splitter.split(actual_path)

            # 转换为 DocumentChunk
            chunks = []
            for section in sections:
                chunk = DocumentChunk(
                    id=section.id,
                    title=section.title,
                    content=section.content,
                    chunk_type=self.split_by,
                    level=section.level,
                    source_file=str(file_path) if file_path else (file_name or ""),
                    metadata={
                        'style': section.style,
                        **section.metadata,
                    },
                )
                chunks.append(chunk)

            return chunks

        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    def _split_doc(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """拆分 DOC 文件（旧版 Word）

        由于 python-docx 无法直接读取 .doc 文件，
        使用 system_manual_loader 加载为文本后按数字标题（如 1.1、2.3）拆分。
        """
        try:
            from 合同审查.app.rag.system_manual_loader import SystemManualLoader
        except ImportError:
            # 直接导入（用于测试）
            from system_manual_loader import SystemManualLoader

        loader = SystemManualLoader()

        # 加载文档内容
        if file_path:
            full_text = loader.load(file_path=file_path)
        elif file_obj:
            # 重置文件指针
            file_obj.seek(0)
            full_text = loader.load(file_obj=file_obj, file_name=file_name)
        else:
            raise ValueError("必须提供 file_path 或 file_obj")

        if not full_text or not full_text.strip():
            return []

        # 按数字标题拆分（如 "1 快速开始", "1.1 如何登录"）
        return self._split_by_numbered_headings(full_text, file_path, file_name)

    def _split_by_numbered_headings(
        self,
        text: str,
        file_path: Optional[Union[str, Path]] = None,
        file_name: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """按数字标题（如 1.1、2.3）拆分文本"""
        import re

        lines = text.split('\n')

        # 识别数字标题行（如 "1 标题", "1.1 标题", "1.1.1 标题"）
        heading_pattern = re.compile(r'^(\d+(?:\.\d+){0,2})\s+(.+)$')

        # 收集所有标题
        headings = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            match = heading_pattern.match(line)
            if match:
                number = match.group(1)  # 如 "1", "1.1", "1.1.1"
                title = match.group(2)
                level = number.count('.') + 1  # 根据点数确定级别
                headings.append({
                    'index': i,
                    'number': number,
                    'title': title,
                    'level': level,
                    'line': line,
                })

        if not headings:
            # 没有数字标题，按段落组合拆分
            return self._split_by_paragraphs(text, file_path, file_name)

        # 根据标题拆分章节
        chunks = []
        for i, heading in enumerate(headings):
            level = heading['level']

            # 只处理指定深度以内的标题
            if level > self.max_depth:
                continue

            # 确定当前章节的结束位置
            start_idx = heading['index']
            if i + 1 < len(headings):
                # 找到下一个同等级或更高等级的标题
                end_idx = len(lines)
                for next_heading in headings[i + 1:]:
                    if next_heading['level'] <= level:
                        end_idx = next_heading['index']
                        break
            else:
                end_idx = len(lines)

            # 提取章节内容
            section_lines = lines[start_idx:end_idx]
            content = '\n'.join(section_lines).strip()

            # 检查内容长度
            if len(content) >= self.min_content_length:
                chunks.append(DocumentChunk(
                    id=str(len(chunks) + 1),
                    title=heading['line'],
                    content=content,
                    chunk_type='heading',
                    level=level,
                    source_file=str(file_path) if file_path else (file_name or ""),
                    metadata={
                        'number': heading['number'],
                        'heading_title': heading['title'],
                    },
                ))

        # 如果没有拆分到任何章节（可能都太短），将整个文档作为一个章节
        if not chunks and text.strip():
            chunks.append(DocumentChunk(
                id="1",
                title=file_name or "完整文档",
                content=text.strip(),
                chunk_type='document',
                level=0,
                source_file=str(file_path) if file_path else (file_name or ""),
                metadata={},
            ))

        return chunks

    def _split_by_paragraphs(
        self,
        text: str,
        file_path: Optional[Union[str, Path]] = None,
        file_name: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """按段落组合拆分（无数字标题时的备选方案）"""
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

        if not paragraphs:
            return []

        # 将段落组合成章节
        chunks = []
        current_content = []
        chunk_index = 0

        for para in paragraphs:
            current_content.append(para)

            # 当累积的内容足够长时，创建一个新章节
            content_text = '\n'.join(current_content)
            if len(content_text) >= self.min_content_length:
                chunk_index += 1
                chunks.append(DocumentChunk(
                    id=str(chunk_index),
                    title=current_content[0][:50] if current_content else f"段落 {chunk_index}",
                    content=content_text,
                    chunk_type='paragraph',
                    level=0,
                    source_file=str(file_path) if file_path else (file_name or ""),
                    metadata={},
                ))
                current_content = []

        # 保存剩余内容
        if current_content:
            content_text = '\n'.join(current_content)
            if len(content_text) >= self.min_content_length:
                chunk_index += 1
                chunks.append(DocumentChunk(
                    id=str(chunk_index),
                    title=current_content[0][:50] if current_content else f"段落 {chunk_index}",
                    content=content_text,
                    chunk_type='paragraph',
                    level=0,
                    source_file=str(file_path) if file_path else (file_name or ""),
                    metadata={},
                ))

        # 如果没有拆分到任何章节，将整个文档作为一个章节
        if not chunks and text.strip():
            chunks.append(DocumentChunk(
                id="1",
                title=file_name or "完整文档",
                content=text.strip(),
                chunk_type='document',
                level=0,
                source_file=str(file_path) if file_path else (file_name or ""),
                metadata={},
            ))

        return chunks

    def _get_file_path(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
    ) -> str:
        """获取文件路径（如有需要创建临时文件）"""
        if file_path is not None:
            return str(file_path)

        if file_obj is not None:
            if file_name is None:
                raise ValueError("使用 file_obj 时必须提供 file_name")

            # 创建临时文件
            suffix = Path(file_name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_obj.read())
                tmp_path = tmp.name

            # 重置文件对象指针
            file_obj.seek(0)
            return tmp_path

        raise ValueError("必须提供 file_path 或 file_obj")


class DocumentSplitterFactory:
    """
    文档拆分器工厂

    根据文件后缀自动创建对应的拆分器。
    """

    # 文件扩展名到拆分器类型的映射
    SPLITTER_MAP = {
        '.md': MarkdownDocumentSplitter,
        '.markdown': MarkdownDocumentSplitter,
        '.doc': WordDocumentSplitter,
        '.docx': WordDocumentSplitter,
    }

    @classmethod
    def create_splitter(
        cls,
        file_path: Optional[Union[str, Path]] = None,
        file_name: Optional[str] = None,
        **kwargs,
    ) -> BaseDocumentSplitter:
        """
        创建对应文件类型的拆分器

        Args:
            file_path: 文件路径
            file_name: 文件名（用于确定文件类型）
            **kwargs: 传递给拆分器的参数

        Returns:
            BaseDocumentSplitter: 对应的拆分器实例
        """
        # 确定文件扩展名
        if file_path is not None:
            ext = Path(file_path).suffix.lower()
        elif file_name is not None:
            ext = Path(file_name).suffix.lower()
        else:
            raise ValueError("必须提供 file_path 或 file_name")

        # 获取对应的拆分器类
        splitter_class = cls.SPLITTER_MAP.get(ext)
        if not splitter_class:
            raise ValueError(f"不支持的文件格式: {ext}，支持的格式: {list(cls.SPLITTER_MAP.keys())}")

        return splitter_class(**kwargs)

    @classmethod
    def split_document(
        cls,
        file_path: Optional[Union[str, Path]] = None,
        file_obj: Optional[BinaryIO] = None,
        file_name: Optional[str] = None,
        content: Optional[str] = None,
        **kwargs,
    ) -> List[DocumentChunk]:
        """
        便捷方法：直接拆分文档

        Args:
            file_path: 文件路径
            file_obj: 文件对象
            file_name: 文件名
            content: 文本内容（Markdown 可直接传入）
            **kwargs: 拆分参数

        Returns:
            List[DocumentChunk]: 拆分后的文档块列表
        """
        # 确定文件名
        name = file_name
        if not name and file_path:
            name = Path(file_path).name

        # 创建拆分器
        splitter = cls.create_splitter(file_path=file_path, file_name=name, **kwargs)

        # 执行拆分
        return splitter.split(
            file_path=file_path,
            file_obj=file_obj,
            file_name=name,
            content=content,
        )


# 便捷函数
def split_document(
    file_path: Optional[Union[str, Path]] = None,
    file_obj: Optional[BinaryIO] = None,
    file_name: Optional[str] = None,
    content: Optional[str] = None,
    **kwargs,
) -> List[DocumentChunk]:
    """
    拆分文档（便捷函数）

    Args:
        file_path: 文件路径
        file_obj: 文件对象
        file_name: 文件名
        content: 文本内容
        **kwargs: 拆分参数

    Returns:
        List[DocumentChunk]: 拆分后的文档块列表
    """
    return DocumentSplitterFactory.split_document(
        file_path=file_path,
        file_obj=file_obj,
        file_name=file_name,
        content=content,
        **kwargs,
    )


def split_markdown(content: str, **kwargs) -> List[DocumentChunk]:
    """
    拆分 Markdown 内容（便捷函数）

    Args:
        content: Markdown 文本内容
        **kwargs: 拆分参数

    Returns:
        List[DocumentChunk]: 拆分后的文档块列表
    """
    splitter = MarkdownDocumentSplitter(**kwargs)
    return splitter.split(content=content)


def split_word_document(
    file_path: Optional[Union[str, Path]] = None,
    file_obj: Optional[BinaryIO] = None,
    file_name: Optional[str] = None,
    **kwargs,
) -> List[DocumentChunk]:
    """
    拆分 Word 文档（便捷函数）

    Args:
        file_path: 文件路径
        file_obj: 文件对象
        file_name: 文件名
        **kwargs: 拆分参数

    Returns:
        List[DocumentChunk]: 拆分后的文档块列表
    """
    splitter = WordDocumentSplitter(**kwargs)
    return splitter.split(file_path=file_path, file_obj=file_obj, file_name=file_name)


if __name__ == "__main__":
    # 测试文档拆分器工厂
    print("=" * 60)
    print("测试文档拆分器工厂")
    print("=" * 60)

    # 测试 Markdown 拆分
    md_content = """# 合同审查系统

## 1. 快速开始

### 1.1 登录系统
打开浏览器访问系统地址。

### 1.2 注册账号
填写注册信息完成注册。

## 2. 合同管理

### 2.1 上传合同
支持拖拽上传和选择文件。
"""

    print("\n1. 测试 Markdown 拆分:")
    print("-" * 60)
    chunks = split_markdown(md_content, max_depth=3)
    print(f"共拆分成 {len(chunks)} 个块")
    for chunk in chunks:
        print(f"  [{chunk.id}] {chunk.title} (级别: {chunk.level})")

    # 测试工厂方法
    print("\n2. 测试工厂方法 (Markdown):")
    print("-" * 60)
    chunks = split_document(content=md_content, file_name="test.md", max_depth=2)
    print(f"共拆分成 {len(chunks)} 个块 (max_depth=2)")
    for chunk in chunks:
        print(f"  [{chunk.id}] {chunk.title}")

    # 测试 DOCX 文件（如果有）
    docx_file = r"e:\Professional\合同审查agent\合同审查\documents\新建 DOC 文档.docx"
    if os.path.exists(docx_file):
        print("\n3. 测试 DOCX 拆分:")
        print("-" * 60)
        try:
            chunks = split_word_document(file_path=docx_file, split_by="heading")
            print(f"共拆分成 {len(chunks)} 个块")
            for chunk in chunks[:5]:
                print(f"  [{chunk.id}] {chunk.title} (类型: {chunk.chunk_type})")
        except Exception as e:
            print(f"拆分失败: {e}")
    else:
        print(f"\n3. 跳过 DOCX 测试（文件不存在: {docx_file}）")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
