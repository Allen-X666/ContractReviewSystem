"""
Qwen LLM接口

基于HuggingFace transformers pipeline的Qwen多模态大语言模型封装，
兼容LangChain BaseChatModel接口。
支持 image-text-to-text 任务，可处理文本和图像输入。
"""

import json
import logging
import threading
import uuid
from typing import Optional, List, Dict, Any, AsyncIterator, Iterator, Sequence, Type, Callable, Union

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
from pydantic import BaseModel, Field

from 合同审查.app.core.config import settings

logger = logging.getLogger(__name__)

_qwen_pipe_cache: Dict[str, Any] = {}


def _get_qwen_pipeline(model_name: str, hf_token: Optional[str] = None, task: str = "image-text-to-text"):
    """获取或创建 Qwen transformers pipeline 实例（带缓存）

    Args:
        model_name: HuggingFace 模型名称
        hf_token: HuggingFace 访问令牌
        task: pipeline 任务类型

    Returns:
        transformers Pipeline 实例
    """
    cache_key = f"{task}:{model_name}"
    if cache_key not in _qwen_pipe_cache:
        from transformers import pipeline as hf_pipeline
        import torch

        kwargs: Dict[str, Any] = {
            "task": task,
            "model": model_name,
            "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
            "device_map": "auto",
            "trust_remote_code": True,
        }
        if hf_token:
            kwargs["token"] = hf_token

        logger.info(f"正在加载 Qwen 模型: {model_name}, 任务: {task}")
        _qwen_pipe_cache[cache_key] = hf_pipeline(**kwargs)
        logger.info(f"Qwen 模型加载完成: {model_name}")

    return _qwen_pipe_cache[cache_key]


class QwenLLM(BaseChatModel):
    """
    Qwen 多模态大语言模型

    基于 HuggingFace transformers pipeline 的 Qwen 模型封装，
    兼容 LangChain BaseChatModel 接口。
    支持 image-text-to-text 任务，可处理文本和图像输入。
    """

    model: str = settings.QWEN_MODEL
    pipeline_task: str = settings.QWEN_PIPELINE_TASK
    temperature: float = 0.7
    max_tokens: Optional[int] = 2048
    top_p: float = 0.9
    hf_token: Optional[str] = None
    streaming: bool = False
    timeout: int = 120
    max_retries: int = 3
    bound_tools: List[Dict[str, Any]] = Field(default_factory=list, exclude=True)
    tool_choice: Optional[Any] = Field(default=None, exclude=True)

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        """
        初始化 Qwen LLM

        Args:
            config: 配置字典，支持 model, pipeline_task, temperature, max_tokens, top_p, hf_token 等
            **kwargs: 其他参数
        """
        config = config or {}
        hf_token = (
            config.get("hf_token")
            or kwargs.get("hf_token")
            or settings.HF_TOKEN
        )

        super().__init__(
            model=config.get("model") or kwargs.get("model", settings.QWEN_MODEL),
            pipeline_task=config.get("pipeline_task") or kwargs.get("pipeline_task", settings.QWEN_PIPELINE_TASK),
            temperature=config.get("temperature") or kwargs.get("temperature", 0.7),
            max_tokens=config.get("max_tokens") or kwargs.get("max_tokens", 2048),
            top_p=config.get("top_p") or kwargs.get("top_p", 0.9),
            hf_token=hf_token,
            streaming=config.get("streaming") or kwargs.get("streaming", False),
            timeout=config.get("timeout") or kwargs.get("timeout", 120),
            max_retries=config.get("max_retries") or kwargs.get("max_retries", 3),
        )

        self._pipe = _get_qwen_pipeline(self.model, self.hf_token, self.pipeline_task)

    def bind_tools(
        self,
        tools: Sequence[Union[Dict[str, Any], Type, Callable, Any]],
        *,
        tool_choice: Optional[Union[str, bool]] = None,
        **kwargs: Any,
    ) -> Runnable:
        """绑定工具到 LLM

        Args:
            tools: 工具列表
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
        return "qwen"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "pipeline_task": self.pipeline_task,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """将 LangChain 消息格式转换为 Qwen pipeline 消息格式

        支持多模态内容格式，包括文本和图像。

        Args:
            messages: LangChain 消息列表

        Returns:
            Qwen pipeline 格式的消息列表
        """
        converted = []
        for message in messages:
            if isinstance(message, SystemMessage):
                converted.append({"role": "system", "content": message.content})
            elif isinstance(message, ToolMessage):
                converted.append({"role": "tool", "content": message.content})
            elif isinstance(message, AIMessage):
                entry: Dict[str, Any] = {"role": "assistant", "content": message.content or ""}
                if message.tool_calls:
                    entry["tool_calls"] = [
                        {
                            "id": tc.get("id", f"call_{uuid.uuid4().hex[:8]}"),
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
                content = message.content
                if isinstance(content, str):
                    converted.append({"role": "user", "content": content})
                elif isinstance(content, list):
                    multimodal_content = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "image":
                                multimodal_content.append({
                                    "type": "image",
                                    "url": item.get("url", item.get("image_url", "")),
                                })
                            elif item.get("type") == "text":
                                multimodal_content.append({
                                    "type": "text",
                                    "text": item.get("text", ""),
                                })
                            else:
                                multimodal_content.append(item)
                        else:
                            multimodal_content.append({"type": "text", "text": str(item)})
                    converted.append({"role": "user", "content": multimodal_content})
                else:
                    converted.append({"role": "user", "content": str(content)})
            else:
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
        生成响应（同步）

        Args:
            messages: 消息列表
            stop: 停止词列表
            run_manager: 回调管理器

        Returns:
            ChatResult: 聊天结果
        """
        pipe_messages = self._convert_messages(messages)

        for idx, msg in enumerate(messages):
            logger.info(f"【LLM输入】message[{idx}] type={type(msg).__name__}, content={msg.content}")

        pipe_kwargs: Dict[str, Any] = {
            "max_new_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "do_sample": self.temperature > 0,
        }
        if stop:
            pipe_kwargs["stop_strings"] = stop

        response = self._pipe(text=pipe_messages, **pipe_kwargs)

        generated = response[0]["generated_text"]
        if isinstance(generated, list):
            content = generated[-1].get("content", "")
        else:
            content = str(generated)

        logger.info(f"【LLM输出】content={content}")

        generation = ChatGeneration(
            message=AIMessage(content=content),
            generation_info={"finish_reason": "stop"},
        )
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
        from transformers import TextIteratorStreamer

        pipe_messages = self._convert_messages(messages)

        pipe_kwargs: Dict[str, Any] = {
            "max_new_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "do_sample": self.temperature > 0,
        }

        streamer = TextIteratorStreamer(
            self._pipe.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )
        pipe_kwargs["streamer"] = streamer

        thread = threading.Thread(
            target=self._pipe,
            kwargs={"text": pipe_messages, **pipe_kwargs},
        )
        thread.start()

        for text in streamer:
            if text:
                yield ChatGenerationChunk(
                    message=AIMessageChunk(content=text),
                    generation_info={"finish_reason": None},
                )

        thread.join()

        yield ChatGenerationChunk(
            message=AIMessageChunk(content=""),
            generation_info={"finish_reason": "stop"},
        )

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        异步生成响应

        Args:
            messages: 消息列表
            stop: 停止词列表
            run_manager: 回调管理器

        Returns:
            ChatResult: 聊天结果
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._generate(messages, stop, run_manager, **kwargs)
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

        def sync_collect():
            return list(self._stream(messages, stop, run_manager, **kwargs))

        chunks = await loop.run_in_executor(None, sync_collect)
        for chunk in chunks:
            yield chunk

    def with_structured_output(self, schema: Type[BaseModel], **kwargs: Any) -> "StructuredOutputLLM":
        """
        创建支持结构化输出的 LLM 包装器

        Args:
            schema: Pydantic 模型类，定义输出结构

        Returns:
            StructuredOutputLLM: 支持结构化输出的 LLM 包装器
        """
        return StructuredOutputLLM(self, schema)


class QwenLLMFactory:
    """
    Qwen LLM工厂类

    提供不同场景的LLM实例。
    """

    @staticmethod
    def create_review_llm(**kwargs) -> QwenLLM:
        """
        创建用于合同审查的LLM实例

        使用较低的温度以获得更确定性的输出。
        """
        return QwenLLM({
            "model": kwargs.get("model", settings.QWEN_MODEL),
            "pipeline_task": kwargs.get("pipeline_task", settings.QWEN_PIPELINE_TASK),
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "top_p": kwargs.get("top_p", 0.9),
            "hf_token": kwargs.get("hf_token"),
        })

    @staticmethod
    def create_summary_llm(**kwargs) -> QwenLLM:
        """
        创建用于合同摘要的LLM实例

        使用适中的温度以平衡创造性和准确性。
        """
        return QwenLLM({
            "model": kwargs.get("model", settings.QWEN_MODEL),
            "pipeline_task": kwargs.get("pipeline_task", settings.QWEN_PIPELINE_TASK),
            "temperature": kwargs.get("temperature", 0.5),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "top_p": kwargs.get("top_p", 0.9),
            "hf_token": kwargs.get("hf_token"),
        })

    @staticmethod
    def create_chat_llm(**kwargs) -> QwenLLM:
        """
        创建用于对话的LLM实例

        使用较高的温度以获得更自然的对话体验。
        """
        return QwenLLM({
            "model": kwargs.get("model", settings.QWEN_MODEL),
            "pipeline_task": kwargs.get("pipeline_task", settings.QWEN_PIPELINE_TASK),
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "top_p": kwargs.get("top_p", 0.9),
            "hf_token": kwargs.get("hf_token"),
        })

    @staticmethod
    def create_streaming_llm(**kwargs) -> QwenLLM:
        """
        创建用于流式对话的LLM实例

        使用适中的温度以平衡创造性和准确性，支持流式输出。
        """
        return QwenLLM({
            "model": kwargs.get("model", settings.QWEN_MODEL),
            "pipeline_task": kwargs.get("pipeline_task", settings.QWEN_PIPELINE_TASK),
            "temperature": kwargs.get("temperature", 0.5),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "top_p": kwargs.get("top_p", 0.9),
            "hf_token": kwargs.get("hf_token"),
            "streaming": True,
        })


class StructuredOutputLLM(RunnableSerializable):
    """
    结构化输出 LLM 包装器

    将 LLM 的输出解析为指定的 Pydantic 模型。
    """

    llm: BaseChatModel
    response_schema: Type[BaseModel]

    def __init__(self, llm: BaseChatModel, response_schema: Type[BaseModel], **kwargs):
        super().__init__(llm=llm, response_schema=response_schema, **kwargs)

    def invoke(
        self,
        input: Any,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> BaseModel:
        """
        同步调用 LLM 并解析输出
        """
        if hasattr(input, "to_messages"):
            messages = input.to_messages()
        elif hasattr(input, "get"):
            messages = input.get("messages", [])
            if not messages:
                messages = []
                for key, value in input.items():
                    if isinstance(value, str):
                        messages.append(HumanMessage(content=f"{key}: {value}"))
        else:
            messages = [HumanMessage(content=str(input))]

        response = self.llm._generate(messages)
        content = response.generations[0].message.content
        return self._parse_output(content)

    async def ainvoke(
        self,
        input: Any,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> BaseModel:
        """
        异步调用 LLM 并解析输出
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.invoke(input, config, **kwargs))

    def _parse_output(self, content: str) -> BaseModel:
        """解析 LLM 输出为 Pydantic 模型"""
        json_content = self._extract_json(content)
        try:
            data = json.loads(json_content)
            return self.response_schema(**data)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"JSON 解析失败: {e}, 内容: {json_content[:200]}")
            try:
                fixed = self._fix_json(json_content)
                data = json.loads(fixed)
                return self.response_schema(**data)
            except Exception:
                return self._create_empty_model()

    @staticmethod
    def _extract_json(content: str) -> str:
        """从 LLM 输出中提取 JSON 字符串"""
        import re
        json_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        match = re.search(json_pattern, content)
        if match:
            return match.group(1).strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            return content[start:end]
        start = content.find("[")
        end = content.rfind("]") + 1
        if start != -1 and end > start:
            return content[start:end]
        return content.strip()

    @staticmethod
    def _fix_json(json_str: str) -> str:
        """尝试修复常见的 JSON 格式问题"""
        import re
        json_str = re.sub(r",\s*([\]}])", r"\1", json_str)
        json_str = json_str.replace("'", '"')
        json_str = re.sub(r"//.*$", "", json_str, flags=re.MULTILINE)
        return json_str

    def _create_empty_model(self) -> BaseModel:
        """创建空模型实例"""
        defaults = {}
        for field_name, field_info in self.response_schema.model_fields.items():
            if hasattr(field_info, "default") and field_info.default is not None:
                defaults[field_name] = field_info.default
            elif field_info.is_required():
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
        """从部分数据创建模型实例"""
        for field_name, field_info in self.response_schema.model_fields.items():
            if field_name not in data:
                if hasattr(field_info, "default") and field_info.default is not None:
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
