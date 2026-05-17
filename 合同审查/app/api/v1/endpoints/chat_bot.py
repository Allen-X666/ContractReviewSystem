import asyncio
import json
import logging
import threading
import uuid
from typing import Optional, AsyncGenerator

from fastapi import APIRouter, Body, HTTPException, Query, Request
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from rest_framework import status
from starlette.responses import StreamingResponse

from 合同审查.app.agent import (
    # 统一的合同审查工具
    SYSTEM_PROMPT,
)
from 合同审查.app.agent.create_redis_checkpoint import get_redis_checkpointer
from 合同审查.app.agent.tools_helper import (
    set_request_token,
    clear_request_token,
)
from 合同审查.app.core.config import settings
from 合同审查.app.llm.llm_factory import LLMFactory
from 合同审查.app.utils import jwt_utils
from 合同审查.app.utils.context import RequestContext
from 合同审查.app.utils.conversation_stopper import (
    stop_conversation,
    is_conversation_stopped,
    clear_stop_flag,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ConversationThread(threading.Thread):
    def __init__(self, conversation_id, message, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_id = conversation_id
        self.message = message
        self.name = f"conv-{conversation_id}"


def _extract_text(content) -> str:
    """
    从 AIMessage.content 中提取纯文本。

    部分模型（如 Qwen）会将 content 返回为 list[dict] 格式，
    例如 [{'text': '你好'}, {'text': '！'}]，需要统一转换为字符串。
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return str(content)


# 工具列表 - 从 tools.py 导入的所有工具
from 合同审查.app.agent.tools import (
    search_contract_knowledge,
    review_contract,
    check_contract_exists,
    get_law_reference,
    get_contract_list,
    get_review_list,
    download_file,
    get_user_info,
    update_user_information,
    get_store_path,
    update_store_path,
    get_sys_information,
)

tools = [
    search_contract_knowledge,   # 搜索合同法律知识
    review_contract,             # 审查合同（风险分析/评分/启动审查）
    check_contract_exists,       # 检查合同是否存在
    get_law_reference,           # 查询具体法条
    get_contract_list,           # 获取合同列表
    get_review_list,             # 获取审查列表
    download_file,               # 下载合同或审查文件
    get_user_info,               # 获取用户信息
    update_user_information,     # 更新用户信息
    get_store_path,              # 获取存储路径设置
    update_store_path,           # 修改存储路径设置
    get_sys_information,         # 回答系统操作问题
]

# 全局 checkpointer 实例（延迟初始化）
_checkpointer = None


async def get_checkpointer():
    """
    获取 Checkpointer 实例（单例模式，异步版本）

    延迟初始化，只在首次调用时创建连接。
    """
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = await get_redis_checkpointer()
    return _checkpointer


async def create_contract_agent(llm):
    """
    创建合同法律顾问 Agent（异步版本）

    Args:
        llm: LLM 实例

    Returns:
        CompiledStateGraph 实例
    """
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
    """
    发送消息（SSE 流式输出）

    以 SSE 格式逐 token 返回 AI 回答，前端可实时渲染。
    使用 Redis Checkpointer 持久化对话状态。

    首次对话无需提供 conversation_id，系统会自动创建。

    请求体：纯文本字符串（用户消息）
    响应：text/event-stream 流
    """
    content = content_bytes.decode('utf-8')

    # 从请求头中获取 Authorization
    authorization = request.headers.get("Authorization")
    logger.info(f"收到用户消息：{content}, conversation_id={conversation_id}, authorization={authorization}")
    token = jwt_utils.extract_token_from_header(authorization)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供有效的认证信息"
        )
    
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="消息内容不能为空"
        )

    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    async def event_generator() -> AsyncGenerator[str, None]:
        full_response = ""
        try:
            # 在生成器中设置认证上下文
            # 注意：生成器在异步环境中执行，需要设置上下文供工具使用
            RequestContext.set_auth(token)
            # 同时设置全局 token 供工具函数使用（LangGraph 在独立线程中执行工具）
            set_request_token(token)
            # 清除之前的中断标记（如果有）
            await clear_stop_flag(conversation_id)
            logger.info(f"开始调用 Agent，thread_id={conversation_id}")

            # 只传递当前用户消息，让 LangGraph 自动从 checkpointer 恢复历史消息并追加
            # AgentState 使用 add_messages reducer，会自动合并消息
            messages = [HumanMessage(content=content)]
            logger.info(f"传递新消息给 Agent，等待自动合并历史消息")

            llm = LLMFactory.create_streaming_llm()
            agent = await create_contract_agent(llm)

            # 使用 thread_id 让 checkpointer 持久化对话状态
            # 同时将 token 传递给工具使用
            response = await agent.ainvoke(
                {"messages": messages},
                config={
                    "configurable": {
                        "thread_id": conversation_id,
                        "token": token,  # 将 token 传递给工具
                    }
                }
            )

            # 检查是否被中断
            if await is_conversation_stopped(conversation_id):
                logger.info(f"对话 {conversation_id} 已被中断，停止输出")
                yield "data: [STOPPED]\n\n"
                return

            # 从返回的 messages 中提取最后一条 AI 回复
            output = ""
            for msg in reversed(response["messages"]):
                if isinstance(msg, AIMessage) and msg.content:
                    output = _extract_text(msg.content)
                    break

            logger.info(f"Agent 响应完成，总长度: {len(output)}")

            # 再次检查是否被中断
            if await is_conversation_stopped(conversation_id):
                logger.info(f"对话 {conversation_id} 已被中断，停止输出")
                yield "data: [STOPPED]\n\n"
                return

            # 直接发送完整响应，不做字符级拆分
            data = json.dumps({"content": output}, ensure_ascii=False)
            yield f"data: {data}\n\n"

            yield "data: [DONE]\n\n"

        except asyncio.CancelledError:
            logger.info(f"对话 {conversation_id} 的任务被取消")
            yield "data: [STOPPED]\n\n"
        except Exception as e:
            logger.error(f"生成回复时出错: {e}", exc_info=True)
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
            yield "data: [DONE]\n\n"
        finally:
            # 清理认证上下文
            RequestContext.clear_auth()
            # 清理全局 token
            clear_request_token()
            # 清理中断标记
            await clear_stop_flag(conversation_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/conversations/{conversation_id}/stop")
async def stop_conversation_endpoint(conversation_id: str):
    """
    中断对话

    当用户点击中断按钮时调用此接口，立即停止 AI 的思考和输出。
    """
    try:
        success = await stop_conversation(conversation_id)
        if success:
            logger.info(f"已中断对话: {conversation_id}")
            return {
                "code": 200,
                "message": "对话已中断",
                "conversation_id": conversation_id
            }
        else:
            return {
                "code": 400,
                "message": "中断对话失败",
                "conversation_id": conversation_id
            }
    except Exception as e:
        logger.error(f"中断对话失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"中断对话失败: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """
    清空对话历史

    同时清除 Redis 中持久化的对话状态。
    """
    try:
        # 获取 checkpointer 并删除对应 thread_id 的状态
        checkpointer = await get_checkpointer()

        # 使用 checkpointer 的 adelete 方法删除
        config = {"configurable": {"thread_id": conversation_id}}
        await checkpointer.adelete(config)

        logger.info(f"已清空对话: {conversation_id}")
        return {"message": "对话已清空", "conversation_id": conversation_id}

    except Exception as e:
        logger.error(f"清空对话失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清空对话失败: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(conversation_id: str):
    """
    获取对话历史

    从 Redis Checkpointer 中读取持久化的对话状态。
    """
    try:
        checkpointer = await get_checkpointer()

        # 尝试从 checkpointer 读取状态
        config = {"configurable": {"thread_id": conversation_id}}

        # 使用 aget_tuple 方法获取状态
        result = await checkpointer.aget_tuple(config)
        if result:
            checkpoint = result.checkpoint
            if checkpoint and 'channel_values' in checkpoint:
                channel_values = checkpoint['channel_values']
                if 'messages' in channel_values:
                    messages = channel_values['messages']
                    # 转换为前端需要的格式
                    history = []
                    for msg in messages:
                        if isinstance(msg, HumanMessage):
                            history.append({'role': 'user', 'content': msg.content})
                        elif isinstance(msg, AIMessage):
                            history.append({'role': 'assistant', 'content': msg.content})

                    return {
                        "conversation_id": conversation_id,
                        "messages": history,
                        "source": "redis"
                    }

        # 如果无法读取或为空，返回空列表
        return {
            "conversation_id": conversation_id,
            "messages": [],
            "source": "redis"
        }

    except Exception as e:
        logger.error(f"获取对话历史失败: {e}", exc_info=True)
        return {
            "conversation_id": conversation_id,
            "messages": [],
            "error": str(e)
        }
