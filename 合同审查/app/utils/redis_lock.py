"""
Redis 分布式锁实现模块

基于 Redis 的 SET NX EX 原子操作实现分布式锁，支持：
- 阻塞/非阻塞获取锁
- 自动过期防止死锁
- 锁续期（Watchdog 机制）
- 异步上下文管理器支持
"""

import asyncio
import logging
import uuid
from typing import Optional, Callable, Any
from functools import wraps

from redis.asyncio import Redis

from 合同审查.app.agent.create_redis_checkpoint import get_redis_client

logger = logging.getLogger(__name__)


class RedisLock:
    """
    基于 Redis 的分布式锁
    
    使用 SET key value NX EX seconds 原子命令实现，确保：
    1. 互斥性：同一时间只有一个客户端能获取锁
    2. 防死锁：锁自动过期
    3. 安全性：只有获取锁的客户端才能释放锁
    
    示例：
        async with RedisLock(redis_client, "my_resource", timeout=30) as lock:
            if lock.acquired:
                # 执行业务逻辑
                pass
    """
    
    # Lua 脚本：释放锁（原子操作）
    RELEASE_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    
    # Lua 脚本：延长锁时间
    EXTEND_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("expire", KEYS[1], ARGV[2])
    else
        return 0
    end
    """
    
    def __init__(
        self,
        redis: Optional[Redis] = None,
        lock_key: str = "",
        lock_value: Optional[str] = None,
        timeout: int = 30,  # 锁超时时间（秒）
        auto_extend: bool = False,  # 是否自动续期
        extend_interval: int = 10  # 自动续期间隔（秒）
    ):
        """
        初始化分布式锁
        
        Args:
            redis: Redis 客户端实例，为 None 时会自动获取
            lock_key: 锁的键名（会自动添加 lock: 前缀）
            lock_value: 锁的值（默认自动生成 UUID）
            timeout: 锁自动过期时间（秒）
            auto_extend: 是否启用自动续期（Watchdog 机制）
            extend_interval: 自动续期间隔（秒）
        """
        self._redis = redis
        self._lock_key = f"lock:{lock_key}"
        self._lock_value = lock_value or str(uuid.uuid4())
        self._timeout = timeout
        self._auto_extend = auto_extend
        self._extend_interval = extend_interval
        self._acquired = False
        self._extend_task: Optional[asyncio.Task] = None
        self._closed = False
    
    @property
    def acquired(self) -> bool:
        """检查是否已成功获取锁"""
        return self._acquired
    
    @property
    def lock_key(self) -> str:
        """获取锁的键名"""
        return self._lock_key
    
    async def _get_redis(self) -> Redis:
        """获取 Redis 客户端"""
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis
    
    async def acquire(
        self, 
        blocking: bool = True, 
        block_timeout: Optional[int] = None
    ) -> bool:
        """
        获取分布式锁
        
        Args:
            blocking: 是否阻塞等待，False 时立即返回
            block_timeout: 阻塞等待的最大时间（秒），None 表示无限等待
            
        Returns:
            bool: 是否成功获取锁
        """
        if self._acquired:
            logger.warning(f"锁 {self._lock_key} 已被当前实例持有，无需重复获取")
            return True
        
        if self._closed:
            raise RuntimeError("锁实例已关闭，无法重新获取")
        
        redis = await self._get_redis()
        start_time = asyncio.get_event_loop().time()
        attempt = 0
        
        while True:
            attempt += 1
            try:
                # 使用 SET NX EX 原子操作尝试获取锁
                acquired = await redis.set(
                    self._lock_key,
                    self._lock_value,
                    nx=True,  # 仅在键不存在时设置
                    ex=self._timeout  # 设置过期时间
                )
                
                if acquired:
                    self._acquired = True
                    logger.debug(f"成功获取锁 {self._lock_key} (attempt={attempt})")
                    
                    # 启动自动续期任务
                    if self._auto_extend:
                        self._start_extend_task()
                    
                    return True
                
                # 非阻塞模式，立即返回
                if not blocking:
                    logger.debug(f"非阻塞获取锁 {self._lock_key} 失败")
                    return False
                
                # 检查是否超时
                if block_timeout is not None:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= block_timeout:
                        logger.warning(f"获取锁 {self._lock_key} 超时 ({block_timeout}s)")
                        return False
                
                # 等待后重试
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"获取锁 {self._lock_key} 时发生错误: {e}")
                if not blocking:
                    return False
                await asyncio.sleep(0.5)
    
    async def release(self) -> bool:
        """
        释放分布式锁
        
        Returns:
            bool: 是否成功释放锁
        """
        if not self._acquired:
            return False
        
        # 停止自动续期任务
        if self._extend_task:
            self._extend_task.cancel()
            try:
                await self._extend_task
            except asyncio.CancelledError:
                pass
            self._extend_task = None
        
        try:
            redis = await self._get_redis()
            
            # 使用 Lua 脚本原子释放锁
            result = await redis.eval(
                self.RELEASE_SCRIPT,
                1,  # key 的数量
                self._lock_key,
                self._lock_value
            )
            
            self._acquired = False
            
            if result == 1:
                logger.debug(f"成功释放锁 {self._lock_key}")
                return True
            else:
                logger.warning(f"释放锁 {self._lock_key} 失败，可能已被其他客户端获取")
                return False
                
        except Exception as e:
            logger.error(f"释放锁 {self._lock_key} 时发生错误: {e}")
            self._acquired = False
            return False
    
    async def extend(self, additional_time: int) -> bool:
        """
        延长锁的过期时间
        
        Args:
            additional_time: 延长的时间（秒）
            
        Returns:
            bool: 是否成功延长
        """
        if not self._acquired:
            return False
        
        try:
            redis = await self._get_redis()
            
            # 使用 Lua 脚本原子延长锁时间
            result = await redis.eval(
                self.EXTEND_SCRIPT,
                1,
                self._lock_key,
                self._lock_value,
                str(additional_time)
            )
            
            if result == 1:
                logger.debug(f"成功延长锁 {self._lock_key} 时间 {additional_time}s")
                return True
            else:
                logger.warning(f"延长锁 {self._lock_key} 时间失败")
                return False
                
        except Exception as e:
            logger.error(f"延长锁 {self._lock_key} 时间时发生错误: {e}")
            return False
    
    def _start_extend_task(self):
        """启动自动续期任务（Watchdog）"""
        if self._extend_task is None or self._extend_task.done():
            self._extend_task = asyncio.create_task(self._extend_worker())
    
    async def _extend_worker(self):
        """自动续期工作协程"""
        try:
            while self._acquired:
                await asyncio.sleep(self._extend_interval)
                
                if not self._acquired:
                    break
                
                # 延长锁时间
                success = await self.extend(self._timeout)
                if not success:
                    logger.error(f"自动续期锁 {self._lock_key} 失败，锁可能已丢失")
                    break
                    
        except asyncio.CancelledError:
            logger.debug(f"锁 {self._lock_key} 的自动续期任务已取消")
        except Exception as e:
            logger.error(f"锁 {self._lock_key} 的自动续期任务发生错误: {e}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口，确保锁被释放"""
        await self.release()
    
    async def close(self):
        """关闭锁实例，释放资源"""
        if self._acquired:
            await self.release()
        self._closed = True


# ==================== 装饰器工具 ====================

def with_distributed_lock(
    lock_key_prefix: str,
    timeout: int = 30,
    blocking: bool = True,
    block_timeout: Optional[int] = None,
    auto_extend: bool = False
):
    """
    分布式锁装饰器
    
    为异步函数添加分布式锁保护
    
    Args:
        lock_key_prefix: 锁键名前缀
        timeout: 锁超时时间（秒）
        blocking: 是否阻塞等待
        block_timeout: 阻塞等待超时时间（秒）
        auto_extend: 是否自动续期
        
    示例：
        @with_distributed_lock("review", timeout=60)
        async def start_review(self, contract_id: int):
            # 自动获取锁，函数执行完毕后自动释放
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中提取资源 ID
            resource_id = None
            
            # 尝试从 kwargs 中获取常见 ID 参数
            for key in ['contract_id', 'review_id', 'file_id', 'task_id', 'model_name']:
                if key in kwargs:
                    resource_id = kwargs[key]
                    break
            
            # 如果 kwargs 中没有，尝试从 args 中获取（假设第一个非 self 参数）
            if resource_id is None and len(args) > 1:
                resource_id = args[1]  # args[0] 通常是 self
            
            if resource_id is None:
                resource_id = "default"
            
            lock_key = f"{lock_key_prefix}:{resource_id}"
            
            lock = RedisLock(
                lock_key=lock_key,
                timeout=timeout,
                auto_extend=auto_extend
            )
            
            acquired = await lock.acquire(blocking=blocking, block_timeout=block_timeout)
            
            if not acquired:
                raise ResourceLockedException(
                    f"无法获取资源锁: {lock_key}，资源可能正在被其他进程处理"
                )
            
            try:
                return await func(*args, **kwargs)
            finally:
                await lock.release()
        
        return wrapper
    return decorator


class ResourceLockedException(Exception):
    """资源被锁定异常"""
    pass


# ==================== 便捷函数 ====================

async def acquire_lock(
    lock_key: str,
    timeout: int = 30,
    blocking: bool = True,
    block_timeout: Optional[int] = None
) -> RedisLock:
    """
    便捷函数：获取分布式锁
    
    示例：
        lock = await acquire_lock("review:123", timeout=60)
        try:
            # 执行业务逻辑
            pass
        finally:
            await lock.release()
    """
    lock = RedisLock(lock_key=lock_key, timeout=timeout)
    acquired = await lock.acquire(blocking=blocking, block_timeout=block_timeout)
    
    if not acquired:
        raise ResourceLockedException(f"无法获取锁: {lock_key}")
    
    return lock


async def is_locked(lock_key: str) -> bool:
    """
    检查指定资源是否已被锁定
    
    Args:
        lock_key: 锁键名
        
    Returns:
        bool: 是否已被锁定
    """
    try:
        redis = await get_redis_client()
        exists = await redis.exists(f"lock:{lock_key}")
        return bool(exists)
    except Exception as e:
        logger.error(f"检查锁状态失败: {e}")
        return False
