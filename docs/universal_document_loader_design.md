# 通用文档加载器设计方案

## 1. 现状分析

### 1.1 当前文件结构

```
合同审查/app/rag/
├── document_loader.py      # 通用文档加载器（PDF/TXT/DOCX/JSON/Markdown/CSV）
├── system_manual_loader.py # 系统手册专用加载器（Markdown）
└── ...
```

### 1.2 两个加载器的对比

| 特性 | `document_loader.py` | `system_manual_loader.py` |
|------|---------------------|---------------------------|
| **返回类型** | `List[ClauseChunk]` | `List[Document]` |
| **支持格式** | PDF, TXT, DOCX, JSON, Markdown, CSV, Contract | Markdown (专用) |
| **文件处理** | 文件路径 + 文件对象(BytesIO) | 文件路径 + 文件对象(BytesIO) |
| **基类设计** | `BaseLoader` 抽象基类 | 无基类，独立实现 |
| **元数据** | 包含 source, file_type, page_number 等 | 包含 source_file, file_type, doc_type |
| **专用逻辑** | 通用文档处理 | 添加 doc_type="system_manual" 标记 |

### 1.3 重复代码分析

两个文件中重复的实现：

1. **文件信息处理方法** (`_get_file_info`)
   - 功能完全相同：处理文件路径和文件对象
   - 都创建临时文件来处理 BytesIO

2. **临时文件清理** (`_cleanup_temp_file`)
   - 功能完全相同：删除临时文件

3. **方法签名**
   - `load()` 方法参数完全一致
   - 都支持 `file_path` 和 `file_obj` 两种加载方式

## 2. 合并方案

### 2.1 推荐方案：扩展通用加载器

**核心思路**：将 `system_manual_loader.py` 的功能合并到 `document_loader.py` 中，通过配置参数区分通用 Markdown 和系统手册 Markdown。

#### 方案优势

1. **代码复用**：消除重复的文件处理逻辑
2. **统一接口**：所有文档类型使用相同的返回类型和调用方式
3. **易于维护**：单一文件，减少维护成本
4. **向后兼容**：保留现有 API，添加新功能

### 2.2 合并后的架构设计

```python
# 统一返回类型（推荐使用 ClauseChunk）
class ClauseChunk:
    clause_id: str
    clause_no: str
    clause_content: str
    clause_title: Optional[str]
    metadata: Dict[str, Any]  # 包含 doc_type 等标记

# 基类保持不变
class BaseLoader(ABC):
    @abstractmethod
    def load(...) -> List[ClauseChunk]: ...

# 通用 Markdown 加载器（合并后）
class MarkdownLoader(BaseLoader):
    def __init__(self, doc_type: str = "markdown", encoding: str = "utf-8"):
        self.doc_type = doc_type  # "markdown" 或 "system_manual"
        self.encoding = encoding

# 工厂类增强
class DocumentLoader:
    LOADERS = {
        ".md": MarkdownLoader,
        ".markdown": MarkdownLoader,
        # ... 其他格式
    }

    def load_system_manual(self, file_path: str) -> List[ClauseChunk]:
        """便捷方法：加载系统手册"""
        loader = MarkdownLoader(doc_type="system_manual")
        return loader.load(file_path=file_path)
```

### 2.3 代码合并细节

#### A. 文件处理工具函数（提取为公共函数）

```python
# 当前：两个文件中各自实现
# 合并后：统一使用基类方法或工具函数

def get_file_info(...) -> tuple[Path, Optional[BinaryIO], str]:
    """统一处理文件路径和文件对象"""

def cleanup_temp_file(file_path: Path) -> None:
    """清理临时文件"""
```

#### B. MarkdownLoader 增强

```python
class MarkdownLoader(BaseLoader):
    """
    Markdown 文档加载器

    支持通用 Markdown 和系统操作手册 Markdown。
    通过 doc_type 参数区分不同用途。
    """

    def __init__(self, doc_type: str = "markdown", encoding: str = "utf-8"):
        self.doc_type = doc_type
        self.encoding = encoding

    def load(...) -> List[ClauseChunk]:
        # 使用 UnstructuredMarkdownLoader 加载
        loader = UnstructuredMarkdownLoader(str(path), encoding=self.encoding)
        docs = loader.load()

        # 转换为 ClauseChunk
        result = []
        for i, doc in enumerate(docs):
            chunk = ClauseChunk(
                clause_id=f"{name}_chunk_{i}",
                clause_no="",
                clause_content=doc.page_content,
                clause_title=None,
                metadata={
                    "source": name if file_obj else str(file_path),
                    "file_type": "markdown",
                    "doc_type": self.doc_type,  # "markdown" 或 "system_manual"
                    "file_name": name,
                },
            )
            result.append(chunk)
        return result
```

#### C. DocumentLoader 工厂类增强

```python
class DocumentLoader:
    """通用文档加载器工厂"""

    def load(self, ...) -> List[ClauseChunk]:
        """根据文件类型自动选择加载器"""

    def load_system_manual(self, file_path: str) -> List[ClauseChunk]:
        """
        便捷方法：加载系统操作手册

        自动设置 doc_type="system_manual"
        """
        loader = MarkdownLoader(doc_type="system_manual")
        return loader.load(file_path=file_path)

    def load_contract(self, file_path: str) -> List[ClauseChunk]:
        """便捷方法：加载合同文档"""
        loader = ContractLoader()
        return loader.load(file_path=file_path)
```

## 3. 迁移步骤

### 3.1 第一阶段：增强现有代码

1. 修改 `document_loader.py` 中的 `MarkdownLoader`：
   - 添加 `doc_type` 参数
   - 支持返回 `ClauseChunk` 列表

2. 在 `DocumentLoader` 中添加便捷方法：
   - `load_system_manual()`
   - `load_contract()`

### 3.2 第二阶段：废弃旧文件

1. 标记 `system_manual_loader.py` 为废弃：
   ```python
   import warnings
   warnings.warn(
       "SystemManualLoader is deprecated. Use DocumentLoader.load_system_manual() instead.",
       DeprecationWarning,
       stacklevel=2
   )
   ```

2. 更新所有引用：
   - 搜索项目中所有使用 `SystemManualLoader` 的地方
   - 替换为 `DocumentLoader.load_system_manual()`

### 3.3 第三阶段：清理

1. 删除 `system_manual_loader.py`
2. 更新文档和导入语句

## 4. 接口兼容性

### 4.1 现有代码兼容性

| 现有用法 | 迁移后用法 | 兼容性 |
|---------|-----------|--------|
| `MarkdownLoader().load(file_path)` | 保持不变 | ✅ 完全兼容 |
| `SystemManualLoader().load(file_path)` | `DocumentLoader().load_system_manual(file_path)` | ⚠️ 需要修改 |
| `DocumentLoader().load(file_path)` | 保持不变 | ✅ 完全兼容 |

### 4.2 推荐的新用法

```python
from 合同审查.app.rag.document_loader import DocumentLoader

# 通用加载器
loader = DocumentLoader()

# 加载任意文档（自动识别类型）
chunks = loader.load(file_path="document.pdf")

# 加载系统手册（专用方法）
chunks = loader.load_system_manual(file_path="用户操作手册.md")

# 加载合同（专用方法）
chunks = loader.load_contract(file_path="contract.json")
```

## 5. 文件结构（合并后）

```
合同审查/app/rag/
├── document_loader.py          # 通用文档加载器（合并后的主文件）
├── contract_schema.py          # 数据结构定义
├── text_splitter.py            # 文本分割器
├── embeddings.py               # 嵌入模型
├── vector_store.py             # 向量存储
├── retriever.py                # 检索器
└── rag_chain.py                # RAG 链
```

## 6. 总结

### 可以合并 ✅

两个加载器**可以合并**成一个通用加载器：

1. **功能重叠**：`SystemManualLoader` 本质上就是带特殊标记的 `MarkdownLoader`
2. **代码重复**：文件处理逻辑完全相同
3. **统一接口**：合并后使用统一的 `ClauseChunk` 返回类型

### 合并收益

- **减少代码量**：约减少 150 行重复代码
- **统一维护**：单一文件维护所有文档加载逻辑
- **清晰架构**：通过 `doc_type` 元数据区分文档用途
- **向后兼容**：现有 API 基本保持不变

### 建议行动

1. **短期**：保留两个文件，在 `document_loader.py` 中添加 `load_system_manual()` 方法
2. **中期**：标记 `system_manual_loader.py` 为废弃，迁移所有引用
3. **长期**：删除 `system_manual_loader.py`，完全使用通用加载器
