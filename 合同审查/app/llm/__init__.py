"""
LLM模块 - 基于LangChain的合同审查语言模型接口

提供：
- 基础LLM调用（支持通义千问、DeepSeek 和本地 Qwen3.5-9B）
- 合同审查专用链
- Prompt模板管理
- 输出解析器
- 智能分析功能
- 统一LLM工厂（根据配置自动选择后端）
"""

from .models import (
    RiskItem,
    ComplianceResult,
    ContractSummary,
    ReviewResult,
    RiskLevel,
    RiskAnalysisResponse,
    ComplianceCheckResponse,
)
from .tongyi_llm import TongyiLLM, LLMConfig, TongyiLLMFactory
from .local_qwen_llm import LocalQwenLLM, LocalLLMConfig, LocalQwenLLMFactory
from .llm_factory import LLMFactory
from .prompts import PromptTemplateManager, ReviewPrompts
from .output_parsers import (
    RiskItemParser,
    ComplianceResultParser,
    ContractSummaryParser,
)

from .review_chains import (
    StructuredReviewChain,
    RiskAnalysisChain,
    ComplianceCheckChain,
    ContractSummaryChain,
    ClauseExplanationChain,
    RevisionSuggestionChain,
    CompleteReviewChain,
)

__all__ = [
    # LLM
    "TongyiLLM",
    "LLMConfig",
    "TongyiLLMFactory",
    "LocalQwenLLM",
    "LocalLLMConfig",
    "LocalQwenLLMFactory",
    "LLMFactory",
    # Chains
    "StructuredReviewChain",
    "RiskAnalysisChain",
    "ComplianceCheckChain",
    "ContractSummaryChain",
    "ClauseExplanationChain",
    "RevisionSuggestionChain",
    "CompleteReviewChain",
    # Prompts
    "PromptTemplateManager",
    "ReviewPrompts",
    # Parsers
    "RiskItemParser",
    "ComplianceResultParser",
    "ContractSummaryParser",
    # Models
    "RiskItem",
    "ComplianceResult",
    "ContractSummary",
    "ReviewResult",
    "RiskLevel",
    "RiskAnalysisResponse",
    "ComplianceCheckResponse",
]