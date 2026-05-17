# FastAPI 部分修改优化建议

## 一、项目结构概述

当前FastAPI项目位于 `合同审查/app/` 目录下，采用标准的FastAPI项目结构：

```
合同审查/app/
├── main.py                 # 应用入口
├── core/
│   └── config.py          # 配置管理（Pydantic Settings）
├── api/
│   └── v1/
│       ├── router.py      # 路由聚合
│       └── endpoints/     # 接口实现
│           ├── health.py
│           ├── review.py
│           ├── laws.py
│           └── report.py
├── schemas/               # Pydantic模型
│   ├── models.py
│   └── enums.py
├── services/              # 业务逻辑层
│   ├── review_task_service.py
│   ├── review_worker.py
│   └── law_upload_service.py
├── rag/                   # RAG相关模块
│   ├── vector_store.py
│   ├── retriever.py
│   ├── embeddings.py
│   └── ...
├── llm/                   # LLM相关模块
│   ├── tongyi_llm.py
│   ├── review_chains.py
│   └── ...
└── utils/                 # 工具函数
    └── file_utils.py
```

---

## 二、架构设计优化建议

### 2.1 配置管理问题

**现状问题**：
- 存在两个配置文件：`app/core/config.py`（Pydantic Settings）和根目录 `settings.py`（普通类）
- 配置分散，存在重复定义（如CORS配置、LLM配置等）
- 环境变量加载逻辑重复

**优化建议**：

```python
# 建议统一使用 Pydantic Settings，并采用分层配置
# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """数据库配置"""
    model_config = SettingsConfigDict(env_prefix="DB_")
    
    host: str = "localhost"
    port: int = 3306
    name: str = "contract_review"
    user: str = "root"
    password: str = ""
    
    @property
    def url(self) -> str:
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

class LLMSettings(BaseSettings):
    """LLM配置"""
    model_config = SettingsConfigDict(env_prefix="LLM_")
    
    type: str = "tongyi"
    model_default: str = "qwen3.5-flash"
    model_review: str = "qwen3.5-flash"
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key: Optional[str] = None

class Settings(BaseSettings):
    """主配置类"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # 应用配置
    app_name: str = "Contract Review AI Service"
    app_version: str = "1.0.0"
    app_debug: bool = False
    
    # API配置
    api_prefix: str = "/api/v1"
    
    # 子配置
    db: DatabaseSettings = DatabaseSettings()
    llm: LLMSettings = LLMSettings()
    
    # CORS配置
    cors_origins: List[str] = ["*"]
    cors_credentials: bool = True

@lru_cache()
def get_settings() -> Settings:
    """获取配置单例（缓存）"""
    return Settings()
```

**收益**：
- 配置集中管理，避免重复
- 环境变量前缀隔离，避免冲突
- 支持配置验证和类型检查
- 使用 `@lru_cache` 避免重复解析

---

### 2.2 依赖注入优化

**现状问题**：
- 服务层使用全局单例模式（`get_review_task_service()`）
- 难以进行单元测试和Mock
- 服务间耦合度高

**优化建议**：

```python
# app/dependencies.py
from typing import Annotated
from fastapi import Depends

# 使用依赖注入替代全局单例
async def get_task_service() -> ReviewTaskService:
    """获取任务服务"""
    # 可以从请求状态或上下文获取
    # 支持按请求创建或使用连接池
    return ReviewTaskService(storage=MemoryTaskStorage())

async def get_review_worker(
    service: Annotated[ReviewTaskService, Depends(get_task_service)]
) -> ReviewWorker:
    """获取审查工作器"""
    return ReviewWorker(task_service=service)

# 在路由中使用
@router.post("/start")
async def start_review(
    service: Annotated[ReviewTaskService, Depends(get_task_service)],
    worker: Annotated[ReviewWorker, Depends(get_review_worker)],
    # ... 其他参数
):
    # 使用注入的服务
    pass
```

**收益**：
- 支持依赖注入，便于测试
- 可以按请求生命周期管理服务
- 支持连接池和资源复用

---

### 2.3 统一响应模型优化

**现状问题**：
- `Result` 模型使用 `data: Optional[Any]`，缺乏类型约束
- 前端难以知道具体返回结构
- 无法利用FastAPI的自动文档生成

**优化建议**：

```python
# app/schemas/response.py
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")

class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="提示信息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))

class PaginationModel(BaseModel, Generic[T]):
    """分页响应模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    items: list[T] = Field(..., description="数据列表")

# 在路由中使用具体类型
from fastapi import APIRouter

@router.post("/start", response_model=ResponseModel[StartReviewResponse])
async def start_review(
    # ...
) -> ResponseModel[StartReviewResponse]:
    return ResponseModel(data=StartReviewResponse(...))

@router.get("/{review_id}/result", response_model=ResponseModel[ReviewResult])
async def get_review_result(
    review_id: int
) -> ResponseModel[ReviewResult]:
    # ...
    return ResponseModel(data=result)
```

**收益**：
- 完整的类型提示和自动文档
- IDE智能提示支持
- 响应结构清晰可预测

---

## 三、API接口优化建议

### 3.1 异常处理统一化

**现状问题**：
- 异常处理分散在各接口中
- 返回的错误格式不统一
- 部分接口使用 `return Result(code=400, ...)`，部分使用 `raise HTTPException`

**优化建议**：

```python
# app/core/exceptions.py
from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class BusinessException(HTTPException):
    """业务异常基类"""
    def __init__(
        self,
        code: int = 400,
        message: str = "业务错误",
        data: Optional[Dict[str, Any]] = None
    ):
        self.business_code = code
        self.business_message = message
        self.business_data = data
        super().__init__(status_code=status.HTTP_200_OK, detail=message)

class TaskNotFoundException(BusinessException):
    """任务不存在异常"""
    def __init__(self, review_id: int):
        super().__init__(
            code=404,
            message=f"审查任务不存在: {review_id}",
            data={"review_id": review_id}
        )

class FileValidationException(BusinessException):
    """文件验证异常"""
    def __init__(self, message: str):
        super().__init__(code=400, message=message)

# app/core/exception_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse

async def business_exception_handler(
    request: Request,
    exc: BusinessException
) -> JSONResponse:
    """业务异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "code": exc.business_code,
            "message": exc.business_message,
            "data": exc.business_data,
            "timestamp": int(time.time() * 1000)
        }
    )

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """参数验证异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "参数验证失败",
            "data": {"errors": exc.errors()},
            "timestamp": int(time.time() * 1000)
        }
    )

# 在main.py中注册
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
```

**收益**：
- 异常处理集中化
- 错误格式统一
- 支持业务错误码

---

### 3.2 文件上传接口优化

**现状问题**：
- `review.py` 中文件读取和验证逻辑冗长
- 文件大小限制硬编码
- 缺少文件类型魔数验证

**优化建议**：

```python
# app/core/upload.py
from typing import BinaryIO
import magic
from dataclasses import dataclass

@dataclass
class UploadConfig:
    """上传配置"""
    max_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: set[str] = None
    allowed_mime_types: set[str] = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = {".pdf", ".docx", ".txt", ".doc"}
        if self.allowed_mime_types is None:
            self.allowed_mime_types = {
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain"
            }

class FileValidator:
    """文件验证器"""
    
    def __init__(self, config: UploadConfig = None):
        self.config = config or UploadConfig()
    
    async def validate(self, file: UploadFile) -> bytes:
        """验证文件并返回内容"""
        # 读取内容
        content = await file.read()
        
        # 大小验证
        if len(content) == 0:
            raise FileValidationException("文件内容为空")
        if len(content) > self.config.max_size:
            raise FileValidationException(
                f"文件大小超过限制（{self.config.max_size // 1024 // 1024}MB）"
            )
        
        # 扩展名验证
        ext = Path(file.filename).suffix.lower()
        if ext not in self.config.allowed_extensions:
            raise FileValidationException(
                f"不支持的文件格式: {ext}"
            )
        
        # MIME类型验证（使用python-magic）
        mime = magic.from_buffer(content, mime=True)
        if mime not in self.config.allowed_mime_types:
            raise FileValidationException(
                f"文件类型不匹配: 声明为 {ext}，实际为 {mime}"
            )
        
        return content

# 使用依赖注入
async def validated_file(
    file: UploadFile = File(...),
    validator: FileValidator = Depends(lambda: FileValidator())
) -> bytes:
    """验证后的文件内容"""
    return await validator.validate(file)

# 在路由中使用
@router.post("/start")
async def start_review(
    contract_id: int = Form(..., gt=0),
    file_content: bytes = Depends(validated_file),
    # ...
):
    # file_content 已经是验证过的字节内容
    pass
```

**收益**：
- 文件验证逻辑复用
- 支持MIME类型验证，防止伪造扩展名
- 配置集中管理

---

### 3.3 SSE流式接口优化

**现状问题**：
- SSE实现使用 `asyncio.sleep(1)` 轮询，效率低
- 没有连接断开检测
- 缺少心跳机制

**优化建议**：

```python
# app/services/progress_notifier.py
from typing import Dict, Set, Callable
import asyncio
from dataclasses import dataclass

@dataclass
class ProgressEvent:
    """进度事件"""
    review_id: int
    status: str
    progress: int
    stage: str
    message: str

class ProgressNotifier:
    """进度通知器 - 使用事件驱动替代轮询"""
    
    def __init__(self):
        self._subscribers: Dict[int, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
    
    async def subscribe(self, review_id: int) -> asyncio.Queue:
        """订阅进度更新"""
        queue = asyncio.Queue()
        async with self._lock:
            if review_id not in self._subscribers:
                self._subscribers[review_id] = set()
            self._subscribers[review_id].add(queue)
        return queue
    
    async def unsubscribe(self, review_id: int, queue: asyncio.Queue):
        """取消订阅"""
        async with self._lock:
            if review_id in self._subscribers:
                self._subscribers[review_id].discard(queue)
    
    async def notify(self, event: ProgressEvent):
        """通知所有订阅者"""
        async with self._lock:
            queues = self._subscribers.get(event.review_id, set()).copy()
        
        # 并发发送给所有订阅者
        tasks = [q.put(event) for q in queues]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

# 在路由中使用
@router.get("/{review_id}/progress/stream")
async def stream_review_progress(
    review_id: int,
    notifier: Annotated[ProgressNotifier, Depends(get_progress_notifier)]
):
    """SSE 流式获取审查进度 - 事件驱动版"""
    
    async def event_generator():
        queue = await notifier.subscribe(review_id)
        try:
            while True:
                try:
                    # 等待事件，带超时（作为心跳）
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=30.0  # 30秒心跳
                    )
                    
                    data = {
                        "review_id": event.review_id,
                        "status": event.status,
                        "progress": event.progress,
                        "stage": event.stage,
                        "message": event.message,
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    
                    # 检查是否完成
                    if event.status in ["completed", "failed", "cancelled"]:
                        yield f"event: complete\ndata: {json.dumps({'status': event.status})}\n\n"
                        break
                        
                except asyncio.TimeoutError:
                    # 发送心跳保持连接
                    yield ": heartbeat\n\n"
                    
        finally:
            await notifier.unsubscribe(review_id, queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
```

**收益**：
- 事件驱动，实时推送
- 支持多客户端同时订阅
- 心跳机制保持连接

---

## 四、业务逻辑优化建议

### 4.1 任务服务优化

**现状问题**：
- `MemoryTaskStorage` 使用内存存储，重启后数据丢失
- 缺少持久化机制
- 任务状态变更没有事件通知

**优化建议**：

```python
# app/services/task_storage.py
from abc import ABC, abstractmethod
from typing import Optional, List
import json
import aiofiles
from datetime import datetime

class PersistentTaskStorage(TaskStorage):
    """持久化任务存储（基于文件）"""
    
    def __init__(self, storage_path: str = "data/tasks.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._tasks: Dict[int, ReviewTask] = {}
        self._lock = asyncio.Lock()
        self._load_tasks()
    
    def _load_tasks(self):
        """从文件加载任务"""
        if not self.storage_path.exists():
            return
        
        with open(self.storage_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    task = ReviewTask.from_dict(data)
                    self._tasks[task.review_id] = task
                except Exception as e:
                    logger.error(f"加载任务失败: {e}")
    
    async def _persist_task(self, task: ReviewTask):
        """持久化单个任务"""
        async with aiofiles.open(self.storage_path, "a", encoding="utf-8") as f:
            await f.write(json.dumps(task.to_dict(), ensure_ascii=False) + "\n")
    
    async def save_task(self, task: ReviewTask) -> None:
        async with self._lock:
            self._tasks[task.review_id] = task
            await self._persist_task(task)

# 或使用Redis存储
class RedisTaskStorage(TaskStorage):
    """Redis任务存储（支持分布式）"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = aioredis.from_url(redis_url)
        self.key_prefix = "review:task:"
    
    async def save_task(self, task: ReviewTask) -> None:
        key = f"{self.key_prefix}{task.review_id}"
        await self.redis.setex(
            key,
            timedelta(hours=24),  # 24小时过期
            json.dumps(task.to_dict())
        )
    
    async def get_task(self, review_id: int) -> Optional[ReviewTask]:
        key = f"{self.key_prefix}{review_id}"
        data = await self.redis.get(key)
        if data:
            return ReviewTask.from_dict(json.loads(data))
        return None
```

**收益**：
- 任务数据持久化
- 支持服务重启恢复
- 可选Redis支持分布式部署

---

### 4.2 审查工作器优化

**现状问题**：
- `ReviewWorker` 使用 `asyncio.Semaphore(1)` 串行处理，效率低
- 缺少任务队列和重试机制
- 异常处理不够完善

**优化建议**：

```python
# app/services/review_worker.py
from typing import Callable
import backoff
from tenacity import retry, stop_after_attempt, wait_exponential

class ReviewWorker:
    """优化后的审查工作器"""
    
    def __init__(
        self,
        task_service: ReviewTaskService,
        max_concurrent: int = 3,  # 并发数可配置
        progress_callback: Optional[Callable[[int, ProgressEvent], None]] = None
    ):
        self._task_service = task_service
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._progress_callback = progress_callback
        self._running_tasks: Dict[int, asyncio.Task] = {}
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=lambda e: isinstance(e, (TimeoutError, ConnectionError))
    )
    async def _analyze_with_retry(
        self,
        clauses: List[Dict],
        review_options: Dict[str, Any]
    ) -> List[Dict]:
        """带重试的分析调用"""
        return await self._analyze_clauses(clauses, review_options)
    
    async def _process_with_progress(
        self,
        review_id: int,
        clauses: List[Dict],
        review_options: Dict[str, Any]
    ) -> List[Dict]:
        """处理并发送进度通知"""
        async with self._semaphore:
            total = len(clauses)
            results = []
            
            # 分批处理
            batch_size = 5
            for i in range(0, total, batch_size):
                batch = clauses[i:i + batch_size]
                
                # 更新进度
                progress = int((i / total) * 100)
                self._task_service.update_task_status(
                    review_id,
                    progress=progress,
                    message=f"正在分析条款 ({i+1}/{total})..."
                )
                
                # 发送进度事件
                if self._progress_callback:
                    event = ProgressEvent(
                        review_id=review_id,
                        status="processing",
                        progress=progress,
                        stage="analyzing",
                        message=f"正在分析条款 ({i+1}/{total})..."
                    )
                    await self._progress_callback(review_id, event)
                
                # 分析批次
                batch_results = await self._analyze_with_retry(batch, review_options)
                results.extend(batch_results)
            
            return results
```

**收益**：
- 支持可配置的并发处理
- 自动重试机制
- 进度实时通知

---

## 五、性能优化建议

### 5.1 向量检索优化

**现状问题**：
- 每次检索都重新初始化检索器
- 向量库连接没有连接池
- 缺少检索结果缓存

**优化建议**：

```python
# app/rag/retriever.py
from functools import lru_cache
from cachetools import TTLCache

class CachedLawRetriever:
    """带缓存的法律文档检索器"""
    
    def __init__(
        self,
        vector_store: BaseVectorStore,
        cache_size: int = 1000,
        cache_ttl: int = 3600  # 1小时
    ):
        self._vector_store = vector_store
        self._cache = TTLCache(maxsize=cache_size, ttl=cache_ttl)
        self._embedding = None
    
    async def _get_embedding(self) -> Embeddings:
        """延迟初始化嵌入模型"""
        if self._embedding is None:
            self._embedding = get_embeddings(
                embedding_type=settings.EMBEDDING_TYPE,
                model=settings.EMBEDDING_MODEL
            )
        return self._embedding
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        use_cache: bool = True
    ) -> List[RelatedLaw]:
        """检索关联法条（带缓存）"""
        cache_key = f"{query}:{top_k}"
        
        # 检查缓存
        if use_cache and cache_key in self._cache:
            logger.debug(f"缓存命中: {cache_key}")
            return self._cache[cache_key]
        
        # 生成查询向量
        embedding = await self._get_embedding()
        query_vector = embedding.embed_query(query)
        
        # 执行检索
        results = self._vector_store.search(
            query_embedding=query_vector,
            top_k=top_k
        )
        
        # 转换为RelatedLaw
        laws = [
            RelatedLaw(
                law_id=0,
                law_name=r.metadata.get("law_name", "未知法规"),
                article_no=r.clause_no or "相关条款",
                content=r.clause_content or ""
            )
            for r, _ in results
        ]
        
        # 存入缓存
        if use_cache:
            self._cache[cache_key] = laws
        
        return laws
```

**收益**：
- 减少重复检索
- 降低向量库压力
- 提高响应速度

---

### 5.2 异步数据库操作

**现状问题**：
- 当前使用内存存储，没有数据库
- 如果后续添加数据库，需要使用异步驱动

**优化建议**：

```python
# 使用 SQLAlchemy + asyncpg 进行异步数据库操作
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base

# 数据库配置
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=0,
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 依赖注入获取会话
async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# 在路由中使用
@router.get("/{review_id}/result")
async def get_review_result(
    review_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Result:
    # 使用异步查询
    result = await db.execute(
        select(ReviewTaskORM).where(ReviewTaskORM.review_id == review_id)
    )
    task = result.scalar_one_or_none()
    # ...
```

---

## 六、安全优化建议

### 6.1 API限流

**现状问题**：
- 没有API限流机制
- 容易被恶意调用

**优化建议**：

```python
# app/core/rate_limit.py
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 基于内存的限流（生产环境建议使用Redis）
limiter = Limiter(key_func=get_remote_address)

# 在main.py中注册
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 在路由中使用
@router.post("/start")
@limiter.limit("10/minute")  # 每分钟最多10次
async def start_review(
    request: Request,  # 必须添加request参数
    # ...
):
    pass

@router.get("/{review_id}/progress")
@limiter.limit("60/minute")  # 查询接口可以更宽松
async def get_review_progress(
    request: Request,
    review_id: int
):
    pass
```

### 6.2 输入验证强化

**现状问题**：
- 部分接口缺少参数验证
- `review_options` 使用JSON字符串，容易出错

**优化建议**：

```python
# 使用Pydantic模型替代JSON字符串
class ReviewOptions(BaseModel):
    """审查选项"""
    check_invalid_clause: bool = Field(True, description="检查无效条款")
    check_missing_clause: bool = Field(True, description="检查缺失条款")
    check_unreasonable_clause: bool = Field(True, description="检查不合理条款")
    check_legal_risk: bool = Field(True, description="检查法律风险")
    contract_type: Optional[ContractCategory] = Field(None, description="合同类型")
    
    @field_validator('contract_type', mode='before')
    @classmethod
    def validate_contract_type(cls, v):
        if isinstance(v, str):
            try:
                return ContractCategory(v)
            except ValueError:
                raise ValueError(f"无效的合同类型: {v}")
        return v

# 在路由中使用模型
@router.post("/start")
async def start_review(
    contract_id: int = Form(..., gt=0, description="合同ID"),
    file: UploadFile = File(..., description="合同文件"),
    options: ReviewOptions = Depends(),  # 使用模型自动验证
):
    pass
```

---

## 七、监控与日志优化

### 7.1 结构化日志

**现状问题**：
- 使用标准logging，格式不统一
- 缺少请求追踪ID
- 难以进行日志分析

**优化建议**：

```python
# app/core/logging.py
import structlog
from structlog.processors import JSONRenderer
import uuid

# 配置structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.dict_tracebacks,
        JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

# 请求上下文中间件
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # 绑定请求ID到日志上下文
    logger = structlog.get_logger()
    logger = logger.bind(request_id=request_id)
    
    start_time = time.time()
    
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else None
    )
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2)
        )
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "request_failed",
            error=str(e),
            duration_ms=round(duration * 1000, 2)
        )
        raise
```

### 7.2 健康检查增强

**现状问题**：
- 健康检查只返回简单状态
- 没有检查依赖服务状态

**优化建议**：

```python
# app/api/v1/endpoints/health.py
from typing import Dict, Any
import asyncio

class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.checks: Dict[str, Callable[[], Coroutine[Any, Any, bool]]] = {}
    
    def register(self, name: str, check_func: Callable):
        """注册健康检查项"""
        self.checks[name] = check_func
    
    async def check_all(self) -> Dict[str, Any]:
        """执行所有健康检查"""
        results = {}
        
        async def run_check(name: str, func: Callable) -> tuple:
            try:
                # 5秒超时
                result = await asyncio.wait_for(func(), timeout=5.0)
                return name, {"status": "healthy" if result else "unhealthy", "healthy": result}
            except asyncio.TimeoutError:
                return name, {"status": "timeout", "healthy": False}
            except Exception as e:
                return name, {"status": "error", "healthy": False, "error": str(e)}
        
        # 并发执行所有检查
        tasks = [run_check(name, func) for name, func in self.checks.items()]
        check_results = await asyncio.gather(*tasks)
        
        for name, result in check_results:
            results[name] = result
        
        # 整体状态
        all_healthy = all(r["healthy"] for r in results.values())
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": results,
            "timestamp": datetime.utcnow().isoformat()
        }

# 初始化检查器
health_checker = HealthChecker()

# 注册检查项
health_checker.register("llm_service", check_llm_service)
health_checker.register("vector_store", check_vector_store)
health_checker.register("disk_space", check_disk_space)

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """详细健康检查"""
    return await health_checker.check_all()

@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """就绪检查（用于K8s）"""
    result = await health_checker.check_all()
    if result["status"] != "healthy":
        raise HTTPException(status_code=503, detail=result)
    return result
```

---

## 八、测试优化建议

### 8.1 测试结构

**现状问题**：
- 测试文件较少，覆盖率低
- 缺少单元测试和集成测试分离

**优化建议**：

```
tests/
├── conftest.py              # 测试配置和fixture
├── unit/                    # 单元测试
│   ├── test_services/
│   ├── test_utils/
│   └── test_schemas/
├── integration/             # 集成测试
│   ├── test_api/
│   └── test_rag/
├── e2e/                     # 端到端测试
│   └── test_review_flow.py
└── fixtures/                # 测试数据
    ├── sample_contract.pdf
    └── sample_laws.json
```

### 8.2 测试Fixture示例

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

@pytest.fixture
def app():
    """创建测试应用"""
    from 合同审查.app.main import create_application
    return create_application()

@pytest.fixture
def client(app):
    """同步测试客户端"""
    return TestClient(app)

@pytest.fixture
async def async_client(app):
    """异步测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def mock_task_service(monkeypatch):
    """Mock任务服务"""
    class MockTaskService:
        def __init__(self):
            self.tasks = {}
        
        def create_task(self, **kwargs):
            task = MockTask(**kwargs)
            self.tasks[task.review_id] = task
            return task
        
        def get_task(self, review_id):
            return self.tasks.get(review_id)
    
    service = MockTaskService()
    monkeypatch.setattr(
        "合同审查.app.services.review_task_service.get_review_task_service",
        lambda: service
    )
    return service
```

---

## 九、部署优化建议

### 9.1 Docker化

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY 合同审查/app ./app
COPY 合同审查/settings.py .

# 非root用户运行
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 9.2 生产环境配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  fastapi:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
      - REDIS_URL=redis://redis:6379
      - DB_URL=postgresql+asyncpg://postgres:password@db:5432/contract_review
    volumes:
      - ./data:/app/data
    depends_on:
      - redis
      - db
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=contract_review
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## 十、优先级建议

### 高优先级（建议立即实施）

1. **统一配置管理** - 合并两个配置文件，避免重复和冲突
2. **统一异常处理** - 实现全局异常处理器，统一错误格式
3. **文件上传验证** - 添加MIME类型验证，防止伪造文件
4. **API限流** - 防止恶意调用和过载

### 中优先级（建议近期实施）

5. **依赖注入优化** - 替换全局单例，支持测试
6. **响应模型类型化** - 使用泛型响应模型，提高类型安全
7. **SSE事件驱动优化** - 替换轮询为事件驱动
8. **任务持久化** - 实现任务数据持久化

### 低优先级（建议后续实施）

9. **向量检索缓存** - 优化检索性能
10. **结构化日志** - 支持日志分析和监控
11. **健康检查增强** - 检查依赖服务状态
12. **Docker化部署** - 容器化部署支持

---

## 十一、总结

当前FastAPI代码整体结构清晰，功能完整，但在以下方面可以进一步优化：

1. **架构层面**：配置管理需要统一，依赖注入需要完善
2. **API层面**：异常处理需要统一，响应模型需要类型化
3. **性能层面**：SSE需要事件驱动，向量检索需要缓存
4. **安全层面**：需要添加限流和更强的输入验证
5. **运维层面**：需要结构化日志和健康检查

建议按照优先级逐步实施，优先解决高优先级问题，确保系统稳定性和安全性。
