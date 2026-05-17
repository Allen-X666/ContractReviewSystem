"""
本地 Qwen/WebWorld-8B LLM 接口

基于 transformers pipeline 的本地大语言模型封装，使用 Qwen/WebWorld-8B 模型。
"""

import logging
from typing import Optional, List, Dict, Any, AsyncIterator, Iterator, Type
from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    AIMessageChunk,
)
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.runnables import RunnableSerializable
from pydantic import BaseModel

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

from 合同审查.app.core.config import settings

DEFAULT_MODEL_NAME = settings.LOCAL_QWEN_MODEL
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9


@dataclass
class LocalLLMConfig:
    """本地LLM配置类"""
    model: str = DEFAULT_MODEL_NAME
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    top_p: float = DEFAULT_TOP_P
    device: str = "auto"  # "auto", "cuda", "cpu"
    streaming: bool = False


class LocalQwenLLM(BaseChatModel):
    """
    本地 Qwen/WebWorld-8B 大语言模型

    基于 transformers pipeline 的本地模型封装，兼容 LangChain 接口。
    """

    model: str = DEFAULT_MODEL_NAME
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    top_p: float = DEFAULT_TOP_P
    device: str = "auto"
    streaming: bool = False

    def __init__(self, config: Optional[LocalLLMConfig] = None, **kwargs):
        """
        初始化本地 Qwen LLM

        Args:
            config: LLM配置对象
            **kwargs: 其他参数
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "使用本地模型需要安装 transformers: "
                "pip install transformers torch"
            )

        config = config or LocalLLMConfig()

        super().__init__(
            model=config.model or kwargs.get("model", DEFAULT_MODEL_NAME),
            temperature=config.temperature or kwargs.get("temperature", DEFAULT_TEMPERATURE),
            max_tokens=config.max_tokens or kwargs.get("max_tokens", DEFAULT_MAX_TOKENS),
            top_p=config.top_p or kwargs.get("top_p", DEFAULT_TOP_P),
            device=config.device or kwargs.get("device", "auto"),
            streaming=config.streaming or kwargs.get("streaming", False),
        )

        # 初始化 pipeline（使用私有属性，不纳入 Pydantic 管理）
        object.__setattr__(self, "_pipe", None)
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """初始化 HuggingFace pipeline"""
        try:
            logger.info(f"正在加载本地模型: {self.model}")
            pipe = pipeline(
                "text-generation",
                model=self.model,
                device_map=self.device if self.device != "auto" else None,
                torch_dtype="auto",
                trust_remote_code=True
            )
            object.__setattr__(self, "_pipe", pipe)
            logger.info(f"模型加载完成: {self.model}")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise

    @property
    def _llm_type(self) -> str:
        """返回LLM类型"""
        return "local_qwen"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """返回标识参数"""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """
        转换 LangChain 消息格式为 transformers 格式

        Args:
            messages: LangChain 消息列表

        Returns:
            transformers 格式的消息列表
        """
        converted = []
        for message in messages:
            if isinstance(message, SystemMessage):
                converted.append({"role": "system", "content": message.content})
            elif isinstance(message, HumanMessage):
                converted.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                converted.append({"role": "assistant", "content": message.content})
            else:
                # 默认作为用户消息
                converted.append({"role": "user", "content": str(message.content)})
        return converted

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        同步生成响应

        Args:
            messages: 消息列表
            stop: 停止词列表
            run_manager: 回调管理器

        Returns:
            ChatResult: 聊天生成结果
        """
        # 转换消息格式
        chat_messages = self._convert_messages(messages)

        # 使用 pipeline 生成响应
        pipe = object.__getattribute__(self, "_pipe")
        response = pipe(
            chat_messages,
            max_new_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            top_p=kwargs.get("top_p", self.top_p),
            do_sample=True,
            stop_sequence=stop
        )

        # 提取生成的文本
        if isinstance(response, list) and len(response) > 0:
            if isinstance(response[0], dict) and "generated_text" in response[0]:
                response_text = response[0]["generated_text"]
            else:
                response_text = str(response[0])
        elif isinstance(response, dict) and "generated_text" in response:
            response_text = response["generated_text"]
        else:
            response_text = str(response)

        # 创建 ChatResult
        message = AIMessage(content=response_text)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

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
        # 转换消息格式
        chat_messages = self._convert_messages(messages)

        # 使用 pipeline 流式生成
        pipe = object.__getattribute__(self, "_pipe")
        streamer = pipe(
            chat_messages,
            max_new_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            top_p=kwargs.get("top_p", self.top_p),
            do_sample=True,
            stop_sequence=stop,
            stream=True
        )

        for chunk in streamer:
            if isinstance(chunk, dict) and "generated_text" in chunk:
                text = chunk["generated_text"]
            else:
                text = str(chunk)

            yield ChatGenerationChunk(
                message=AIMessageChunk(content=text),
                generation_info={"finish_reason": None}
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

        chunks = await loop.run_in_executor(None, sync_generator)
        for chunk in chunks:
            yield chunk

    def with_structured_output(self, schema: Type[BaseModel], **kwargs: Any) -> "LocalStructuredOutputLLM":
        """
        创建支持结构化输出的 LLM 包装器

        Args:
            schema: Pydantic 模型类，定义输出结构
            **kwargs: 其他参数

        Returns:
            LocalStructuredOutputLLM: 支持结构化输出的 LLM 包装器
        """
        return LocalStructuredOutputLLM(self, schema)


class LocalStructuredOutputLLM(RunnableSerializable):
    """
    结构化输出 LLM 包装器

    将 LLM 的输出解析为指定的 Pydantic 模型。
    """

    llm: LocalQwenLLM
    response_schema: Type[BaseModel]

    def __init__(self, llm: LocalQwenLLM, response_schema: Type[BaseModel], **kwargs):
        """
        初始化结构化输出包装器

        Args:
            llm: LocalQwenLLM 实例
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
        import json
        try:
            # 尝试直接解析
            data = json.loads(content)
            return self.response_schema(**data)
        except json.JSONDecodeError:
            # 尝试从文本中提取 JSON
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return self.response_schema(**data)
            else:
                raise ValueError(f"无法解析输出为 JSON: {content}")


class LocalQwenLLMFactory:
    """
    本地 Qwen/WebWorld-8B LLM 工厂

    提供不同场景下的 LLM 实例创建方法。
    """

    @staticmethod
    def create_review_llm(**kwargs) -> LocalQwenLLM:
        """
        创建用于合同审查的LLM实例

        使用较低的温度以获得更稳定的输出。
        """
        config = LocalLLMConfig(
            model=kwargs.get("model", DEFAULT_MODEL_NAME),
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 4096),
            top_p=kwargs.get("top_p", 0.9),
            device=kwargs.get("device", "auto"),
        )
        return LocalQwenLLM(config)

    @staticmethod
    def create_summary_llm(**kwargs) -> LocalQwenLLM:
        """
        创建用于合同摘要的LLM实例

        使用适中的温度以平衡创造性和准确性。
        """
        config = LocalLLMConfig(
            model=kwargs.get("model", DEFAULT_MODEL_NAME),
            temperature=kwargs.get("temperature", 0.5),
            max_tokens=kwargs.get("max_tokens", 2048),
            top_p=kwargs.get("top_p", 0.9),
            device=kwargs.get("device", "auto"),
        )
        return LocalQwenLLM(config)

    @staticmethod
    def create_chat_llm(**kwargs) -> LocalQwenLLM:
        """
        创建用于对话的LLM实例

        使用较高的温度以获得更自然的对话体验。
        """
        config = LocalLLMConfig(
            model=kwargs.get("model", DEFAULT_MODEL_NAME),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2048),
            top_p=kwargs.get("top_p", 0.9),
            device=kwargs.get("device", "auto"),
        )
        return LocalQwenLLM(config)

    @staticmethod
    def create_streaming_llm(**kwargs) -> LocalQwenLLM:
        """
        创建用于流式对话的LLM实例

        使用适中的温度以平衡创造性和准确性，支持流式输出。
        """
        config = LocalLLMConfig(
            model=kwargs.get("model", DEFAULT_MODEL_NAME),
            temperature=kwargs.get("temperature", 0.5),
            max_tokens=kwargs.get("max_tokens", 4096),
            top_p=kwargs.get("top_p", 0.9),
            device=kwargs.get("device", "auto"),
            streaming=True,
        )
        return LocalQwenLLM(config)
