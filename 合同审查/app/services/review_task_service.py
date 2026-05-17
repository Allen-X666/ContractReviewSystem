"""
审查任务存储服务
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from threading import Lock

from 合同审查.app.schemas.enums import ReviewStatus, ReviewStage

logger = logging.getLogger(__name__)


class ReviewTask:
    """审查任务模型（简化版）"""

    def __init__(
        self,
        review_id: int,
        contract_id: int,
        file_name: str,
        file_type: str,
        review_options: Dict[str, Any]
    ):
        self.review_id = review_id
        self.contract_id = contract_id
        self.file_name = file_name
        self.file_type = file_type
        self.review_options = review_options

        # 状态
        self.status = ReviewStatus.PENDING
        self.stage = ReviewStage.PARSING
        self.progress = 0
        self.message = "任务已创建"

        # 进度
        self.total_clauses = 0
        self.processed_clauses = 0

        # 结果
        self.risk_items: List[Dict] = []
        self.average_score: Optional[float] = None

        # 时间戳
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        # 取消标志
        self.cancel_requested = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "review_id": self.review_id,
            "contract_id": self.contract_id,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "status": self.status.value if isinstance(self.status, ReviewStatus) else self.status,
            "stage": self.stage.value if isinstance(self.stage, ReviewStage) else self.stage,
            "progress": self.progress,
            "message": self.message,
            "total_clauses": self.total_clauses,
            "processed_clauses": self.processed_clauses,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class TaskStorage(ABC):
    """任务存储抽象基类"""

    @abstractmethod
    def save_task(self, task: ReviewTask) -> None:
        """保存任务"""
        pass

    @abstractmethod
    def get_task(self, review_id: int) -> Optional[ReviewTask]:
        """获取任务"""
        pass

    @abstractmethod
    def update_task(self, review_id: int, updates: Dict[str, Any]) -> bool:
        """更新任务字段"""
        pass

    @abstractmethod
    def delete_task(self, review_id: int) -> bool:
        """删除任务"""
        pass


class MemoryTaskStorage(TaskStorage):
    """内存任务存储（适合单实例部署）"""

    def __init__(self):
        self._tasks: Dict[int, ReviewTask] = {}
        self._next_id: int = 1
        self._lock = Lock()

    def get_next_id(self) -> int:
        """获取下一个自增ID"""
        with self._lock:
            review_id = self._next_id
            self._next_id += 1
            return review_id

    def save_task(self, task: ReviewTask) -> None:
        with self._lock:
            self._tasks[task.review_id] = task
        logger.debug(f"任务 {task.review_id} 已保存到内存")

    def get_task(self, review_id: int) -> Optional[ReviewTask]:
        with self._lock:
            return self._tasks.get(review_id)

    def update_task(self, review_id: int, updates: Dict[str, Any]) -> bool:
        with self._lock:
            if review_id not in self._tasks:
                return False
            task = self._tasks[review_id]
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)
        return True

    def delete_task(self, review_id: int) -> bool:
        with self._lock:
            if review_id in self._tasks:
                del self._tasks[review_id]
                return True
            return False

    def list_tasks(self, status: Optional[ReviewStatus] = None) -> List[ReviewTask]:
        with self._lock:
            tasks = list(self._tasks.values())
            if status:
                tasks = [t for t in tasks if t.status == status]
            return tasks


class ReviewTaskService:
    """审查任务服务"""

    def __init__(self, storage: TaskStorage):
        self._storage = storage

    def create_task(
        self,
        review_id: int,
        contract_id: int,
        file_name: str,
        file_type: str,
        review_options: Dict[str, Any]
    ) -> ReviewTask:
        """创建新任务"""
        task = ReviewTask(
            review_id=review_id,
            contract_id=contract_id,
            file_name=file_name,
            file_type=file_type,
            review_options=review_options
        )
        self._storage.save_task(task)
        logger.info(f"创建审查任务: {review_id}")
        return task

    def get_task(self, review_id: int) -> Optional[ReviewTask]:
        """获取任务"""
        return self._storage.get_task(review_id)

    def update_task(self, review_id: int, updates: Dict[str, Any]) -> bool:
        """更新任务"""
        return self._storage.update_task(review_id, updates)

    def update_task_status(
        self,
        review_id: int,
        status: Optional[ReviewStatus] = None,
        stage: Optional[ReviewStage] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        processed_clauses: Optional[int] = None
    ) -> bool:
        """更新任务状态"""
        updates = {}
        if status is not None:
            updates["status"] = status
        if stage is not None:
            updates["stage"] = stage
        if progress is not None:
            updates["progress"] = progress
        if message is not None:
            updates["message"] = message
        if processed_clauses is not None:
            updates["processed_clauses"] = processed_clauses

        if updates:
            return self._storage.update_task(review_id, updates)
        return False

    def complete_task(self, review_id: int, risk_items: List[Dict]) -> bool:
        """完成任务"""
        scores = [item.get("score") for item in risk_items if item.get("score") is not None]
        average_score = sum(scores) / len(scores) if scores else None
        logger.info(f"任务 {review_id} 计算平均分: {average_score} (基于 {len(scores)} 个score)")

        updates = {
            "status": ReviewStatus.COMPLETED,
            "progress": 100,
            "risk_items": risk_items,
            "completed_at": datetime.now(),
            "message": "审查完成",
            "average_score": average_score
        }
        success = self._storage.update_task(review_id, updates)
        if success:
            logger.info(f"任务 {review_id} 完成，发现 {len(risk_items)} 个风险")
        return success

    def fail_task(self, review_id: int, error_message: str) -> bool:
        """标记任务失败"""
        updates = {
            "status": ReviewStatus.FAILED,
            "message": f"审查失败: {error_message}",
            "completed_at": datetime.now()
        }
        return self._storage.update_task(review_id, updates)

    def request_cancel(self, review_id: int) -> bool:
        """请求取消任务"""
        return self._storage.update_task(review_id, {
            "cancel_requested": True,
            "message": "正在取消任务..."
        })

    def cancel_task(self, review_id: int) -> bool:
        """确认取消任务"""
        updates = {
            "status": ReviewStatus.CANCELLED,
            "message": "任务已取消",
            "completed_at": datetime.now()
        }
        return self._storage.update_task(review_id, updates)

    def is_cancel_requested(self, review_id: int) -> bool:
        """检查是否请求了取消"""
        task = self.get_task(review_id)
        return task.cancel_requested if task else False

    def get_next_review_id(self) -> int:
        """获取下一个审查任务ID"""
        if isinstance(self._storage, MemoryTaskStorage):
            return self._storage.get_next_id()
        # 对于其他存储实现，需要自行实现ID生成逻辑
        raise NotImplementedError("当前存储实现不支持自增ID")


# 全局服务实例（单例模式）
_task_service: Optional[ReviewTaskService] = None


def get_review_task_service() -> ReviewTaskService:
    """获取任务服务实例"""
    global _task_service
    if _task_service is None:
        storage = MemoryTaskStorage()
        _task_service = ReviewTaskService(storage)
    return _task_service


def init_task_service(storage: TaskStorage) -> ReviewTaskService:
    """初始化任务服务（用于自定义存储）"""
    global _task_service
    _task_service = ReviewTaskService(storage)
    return _task_service
