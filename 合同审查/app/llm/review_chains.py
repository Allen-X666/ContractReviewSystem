"""
合同审查专用链模块 - 优化版

使用 with_structured_output 实现结构化输出。
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, AsyncIterator, Type
from langchain_core.runnables import RunnableSequence, RunnableSerializable
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel

from .tongyi_llm import TongyiLLM, LLMConfig
from .llm_factory import LLMFactory
from .prompts import PromptTemplateManager, get_prompt_manager
from .models import (
    RiskItem,
    ComplianceResult,
    ContractSummary,
    RiskAnalysisResponse,
    ComplianceCheckResponse,
)

logger = logging.getLogger(__name__)


class StructuredReviewChain:
    """
    结构化审查链基类

    使用 with_structured_output 实现类型安全的结构化输出。
    """

    def __init__(
        self,
        llm: Optional[TongyiLLM] = None,
        prompt_manager: Optional[PromptTemplateManager] = None,
    ):
        self.llm = llm or LLMFactory.create_review_llm()
        self.prompt_manager = prompt_manager or get_prompt_manager()

    def _create_structured_chain(
        self,
        prompt_template_name: str,
        output_schema: Type[BaseModel],
    ) -> RunnableSerializable:
        """
        创建结构化输出链

        Args:
            prompt_template_name: 提示模板名称
            output_schema: Pydantic 模型类

        Returns:
            配置好的链
        """
        # 获取提示模板
        prompt = self.prompt_manager.get_chat_template(prompt_template_name)

        # 创建支持结构化输出的 LLM
        structured_llm = self.llm.with_structured_output(output_schema)

        # 构建链：prompt | structured_llm
        chain = prompt | structured_llm

        return chain

    async def arun_structured(
        self,
        prompt_template_name: str,
        output_schema: Type[BaseModel],
        **kwargs,
    ) -> BaseModel:
        """
        异步运行结构化链

        Args:
            prompt_template_name: 提示模板名称
            output_schema: 输出模型类
            **kwargs: 输入参数

        Returns:
            Pydantic 模型实例
        """
        chain = self._create_structured_chain(prompt_template_name, output_schema)
        result = await chain.ainvoke(kwargs)
        return result


class RiskAnalysisChain(StructuredReviewChain):
    """
    风险分析链 - 优化版

    使用 with_structured_output 输出 RiskAnalysisResponse。
    """

    async def analyze_clause(
        self,
        clause_no: str,
        clause_content: str,
        contract_type: str = "一般合同",
        legal_basis: str = "",
    ) -> RiskAnalysisResponse:
        """
        分析单个条款的风险

        Args:
            clause_no: 条款编号
            clause_content: 条款内容
            contract_type: 合同类型
            legal_basis: 法律依据

        Returns:
            RiskAnalysisResponse 对象
        """
        logger.info(f"开始分析条款 {clause_no} 风险...")

        result = await self.arun_structured(
            prompt_template_name="risk_analysis",
            output_schema=RiskAnalysisResponse,
            contract_type=contract_type,
            clause_no=clause_no,
            clause_content=clause_content,
            legal_basis=legal_basis or "《中华人民共和国民法典》合同编及相关司法解释",
        )

        logger.info(f"条款 {clause_no} 风险分析完成，发现 {len(result.risks)} 个风险")
        return result

    async def analyze_risks(
        self,
        clauses: List[Dict[str, str]],
        contract_type: str = "一般合同",
        legal_basis: str = "",
        max_concurrent: int = 5,
    ) -> List[RiskItem]:
        """
        并发分析多个条款的风险

        Args:
            clauses: 条款列表
            contract_type: 合同类型
            legal_basis: 默认法律依据
            max_concurrent: 最大并发数

        Returns:
            所有识别的风险项列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        all_risks: List[RiskItem] = []

        async def _analyze_single(clause: Dict[str, str]) -> List[RiskItem]:
            async with semaphore:
                try:
                    response = await self.analyze_clause(
                        clause_no=clause.get("clause_no", "unknown"),
                        clause_content=clause["clause_content"],
                        contract_type=contract_type,
                        legal_basis=clause.get("legal_basis", legal_basis),
                    )
                    return response.risks
                except Exception as e:
                    logger.error(f"分析条款失败: {e}")
                    return []

        # 并发执行所有分析任务
        tasks = [_analyze_single(clause) for clause in clauses]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集所有风险项
        for result in results:
            if isinstance(result, list):
                all_risks.extend(result)

        logger.info(f"风险分析完成，共 {len(all_risks)} 个风险项")
        return all_risks

    async def analyze_single_clause(
        self,
        clause_no: str,
        clause_content: str,
        contract_type: str = "一般合同",
        legal_basis: str = "",
    ) -> List[RiskItem]:
        """
        分析单个条款的风险

        Args:
            clause_no: 条款编号
            clause_content: 条款内容
            contract_type: 合同类型
            legal_basis: 法律依据

        Returns:
            风险项列表
        """
        response = await self.analyze_clause(
            clause_no=clause_no,
            clause_content=clause_content,
            contract_type=contract_type,
            legal_basis=legal_basis,
        )
        return response.risks


class ComplianceCheckChain(StructuredReviewChain):
    """
    合规检查链 - 优化版

    使用 with_structured_output 输出 ComplianceCheckResponse。
    """

    async def check_single(
        self,
        clause_no: str,
        clause_content: str,
        contract_type: str = "一般合同",
        legal_basis: str = "",
    ) -> ComplianceCheckResponse:
        """
        检查单个条款的合规性

        Args:
            clause_no: 条款编号
            clause_content: 条款内容
            contract_type: 合同类型
            legal_basis: 法律依据

        Returns:
            ComplianceCheckResponse 对象
        """
        logger.info(f"开始检查条款 {clause_no} 合规性...")

        result = await self.arun_structured(
            prompt_template_name="compliance_check",
            output_schema=ComplianceCheckResponse,
            contract_type=contract_type,
            clause_no=clause_no,
            clause_content=clause_content,
            legal_basis=legal_basis or "《中华人民共和国民法典》合同编及相关司法解释",
        )

        logger.info(f"条款 {clause_no} 合规检查完成")
        return result

    async def check_compliance(
        self,
        clauses: List[Dict[str, str]],
        legal_basis: Optional[str] = None,
        contract_type: str = "一般合同",
        max_concurrent: int = 5,
    ) -> List[ComplianceResult]:
        """
        并发检查多个条款的合规性

        Args:
            clauses: 条款列表
            legal_basis: 默认法律依据
            contract_type: 合同类型
            max_concurrent: 最大并发数

        Returns:
            合规检查结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        all_results: List[ComplianceResult] = []

        async def _check_single(clause: Dict[str, str]) -> List[ComplianceResult]:
            async with semaphore:
                try:
                    response = await self.check_single(
                        clause_no=clause.get("clause_no", "unknown"),
                        clause_content=clause["clause_content"],
                        contract_type=contract_type,
                        legal_basis=clause.get("legal_basis", legal_basis),
                    )
                    return response.results
                except Exception as e:
                    logger.error(f"检查条款合规性失败: {e}")
                    return []

        # 并发执行所有检查任务
        tasks = [_check_single(clause) for clause in clauses]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集所有结果
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)

        logger.info(f"合规检查完成，共 {len(all_results)} 个结果")
        return all_results


class ContractSummaryChain:
    """
    合同摘要链 - 优化版

    使用 with_structured_output 输出 ContractSummary。
    """

    def __init__(
        self,
        llm: Optional[TongyiLLM] = None,
        prompt_manager: Optional[PromptTemplateManager] = None,
    ):
        self.llm = llm or LLMFactory.create_summary_llm()
        self.prompt_manager = prompt_manager or get_prompt_manager()

    def _create_chain(self) -> RunnableSerializable:
        """创建结构化输出链"""
        prompt = self.prompt_manager.get_chat_template("contract_summary")
        structured_llm = self.llm.with_structured_output(ContractSummary)
        chain = prompt | structured_llm
        return chain

    async def generate_summary(
        self,
        contract_content: str,
        risk_items: Optional[List[RiskItem]] = None,
    ) -> ContractSummary:
        """
        生成合同摘要

        Args:
            contract_content: 合同全文内容
            risk_items: 已识别的风险项（可选）

        Returns:
            ContractSummary 对象
        """
        logger.info("开始生成合同摘要...")

        # 如果提供了风险项，添加到上下文中
        context = contract_content
        if risk_items:
            risk_summary = "\n\n已识别的风险项:\n"
            for risk in risk_items:
                risk_summary += f"- {risk.clause_no}: {risk.risk_description} ({risk.risk_level.value})\n"
            context += risk_summary

        chain = self._create_chain()
        result = await chain.ainvoke({"contract_content": context})

        logger.info("合同摘要生成完成")
        return result


class ClauseExplanationChain:
    """
    条款解释链

    解释合同条款的含义和影响（非结构化输出）。
    """

    def __init__(
        self,
        llm: Optional[TongyiLLM] = None,
        prompt_manager: Optional[PromptTemplateManager] = None,
    ):
        self.llm = llm or LLMFactory.create_review_llm()
        self.prompt_manager = prompt_manager or get_prompt_manager()

    def _create_chain(self) -> RunnableSerializable:
        """构建条款解释链"""
        prompt = self.prompt_manager.get_template("clause_explanation")
        chain = prompt | self.llm | StrOutputParser()
        return chain

    async def explain_clause(
        self,
        clause_no: str,
        clause_content: str,
    ) -> str:
        """
        解释条款

        Args:
            clause_no: 条款编号
            clause_content: 条款内容

        Returns:
            条款解释文本
        """
        chain = self._create_chain()
        return await chain.ainvoke({
            "clause_no": clause_no,
            "clause_content": clause_content,
        })


class RevisionSuggestionChain:
    """
    修改建议链

    为问题条款提供修改建议（非结构化输出）。
    """

    def __init__(
        self,
        llm: Optional[TongyiLLM] = None,
        prompt_manager: Optional[PromptTemplateManager] = None,
    ):
        self.llm = llm or LLMFactory.create_review_llm()
        self.prompt_manager = prompt_manager or get_prompt_manager()

    def _create_chain(self) -> RunnableSerializable:
        """构建修改建议链"""
        prompt = self.prompt_manager.get_template("revision_suggestion")
        chain = prompt | self.llm | StrOutputParser()
        return chain

    async def suggest_revision(
        self,
        clause_no: str,
        clause_content: str,
        risk_description: str,
    ) -> str:
        """
        提供修改建议

        Args:
            clause_no: 条款编号
            clause_content: 条款内容
            risk_description: 风险描述

        Returns:
            修改建议文本
        """
        chain = self._create_chain()
        return await chain.ainvoke({
            "clause_no": clause_no,
            "clause_content": clause_content,
            "risk_description": risk_description,
        })


class CompleteReviewChain:
    """
    完整审查链

    组合多个链完成完整的合同审查流程。
    """

    def __init__(
        self,
        risk_chain: Optional[RiskAnalysisChain] = None,
        compliance_chain: Optional[ComplianceCheckChain] = None,
        summary_chain: Optional[ContractSummaryChain] = None,
    ):
        """
        初始化完整审查链

        Args:
            risk_chain: 风险分析链
            compliance_chain: 合规检查链
            summary_chain: 合同摘要链
        """
        self.risk_chain = risk_chain or RiskAnalysisChain()
        self.compliance_chain = compliance_chain or ComplianceCheckChain()
        self.summary_chain = summary_chain or ContractSummaryChain()

    async def review_contract(
        self,
        contract_content: str,
        clauses: List[Dict[str, str]],
        contract_type: str = "一般合同",
        check_risk: bool = True,
        check_compliance: bool = True,
        generate_summary: bool = True,
        max_concurrent: int = 5,
    ) -> Dict[str, Any]:
        """
        执行完整合同审查

        风险分析与合规检查并行执行，缩短整体耗时。

        Args:
            contract_content: 合同全文
            clauses: 条款列表
            contract_type: 合同类型
            check_risk: 是否检查风险
            check_compliance: 是否检查合规性
            generate_summary: 是否生成摘要
            max_concurrent: 每类分析的最大并发数

        Returns:
            审查结果字典
        """
        result: Dict[str, Any] = {
            "risk_items": [],
            "compliance_results": [],
            "summary": None,
        }

        parallel_tasks = {}

        if check_risk:
            parallel_tasks["risk"] = self.risk_chain.analyze_risks(
                clauses, contract_type, max_concurrent=max_concurrent,
            )

        if check_compliance:
            parallel_tasks["compliance"] = self.compliance_chain.check_compliance(
                clauses, contract_type=contract_type, max_concurrent=max_concurrent,
            )

        if parallel_tasks:
            logger.info(f"开始并行执行风险分析与合规检查，条款数: {len(clauses)}，并发数: {max_concurrent}")
            keys = list(parallel_tasks.keys())
            tasks = [parallel_tasks[k] for k in keys]
            completed = await asyncio.gather(*tasks, return_exceptions=True)

            for key, outcome in zip(keys, completed):
                if isinstance(outcome, Exception):
                    logger.error(f"{key} 分析失败: {outcome}")
                elif key == "risk":
                    result["risk_items"] = outcome
                    logger.info(f"识别到 {len(outcome)} 个风险项")
                elif key == "compliance":
                    result["compliance_results"] = outcome
                    logger.info(f"完成 {len(outcome)} 个条款的合规检查")

        if generate_summary:
            logger.info("生成合同摘要...")
            result["summary"] = await self.summary_chain.generate_summary(
                contract_content,
                risk_items=result.get("risk_items"),
            )

        return result
