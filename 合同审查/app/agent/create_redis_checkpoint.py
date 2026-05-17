"""
Redis Checkpointer 配置模块

使用标准 Redis 数据类型（字符串/哈希）存储，无需 RedisJSON 模块。
"""

import logging
import pickle
import time
from datetime import datetime
from typing import Optional, AsyncIterator

from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple
from langgraph.checkpoint.serde.types import ERROR, SCHEDULED, INTERRUPT, RESUME
from redis.asyncio import Redis

from 合同审查.app.core.config import settings

logger = logging.getLogger(__name__)

# 全局 Redis 客户端实例
_redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    """获取 Redis 异步客户端单例"""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=False,  # 存储二进制数据
        )
        await _redis_client.ping()
        logger.info(f"Redis 连接成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}")
    return _redis_client


WRITES_IDX_MAP = {ERROR: -1, SCHEDULED: -2, INTERRUPT: -3, RESUME: -4}


class SimpleRedisCheckpointSaver(BaseCheckpointSaver):
    """
    简单的 Redis Checkpointer 实现

    使用 Redis 字符串存储序列化的 checkpoint 数据，
    不需要 RedisJSON 模块。
    """

    def __init__(self, redis_client: Redis):
        super().__init__()
        self.redis = redis_client
        self.key_prefix = settings.REDIS_KEY__PREFIX   #chatRecord:checkpoint

    def _make_key(self, thread_id: str, checkpoint_ns: str = "", checkpoint_id: Optional[str] = None) -> str:
        """生成 Redis 键名"""
        if checkpoint_id:
            return f"{self.key_prefix}:{thread_id}:{checkpoint_ns}:{checkpoint_id}"
        return f"{self.key_prefix}:{thread_id}:{checkpoint_ns}"

    async def aget_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """异步获取 checkpoint"""
        thread_id = config.get("configurable", {}).get("thread_id")
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")

        if not thread_id:
            return None

        try:
            key = self._make_key(thread_id, checkpoint_ns, checkpoint_id)
            data = await self.redis.get(key)

            if data is None:
                # 如果没有指定 checkpoint_id，尝试获取最新的
                if checkpoint_id is None:
                    pattern = f"{self.key_prefix}:{thread_id}:{checkpoint_ns}:*"
                    keys = []
                    async for k in self.redis.scan_iter(match=pattern):
                        keys.append(k.decode() if isinstance(k, bytes) else k)

                    if not keys:
                        return None

                    # 获取最新的 checkpoint（按字典序排序，通常是时间戳）
                    latest_key = sorted(keys)[-1]
                    data = await self.redis.get(latest_key)

                if data is None:
                    return None

            # 反序列化数据
            if isinstance(data, bytes):
                saved_data = pickle.loads(data)
            else:
                saved_data = pickle.loads(data.encode())

            checkpoint = saved_data.get("checkpoint")
            parent_checkpoint_id = saved_data.get("parent_checkpoint_id")
            metadata = saved_data.get("metadata", {})

            # 构建 parent_config（如果存在 parent_checkpoint_id）
            parent_config = None
            if parent_checkpoint_id:
                parent_config = {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": parent_checkpoint_id,
                    }
                }

            return CheckpointTuple(
                config=config,
                checkpoint=checkpoint,
                metadata=CheckpointMetadata(**metadata),
                parent_config=parent_config,
                pending_writes=None,
            )

        except Exception as e:
            logger.error(f"获取 checkpoint 失败: {e}")
            return None

    async def aput(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict,
    ) -> dict:
        """异步保存 checkpoint"""
        thread_id = config.get("configurable", {}).get("thread_id")
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")

        if not thread_id:
            raise ValueError("thread_id is required")

        # 生成新的 checkpoint_id
        checkpoint_id = str(checkpoint.get("id", ""))
        if not checkpoint_id:
            import uuid
            checkpoint_id = str(uuid.uuid4())
            checkpoint["id"] = checkpoint_id

        parent_checkpoint_id = config.get("configurable", {}).get("checkpoint_id")

        try:
            # 序列化数据（metadata 可能是 TypedDict 或普通 dict）
            metadata_dict = dict(metadata) if metadata else {}
            saved_data = {
                "checkpoint": checkpoint,
                "parent_checkpoint_id": parent_checkpoint_id,
                "metadata": metadata_dict,
            }

            key = self._make_key(thread_id, checkpoint_ns, checkpoint_id)
            data = pickle.dumps(saved_data)

            # 保存到 Redis
            await self.redis.set(key, data)

            index_key = f"{self.key_prefix}:index:{thread_id}"
            ts_value = checkpoint.get("ts", None)
            try:
                if isinstance(ts_value, (int, float)):
                    score = float(ts_value)
                elif isinstance(ts_value, str):
                    score = datetime.fromisoformat(ts_value).timestamp()
                elif isinstance(ts_value, datetime):
                    score = ts_value.timestamp()
                else:
                    score = time.time()
            except (ValueError, TypeError):
                score = time.time()
            await self.redis.zadd(index_key, {checkpoint_id: score})

            logger.debug(f"Checkpoint 已保存: {key}")

            # 返回更新后的 config（包含新的 checkpoint_id）
            return {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": checkpoint_id,
                }
            }

        except Exception as e:
            logger.error(f"保存 checkpoint 失败: {e}")
            raise

    async def aget(self, config: dict) -> Optional[Checkpoint]:
        """异步获取 checkpoint（简化接口）"""
        result = await self.aget_tuple(config)
        if result:
            return result.checkpoint
        return None

    async def alist(self, config: dict) -> AsyncIterator[tuple[str, CheckpointMetadata]]:
        """异步列出所有 checkpoint"""
        thread_id = config.get("configurable", {}).get("thread_id")
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")

        if not thread_id:
            return

        pattern = f"{self.key_prefix}:{thread_id}:{checkpoint_ns}:*"
        keys = []
        async for k in self.redis.scan_iter(match=pattern):
            keys.append(k.decode() if isinstance(k, bytes) else k)

        for key in sorted(keys):
            try:
                data = await self.redis.get(key)
                if data:
                    if isinstance(data, bytes):
                        saved_data = pickle.loads(data)
                    else:
                        saved_data = pickle.loads(data.encode())
                    metadata = saved_data.get("metadata", {})
                    checkpoint_id = key.split(":")[-1]
                    yield checkpoint_id, CheckpointMetadata(**metadata)
            except Exception as e:
                logger.error(f"列出 checkpoint 失败: {e}")

    async def adelete(self, config: dict) -> None:
        """异步删除 checkpoint"""
        thread_id = config.get("configurable", {}).get("thread_id")
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")

        if not thread_id:
            return

        try:
            if checkpoint_id:
                key = self._make_key(thread_id, checkpoint_ns, checkpoint_id)
                await self.redis.delete(key)
                index_key = f"{self.key_prefix}:index:{thread_id}"
                await self.redis.zrem(index_key, checkpoint_id)
            else:
                # 删除所有相关的 checkpoint
                pattern = f"{self.key_prefix}:{thread_id}:{checkpoint_ns}:*"
                async for key in self.redis.scan_iter(match=pattern):
                    await self.redis.delete(key)
                index_key = f"{self.key_prefix}:index:{thread_id}"
                await self.redis.delete(index_key)

        except Exception as e:
            logger.error(f"删除 checkpoint 失败: {e}")

    async def aput_writes(
        self,
        config: dict,
        writes: list[tuple[str, any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """异步存储中间写入数据（关联到 checkpoint）

        Args:
            config: 关联 checkpoint 的配置
            writes: 要存储的写入列表，每个元素为 (channel, value) 元组
            task_id: 创建写入的任务标识符
            task_path: 创建写入的任务路径
        """
        if not writes:
            return

        thread_id = config.get("configurable", {}).get("thread_id")
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")

        if not thread_id or not checkpoint_id:
            logger.warning("aput_writes: 缺少 thread_id 或 checkpoint_id")
            return

        try:
            writes_key = f"{self.key_prefix}:writes:{thread_id}:{checkpoint_ns}:{checkpoint_id}"

            for idx, (channel, value) in enumerate(writes):
                write_idx = WRITES_IDX_MAP.get(channel, idx)
                write_data = {
                    "task_id": task_id,
                    "channel": channel,
                    "idx": write_idx,
                    "value": pickle.dumps(value),
                    "task_path": task_path,
                }

                field_key = f"{task_id}:{write_idx}"
                await self.redis.hset(writes_key, field_key, pickle.dumps(write_data))

            logger.debug(f"Writes 已保存: {writes_key}, task_id={task_id}")

        except Exception as e:
            logger.error(f"保存 writes 失败: {e}")
            raise


# 全局 checkpointer 实例
_checkpointer: Optional[SimpleRedisCheckpointSaver] = None


async def get_redis_checkpointer() -> SimpleRedisCheckpointSaver:
    """
    获取 Redis Checkpointer 单例实例（异步版本）

    Returns:
        SimpleRedisCheckpointSaver: 配置好的 Redis Checkpointer 实例
    """
    global _checkpointer
    if _checkpointer is None:
        redis_client = await get_redis_client()
        _checkpointer = SimpleRedisCheckpointSaver(redis_client)
        logger.info("SimpleRedisCheckpointSaver 初始化成功")
    return _checkpointer


# 保持向后兼容的别名
create_redis_checkpoint = get_redis_checkpointer
create_redis_client = get_redis_checkpointer
