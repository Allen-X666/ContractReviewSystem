"""
服务预热与预加载模块

负责在应用启动时预加载 Embedding 模型、向量数据库索引等资源，
避免首次请求时的冷启动延迟。
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class WarmupStatus(Enum):
    """预热状态枚举"""
    PENDING = "pending"           # 等待预热
    IN_PROGRESS = "in_progress"   # 预热中
    COMPLETED = "completed"       # 预热完成
    FAILED = "failed"             # 预热失败
    PARTIAL = "partial"           # 部分成功


@dataclass
class WarmupResult:
    """预热结果"""
    component: str
    status: WarmupStatus
    message: str = ""
    error: Optional[str] = None
    duration_ms: Optional[float] = None


@dataclass
class ServiceReadiness:
    """服务就绪状态"""
    ready: bool = False
    overall_status: WarmupStatus = WarmupStatus.PENDING
    components: Dict[str, WarmupResult] = field(default_factory=dict)
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def duration_ms(self) -> Optional[float]:
        """计算预热耗时"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None


class WarmupService:
    """
    服务预热服务

    管理应用启动时的资源预加载，包括：
    - Embedding 模型加载
    - 向量数据库索引加载
    - LLM 链初始化
    - 法律文档检索器初始化
    """

    def __init__(self):
        self._readiness = ServiceReadiness()
        self._lock = asyncio.Lock()
        self._embedding_model: Optional[Any] = None
        self._vector_store: Optional[Any] = None
        self._law_retriever: Optional[Any] = None
        self._llm_chains_initialized = False

    @property
    def readiness(self) -> ServiceReadiness:
        """获取当前就绪状态"""
        return self._readiness

    def is_ready(self) -> bool:
        """检查服务是否已就绪"""
        return self._readiness.ready

    async def get_embedding_model(self, timeout: float = 60.0) -> Optional[Any]:
        """
        获取预热的 Embedding 模型实例

        如果预热尚未完成，会等待最多 timeout 秒

        Args:
            timeout: 最大等待时间（秒）

        Returns:
            Embedding 模型实例，如果预热失败则返回 None
        """
        # 如果模型已加载，直接返回
        if self._embedding_model is not None:
            return self._embedding_model

        # 如果预热尚未完成，等待
        if self._readiness.overall_status == WarmupStatus.IN_PROGRESS:
            logger.info("等待 Embedding 模型预热完成...")
            start_time = asyncio.get_event_loop().time()
            while (self._embedding_model is None and
                   self._readiness.overall_status == WarmupStatus.IN_PROGRESS):
                await asyncio.sleep(0.1)
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.warning(f"等待 Embedding 模型预热超时（{timeout}秒）")
                    break

        return self._embedding_model

    async def get_vector_store(self, timeout: float = 30.0) -> Optional[Any]:
        """
        获取预热的向量数据库实例

        Args:
            timeout: 最大等待时间（秒）

        Returns:
            向量数据库实例，如果预热失败则返回 None
        """
        if self._vector_store is not None:
            return self._vector_store

        if self._readiness.overall_status == WarmupStatus.IN_PROGRESS:
            logger.info("等待向量数据库预热完成...")
            start_time = asyncio.get_event_loop().time()
            while (self._vector_store is None and
                   self._readiness.overall_status == WarmupStatus.IN_PROGRESS):
                await asyncio.sleep(0.1)
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.warning(f"等待向量数据库预热超时（{timeout}秒）")
                    break

        return self._vector_store

    async def get_law_retriever(self, timeout: float = 30.0) -> Optional[Any]:
        """
        获取预热的法律文档检索器实例

        Args:
            timeout: 最大等待时间（秒）

        Returns:
            法律文档检索器实例，如果预热失败则返回 None
        """
        if self._law_retriever is not None:
            return self._law_retriever

        if self._readiness.overall_status == WarmupStatus.IN_PROGRESS:
            logger.info("等待法律文档检索器预热完成...")
            start_time = asyncio.get_event_loop().time()
            while (self._law_retriever is None and
                   self._readiness.overall_status == WarmupStatus.IN_PROGRESS):
                await asyncio.sleep(0.1)
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.warning(f"等待法律文档检索器预热超时（{timeout}秒）")
                    break

        return self._law_retriever

    async def warmup(self) -> ServiceReadiness:
        """
        执行服务预热

        在后台异步加载所有需要的资源

        Returns:
            ServiceReadiness: 服务就绪状态
        """
        import time

        async with self._lock:
            if self._readiness.overall_status in [WarmupStatus.COMPLETED, WarmupStatus.IN_PROGRESS]:
                logger.info(f"预热已在{self._readiness.overall_status.value}状态，跳过")
                return self._readiness

            self._readiness.start_time = time.time()
            self._readiness.overall_status = WarmupStatus.IN_PROGRESS
            logger.info("开始服务预热...")

        # 第一阶段：预热基础组件（embedding_model 必须先完成）
        logger.info("预热阶段1: 基础组件 (embedding_model)")
        base_tasks = [
            ("embedding_model", self._warmup_embedding_model),
        ]
        base_results = await asyncio.gather(
            *[self._run_warmup_task(name, task) for name, task in base_tasks],
            return_exceptions=True
        )

        # 第二阶段：预热依赖 embedding_model 的组件
        logger.info("预热阶段2: 依赖组件 (vector_store, law_retriever, llm_chains)")
        dependent_tasks = [
            ("vector_store", self._warmup_vector_store),
            ("law_retriever", self._warmup_law_retriever),
            ("llm_chains", self._warmup_llm_chains),
        ]
        dependent_results = await asyncio.gather(
            *[self._run_warmup_task(name, task) for name, task in dependent_tasks],
            return_exceptions=True
        )

        # 合并结果
        results = base_results + dependent_results
        all_tasks = base_tasks + dependent_tasks

        # 处理结果
        async with self._lock:
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # 任务抛出异常
                    component_name = all_tasks[i][0]
                    self._readiness.components[component_name] = WarmupResult(
                        component=component_name,
                        status=WarmupStatus.FAILED,
                        error=str(result)
                    )
                else:
                    self._readiness.components[result.component] = result

            self._readiness.end_time = time.time()
            self._readiness = self._calculate_overall_status()

            logger.info(
                f"服务预热完成，状态: {self._readiness.overall_status.value}, "
                f"耗时: {self._readiness.duration_ms:.2f}ms"
            )

            return self._readiness

    async def _run_warmup_task(
        self,
        component: str,
        task_func
    ) -> WarmupResult:
        """执行单个预热任务并记录耗时（支持同步和异步任务）"""
        import time
        import asyncio
        import inspect

        start = time.time()
        logger.info(f"开始预热组件: {component}")

        try:
            # 检查任务函数是否是异步的
            if inspect.iscoroutinefunction(task_func):
                # 直接执行异步函数
                await task_func()
            else:
                # 在线程池中执行同步的初始化代码
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, task_func)

            duration = (time.time() - start) * 1000
            logger.info(f"组件 {component} 预热完成，耗时: {duration:.2f}ms")

            return WarmupResult(
                component=component,
                status=WarmupStatus.COMPLETED,
                message=f"预热成功",
                duration_ms=duration
            )

        except Exception as e:
            duration = (time.time() - start) * 1000
            logger.error(f"组件 {component} 预热失败: {e}")

            return WarmupResult(
                component=component,
                status=WarmupStatus.FAILED,
                message="预热失败",
                error=str(e),
                duration_ms=duration
            )

    def _warmup_embedding_model(self):
        """预热 Embedding 模型"""
        try:
            from 合同审查.app.rag.embeddings import get_embeddings
            self._embedding_model = get_embeddings()
            logger.info("Embedding 模型预热完成")
        except Exception as e:
            logger.warning(f"Embedding 模型预热失败: {e}，将在首次请求时重试")
            raise

    def _warmup_vector_store(self):
        """预热向量数据库"""
        try:
            from 合同审查.app.rag.vector_store import get_vector_store
            self._vector_store = get_vector_store()
            logger.info("向量数据库预热完成")
        except Exception as e:
            logger.warning(f"向量数据库预热失败: {e}，将在首次请求时重试")
            raise

    async def _warmup_law_retriever(self):
        """预热法律文档检索器（异步版本）"""
        try:
            from 合同审查.app.rag.retriever import get_law_retriever
            self._law_retriever = await get_law_retriever()
            logger.info("法律文档检索器预热完成")
        except Exception as e:
            logger.warning(f"法律文档检索器预热失败: {e}，将在首次请求时重试")
            raise

    def _warmup_llm_chains(self):
        """预热 LLM 链（轻量级，仅验证配置）"""
        try:
            from 合同审查.app.llm.llm_factory import LLMFactory
            from 合同审查.app.core.config import settings

            # 验证 LLM 配置是否正确
            llm_type = settings.LLM_TYPE
            api_key = settings.DASHSCOPE_API_KEY

            if llm_type == "tongyi" and not api_key:
                raise ValueError("LLM 类型为 tongyi 但未配置 DASHSCOPE_API_KEY")

            # 尝试创建 LLM 实例（不实际调用）
            # 注意：这里只验证配置，不实际加载模型权重
            logger.info("LLM 配置验证完成")
            self._llm_chains_initialized = True

        except Exception as e:
            logger.warning(f"LLM 链预热失败: {e}")
            raise

    def _calculate_overall_status(self) -> ServiceReadiness:
        """计算整体就绪状态"""
        results = list(self._readiness.components.values())

        if not results:
            self._readiness.overall_status = WarmupStatus.PENDING
            self._readiness.ready = False
            return self._readiness

        failed_count = sum(1 for r in results if r.status == WarmupStatus.FAILED)
        completed_count = sum(1 for r in results if r.status == WarmupStatus.COMPLETED)

        if failed_count == 0:
            self._readiness.overall_status = WarmupStatus.COMPLETED
            self._readiness.ready = True
        elif completed_count > 0:
            self._readiness.overall_status = WarmupStatus.PARTIAL
            # 部分成功时，如果核心组件（embedding、vector_store）成功，也视为就绪
            core_components = ["embedding_model", "vector_store"]
            core_ready = all(
                self._readiness.components.get(c, WarmupResult("", WarmupStatus.FAILED)).status == WarmupStatus.COMPLETED
                for c in core_components
            )
            self._readiness.ready = core_ready
        else:
            self._readiness.overall_status = WarmupStatus.FAILED
            self._readiness.ready = False

        return self._readiness

    def get_readiness_report(self) -> Dict[str, Any]:
        """获取就绪状态报告"""
        return {
            "ready": self._readiness.ready,
            "status": self._readiness.overall_status.value,
            "duration_ms": self._readiness.duration_ms,
            "components": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "error": result.error,
                    "duration_ms": result.duration_ms
                }
                for name, result in self._readiness.components.items()
            }
        }


# 全局预热服务实例
_warmup_service: Optional[WarmupService] = None


def get_warmup_service() -> WarmupService:
    """获取全局预热服务实例"""
    global _warmup_service
    if _warmup_service is None:
        _warmup_service = WarmupService()
    return _warmup_service
