"""
Prompt模板管理模块

定义和管理合同审查相关的Prompt模板。
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass

from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


@dataclass
class ReviewPrompts:
    """审查Prompt模板集合"""

    # 系统Prompt
    SYSTEM_PROMPT: str = """你是一位专业的合同审查专家，精通中国合同法律法规。
你的任务是分析合同条款，识别潜在风险，并提供专业的修改建议。
请确保分析准确、全面，并基于现行法律法规。"""

    # 风险分析Prompt - 优化版（使用 with_structured_output）
    RISK_ANALYSIS_TEMPLATE: str = """请分析以下合同条款，识别潜在的法律风险：

合同类型: {contract_type}
条款编号: {clause_no}

【合同条款原文】
{clause_content}

【相关法律依据】
{legal_basis}

请从以下维度进行分析：
1. 法律风险：是否违反相关法律法规（请结合上述法律依据）
2. 商业风险：是否对一方明显不利
3. 执行风险：条款是否明确可执行

分析时请重点参考上述法律依据，确保分析结果有法可依。

【重要】你必须以 JSON 格式输出结果，不要添加任何 Markdown 格式标记或解释性文字。
输出格式示例：
{{
  "risks": [
    {{
      "clause_no": "第一条",
      "clause_content": "条款内容",
      "risk_level": "HIGH",
      "risk_type": "LEGAL_RISK",
      "risk_description": "风险描述",
      "legal_basis": "法律依据",
      "suggestions": ["建议1", "建议2"],
      "score": 60
    }}
  ],
  "summary": "风险分析总结"
}}
"""

    # 合规检查Prompt - 优化版（使用 with_structured_output）
    COMPLIANCE_CHECK_TEMPLATE: str = """请检查以下合同条款是否符合中国法律法规：

合同类型: {contract_type}
条款编号: {clause_no}

【合同条款原文】
{clause_content}

【相关法律依据】
{legal_basis}

请判断该条款是否合规，如果不合规请说明：
1. 违反的具体法律法规条款（请从上述法律依据中引用）
2. 违规的具体内容
3. 合规化建议（参考上述法律依据给出具体建议）

检查时必须结合上述法律依据，确保判断准确。

【重要】你必须以 JSON 格式输出结果，不要添加任何 Markdown 格式标记或解释性文字。
输出格式示例：
{{
  "results": [
    {{
      "clause_no": "第一条",
      "clause_content": "条款内容",
      "is_compliant": false,
      "violated_laws": ["违反的法律1", "违反的法律2"],
      "violation_details": "违规详情",
      "recommendations": ["建议1", "建议2"],
      "severity": "HIGH",
      "score": 40
    }}
  ],
  "overall_compliant": false
}}
"""

    # 合同摘要Prompt - 优化版（不含 format_instructions）
    CONTRACT_SUMMARY_TEMPLATE: str = """请对以下合同进行整体分析和摘要：

合同内容:
{contract_content}

请提供以下信息：
1. 合同类型识别
2. 合同双方识别
3. 关键条款摘要（付款、交付、违约责任等）
4. 整体风险评估
5. 主要关注点

请输出结构化的合同摘要信息。
"""

    # 条款解释Prompt
    CLAUSE_EXPLANATION_TEMPLATE: str = """请解释以下合同条款的含义和潜在影响：

条款编号: {clause_no}
条款内容:
{clause_content}

请从以下角度解释：
1. 条款的通俗解释
2. 对甲方的意义和影响
3. 对乙方的意义和影响
4. 实际执行中可能遇到的问题
5. 建议的谈判要点

请用通俗易懂的语言解释，避免过多法律术语。
"""

    # 修改建议Prompt
    REVISION_SUGGESTION_TEMPLATE: str = """请为以下有风险的条款提供修改建议：

条款编号: {clause_no}
当前条款内容:
{clause_content}

识别出的问题:
{risk_description}

请提供：
1. 修改后的条款文本（保持原意但降低风险）
2. 修改说明（解释为什么这样修改）
3. 备选方案（如果有多种修改方式）

修改原则：
- 保持合同双方权利义务平衡
- 明确具体，避免模糊表述
- 符合相关法律法规
- 具有可执行性
"""


class PromptTemplateManager:
    """
    Prompt模板管理器

    管理和提供各种场景的Prompt模板。
    """

    def __init__(self):
        self.review_prompts = ReviewPrompts()
        self._templates: Dict[str, PromptTemplate] = {}
        self._chat_templates: Dict[str, ChatPromptTemplate] = {}
        self._init_templates()

    def _init_templates(self):
        """初始化所有模板"""
        # 基础Prompt模板（不含 format_instructions，使用 with_structured_output）
        self._templates["risk_analysis"] = PromptTemplate(
            template=self.review_prompts.RISK_ANALYSIS_TEMPLATE,
            input_variables=["contract_type", "clause_no", "clause_content", "legal_basis"],
        )

        self._templates["compliance_check"] = PromptTemplate(
            template=self.review_prompts.COMPLIANCE_CHECK_TEMPLATE,
            input_variables=["contract_type", "clause_no", "clause_content", "legal_basis"],
        )

        self._templates["contract_summary"] = PromptTemplate(
            template=self.review_prompts.CONTRACT_SUMMARY_TEMPLATE,
            input_variables=["contract_content"],
        )

        self._templates["clause_explanation"] = PromptTemplate(
            template=self.review_prompts.CLAUSE_EXPLANATION_TEMPLATE,
            input_variables=["clause_no", "clause_content"],
        )

        self._templates["revision_suggestion"] = PromptTemplate(
            template=self.review_prompts.REVISION_SUGGESTION_TEMPLATE,
            input_variables=["clause_no", "clause_content", "risk_description"],
        )

        # Chat Prompt模板
        system_message = SystemMessagePromptTemplate.from_template(
            self.review_prompts.SYSTEM_PROMPT
        )

        self._chat_templates["risk_analysis"] = ChatPromptTemplate.from_messages([
            system_message,
            HumanMessagePromptTemplate.from_template(self.review_prompts.RISK_ANALYSIS_TEMPLATE),
        ])

        self._chat_templates["compliance_check"] = ChatPromptTemplate.from_messages([
            system_message,
            HumanMessagePromptTemplate.from_template(self.review_prompts.COMPLIANCE_CHECK_TEMPLATE),
        ])

        self._chat_templates["contract_summary"] = ChatPromptTemplate.from_messages([
            system_message,
            HumanMessagePromptTemplate.from_template(self.review_prompts.CONTRACT_SUMMARY_TEMPLATE),
        ])

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """
        获取Prompt模板

        Args:
            name: 模板名称

        Returns:
            PromptTemplate对象或None
        """
        return self._templates.get(name)

    def get_chat_template(self, name: str) -> Optional[ChatPromptTemplate]:
        """
        获取Chat Prompt模板

        Args:
            name: 模板名称

        Returns:
            ChatPromptTemplate对象或None
        """
        return self._chat_templates.get(name)

    def format_prompt(self, name: str, **kwargs) -> Optional[str]:
        """
        格式化Prompt

        Args:
            name: 模板名称
            **kwargs: 模板变量

        Returns:
            格式化后的Prompt文本
        """
        template = self._templates.get(name)
        if template:
            return template.format(**kwargs)
        return None

    def create_custom_template(
        self,
        name: str,
        template: str,
        input_variables: list,
        is_chat: bool = False
    ) -> ChatPromptTemplate | PromptTemplate:
        """
        创建自定义模板

        Args:
            name: 模板名称
            template: 模板字符串
            input_variables: 输入变量列表
            is_chat: 是否为Chat模板

        Returns:
            创建的模板对象
        """
        if is_chat:
            system_message = SystemMessagePromptTemplate.from_template(
                self.review_prompts.SYSTEM_PROMPT
            )
            chat_template = ChatPromptTemplate.from_messages([
                system_message,
                HumanMessagePromptTemplate.from_template(template),
            ])
            self._chat_templates[name] = chat_template
            return chat_template
        else:
            prompt_template = PromptTemplate(
                template=template,
                input_variables=input_variables,
            )
            self._templates[name] = prompt_template
            return prompt_template


# 全局模板管理器实例
prompt_manager = PromptTemplateManager()


def get_prompt_manager() -> PromptTemplateManager:
    """获取全局Prompt管理器实例"""
    return prompt_manager
