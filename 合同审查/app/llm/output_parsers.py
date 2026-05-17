"""
输出解析器模块

用于解析LLM的输出为结构化数据。
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import ValidationError

from langchain_core.output_parsers import BaseOutputParser

from .models import RiskItem, ComplianceResult, ContractSummary, RiskLevel

logger = logging.getLogger(__name__)


class JSONOutputParser(BaseOutputParser[Dict[str, Any]]):
    """
    JSON输出解析器

    解析LLM输出的JSON字符串。
    """

    def _extract_json(self, text: str) -> str:
        """
        从文本中提取JSON内容

        Args:
            text: 包含JSON的文本

        Returns:
            提取的JSON字符串
        """
        # 找到第一个 '[' 或 '{' 的位置
        start_pos = -1
        for i, char in enumerate(text):
            if char == '[' or char == '{':
                start_pos = i
                break

        if start_pos == -1:
            raise ValueError("未找到JSON起始标记")

        # 根据起始字符确定结束字符
        if text[start_pos] == '[':
            end_char = ']'
        else:
            end_char = '}'

        # 找到匹配的闭合括号
        count = 0
        in_string = False
        escape_next = False
        end_pos = 0

        for i in range(start_pos, len(text)):
            char = text[i]
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            if not in_string:
                if char == text[start_pos]:
                    count += 1
                elif char == end_char:
                    count -= 1
                    if count == 0:
                        end_pos = i + 1
                        break

        if end_pos == 0:
            # JSON不完整，尝试修复
            logger.warning("JSON不完整，尝试修复...")
            return self._fix_incomplete_json(text[start_pos:], text[start_pos] == '[')

        return text[start_pos:end_pos]

    def _fix_incomplete_json(self, text: str, is_array: bool) -> str:
        """
        尝试修复不完整的JSON

        Args:
            text: 不完整的JSON文本
            is_array: 是否是数组

        Returns:
            修复后的JSON字符串
        """
        # 找到最后一个完整的对象
        if is_array:
            # 对于数组，找到最后一个完整的对象
            # 查找最后一个完整的 {...}
            last_complete_end = 0
            brace_count = 0
            bracket_count = 0
            in_string = False
            escape_next = False

            for i, char in enumerate(text):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        # 只有当brace_count回到0且bracket_count也是0时，才是一个完整的对象
                        if brace_count == 0 and bracket_count == 0:
                            last_complete_end = i + 1
                    elif char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1

            if last_complete_end > 0:
                # 找到完整的对象，截断到此处
                fixed = text[:last_complete_end].rstrip()
                # 确保以 ] 结尾
                if not fixed.endswith(']'):
                    fixed = fixed.rstrip(', \n') + ']'
                logger.info(f"修复后的JSON长度: {len(fixed)}")
                return fixed
            else:
                # 没有找到完整对象，返回空数组
                logger.warning("无法修复JSON，返回空数组")
                return "[]"
        else:
            # 对于对象，尝试补全
            # 简单的补全策略：添加缺失的 }
            open_braces = text.count('{') - text.count('}')
            open_brackets = text.count('[') - text.count(']')

            fixed = text
            fixed += ']' * open_brackets
            fixed += '}' * open_braces

            logger.info(f"修复后的JSON: {fixed[:200]}...")
            return fixed

    def parse(self, text: str) -> Dict[str, Any]:
        """
        解析JSON输出

        Args:
            text: LLM输出的文本

        Returns:
            解析后的字典
        """
        if not text or not text.strip():
            logger.error("LLM输出为空")
            raise ValueError("LLM输出为空")

        # 尝试提取JSON内容（处理markdown代码块）
        text = text.strip()

        # 移除markdown代码块标记
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        # 处理 "Extra data" 错误 - 只取第一个有效的JSON对象/数组
        # 尝试找到完整的JSON结构
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            pass

            # 尝试提取第一个完整的JSON对象或数组
            try:
                # 使用通用的JSON提取方法
                first_json = self._extract_json(text)
                return json.loads(first_json)

            except json.JSONDecodeError as e2:
                logger.warning(f"提取后JSON解析失败: {e2}")

                # 最后尝试：使用更宽松的解析
                try:
                    import re
                    # 尝试找到JSON数组
                    array_match = re.search(r'\[.*\]', text, re.DOTALL)
                    if array_match:
                        return json.loads(array_match.group())

                    # 尝试找到JSON对象
                    object_match = re.search(r'\{.*\}', text, re.DOTALL)
                    if object_match:
                        return json.loads(object_match.group())
                except Exception as re_error:
                    logger.error(f"正则提取JSON失败: {re_error}")

            except Exception as extract_error:
                logger.error(f"提取JSON失败: {extract_error}")

            logger.error(f"JSON解析失败: {e}, 文本: {text}...")
            raise ValueError(f"无法解析JSON输出: {e}")

    def get_format_instructions(self) -> str:
        """返回格式说明"""
        return "请确保输出为有效的JSON格式。"


class RiskItemParser(BaseOutputParser[List[RiskItem]]):
    """
    风险项解析器

    将LLM输出解析为RiskItem对象列表。
    """

    def parse(self, text: str) -> List[RiskItem]:
        """
        解析风险项列表

        Args:
            text: LLM输出的JSON文本

        Returns:
            RiskItem对象列表
        """
        json_parser = JSONOutputParser()
        data = json_parser.parse(text)

        # 处理不同的输出格式
        if isinstance(data, list):
            risk_items_data = data
        elif isinstance(data, dict):
            risk_items_data = data.get("risk_items", data.get("risks", []))
        else:
            raise ValueError(f"意外的数据格式: {type(data)}")

        risk_items = []
        for item_data in risk_items_data:
            try:
                # 标准化风险等级
                if "risk_level" in item_data:
                    risk_level = item_data["risk_level"].upper()
                    if risk_level not in ["HIGH", "MEDIUM", "LOW", "NONE"]:
                        risk_level = "MEDIUM"  # 默认中等风险
                    item_data["risk_level"] = risk_level

                risk_item = RiskItem(**item_data)
                risk_items.append(risk_item)
            except ValidationError as e:
                logger.warning(f"风险项解析失败: {e}, 数据: {item_data}")
                continue

        return risk_items

    def get_format_instructions(self) -> str:
        """返回格式说明"""
        return """
请输出JSON格式的风险项列表，格式如下：
[
  {
    "clause_no": "条款编号",
    "clause_content": "条款内容",
    "risk_level": "HIGH/MEDIUM/LOW/NONE",
    "risk_type": "风险类型",
    "risk_description": "风险描述",
    "legal_basis": "法律依据（可选）",
    "suggestions": ["修改建议1", "修改建议2"],
    "score": "对该条款的评价（0到100）分"
  }
]
"""


class ComplianceResultParser(BaseOutputParser[List[ComplianceResult]]):
    """
    合规结果解析器

    将LLM输出解析为ComplianceResult对象列表。
    """

    def parse(self, text: str) -> List[ComplianceResult]:
        """
        解析合规结果列表

        Args:
            text: LLM输出的JSON文本

        Returns:
            ComplianceResult对象列表
        """
        json_parser = JSONOutputParser()
        data = json_parser.parse(text)

        # 处理不同的输出格式
        if isinstance(data, list):
            compliance_data = data
        elif isinstance(data, dict):
            compliance_data = data.get("compliance_results", data.get("results", []))
        else:
            raise ValueError(f"意外的数据格式: {type(data)}")

        compliance_results = []
        for item_data in compliance_data:
            try:
                compliance_result = ComplianceResult(**item_data)
                compliance_results.append(compliance_result)
            except ValidationError as e:
                logger.warning(f"合规结果解析失败: {e}, 数据: {item_data}")
                continue

        return compliance_results

    def get_format_instructions(self) -> str:
        """返回格式说明"""
        return """
请输出JSON格式的合规检查结果列表，格式如下：
[
  {
    "clause_no": "条款编号",
    "clause_content": "条款内容",
    "is_compliant": true/false,
    "violated_laws": ["违反的法律法规"],
    "violation_details": "违规详情",
    "recommendations": ["合规建议1", "合规建议2"],
    "score": "对该条款的评价（0到100）分"
  }
]
"""


class ContractSummaryParser(BaseOutputParser[ContractSummary]):
    """
    合同摘要解析器

    将LLM输出解析为ContractSummary对象。
    """

    def parse(self, text: str) -> ContractSummary:
        """
        解析合同摘要

        Args:
            text: LLM输出的JSON文本

        Returns:
            ContractSummary对象
        """
        json_parser = JSONOutputParser()
        data = json_parser.parse(text)

        # 处理不同的输出格式
        if isinstance(data, dict):
            summary_data = data.get("summary", data)
        else:
            raise ValueError(f"意外的数据格式: {type(data)}")

        try:
            # 标准化风险计数
            if "risk_count" in summary_data:
                risk_count = summary_data["risk_count"]
                # 确保所有风险等级都有计数
                for level in ["HIGH", "MEDIUM", "LOW", "NONE"]:
                    if level not in risk_count:
                        risk_count[level] = 0

            return ContractSummary(**summary_data)
        except ValidationError as e:
            logger.error(f"合同摘要解析失败: {e}, 数据: {summary_data}")
            raise ValueError(f"无法解析合同摘要: {e}")

    def get_format_instructions(self) -> str:
        """返回格式说明"""
        return """
请输出JSON格式的合同摘要，格式如下：
{
  "contract_type": "合同类型",
  "parties": ["甲方", "乙方"],
  "key_terms": ["关键条款1", "关键条款2"],
  "overall_assessment": "整体评估",
  "risk_count": {
    "HIGH": 0,
    "MEDIUM": 0,
    "LOW": 0,
    "NONE": 0
  },
  "main_concerns": ["关注点1", "关注点2"],
  "score": "对该条款的评价（0到100）分"
}
"""


class StructuredOutputParser(BaseOutputParser[Dict[str, Any]]):
    """
    结构化输出解析器

    通用的结构化输出解析器，支持自定义schema。
    """

    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        """
        初始化解析器

        Args:
            schema: 期望的输出schema
        """
        self.schema = schema or {}

    def parse(self, text: str) -> Dict[str, Any]:
        """
        解析结构化输出

        Args:
            text: LLM输出的JSON文本

        Returns:
            解析后的字典
        """
        json_parser = JSONOutputParser()
        data = json_parser.parse(text)

        # 验证schema（简单验证）
        if self.schema:
            for key, expected_type in self.schema.items():
                if key not in data:
                    logger.warning(f"缺少字段: {key}")

        return data

    def get_format_instructions(self) -> str:
        """返回格式说明"""
        if self.schema:
            schema_desc = "\n".join([f'  "{k}": <{v}>' for k, v in self.schema.items()])
            return f"请输出JSON格式，包含以下字段：\n{{{schema_desc}\n}}"
        return "请输出JSON格式。"
