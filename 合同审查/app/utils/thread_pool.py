"""
线程池工具

提供可自定义的线程池实现，支持提交任务、批量执行、回调函数等功能
"""

import threading
import queue
import time
import uuid
from asyncio import wait
from typing import Callable, Any, Optional, List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, field
from enum import Enum
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """获取任务执行时长"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


@dataclass
class TaskConfig:
    """任务配置"""
    # 任务超时时间（秒），None表示不超时
    timeout: Optional[float] = None
    # 任务优先级（数字越小优先级越高）
    priority: int = 5
    # 失败重试次数
    retry_count: int = 0
    # 重试间隔（秒）
    retry_delay: float = 1.0
    # 回调函数
    on_success: Optional[Callable[[Any], None]] = None
    on_error: Optional[Callable[[Exception], None]] = None
    on_complete: Optional[Callable[[TaskResult], None]] = None


class CustomThreadPool:
    """
    自定义线程池
    
    支持自定义任务执行逻辑、回调函数、超时控制、重试机制等
    """
    
    def __init__(
        self,
        max_workers: int = 5,
        thread_name_prefix: str = "CustomThreadPool",
        queue_size: int = 100
    ):
        """
        初始化线程池
        
        Args:
            max_workers: 最大工作线程数
            thread_name_prefix: 线程名前缀
            queue_size: 任务队列大小
        """
        self.max_workers = max_workers
        self.thread_name_prefix = thread_name_prefix
        self._executor: Optional[ThreadPoolExecutor] = None
        self._task_queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=queue_size)
        self._running = False
        self._lock = threading.Lock()
        self._task_results: Dict[str, TaskResult] = {}
        self._futures: Dict[str, Future] = {}
        
    def start(self) -> None:
        """启动线程池"""
        with self._lock:
            if not self._running:
                self._executor = ThreadPoolExecutor(
                    max_workers=self.max_workers,
                    thread_name_prefix=self.thread_name_prefix
                )
                self._running = True
                logger.info(f"线程池已启动，工作线程数: {self.max_workers}")
    
    def shutdown(self, wait: bool = True) -> None:
        """
        关闭线程池
        
        Args:
            wait: 是否等待所有任务完成
        """
        with self._lock:
            if self._running and self._executor:
                self._executor.shutdown(wait=wait)
                self._running = False
                logger.info("线程池已关闭")
    
    def submit(
        self,
        func: Callable[..., Any],
        *args,
        config: Optional[TaskConfig] = None,
        **kwargs
    ) -> str:
        """
        提交任务到线程池
        
        Args:
            func: 要执行的函数
            *args: 函数的位置参数
            config: 任务配置
            **kwargs: 函数的关键字参数
            
        Returns:
            任务ID
            
        Example:
            >>> def my_task(name):
            ...     return f"Hello, {name}!"
            >>> 
            >>> config = TaskConfig(timeout=10, on_success=print)
            >>> task_id = pool.submit(my_task, "World", config=config)
        """
        if not self._running:
            raise RuntimeError("线程池未启动，请先调用start()")
        
        task_id = str(uuid.uuid4())
        config = config or TaskConfig()
        
        # 创建任务结果对象
        task_result = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING
        )
        self._task_results[task_id] = task_result
        
        # 提交任务
        future = self._executor.submit(
            self._execute_task,
            task_id,
            func,
            args,
            kwargs,
            config
        )
        self._futures[task_id] = future
        
        return task_id
    
    def _execute_task(
        self,
        task_id: str,
        func: Callable[..., Any],
        args: Tuple,
        kwargs: Dict,
        config: TaskConfig
    ) -> Any:
        """
        执行任务（内部方法）
        
        支持超时控制、重试机制、回调函数
        """
        task_result = self._task_results[task_id]
        task_result.status = TaskStatus.RUNNING
        task_result.start_time = time.time()
        
        last_error = None
        attempts = config.retry_count + 1
        
        for attempt in range(attempts):
            try:
                # 执行实际任务
                if config.timeout:
                    # 使用超时控制
                    result = self._run_with_timeout(func, args, kwargs, config.timeout)
                else:
                    result = func(*args, **kwargs)
                
                # 任务成功
                task_result.status = TaskStatus.COMPLETED
                task_result.result = result
                task_result.end_time = time.time()
                
                # 调用成功回调
                if config.on_success:
                    try:
                        config.on_success(result)
                    except Exception as e:
                        logger.error(f"成功回调执行失败: {e}")
                
                break
                
            except Exception as e:
                last_error = e
                logger.warning(f"任务 {task_id} 第 {attempt + 1} 次执行失败: {e}")
                
                if attempt < attempts - 1:
                    # 等待后重试
                    time.sleep(config.retry_delay)
                else:
                    # 所有重试都失败
                    task_result.status = TaskStatus.FAILED
                    task_result.error = str(e)
                    task_result.end_time = time.time()
                    
                    # 调用错误回调
                    if config.on_error:
                        try:
                            config.on_error(e)
                        except Exception as callback_e:
                            logger.error(f"错误回调执行失败: {callback_e}")
        
        # 调用完成回调
        if config.on_complete:
            try:
                config.on_complete(task_result)
            except Exception as e:
                logger.error(f"完成回调执行失败: {e}")
        
        return task_result.result if task_result.status == TaskStatus.COMPLETED else None
    
    def _run_with_timeout(
        self,
        func: Callable[..., Any],
        args: Tuple,
        kwargs: Dict,
        timeout: float
    ) -> Any:
        """带超时控制的执行任务"""
        future = self._executor.submit(func, *args, **kwargs)
        return future.result(timeout=timeout)
    
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[TaskResult]:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            timeout: 等待超时时间
            
        Returns:
            任务结果，如果任务不存在返回None
        """
        if task_id not in self._futures:
            return self._task_results.get(task_id)
        
        future = self._futures[task_id]
        try:
            future.result(timeout=timeout)
        except Exception:
            pass
        
        return self._task_results.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        if task_id in self._futures:
            future = self._futures[task_id]
            cancelled = future.cancel()
            if cancelled:
                self._task_results[task_id].status = TaskStatus.CANCELLED
            return cancelled
        return False
    
    def get_all_results(self) -> Dict[str, TaskResult]:
        """获取所有任务结果"""
        return self._task_results.copy()
    
    def get_running_tasks(self) -> List[str]:
        """获取正在运行的任务ID列表"""
        return [
            task_id for task_id, result in self._task_results.items()
            if result.status == TaskStatus.RUNNING
        ]
    
    def wait_for_all(self, timeout: Optional[float] = None) -> bool:
        """
        等待所有任务完成
        
        Args:
            timeout: 超时时间
            
        Returns:
            是否所有任务都已完成
        """
        if not self._executor:
            return True
        
        done, not_done = wait(
            self._futures.values(),
            timeout=timeout,
            return_when='ALL_COMPLETED'
        )
        return len(not_done) == 0


class PriorityThreadPool(CustomThreadPool):
    """
    支持优先级任务的线程池
    
    优先级数字越小，执行优先级越高
    """
    
    def submit(
        self,
        func: Callable[..., Any],
        *args,
        priority: int = 5,
        config: Optional[TaskConfig] = None,
        **kwargs
    ) -> str:
        """
        提交带优先级的任务
        
        Args:
            func: 要执行的函数
            *args: 函数的位置参数
            priority: 优先级（数字越小优先级越高，默认5）
            config: 任务配置
            **kwargs: 函数的关键字参数
            
        Returns:
            任务ID
        """
        config = config or TaskConfig()
        config.priority = priority
        return super().submit(func, *args, config=config, **kwargs)


# 便捷函数

def create_pool(
    max_workers: int = 5,
    priority_support: bool = False
) -> CustomThreadPool:
    """
    创建线程池的工厂函数
    
    Args:
        max_workers: 最大工作线程数
        priority_support: 是否支持优先级
        
    Returns:
        线程池实例
    """
    if priority_support:
        pool = PriorityThreadPool(max_workers=max_workers)
    else:
        pool = CustomThreadPool(max_workers=max_workers)
    pool.start()
    return pool


def run_in_thread(
    func: Callable[..., Any],
    *args,
    callback: Optional[Callable[[Any], None]] = None,
    error_callback: Optional[Callable[[Exception], None]] = None,
    **kwargs
) -> str:
    """
    在后台线程中运行函数
    
    Args:
        func: 要执行的函数
        *args: 函数的位置参数
        callback: 成功回调
        error_callback: 错误回调
        **kwargs: 函数的关键字参数
        
    Returns:
        任务ID
        
    Example:
        >>> def long_running_task(data):
        ...     time.sleep(5)
        ...     return f"Processed: {data}"
        >>> 
        >>> task_id = run_in_thread(
        ...     long_running_task,
        ...     "my_data",
        ...     callback=lambda r: print(f"成功: {r}"),
        ...     error_callback=lambda e: print(f"失败: {e}")
        ... )
    """
    config = TaskConfig(
        on_success=callback,
        on_error=error_callback
    )
    
    # 使用全局默认线程池
    if not hasattr(run_in_thread, '_default_pool'):
        run_in_thread._default_pool = create_pool()
    
    return run_in_thread._default_pool.submit(func, *args, config=config, **kwargs)


def batch_submit(
    pool: CustomThreadPool,
    tasks: List[Tuple[Callable, Tuple, Dict]],
    config: Optional[TaskConfig] = None
) -> List[str]:
    """
    批量提交任务
    
    Args:
        pool: 线程池实例
        tasks: 任务列表，每个元素为 (func, args, kwargs)
        config: 任务配置（所有任务共用）
        
    Returns:
        任务ID列表
        
    Example:
        >>> tasks = [
        ...     (func1, (arg1,), {"key": "value"}),
        ...     (func2, (arg2,), {}),
        ...     (func3, (), {"name": "test"}),
        ... ]
        >>> task_ids = batch_submit(pool, tasks)
    """
    task_ids = []
    for func, args, kwargs in tasks:
        task_id = pool.submit(func, *args, config=config, **kwargs)
        task_ids.append(task_id)
    return task_ids


# 示例用法
if __name__ == "__main__":
    print("=== 线程池工具测试 ===\n")
    
    # 示例1: 基本使用
    def example_task(name: str, sleep_time: int) -> str:
        print(f"[任务] {name} 开始执行，将休眠 {sleep_time} 秒")
        time.sleep(sleep_time)
        return f"{name} 完成"
    
    # 创建线程池
    pool = create_pool(max_workers=3)
    
    # 提交任务
    config = TaskConfig(
        timeout=10,
        on_success=lambda r: print(f"[回调] 任务成功: {r}"),
        on_error=lambda e: print(f"[回调] 任务失败: {e}"),
        on_complete=lambda tr: print(f"[回调] 任务结束，耗时: {tr.duration:.2f}秒")
    )
    
    task_id1 = pool.submit(example_task, "任务1", 2, config=config)
    task_id2 = pool.submit(example_task, "任务2", 1, config=config)
    task_id3 = pool.submit(example_task, "任务3", 3, config=config)
    
    print(f"已提交任务: {task_id1}, {task_id2}, {task_id3}\n")
    
    # 等待任务完成
    time.sleep(5)
    
    # 查看结果
    for task_id in [task_id1, task_id2, task_id3]:
        result = pool.get_result(task_id)
        print(f"任务 {task_id[:8]}... 状态: {result.status.value}, 结果: {result.result}")
    
    # 关闭线程池
    pool.shutdown()
    
    print("\n=== 测试完成 ===")
