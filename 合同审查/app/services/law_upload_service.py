"""
法律文档上传异步处理服务
"""

import logging
import time
import uuid
from datetime import datetime
from queue import Queue, Empty
from threading import Lock, Thread
from typing import Dict, Optional, Any

import 合同审查.app.rag.retriever as _retriever_module
import 合同审查.app.rag.vector_store as _vector_store_module
from 合同审查.app.core.config import settings
from 合同审查.app.rag import (
    DocumentLoader,
    get_embeddings,
    ChromaVectorStore,
    ClauseChunk,
)

logger = logging.getLogger(__name__)

# 向量数据库持久化目录
import os
VECTOR_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "vector_db", "law_documents")
os.makedirs(VECTOR_DB_DIR, exist_ok=True)


class LawUploadTask:
    """法律文档上传任务"""

    def __init__(
        self,
        task_id: str,
        file_name: str,
        file_content: bytes,
        file_ext: str,
        document_type: str,
        effective_date: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.task_id = task_id
        self.file_name = file_name
        self.file_content = file_content
        self.file_ext = file_ext
        self.document_type = document_type
        self.effective_date = effective_date
        self.description = description

        # 状态
        self.status = "pending"  # pending, processing, completed, failed
        self.progress = 0
        self.message = "任务等待中"
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None

        # 时间戳
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "file_name": self.file_name,
            "document_type": self.document_type,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class LawUploadService:
    """法律文档上传异步处理服务"""

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
        self.tasks: Dict[str, LawUploadTask] = {}
        self.task_queue: Queue = Queue()
        self.tasks_lock = Lock()
        self.document_loader = DocumentLoader()
        self.worker_thread: Optional[Thread] = None
        self.running = False

    def start(self):
        """启动后台处理线程"""
        if not self.running:
            self.running = True
            self.worker_thread = Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()
            logger.info("法律文档上传服务已启动")

    def stop(self):
        """停止后台处理线程"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
            logger.info("法律文档上传服务已停止")

    def create_task(
        self,
        file_name: str,
        file_content: bytes,
        file_ext: str,
        document_type: str,
        effective_date: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """创建上传任务"""
        task_id = str(uuid.uuid4())
        task = LawUploadTask(
            task_id=task_id,
            file_name=file_name,
            file_content=file_content,
            file_ext=file_ext,
            document_type=document_type,
            effective_date=effective_date,
            description=description,
        )

        with self.tasks_lock:
            self.tasks[task_id] = task

        self.task_queue.put(task_id)
        logger.info(f"创建法律文档上传任务: {task_id}, 文件名: {file_name}")

        return task_id

    def get_task(self, task_id: str) -> Optional[LawUploadTask]:
        """获取任务状态"""
        with self.tasks_lock:
            return self.tasks.get(task_id)

    def _process_queue(self):
        """后台处理队列"""
        while self.running:
            try:
                task_id = self.task_queue.get(timeout=1)
                self._process_task(task_id)
            except Empty:
                # 队列为空，正常情况，继续等待
                continue
            except Exception as e:
                if self.running:
                    import traceback
                    logger.error(f"处理队列时出错: {e}\n{traceback.format_exc()}")
                time.sleep(1)

    def _process_task(self, task_id: str):
        """处理单个任务"""
        with self.tasks_lock:
            task = self.tasks.get(task_id)
            if not task:
                return

        task.status = "processing"
        task.started_at = datetime.now()
        task.message = "正在处理文档"
        task.progress = 10

        try:
            logger.info(f"开始处理任务: {task_id}")

            # ========== 1. 加载文档内容 ==========
            task.message = "正在加载文档内容"
            task.progress = 20
            logger.info(f"[{task_id}] 开始加载文档内容: {task.file_name}")

            # 直接使用原始文件内容解析，避免 DocumentLoader 处理导致格式丢失
            full_text = task.file_content.decode('utf-8')
            logger.info(f"[{task_id}] 文档加载完成，原始内容长度: {len(full_text)} 字符")

            # ========== 2. 文本预处理和拆分（使用法律文件专用解析） ==========
            task.message = "正在拆分文档条款"
            task.progress = 40
            logger.info(f"[{task_id}] 开始文本预处理和条款拆分")

            # 使用 parse_law_file 解析法律文件（支持多法规）
            import tempfile
            from 合同审查.app.rag.parse_law_file import parse_law_content

            # 解析法律内容（支持多法规段落）
            parse_result = parse_law_content(full_text)

            law_regulations = parse_result["law_regulation"]
            law_articles = parse_result["law_article"]

            logger.info(f"[{task_id}] 解析完成，共 {parse_result['regulation_count']} 个法规，"
                       f"{parse_result['article_count']} 条法条")

            # 使用第一个法规的信息作为文档元数据
            first_regulation = law_regulations[0] if law_regulations else {}
            law_name = first_regulation.get("name", "")
            issuer = first_regulation.get("issuer", "")
            category = first_regulation.get("category", "")
            publish_date = first_regulation.get("publish_date", "")
            effective_date = first_regulation.get("effective_date", "")
            description = first_regulation.get("description", "")

            unique_filename = str(uuid.uuid4().hex)
            clause_chunks = []

            for i, article in enumerate(law_articles):
                article_no = article.get("article_no", str(i + 1))
                title = article.get("title", "")
                article_content = article.get("content", "")

                # 组合内容（仅法规内容，用于向量嵌入）
                content_for_embedding = f"{article_no} {title}\n{article_content}"

                chunk = ClauseChunk(
                    clause_id=f"{unique_filename}_clause_{i}",
                    clause_no=article_no,
                    clause_content=content_for_embedding,
                    clause_title=title,
                    metadata={
                        "source": task.file_name,
                        "file_type": task.file_ext.replace(".", ""),
                        "document_type": task.document_type,
                        "effective_date": effective_date or task.effective_date,
                        "description": description or task.description,
                        "clause_index": i,
                        "law_name": law_name,
                        "issuer": issuer,
                        "category": category,
                        "publish_date": publish_date,
                    }
                )
                clause_chunks.append(chunk)

            logger.info(f"[{task_id}] 法律文件解析完成，共拆分出 {len(clause_chunks)} 个条款，法规名称: {law_name}")

            # ========== 3. 生成向量嵌入 ==========
            task.message = "正在生成向量嵌入"
            task.progress = 60
            logger.info(f"[{task_id}] 开始生成向量嵌入")

            embeddings = get_embeddings(embedding_type=settings.EMBEDDING_TYPE, model=settings.EMBEDDING_MODEL)
            texts_to_embed = [chunk.clause_content for chunk in clause_chunks]
            clause_embeddings = embeddings.embed_documents(texts_to_embed)

            logger.info(f"[{task_id}] 向量嵌入完成，共生成 {len(clause_embeddings)} 个向量")

            # ========== 4. 存入向量数据库 ==========
            task.message = "正在存入向量数据库"
            task.progress = 80
            logger.info(f"[{task_id}] 开始存入向量数据库")

            collection_name = f"law_documents_{task.document_type}"
            _current_dim = len(clause_embeddings[0])

            try:
                import chromadb
                from chromadb.config import Settings as ChromaSettings
                _client = chromadb.PersistentClient(
                    path=VECTOR_DB_DIR,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                _existing = _client.get_collection(collection_name)
                _existing_count = _existing.count()
                if _existing_count > 0:
                    _peek = _existing.peek(1)
                    _old_dim = 0
                    if _peek and "embeddings" in _peek and _peek["embeddings"] and len(_peek["embeddings"]) > 0:
                        _old_dim = len(_peek["embeddings"][0])
                    logger.info(f"[{task_id}] 检测到已有集合 '{collection_name}'，记录数={_existing_count}，维度={_old_dim}，当前模型维度={_current_dim}")
                    if _old_dim != _current_dim and _old_dim > 0:
                        logger.warning(f"[{task_id}] 维度不匹配！删除旧集合并重建...")
                        _client.delete_collection(collection_name)
                        logger.info(f"[{task_id}] 旧集合已删除")
            except Exception as e:
                logger.debug(f"[{task_id}] 检查/删除旧集合时出错（可能集合不存在）: {e}")

            vector_store = ChromaVectorStore(
                collection_name=collection_name,
                persist_directory=VECTOR_DB_DIR,
            )

            ids = vector_store.add_clauses(
                chunks=clause_chunks,
                embeddings=clause_embeddings,
            )

            logger.info(f"[{task_id}] 向量存储完成，共存入 {len(ids)} 条记录")

            # ========== 5. 完成任务 ==========
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.now()
            task.message = "文档处理完成"
            task.result = {
                "task_id": task.task_id,
                "file_name": task.file_name,
                "document_type": task.document_type,
                "effective_date": task.effective_date,
                "description": task.description,
                "file_size": len(task.file_content),
                "chunks_count": len(clause_chunks),
                "embeddings_count": len(clause_embeddings),
                "vector_ids": ids[:5] if len(ids) > 5 else ids,
            }

            logger.info(f"[{task_id}] 任务处理完成")

            _vector_store_module._law_stores_cache = None
            _retriever_module._law_retriever_cache = None
            logger.info(f"[{task_id}] 已清除法律文档检索器缓存，下次检索将加载新数据")

        except Exception as e:
            logger.error(f"[{task_id}] 处理任务失败: {str(e)}", exc_info=True)
            task.status = "failed"
            task.error = str(e)
            task.message = f"处理失败: {str(e)}"
            task.completed_at = datetime.now()


# 全局服务实例
law_upload_service = LawUploadService()
