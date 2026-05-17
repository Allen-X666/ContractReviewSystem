"""
系统操作文档上传异步处理服务

使用 system_manual_loader 加载文档，
使用 document_splitter 拆分文档为条目。
"""

import logging
import uuid
import os
from datetime import datetime
from typing import Dict, Optional, Any, List
from threading import Lock, Thread
from queue import Queue, Empty
import time

from 合同审查.app.core.config import settings
from 合同审查.app.rag import (
    get_embeddings,
    ChromaVectorStore,
    ClauseChunk,
)
from 合同审查.app.rag.system_manual_loader import SystemManualLoader
from 合同审查.app.rag.document_splitter import (
    DocumentSplitterFactory,
    DocumentChunk,
)
import 合同审查.app.rag.vector_store as _vector_store_module

logger = logging.getLogger(__name__)

SYSTEM_VECTOR_DB_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "vector_db", "system_operations"
)
os.makedirs(SYSTEM_VECTOR_DB_DIR, exist_ok=True)


class SystemOpsUploadTask:
    """系统操作文档上传任务"""

    def __init__(
        self,
        task_id: str,
        file_name: str,
        file_content: bytes,
        file_ext: str,
        category: str,
        description: Optional[str] = None,
    ):
        self.task_id = task_id
        self.file_name = file_name
        self.file_content = file_content
        self.file_ext = file_ext
        self.category = category
        self.description = description

        self.status = "pending"
        self.progress = 0
        self.message = "任务等待中"
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None

        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "file_name": self.file_name,
            "category": self.category,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class SystemOpsUploadService:
    """系统操作文档上传异步处理服务"""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.tasks: Dict[str, SystemOpsUploadTask] = {}
        self.task_queue: Queue = Queue()
        self.tasks_lock = Lock()
        self.manual_loader = SystemManualLoader()
        self.worker_thread: Optional[Thread] = None
        self.running = False

    def start(self):
        if not self.running:
            self.running = True
            self.worker_thread = Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()
            logger.info("系统操作文档上传服务已启动")

    def stop(self):
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
            logger.info("系统操作文档上传服务已停止")

    def create_task(
        self,
        file_name: str,
        file_content: bytes,
        file_ext: str,
        category: str,
        description: Optional[str] = None,
    ) -> str:
        task_id = str(uuid.uuid4())
        task = SystemOpsUploadTask(
            task_id=task_id,
            file_name=file_name,
            file_content=file_content,
            file_ext=file_ext,
            category=category,
            description=description,
        )
        with self.tasks_lock:
            self.tasks[task_id] = task
        self.task_queue.put(task_id)
        logger.info(f"创建系统操作文档上传任务: {task_id}, 文件名: {file_name}")
        return task_id

    def get_task(self, task_id: str) -> Optional[SystemOpsUploadTask]:
        with self.tasks_lock:
            return self.tasks.get(task_id)

    def _process_queue(self):
        while self.running:
            try:
                task_id = self.task_queue.get(timeout=1)
                self._process_task(task_id)
            except Empty:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"处理系统操作文档队列时出错: {e}", exc_info=True)
                time.sleep(1)

    def _process_task(self, task_id: str):
        """处理单个系统操作文档上传任务"""
        with self.tasks_lock:
            task = self.tasks.get(task_id)
            if not task:
                return

        task.status = "processing"
        task.started_at = datetime.now()
        task.message = "正在处理文档"
        task.progress = 10

        try:
            logger.info(f"开始处理系统操作文档任务: {task_id}")

            # ========== 1. 加载文档 ==========
            task.message = "正在加载文档内容"
            task.progress = 20
            logger.info(f"[{task_id}] 开始加载文档: {task.file_name}")

            # 使用 SystemManualLoader 加载文档内容
            import io
            full_text = self.manual_loader.load(
                file_obj=io.BytesIO(task.file_content),
                file_name=task.file_name,
            )

            if not full_text or not full_text.strip():
                raise ValueError("文档内容为空")

            logger.info(f"[{task_id}] 文档加载完成，文本长度: {len(full_text)} 字符")

            # ========== 2. 拆分文档为条目 ==========
            task.message = "正在拆分文档条目"
            task.progress = 30
            logger.info(f"[{task_id}] 开始拆分文档条目")

            # 使用 document_splitter 根据文件类型自动拆分
            import io
            doc_chunks: List[DocumentChunk] = DocumentSplitterFactory.split_document(
                file_obj=io.BytesIO(task.file_content),
                file_name=task.file_name,
                max_depth=3,
                min_content_length=10,  # 减小最小长度限制，确保小节也能被拆分
            )

            if not doc_chunks:
                # 如果没有拆分到条目，将整个文档作为一个条目
                logger.warning(f"[{task_id}] 未拆分到条目，将整个文档作为一个条目处理")
                doc_chunks = [
                    DocumentChunk(
                        id="1",
                        title=task.file_name,
                        content=full_text,
                        chunk_type="document",
                        level=0,
                        source_file=task.file_name,
                    )
                ]

            logger.info(f"[{task_id}] 文档拆分完成，共 {len(doc_chunks)} 个条目")

            # ========== 3. 转换为 ClauseChunk ==========
            task.message = "正在转换数据格式"
            task.progress = 40

            unique_filename = uuid.uuid4().hex
            chunks: List[ClauseChunk] = []

            for i, doc_chunk in enumerate(doc_chunks):
                chunk = ClauseChunk(
                    clause_id=f"sysops_{unique_filename}_entry_{i}",
                    clause_no=str(i + 1),
                    clause_content=doc_chunk.content,
                    clause_title=doc_chunk.title,
                    metadata={
                        "knowledge_base": "system_operations",
                        "category": task.category,
                        "description": task.description or "",
                        "upload_time": datetime.now().isoformat(),
                        "source": task.file_name,
                        "file_type": task.file_ext.replace(".", ""),
                        "entry_id": doc_chunk.id,
                        "chunk_type": doc_chunk.chunk_type,
                        "level": doc_chunk.level,
                        **doc_chunk.metadata,
                    },
                )
                chunks.append(chunk)

            logger.info(f"[{task_id}] 数据转换完成，共 {len(chunks)} 个 Chunk")

            # ========== 4. 生成向量 ==========
            task.message = "正在生成向量嵌入"
            task.progress = 60

            embeddings = get_embeddings(
                embedding_type=settings.EMBEDDING_TYPE,
                model=settings.EMBEDDING_MODEL,
            )
            texts = [chunk.clause_content for chunk in chunks]
            clause_embeddings = embeddings.embed_documents(texts)

            logger.info(f"[{task_id}] 向量嵌入完成，共生成 {len(clause_embeddings)} 个向量")

            task.message = "正在存入向量数据库"
            task.progress = 80

            # ========== 5. 存入系统操作专用向量库 ==========
            collection_name = f"system_ops_{task.category}"
            _current_dim = len(clause_embeddings[0])

            # 检查并处理维度不匹配问题
            try:
                import chromadb
                from chromadb.config import Settings as ChromaSettings
                _client = chromadb.PersistentClient(
                    path=SYSTEM_VECTOR_DB_DIR,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                _existing = _client.get_collection(collection_name)
                _existing_count = _existing.count()
                if _existing_count > 0:
                    _peek = _existing.peek(1)
                    _old_dim = 0
                    if _peek and "embeddings" in _peek and _peek["embeddings"] and len(_peek["embeddings"]) > 0:
                        _old_dim = len(_peek["embeddings"][0])
                    logger.info(
                        f"[{task_id}] 检测到已有集合 '{collection_name}'，记录数={_existing_count}，维度={_old_dim}，当前模型维度={_current_dim}")
                    if _old_dim != _current_dim and _old_dim > 0:
                        logger.warning(f"[{task_id}] 维度不匹配！删除旧集合并重建...")
                        _client.delete_collection(collection_name)
                        logger.info(f"[{task_id}] 旧集合已删除")
            except Exception as e:
                logger.debug(f"[{task_id}] 检查/删除旧集合时出错（可能集合不存在）: {e}")

            vector_store = ChromaVectorStore(
                collection_name=collection_name,
                persist_directory=SYSTEM_VECTOR_DB_DIR,
            )

            ids = vector_store.add_clauses(
                chunks=chunks,
                embeddings=clause_embeddings,
            )

            logger.info(f"[{task_id}] 向量存储完成，共存入 {len(ids)} 条记录")

            # ========== 6. 完成任务 ==========
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.now()
            task.message = "文档处理完成"
            task.result = {
                "task_id": task.task_id,
                "file_name": task.file_name,
                "category": task.category,
                "description": task.description,
                "file_size": len(task.file_content),
                "entries_count": len(doc_chunks),
                "chunks_count": len(chunks),
                "embeddings_count": len(clause_embeddings),
                "vector_ids": ids[:5] if len(ids) > 5 else ids,
            }

            logger.info(f"[{task_id}] 系统操作文档任务处理完成")

            # 清除缓存，下次检索将加载新数据
            _vector_store_module.invalidate_system_stores_cache()
            logger.info(f"[{task_id}] 已清除系统操作检索器缓存")

        except Exception as e:
            logger.error(f"[{task_id}] 处理系统操作文档任务失败: {str(e)}", exc_info=True)
            task.status = "failed"
            task.error = str(e)
            task.message = f"处理失败: {str(e)}"
            task.completed_at = datetime.now()


# 全局服务实例
system_ops_upload_service = SystemOpsUploadService()
