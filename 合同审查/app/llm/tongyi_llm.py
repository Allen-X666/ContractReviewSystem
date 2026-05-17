"""
通义千问LLM接口

基于LangChain的通义千问大语言模型封装。
"""

import os
import json
import re
import logging
from typing import Optional, List, Dict, Any, AsyncIterator, Iterator, Sequence, Type, Callable, Union
from dataclasses import dataclass, field

import requests as requests_lib
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    AIMessageChunk,
    ToolMessage,
)
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.runnables import RunnableSerializable, Runnable
from pydantic import BaseModel, Field, ValidationError

from 合同审查.app.core.config import settings

logger = logging.getLogger(__name__)


DEFAULT_TIMEOUT = 120
DEFAULT_MAX_RETRIES = 3
DASHSCOPE_OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


@dataclass
class _CompatMessage:
    content: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class _CompatChoice:
    message: _CompatMessage = field(default_factory=_CompatMessage)
    finish_reason: str = "stop"


@dataclass
class _CompatOutput:
    choices: List[_CompatChoice] = field(default_factory=list)


@dataclass
class _CompatResponse:
    status_code: int = 200
    message: str = ""
    request_id: str = ""
    output: _CompatOutput = field(default_factory=_CompatOutput)


@dataclass
class LLMConfig:
    """LLM配置类"""
    model: str = settings.LLM_MODEL_REVIEW
    temperature: float = 0.7
    max_tokens: Optional[int] = 2048
    top_p: float = 0.9
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    streaming: bool = False
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES


class TongyiLLM(BaseChatModel):
    """
    通义千问大语言模型

    基于阿里云DashScope的通义千问模型封装，兼容LangChain接口。
    """

    model: str = settings.LLM_MODEL_REVIEW
    temperature: float = 0.7
    max_tokens: Optional[int] = 2048
    top_p: float = 0.9
    api_key: Optional[str] = None
    streaming: bool = False
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    bound_tools: List[Dict[str, Any]] = Field(default_factory=list, exclude=True)
    tool_choice: Optional[Any] = Field(default=None, exclude=True)

    def __init__(self, config: Optional[LLMConfig] = None, **kwargs):
        """
        初始化通义千问LLM

        Args:
            config: LLM配置对象
            **kwargs: 其他参数
        """
        config = config or LLMConfig()

        super().__init__(
            model=config.model or kwargs.get("model", settings.LLM_MODEL_REVIEW),
            temperature=config.temperature or kwargs.get("temperature", 0.7),
            max_tokens=config.max_tokens or kwargs.get("max_tokens", 2048),
            top_p=config.top_p or kwargs.get("top_p", 0.9),
            api_key=config.api_key or kwargs.get("api_key") or os.getenv("DASHSCOPE_API_KEY"),
            streaming=config.streaming or kwargs.get("streaming", False),
            timeout=config.timeout or kwargs.get("timeout", DEFAULT_TIMEOUT),
            max_retries=config.max_retries or kwargs.get("max_retries", DEFAULT_MAX_RETRIES),
        )

        # 设置API密钥
        self._setup_api_key()

        self._openai_client = OpenAI(
            api_key=self.api_key,
            base_url=DASHSCOPE_OPENAI_BASE_URL,
        )

    def _setup_api_key(self):
        """设置DashScope API密钥"""
        try:
            import dashscope
            if self.api_key:
                dashscope.api_key = self.api_key
            else:
                self.api_key = os.getenv("DASHSCOPE_API_KEY")
                if not self.api_key:
                    raise ValueError("未设置DashScope API密钥")
                dashscope.api_key = self.api_key
        except ImportError:
            raise ImportError("请安装dashscope: pip install dashscope")

    def bind_tools(
        self,
        tools: Sequence[Union[Dict[str, Any], Type, Callable, Any]],
        *,
        tool_choice: Optional[Union[str, bool]] = None,
        **kwargs: Any,
    ) -> Runnable:
        """绑定工具到 LLM，供 Agent 框架调用

        Args:
            tools: 工具列表，支持 BaseTool、Pydantic 模型、Callable 或 OpenAI 格式 dict
            tool_choice: 工具选择策略
            **kwargs: 其他参数

        Returns:
            绑定了工具的 Runnable
        """
        from langchain_core.tools import BaseTool
        from langchain_core.utils.function_calling import convert_to_openai_tool

        formatted_tools = []
        for tool in tools:
            if isinstance(tool, dict) and "type" in tool:
                formatted_tools.append(tool)
            else:
                formatted_tools.append(convert_to_openai_tool(tool))

        return self.bind(tools=formatted_tools, tool_choice=tool_choice, **kwargs)

    @property
    def _llm_type(self) -> str:
        """返回LLM类型"""
        return "tongyi"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """返回标识参数"""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

    def _call_dashscope_api(
        self,
        messages_list: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
    ) -> Any:
        """调用 DashScope MultiModalConversation API，带超时控制

        统一使用 MultiModalConversation.call() (multimodal-generation 端点)，
        支持纯文本和多模态模型。

        Args:
            messages_list: DashScope 格式的消息列表（多模态格式）
            tools: 工具定义列表（OpenAI 格式）
            tool_choice: 工具选择策略

        Returns:
            DashScope API 响应对象
        """
        from dashscope import MultiModalConversation

        common_kwargs = {
            "model": self.model,
            "messages": messages_list,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

        if tools:
            common_kwargs["tools"] = tools
            if tool_choice is not None:
                common_kwargs["tool_choice"] = tool_choice

        response = MultiModalConversation.call(
            **common_kwargs,
            timeout=self.timeout,
        )

        return response

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        生成响应（同步）

        带超时控制与重试机制：超时或连接异常时自动重试，使用指数退避策略。

        Args:
            messages: 消息列表
            stop: 停止词列表
            run_manager: 回调管理器

        Returns:
            ChatResult: 聊天结果
        """
        tools = kwargs.pop("tools", None)
        tool_choice = kwargs.pop("tool_choice", None)

        messages_list = self._convert_messages(messages)

        for idx, msg in enumerate(messages):
            logger.info(f"【LLM输入】message[{idx}] type={type(msg).__name__}, content={msg.content}")

        response = self._call_dashscope_with_retry(
            messages_list, tools=tools, tool_choice=tool_choice
        )

        if response.status_code != 200:
            raise RuntimeError(f"通义千问API调用失败: {response.message}")

        msg_obj = response.output.choices[0].message
        content = msg_obj.content or ""

        logger.info(f"【LLM输出】request_id={response.request_id}, content={content}")

        parsed_tool_calls = self._parse_tool_calls(msg_obj, tools)

        generation = ChatGeneration(
            message=AIMessage(
                content=content,
                tool_calls=parsed_tool_calls if parsed_tool_calls else [],
            ),
            generation_info={
                "finish_reason": response.output.choices[0].finish_reason,
                "request_id": response.request_id,
            },
        )

        return ChatResult(generations=[generation])

    @staticmethod
    def _parse_tool_calls(
        msg_obj: Any,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """解析 DashScope 响应中的 tool_calls

        Args:
            msg_obj: DashScope 响应中的 message 对象
            tools: 工具定义列表（用于获取参数 schema）

        Returns:
            LangChain 格式的 tool_calls 列表
        """
        import uuid as _uuid

        try:
            raw_tool_calls = getattr(msg_obj, "tool_calls", None)
        except (KeyError, AttributeError):
            raw_tool_calls = None
        if not raw_tool_calls:
            return []

        tool_name_to_schema: Dict[str, Any] = {}
        if tools:
            for t in tools:
                func = t.get("function", {})
                tool_name_to_schema[func.get("name", "")] = func.get("parameters", {})

        parsed = []
        for tc in raw_tool_calls:
            func = tc.get("function", {}) if isinstance(tc, dict) else getattr(tc, "function", {})
            name = func.get("name", "") if isinstance(func, dict) else getattr(func, "name", "")
            raw_args = func.get("arguments", "{}") if isinstance(func, dict) else getattr(func, "arguments", "{}")

            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {"raw": raw_args}
            else:
                args = raw_args

            tc_id = tc.get("id", "") if isinstance(tc, dict) else getattr(tc, "id", "")
            if not tc_id:
                tc_id = f"call_{_uuid.uuid4().hex[:8]}"

            parsed.append({
                "name": name,
                "args": args,
                "id": tc_id,
                "type": "tool_call",
            })

        return parsed

    def _call_dashscope_with_retry(
        self,
        messages_list: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
    ) -> Any:
        """带重试机制的 DashScope API 调用

        使用 tenacity 实现指数退避重试，针对超时和连接异常自动重试。

        Args:
            messages_list: DashScope 格式的消息列表
            tools: 工具定义列表
            tool_choice: 工具选择策略

        Returns:
            DashScope API 响应对象
        """
        max_attempts = self.max_retries

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=2, min=5, max=30),
            retry=retry_if_exception_type((
                requests_lib.exceptions.Timeout,
                requests_lib.exceptions.ConnectionError,
            )),
            before_sleep=lambda retry_state: logger.warning(
                f"DashScope API 调用超时或连接失败，第 {retry_state.attempt_number} 次重试，"
                f"等待 {retry_state.next_action.sleep:.1f} 秒后重试..."
            ),
            reraise=True,
        )
        def _do_call():
            return self._call_dashscope_api(messages_list, tools=tools, tool_choice=tool_choice)

        return _do_call()

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        生成响应（异步）

        Args:
            messages: 消息列表
            stop: 停止词列表
            run_manager: 回调管理器

        Returns:
            ChatResult: 聊天结果
        """
        logger.info(f"TongyiLLM _agenerate 开始调用，模型: {self.model}")

        import asyncio
        loop = asyncio.get_event_loop()

        def sync_generate():
            logger.info("在线程池中执行 _generate...")
            try:
                result = self._generate(messages, stop, run_manager, **kwargs)
                logger.info("_generate 执行完成")
                return result
            except Exception as e:
                logger.error(f"_generate 执行失败: {e}")
                raise

        result = await loop.run_in_executor(None, sync_generate)
        logger.info("TongyiLLM _agenerate 完成")
        return result

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """
        流式生成响应

        Args:
            messages: 消息列表
            stop: 停止词列表
            run_manager: 回调管理器

        Yields:
            ChatGenerationChunk: 聊天生成结果块
        """
        from dashscope import MultiModalConversation

        tools = kwargs.pop("tools", None)
        tool_choice = kwargs.pop("tool_choice", None)

        messages_list = self._convert_messages(messages)

        common_kwargs = {
            "model": self.model,
            "messages": messages_list,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stream": True,
        }

        if tools:
            common_kwargs["tools"] = tools
            if tool_choice is not None:
                common_kwargs["tool_choice"] = tool_choice

        responses = MultiModalConversation.call(**common_kwargs)

        # 用于累积当前工具调用的状态（处理模型为每个片段生成不同tc_id的情况）
        _current_tool_call: Dict[str, Any] = {
            "name": "",
            "args_parts": [],
            "complete": False,
            "tc_id": "",
        }

        for response in responses:
            if response.status_code != 200:
                raise RuntimeError(f"通义千问API流式调用失败: {response.message}")

            if hasattr(response.output, 'choices') and len(response.output.choices) > 0:
                choice = response.output.choices[0]
                delta = choice.message.content

                try:
                    raw_tool_calls = getattr(choice.message, "tool_calls", None)
                except (KeyError, AttributeError):
                    raw_tool_calls = None

                if raw_tool_calls:
                    import uuid as _uuid
                    for tc in raw_tool_calls:
                        func = tc.get("function", {}) if isinstance(tc, dict) else getattr(tc, "function", {})
                        name = func.get("name", "") if isinstance(func, dict) else getattr(func, "name", "")
                        tc_id = tc.get("id", "") if isinstance(tc, dict) else getattr(tc, "id", "")

                        if not tc_id:
                            tc_id = f"call_{_uuid.uuid4().hex[:8]}"

                        # 获取参数片段
                        raw_args = func.get("arguments", "") if isinstance(func, dict) else getattr(func, "arguments", "")

                        logger.info(f"[ToolCall片段] tc_id={tc_id}, name={name!r}, raw_args={raw_args!r}")

                        # 如果有name，说明是新的工具调用开始
                        if name:
                            # 如果之前有未完成的工具调用，先尝试完成它
                            if _current_tool_call["args_parts"] and not _current_tool_call["complete"]:
                                full_args_str = "".join(_current_tool_call["args_parts"])
                                try:
                                    args = json.loads(full_args_str)
                                    if _current_tool_call["name"]:
                                        logger.info(f"[ToolCall完成-新name触发] name={_current_tool_call['name']!r}, args={args}")
                                        tool_call_chunk = AIMessageChunk(
                                            content="",
                                            tool_calls=[{
                                                "name": _current_tool_call["name"],
                                                "args": args,
                                                "id": _current_tool_call["tc_id"] or tc_id,
                                                "type": "tool_call"
                                            }],
                                        )
                                        yield ChatGenerationChunk(message=tool_call_chunk)
                                except json.JSONDecodeError:
                                    logger.warning(f"[ToolCall丢弃] 参数不完整，name={_current_tool_call['name']!r}")

                            # 开始新的工具调用
                            _current_tool_call = {
                                "name": name,
                                "args_parts": [],
                                "complete": False,
                                "tc_id": tc_id,
                            }
                            logger.info(f"[ToolCall开始] name={name}, tc_id={tc_id}")

                        # 累积参数（无论是否为新工具调用）
                        if raw_args:
                            _current_tool_call["args_parts"].append(str(raw_args))

                        # 尝试解析完整的参数
                        if _current_tool_call["args_parts"] and not _current_tool_call["complete"]:
                            full_args_str = "".join(_current_tool_call["args_parts"])
                            if full_args_str and full_args_str.strip():
                                try:
                                    args = json.loads(full_args_str)
                                    # 解析成功，标记为完成并输出
                                    _current_tool_call["complete"] = True

                                    tool_name = _current_tool_call["name"]
                                    if not tool_name:
                                        logger.warning(f"[ToolCall跳过] name为空，累积数据={_current_tool_call}")
                                        continue

                                    logger.info(f"[ToolCall完成] name={tool_name!r}, args={args}")
                                    tool_call_chunk = AIMessageChunk(
                                        content="",
                                        tool_calls=[{
                                            "name": tool_name,
                                            "args": args,
                                            "id": _current_tool_call["tc_id"] or tc_id,
                                            "type": "tool_call"
                                        }],
                                    )
                                    yield ChatGenerationChunk(message=tool_call_chunk)
                                except json.JSONDecodeError:
                                    # 参数还不完整，继续累积
                                    pass

                if delta:
                    yield ChatGenerationChunk(
                        message=AIMessageChunk(content=delta),
                        generation_info={"finish_reason": None},
                    )

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """
        异步流式生成响应

        Args:
            messages: 消息列表
            stop: 停止词列表
            run_manager: 回调管理器

        Yields:
            ChatGenerationChunk: 聊天生成结果块
        """
        import asyncio
        loop = asyncio.get_event_loop()

        # 将同步流式生成器转换为异步
        def sync_generator():
            return list(self._stream(messages, stop, run_manager, **kwargs))

        messages_list = await loop.run_in_executor(None, sync_generator)
        for chunk in messages_list:
            yield chunk

    def with_structured_output(self, schema: Type[BaseModel], **kwargs: Any) -> "StructuredOutputLLM":
        """
        创建支持结构化输出的 LLM 包装器

        Args:
            schema: Pydantic 模型类，定义输出结构
            **kwargs: 其他参数

        Returns:
            StructuredOutputLLM: 支持结构化输出的 LLM 包装器
        """
        return StructuredOutputLLM(self, schema)

    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """
        转换LangChain消息格式为DashScope多模态格式

        统一使用 MultiModalConversation.call() 所需的消息格式，
        content 以列表形式（如 [{"text": "..."}]）表示。

        Args:
            messages: LangChain消息列表

        Returns:
            DashScope多模态格式的消息列表
        """
        converted = []
        for message in messages:
            # 提取消息内容，处理 content 可能是列表的情况
            content = message.content
            if isinstance(content, list):
                # 如果 content 是列表（如 [{'text': '...'}, ...]），合并为字符串
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        text_parts.append(item["text"])
                    elif isinstance(item, str):
                        text_parts.append(item)
                content = "".join(text_parts)

            if isinstance(message, SystemMessage):
                converted.append({"role": "system", "content": [{"text": content}]})
            elif isinstance(message, ToolMessage):
                tool_result = {
                    "role": "tool",
                    "content": content,
                    "tool_call_id": message.tool_call_id,
                }
                converted.append(tool_result)
            elif isinstance(message, AIMessage):
                entry: Dict[str, Any] = {"role": "assistant"}
                entry["content"] = [{"text": content or ""}]
                if message.tool_calls:
                    entry["tool_calls"] = [
                        {
                            "id": tc.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["args"], ensure_ascii=False)
                                if isinstance(tc["args"], dict)
                                else str(tc["args"]),
                            },
                        }
                        for tc in message.tool_calls
                    ]
                converted.append(entry)
            elif isinstance(message, HumanMessage):
                converted.append({"role": "user", "content": [{"text": content}]})
            else:
                converted.append({"role": "user", "content": [{"text": str(content)}]})
        return converted


class TongyiLLMFactory:
    """
    通义千问LLM工厂类

    提供不同场景的LLM实例。
    """

    @staticmethod
    def create_review_llm(**kwargs) -> TongyiLLM:
        """
        创建用于合同审查的LLM实例

        使用较低的温度以获得更确定性的输出。
        """
        config = LLMConfig(
            model=kwargs.get("model", settings.LLM_MODEL_REVIEW),
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 4096),
            top_p=kwargs.get("top_p", 0.9),
            api_key=kwargs.get("api_key"),
        )
        return TongyiLLM(config)

    @staticmethod
    def create_summary_llm(**kwargs) -> TongyiLLM:
        """
        创建用于合同摘要的LLM实例

        使用适中的温度以平衡创造性和准确性。
        """
        config = LLMConfig(
            model=kwargs.get("model", settings.LLM_MODEL_DEFAULT),
            temperature=kwargs.get("temperature", 0.5),
            max_tokens=kwargs.get("max_tokens", 2048),
            top_p=kwargs.get("top_p", 0.9),
            api_key=kwargs.get("api_key"),
        )
        return TongyiLLM(config)

    @staticmethod
    def create_chat_llm(**kwargs) -> TongyiLLM:
        """
        创建用于对话的LLM实例

        使用较高的温度以获得更自然的对话体验。
        """
        config = LLMConfig(
            model=kwargs.get("model", settings.LLM_MODEL_DEFAULT),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2048),
            top_p=kwargs.get("top_p", 0.9),
            api_key=kwargs.get("api_key"),
        )
        return TongyiLLM(config)

    @staticmethod
    def create_streaming_llm(**kwargs) -> TongyiLLM:
        """
        创建用于流式对话的LLM实例

        使用适中的温度以平衡创造性和准确性，支持流式输出。
        """
        config = LLMConfig(
            model=kwargs.get("model", settings.LLM_MODEL_DEFAULT),
            temperature=kwargs.get("temperature", 0.5),
            max_tokens=kwargs.get("max_tokens", 4096),
            top_p=kwargs.get("top_p", 0.9),
            api_key=kwargs.get("api_key"),
            streaming=True,
        )
        return TongyiLLM(config)


class StructuredOutputLLM(RunnableSerializable):
    """
    结构化输出 LLM 包装器

    将 LLM 的输出解析为指定的 Pydantic 模型。
    """

    llm: TongyiLLM
    response_schema: Type[BaseModel]

    def __init__(self, llm: TongyiLLM, response_schema: Type[BaseModel], **kwargs):
        """
        初始化结构化输出包装器

        Args:
            llm: TongyiLLM 实例
            response_schema: Pydantic 模型类
            **kwargs: 其他参数
        """
        super().__init__(llm=llm, response_schema=response_schema, **kwargs)

    def invoke(
        self,
        input: Any,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> BaseModel:
        """
        同步调用 LLM 并解析输出

        Args:
            input: 输入参数（可以是字典或 ChatPromptValue）
            config: 运行配置
            **kwargs: 其他参数

        Returns:
            Pydantic 模型实例
        """
        # 处理不同类型的输入
        if hasattr(input, 'to_messages'):
            # ChatPromptValue 对象
            messages = input.to_messages()
        elif hasattr(input, 'get'):
            # 字典对象
            messages = input.get("messages", [])
            if not messages:
                # 如果没有 messages，构建消息列表
                messages = []
                for key, value in input.items():
                    if isinstance(value, str):
                        messages.append(HumanMessage(content=f"{key}: {value}"))
        else:
            # 其他类型，尝试直接作为消息内容
            messages = [HumanMessage(content=str(input))]

        # 调用 LLM
        response = self.llm._generate(messages)
        content = response.generations[0].message.content

        # 解析 JSON 输出
        return self._parse_output(content)

    def _parse_output(self, content: str) -> BaseModel:
        """
        解析 LLM 输出为 Pydantic 模型

        Args:
            content: LLM 原始输出

        Returns:
            Pydantic 模型实例
        """
        # 尝试提取 JSON 内容
        json_content = self._extract_json(content)

        try:
            # 解析 JSON
            data = json.loads(json_content)
            # 验证并创建模型实例
            return self.response_schema(**data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}, 内容: {json_content[:200]}")
            # 尝试修复常见的 JSON 格式问题
            try:
                fixed_content = self._fix_json(json_content)
                data = json.loads(fixed_content)
                return self.response_schema(**data)
            except Exception as e2:
                logger.error(f"JSON 修复失败: {e2}")
                # 返回空模型实例
                return self._create_empty_model()
        except ValidationError as e:
            logger.error(f"Pydantic 验证失败: {e}, 内容: {json_content[:200]}")
            # 尝试部分匹配
            try:
                data = json.loads(json_content)
                return self._create_partial_model(data)
            except Exception:
                return self._create_empty_model()

    async def ainvoke(
        self,
        input: Any,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> BaseModel:
        """
        异步调用 LLM 并解析输出

        Args:
            input: 输入参数（可以是字典或 ChatPromptValue）
            config: 运行配置
            **kwargs: 其他参数

        Returns:
            Pydantic 模型实例
        """
        import asyncio
        loop = asyncio.get_event_loop()

        def sync_invoke():
            return self.invoke(input, config, **kwargs)

        return await loop.run_in_executor(None, sync_invoke)

    def _extract_json(self, content) -> str:
        """
        从文本中提取 JSON 内容

        Args:
            content: 原始文本（可以是字符串或列表）

        Returns:
            JSON 字符串
        """
        # 处理列表类型（某些模型返回列表格式的内容）
        if isinstance(content, list):
            # 将列表转换为字符串
            content = ''.join(str(item) for item in content)
        elif not isinstance(content, str):
            # 其他类型转换为字符串
            content = str(content)

        content = content.strip()
        
        # 优先处理 Python 字典格式：{'text': '...'}
        if content.startswith("{") and "'" in content and content.count("'") >= 2:
            try:
                # 使用 ast.literal_eval 安全地解析 Python 字典
                import ast
                data = ast.literal_eval(content)
                
                # 如果解析后的数据包含 'text' 键，且值是字符串，可能是嵌套的 JSON
                if isinstance(data, dict) and 'text' in data and isinstance(data['text'], str):
                    nested_content = data['text'].strip()
                    # 递归提取嵌套内容
                    return self._extract_json(nested_content)
                
                # 转换回 JSON 字符串
                return json.dumps(data, ensure_ascii=False)
            except:
                pass

        # 尝试找到 JSON 代码块
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()

        # 尝试找到方括号或花括号包裹的内容
        start_bracket = content.find("[")
        start_brace = content.find("{")

        if start_bracket != -1 and (start_brace == -1 or start_bracket < start_brace):
            # 找到匹配的右方括号
            depth = 0
            for i, char in enumerate(content[start_bracket:], start_bracket):
                if char == "[":
                    depth += 1
                elif char == "]":
                    depth -= 1
                    if depth == 0:
                        return content[start_bracket:i+1]
        elif start_brace != -1:
            # 找到匹配的右花括号
            depth = 0
            for i, char in enumerate(content[start_brace:], start_brace):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return content[start_brace:i+1]

        return content

    def _fix_json(self, content) -> str:
        """
        尝试修复常见的 JSON 格式问题

        Args:
            content: 原始 JSON 字符串（可以是字符串或列表）

        Returns:
            修复后的 JSON 字符串
        """
        # 处理列表类型
        if isinstance(content, list):
            content = ''.join(str(item) for item in content)
        elif not isinstance(content, str):
            content = str(content)

        # 移除 BOM 标记
        content = content.lstrip('\ufeff')
        
        # 移除尾部逗号（在 } 或 ] 之前的逗号）
        content = re.sub(r",(\s*[}\]])", r"\1", content)
        
        # 修复对象内部的尾部逗号
        content = re.sub(r",(\s*})\s*([,}\]])", r"\1\2", content)
        content = re.sub(r",(\s*])\s*([,}\]])", r"\1\2", content)
        
        # 修复单引号（但要小心不要替换字符串内的单引号）
        # 先处理键的单引号
        content = re.sub(r"'([^']+)'\s*:", r'"\1":', content)
        
        # 修复缺少引号的键
        content = re.sub(r"([{,])\s*(\w+)\s*:", r'\1"\2":', content)
        
        # 修复多余的逗号
        content = re.sub(r",\s*}", "}", content)
        content = re.sub(r",\s*]", "]", content)
        
        # 修复缺失的逗号（在两个值之间）
        content = re.sub(r"}\s*{", "},{", content)
        content = re.sub(r"]\s*\[", "],[", content)
        content = re.sub(r"}\s*\[", "},[", content)
        content = re.sub(r"]\s*{", "],{", content)
        
        # 修复字符串中的单引号（简单处理）
        content = content.replace("'", '"')
        
        return content

    def _create_empty_model(self) -> BaseModel:
        """
        创建空模型实例

        Returns:
            空模型实例
        """
        # 获取模型的默认字段
        defaults = {}
        for field_name, field_info in self.response_schema.model_fields.items():
            if hasattr(field_info, 'default') and field_info.default is not None:
                defaults[field_name] = field_info.default
            elif field_info.is_required():
                # 根据类型设置默认值
                if field_info.annotation == str:
                    defaults[field_name] = ""
                elif field_info.annotation == list:
                    defaults[field_name] = []
                elif field_info.annotation == bool:
                    defaults[field_name] = False
                elif field_info.annotation == int:
                    defaults[field_name] = 0
                else:
                    defaults[field_name] = None

        return self.response_schema(**defaults)

    def _create_partial_model(self, data: Dict[str, Any]) -> BaseModel:
        """
        从部分数据创建模型实例

        Args:
            data: 部分数据

        Returns:
            模型实例
        """
        # 填充缺失字段
        for field_name, field_info in self.response_schema.model_fields.items():
            if field_name not in data:
                if hasattr(field_info, 'default') and field_info.default is not None:
                    data[field_name] = field_info.default
                elif field_info.is_required():
                    if field_info.annotation == str:
                        data[field_name] = ""
                    elif field_info.annotation == list:
                        data[field_name] = []
                    elif field_info.annotation == bool:
                        data[field_name] = False
                    elif field_info.annotation == int:
                        data[field_name] = 0
                    else:
                        data[field_name] = None

        return self.response_schema(**data)
