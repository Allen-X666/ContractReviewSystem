# FastAPI Agent 工具携带 Authorization 指南

## 问题背景

在 `chat_bot.py` 中，Agent 工具（如 `review_contract`, `check_contract_exists` 等）需要调用 SpringBoot 后端接口，这些接口需要 JWT Token 进行认证。但工具函数是在 LangChain Agent 执行过程中被调用的，无法直接访问 FastAPI 的 `Request` 对象。

## 解决方案

### 方案一：使用线程本地存储（推荐）

通过 `threading.local()` 在请求上下文中传递 Authorization。

#### 1. 创建上下文管理器

**文件**: `合同审查/app/utils/context.py`

```python
"""
请求上下文管理器

用于在 Agent 工具中传递请求相关的上下文信息（如 Authorization）
"""

import threading
from typing import Optional

# 线程本地存储
_thread_local = threading.local()


class RequestContext:
    """请求上下文"""
    
    @staticmethod
    def set_authorization(token: Optional[str]) -> None:
        """设置当前线程的 Authorization Token"""
        _thread_local.authorization = token
    
    @staticmethod
    def get_authorization() -> Optional[str]:
        """获取当前线程的 Authorization Token"""
        return getattr(_thread_local, 'authorization', None)
    
    @staticmethod
    def clear() -> None:
        """清除当前线程的上下文"""
        if hasattr(_thread_local, 'authorization'):
            delattr(_thread_local, 'authorization')
    
    @staticmethod
    def set(key: str, value: any) -> None:
        """设置自定义上下文值"""
        setattr(_thread_local, key, value)
    
    @staticmethod
    def get(key: str, default=None) -> any:
        """获取自定义上下文值"""
        return getattr(_thread_local, key, default)


# 上下文管理器（用于 with 语句）
class request_context:
    """
    请求上下文管理器
    
    用法:
        with request_context(authorization="Bearer xxx"):
            # 在这个上下文中可以访问 authorization
            result = some_tool()
    """
    
    def __init__(self, authorization: Optional[str] = None, **kwargs):
        self.authorization = authorization
        self.kwargs = kwargs
    
    def __enter__(self):
        RequestContext.set_authorization(self.authorization)
        for key, value in self.kwargs.items():
            RequestContext.set(key, value)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        RequestContext.clear()
        return False
```

#### 2. 修改 chat_bot.py

在 `send_message` 函数中设置上下文：

```python
from 合同审查.app.utils.context import request_context, RequestContext

@router.post("/messages")
async def send_message(
        request: Request,
        content_bytes: bytes = Body(..., media_type="text/plain"),
        conversation_id: Optional[str] = Query(None, alias="conversationId")
):
    content = content_bytes.decode('utf-8')
    
    # 从请求头中获取 Authorization
    authorization = request.headers.get("Authorization")
    token = jwt_utils.extract_token_from_header(authorization)
    
    # 设置请求上下文
    with request_context(authorization=token):
        # ... 原有代码 ...
        
        async def event_generator() -> AsyncGenerator[str, None]:
            # 在生成器中也可以访问上下文
            # 因为上下文绑定到线程，而生成器在同一线程执行
            
            response = await agent.ainvoke(
                {"messages": messages},
                config={"configurable": {"thread_id": conversation_id}}
            )
            # ...
```

#### 3. 修改工具函数

**文件**: `合同审查/app/agent/tools.py`

```python
from 合同审查.app.utils.context import RequestContext
from 合同审查.app.core.http_client import SpringBootHttpClient

@tool
def review_contract(contract_identifier: str, review_type: str = "full") -> str:
    """
    审查合同
    
    在工具内部获取 Authorization 并调用 SpringBoot 接口
    """
    # 获取当前请求的 Authorization
    token = RequestContext.get_authorization()
    
    if not token:
        return "错误：未获取到认证信息，请重新登录"
    
    # 使用 token 调用 SpringBoot 接口
    async def call_springboot_api():
        async with SpringBootHttpClient(token=token) as client:
            # 调用 SpringBoot 的审查接口
            response = await client.post(
                "/review/start",
                json_data={"contractId": contract_id}
            )
            return response.json()
    
    # 注意：工具函数是同步的，需要运行异步代码
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(call_springboot_api())
    except RuntimeError:
        # 如果没有事件循环，创建一个新的
        result = asyncio.run(call_springboot_api())
    
    # 处理结果...
```

### 方案二：使用闭包/偏函数（简单场景）

在创建 Agent 时将 token 注入到工具函数中。

#### 1. 修改工具为可配置

```python
from functools import partial
from langchain_core.tools import tool

def create_review_contract_tool(token: Optional[str]):
    """创建带有 token 的 review_contract 工具"""
    
    @tool
    def review_contract(contract_identifier: str, review_type: str = "full") -> str:
        """审查合同"""
        # 直接使用传入的 token
        if not token:
            return "错误：未获取到认证信息"
        
        # 调用 SpringBoot 接口...
        return f"使用 token {token[:20]}... 审查合同 {contract_identifier}"
    
    return review_contract
```

#### 2. 动态创建工具列表

```python
async def create_contract_agent(llm, token: Optional[str]):
    """
    创建合同法律顾问 Agent（带认证信息）
    
    Args:
        llm: LLM 实例
        token: JWT Token
    """
    # 动态创建带 token 的工具
    tools = [
        search_contract_knowledge,  # 不需要认证的公共工具
        create_review_contract_tool(token),
        create_check_contract_exists_tool(token),
        get_law_reference,
    ]
    
    return create_agent(
        name="智能助手",
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        debug=settings.CHAT_DEBUG,
        checkpointer=await get_checkpointer(),
    )


@router.post("/messages")
async def send_message(
        request: Request,
        content_bytes: bytes = Body(..., media_type="text/plain"),
        conversation_id: Optional[str] = Query(None, alias="conversationId")
):
    # ...
    token = jwt_utils.extract_token_from_header(authorization)
    
    # 创建带 token 的 Agent
    llm = LLMFactory.create_streaming_llm()
    agent = await create_contract_agent(llm, token)
    
    # ...
```

### 方案三：使用 LangGraph 的 State（推荐用于复杂场景）

将 Authorization 存入 LangGraph 的 State 中，在工具节点中访问。

#### 1. 定义 State

```python
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """Agent 状态"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    authorization: Optional[str]  # 添加 authorization 字段
```

#### 2. 创建工具节点

```python
from langgraph.graph import StateGraph, END

def create_tool_node(tool_func):
    """创建可以访问 state 的工具节点"""
    
    def tool_node(state: AgentState):
        # 从 state 中获取 authorization
        token = state.get("authorization")
        
        # 将 token 设置到上下文
        RequestContext.set_authorization(token)
        
        # 执行工具
        result = tool_func(state)
        
        return result
    
    return tool_node
```

#### 3. 构建 Graph

```python
def build_agent_graph(llm, tools, token: Optional[str]):
    """构建带认证的 Agent Graph"""
    
    # 定义节点
    def agent_node(state: AgentState):
        # Agent 决策节点
        messages = state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}
    
    def tool_executor(state: AgentState):
        # 工具执行节点
        last_message = state["messages"][-1]
        
        # 解析工具调用
        if hasattr(last_message, 'tool_calls'):
            tool_calls = last_message.tool_calls
            results = []
            
            for tool_call in tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                # 找到对应的工具函数
                tool_func = next((t for t in tools if t.name == tool_name), None)
                
                if tool_func:
                    # 将 token 注入工具参数
                    tool_args['_token'] = state.get('authorization')
                    result = tool_func.invoke(tool_args)
                    results.append(result)
            
            return {"messages": results}
        
        return state
    
    # 构建图
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_executor)
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END
        }
    )
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()
```

## 完整实现示例

### 步骤 1：创建上下文模块

```python
# 合同审查/app/utils/context.py
import threading
from contextlib import contextmanager
from typing import Optional, Any

_thread_local = threading.local()

class RequestContext:
    """请求上下文管理"""
    
    @staticmethod
    def set_auth(token: Optional[str]) -> None:
        """设置认证令牌"""
        _thread_local.authorization = token
    
    @staticmethod
    def get_auth() -> Optional[str]:
        """获取认证令牌"""
        return getattr(_thread_local, 'authorization', None)
    
    @staticmethod
    def clear_auth() -> None:
        """清除认证令牌"""
        if hasattr(_thread_local, 'authorization'):
            delattr(_thread_local, 'authorization')
    
    @staticmethod
    def set(key: str, value: Any) -> None:
        """设置任意上下文值"""
        setattr(_thread_local, key, value)
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """获取上下文值"""
        return getattr(_thread_local, key, default)


@contextmanager
def auth_context(token: Optional[str]):
    """
    认证上下文管理器
    
    用法:
        with auth_context("Bearer xxx"):
            result = tool_func()
    """
    RequestContext.set_auth(token)
    try:
        yield
    finally:
        RequestContext.clear_auth()
```

### 步骤 2：修改工具函数

```python
# 合同审查/app/agent/tools.py
from 合同审查.app.utils.context import RequestContext
from 合同审查.app.core.http_client import springboot_get, springboot_post

@tool
def check_contract_exists(contract_identifier: str) -> str:
    """
    检查系统中是否存在指定合同
    
    此工具需要调用 SpringBoot 后端接口，会自动使用当前请求的 Authorization
    """
    logger.info(f"[Tool] 检查合同是否存在: {contract_identifier}")
    
    # 获取当前请求的 token
    token = RequestContext.get_auth()
    if not token:
        return "❌ 错误：未获取到认证信息，请重新登录后再试"
    
    # 异步调用 SpringBoot 接口
    import asyncio
    
    async def fetch_contract():
        # 尝试作为合同ID查询
        if contract_identifier.isdigit():
            response = await springboot_get(
                f"/contract/preview/{contract_identifier}",
                token=token
            )
        else:
            # 作为合同名称查询
            response = await springboot_get(
                "/contract/list",
                params={"keyword": contract_identifier, "page": 1, "pageSize": 1},
                token=token
            )
        return response
    
    try:
        # 执行异步调用
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(fetch_contract())
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200 and data.get("data"):
                contract = data["data"]
                return f"✅ 找到合同：{contract.get('contractName')} (ID: {contract.get('id')})"
            else:
                return f"❌ 未找到合同：{contract_identifier}"
        else:
            return f"❌ 查询失败：{response.status_code}"
            
    except Exception as e:
        logger.error(f"查询合同失败: {e}")
        return f"❌ 查询出错：{str(e)}"


@tool
def review_contract(contract_identifier: str, review_type: str = "full") -> str:
    """
    审查合同
    
    调用 SpringBoot 后端启动合同审查流程
    """
    logger.info(f"[Tool] 审查合同: {contract_identifier}, type={review_type}")
    
    token = RequestContext.get_auth()
    if not token:
        return "❌ 错误：未获取到认证信息"
    
    import asyncio
    
    async def start_review():
        # 先获取合同ID
        contract_id = None
        if contract_identifier.isdigit():
            contract_id = int(contract_identifier)
        else:
            # 查询合同名称获取ID
            response = await springboot_get(
                "/contract/list",
                params={"keyword": contract_identifier, "page": 1, "pageSize": 1},
                token=token
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    contract_id = data["data"][0].get("id")
        
        if not contract_id:
            return None, "未找到合同"
        
        # 启动审查
        response = await springboot_post(
            "/review/start",
            json_data={
                "contractId": contract_id,
                "reviewType": review_type
            },
            token=token
        )
        return contract_id, response
    
    try:
        loop = asyncio.get_event_loop()
        contract_id, response = loop.run_until_complete(start_review())
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                review_id = data.get("data", {}).get("reviewId")
                return f"✅ 已启动合同审查（审查ID: {review_id}），请稍后查看结果"
            else:
                return f"❌ 启动审查失败：{data.get('message')}"
        else:
            return "❌ 启动审查失败"
            
    except Exception as e:
        logger.error(f"启动审查失败: {e}")
        return f"❌ 启动审查出错：{str(e)}"
```

### 步骤 3：修改 chat_bot.py

```python
# 合同审查/app/api/v1/endpoints/chat_bot.py
from 合同审查.app.utils.context import auth_context, RequestContext

@router.post("/messages")
async def send_message(
        request: Request,
        content_bytes: bytes = Body(..., media_type="text/plain"),
        conversation_id: Optional[str] = Query(None, alias="conversationId")
):
    """
    发送消息（SSE 流式输出）
    """
    content = content_bytes.decode('utf-8')
    
    # 从请求头中获取 Authorization
    authorization = request.headers.get("Authorization")
    token = jwt_utils.extract_token_from_header(authorization)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供有效的认证信息"
        )
    
    # 设置请求上下文（在整个请求处理期间有效）
    with auth_context(token):
        if not content or not content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="消息内容不能为空"
            )
        
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        async def event_generator() -> AsyncGenerator[str, None]:
            try:
                # 在生成器内部也需要设置上下文
                # 因为生成器可能在不同线程执行
                RequestContext.set_auth(token)
                
                llm = LLMFactory.create_streaming_llm()
                agent = await create_contract_agent(llm)
                
                messages = [HumanMessage(content=content)]
                
                response = await agent.ainvoke(
                    {"messages": messages},
                    config={"configurable": {"thread_id": conversation_id}}
                )
                
                # 提取 AI 回复
                output = ""
                for msg in reversed(response["messages"]):
                    if isinstance(msg, AIMessage) and msg.content:
                        output = _extract_text(msg.content)
                        break
                
                data = json.dumps({"content": output}, ensure_ascii=False)
                yield f"data: {data}\n\n"
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"生成回复时出错: {e}", exc_info=True)
                error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
                yield f"data: {error_data}\n\n"
                yield "data: [DONE]\n\n"
            finally:
                # 清理上下文
                RequestContext.clear_auth()
        
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

## 方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **线程本地存储** | 实现简单，对现有代码改动小 | 依赖线程模型，异步代码需注意 | 大多数场景 |
| **闭包/偏函数** | 每个请求独立，无并发问题 | 需要动态创建工具，开销稍大 | 工具较少时 |
| **LangGraph State** | 符合 LangGraph 设计理念 | 实现复杂，需要重构代码 | 复杂 Agent 流程 |

## 注意事项

1. **异步代码处理**：工具函数是同步的，但调用 SpringBoot 接口需要异步，使用 `asyncio.get_event_loop()` 或 `asyncio.run()` 转换

2. **上下文清理**：确保在请求结束时清理上下文，避免内存泄漏

3. **错误处理**：工具中需要处理 token 不存在或过期的情况

4. **日志记录**：记录工具调用时的认证信息（注意脱敏）
