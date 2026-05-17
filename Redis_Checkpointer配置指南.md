# LangGraph Redis Checkpointer 配置指南

## 概述

本文档介绍如何在合同审查 Agent 中使用 Redis 作为 `checkpointer` 实现对话状态的持久化存储。

## 依赖安装

```bash
pip install langgraph-checkpoint-redis redis
```

已安装版本：
- `langgraph-checkpoint-redis`: 0.4.1
- `redis`: 6.1.0
- `langgraph-checkpoint`: 4.0.1

---

## 基础配置

### 1. 基础用法（单实例Redis）

```python
from langchain.agents import create_agent
from langgraph.checkpoint.redis import RedisSaver
import redis

# 创建 Redis 客户端
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=False  # 必须设置为False，因为存储的是二进制数据
)

# 创建 Redis Checkpointer
checkpointer = RedisSaver(redis_client)

# 创建 Agent
def create_contract_agent(llm):
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,  # 添加 Redis 持久化
    )
    return agent
```

---

### 2. 带连接池的高级配置

```python
from langchain.agents import create_agent
from langgraph.checkpoint.redis import RedisSaver
from redis import Redis, ConnectionPool

# 创建连接池（生产环境推荐）
connection_pool = ConnectionPool(
    host="localhost",
    port=6379,
    db=0,
    max_connections=50,        # 最大连接数
    decode_responses=False,    # 必须保持False
    socket_connect_timeout=5,  # 连接超时
    socket_timeout=5,          # 读取超时
    health_check_interval=30,  # 健康检查间隔
)

redis_client = Redis(connection_pool=connection_pool)

# 创建 Checkpointer
checkpointer = RedisSaver(redis_client)

def create_contract_agent(llm):
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
```

---

### 3. 带密码和SSL的生产环境配置

```python
from langchain.agents import create_agent
from langgraph.checkpoint.redis import RedisSaver
import redis

redis_client = redis.Redis(
    host="your-redis-host.com",
    port=6380,
    password="your-secure-password",
    ssl=True,                    # 启用SSL
    ssl_cert_reqs="required",    # 要求证书验证
    ssl_ca_certs="/path/to/ca.crt",
    db=0,
    decode_responses=False,
)

checkpointer = RedisSaver(redis_client)

def create_contract_agent(llm):
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
```

---

### 4. Redis Sentinel 高可用配置

```python
from langchain.agents import create_agent
from langgraph.checkpoint.redis import RedisSaver
from redis.sentinel import Sentinel

# Sentinel 配置
sentinel = Sentinel([
    ("sentinel-1", 26379),
    ("sentinel-2", 26379),
    ("sentinel-3", 26379),
])

# 获取主节点连接
redis_client = sentinel.master_for(
    "mymaster",           # Sentinel 监控的主节点名称
    socket_timeout=5,
    decode_responses=False,
)

checkpointer = RedisSaver(redis_client)

def create_contract_agent(llm):
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
```

---

### 5. Redis Cluster 集群配置

```python
from langchain.agents import create_agent
from langgraph.checkpoint.redis import RedisSaver
from redis.cluster import RedisCluster

# 集群模式
startup_nodes = [
    {"host": "node1", "port": 7000},
    {"host": "node2", "port": 7000},
    {"host": "node3", "port": 7000},
]

redis_client = RedisCluster(
    startup_nodes=startup_nodes,
    decode_responses=False,
    skip_full_coverage_check=True,
)

checkpointer = RedisSaver(redis_client)

def create_contract_agent(llm):
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
```

---

## 在 chat_bot.py 中的完整集成

### 修改后的完整代码

```python
import asyncio
import json
import logging
from typing import Optional, AsyncGenerator

from fastapi import APIRouter, Body, HTTPException, Query
from langchain.agents import create_agent
from rest_framework import status
from starlette.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Redis Checkpointer 导入
from langgraph.checkpoint.redis import RedisSaver
import redis

from 合同审查.app.llm.tongyi_llm import TongyiLLMFactory
from 合同审查.app.core.config import settings
from 合同审查.app.agent import (
    search_contract_knowledge,
    analyze_contract_risk,
    get_law_reference,
    calculate_contract_score,
    check_contract_exists,
    start_contract_review,
    SYSTEM_PROMPT,
    WELCOME_MESSAGE,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# 工具列表
tools = [
    search_contract_knowledge,
    analyze_contract_risk,
    get_law_reference,
    calculate_contract_score,
    check_contract_exists,
    start_contract_review,
]


# ==================== Redis Checkpointer 配置 ====================

def create_redis_checkpointer():
    """
    创建 Redis Checkpointer
    
    根据环境变量或配置选择不同的连接方式
    """
    # 基础配置
    redis_host = getattr(settings, "REDIS_HOST", "localhost")
    redis_port = getattr(settings, "REDIS_PORT", 6379)
    redis_db = getattr(settings, "REDIS_DB", 0)
    redis_password = getattr(settings, "REDIS_PASSWORD", None)
    
    # 创建 Redis 客户端
    client_kwargs = {
        "host": redis_host,
        "port": redis_port,
        "db": redis_db,
        "decode_responses": False,  # 重要：必须设置为False
    }
    
    if redis_password:
        client_kwargs["password"] = redis_password
    
    redis_client = redis.Redis(**client_kwargs)
    
    # 测试连接
    try:
        redis_client.ping()
        logger.info(f"Redis 连接成功: {redis_host}:{redis_port}")
    except Exception as e:
        logger.error(f"Redis 连接失败: {e}")
        raise
    
    return RedisSaver(redis_client)


# 全局 checkpointer 实例（应用启动时初始化）
checkpointer = None


def init_checkpointer():
    """初始化 checkpointer"""
    global checkpointer
    if checkpointer is None:
        checkpointer = create_redis_checkpointer()
    return checkpointer


# ==================== Agent 创建 ====================

def create_contract_agent(llm):
    """
    创建合同法律顾问 Agent
    
    Args:
        llm: LLM 实例
        
    Returns:
        CompiledStateGraph 实例
    """
    global checkpointer
    
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,  # 使用 Redis 持久化
    )
    
    return agent


# ==================== API 端点 ====================

@router.post("/messages")
async def send_message(
    content = content_bytes.decode('utf-8')
    logger.info(f"收到用户消息：{content}")
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="消息内容不能为空"
        )

    # 确保 checkpointer 已初始化
    init_checkpointer()

    async def event_generator() -> AsyncGenerator[str, None]:
        full_response = ""
        try:
            yield "data: {\"type\": \"start\"}\n\n"

            # 构建消息列表
            messages = []
            for msg in conversations.get(conversation_id, []):
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    messages.append(AIMessage(content=msg['content']))

            # 保存用户消息到历史
            if conversation_id not in conversations:
                conversations[conversation_id] = []
            conversations[conversation_id].append({
                'role': 'user',
                'content': content
            })

            # 添加当前用户消息
            messages.append(HumanMessage(content=content))

            logger.info(f"开始调用 Agent，thread_id={conversation_id}")

            llm = TongyiLLMFactory.create_streaming_llm()
            agent = create_contract_agent(llm)

            # 使用 thread_id 让 checkpointer 持久化对话状态
            response = await agent.ainvoke(
                {"messages": messages},
                config={"configurable": {"thread_id": conversation_id}}
            )

            # 从返回的 messages 中提取最后一条 AI 回复
            output = ""
            for msg in reversed(response["messages"]):
                if isinstance(msg, AIMessage) and msg.content:
                    output = msg.content
                    break

            logger.info(f"Agent 响应完成，总长度: {len(output)}")

            chunk_size = 4
            chunk_count = 0

            for i in range(0, len(output), chunk_size):
                chunk = output[i:i + chunk_size]
                full_response += chunk
                chunk_count += 1

                data = json.dumps({"content": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"

                await asyncio.sleep(0.01)

            logger.info(f"共发送 {chunk_count} 个 chunk")

            conversations[conversation_id].append({
                'role': 'assistant',
                'content': full_response
            })

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"生成回复时出错: {e}", exc_info=True)
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
            yield "data: [DONE]\n\n"

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

---

## 配置项说明

在 `settings.py` 或环境变量中添加以下配置：

```python
# Redis 配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)  # 无密码则设为 None
```

---

## 关键概念：thread_id

使用 `checkpointer` 时，必须通过 `config` 传入 `thread_id`：

```python
response = await agent.ainvoke(
    {"messages": messages},
    config={"configurable": {"thread_id": conversation_id}}  # 必须！
)
```

- `thread_id` 是对话的唯一标识
- 相同 `thread_id` 的请求会读取之前保存的状态
- 不同 `thread_id` 之间状态隔离

---

## Redis 数据结构

Checkpointer 在 Redis 中存储的数据：

```
Key: checkpoint:{thread_id}
Value: {
    "messages": [...],      # 消息历史
    "next_node": "...",     # 下一个执行节点
    "checkpoint_id": "...", # 检查点ID
    "metadata": {...}       # 其他元数据
}
```

---

## 注意事项

| 注意点 | 说明 |
|--------|------|
| `decode_responses=False` | **必须**设置为 `False`，因为存储的是二进制序列化数据 |
| `thread_id` | 调用 `ainvoke` 时必须传入，否则无法正确存取状态 |
| 内存管理 | 定期清理过期的 `thread_id` 数据，避免 Redis 内存无限增长 |
| 序列化 | Checkpointer 自动使用 `msgpack` 序列化数据 |

---

## 故障排查

### 1. 连接失败

```
Redis 连接失败: Error 111 connecting to localhost:6379. Connection refused.
```

**解决**：检查 Redis 服务是否启动

```bash
# Windows
redis-server.exe

# Linux/Mac
redis-server
```

### 2. decode_responses 错误

```
TypeError: a bytes-like object is required, not 'str'
```

**解决**：确保 `decode_responses=False`

### 3. 状态未持久化

**检查**：确认调用时传入了 `thread_id`

```python
# 错误
response = await agent.ainvoke({"messages": messages})

# 正确
response = await agent.ainvoke(
    {"messages": messages},
    config={"configurable": {"thread_id": "unique_id"}}
)
```_bytes: bytes = Body(..., media_type="text/plain"),
    conversation_id: Optional[str] = Query(None, alias="conversationId")
):
    """
    发送消息（SSE 流式输出）
    
    使用 Redis 持久化对话状态
    """
    content