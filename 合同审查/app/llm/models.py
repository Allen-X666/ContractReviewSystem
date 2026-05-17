"""
LLM输出数据模型

定义合同审查相关的数据模型，用于结构化LLM输出。
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class RiskLevel(str, Enum):
    """风险等级枚举"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class RiskItem(BaseModel):
    """
    风险项模型

    表示合同中的一个风险点。
    """
    clause_no: str = Field(description="条款编号")
    clause_content: str = Field(description="条款内容")
    risk_level: RiskLevel = Field(description="风险等级")
    risk_type: str = Field(description="风险类型，如：法律风险、商业风险、合规风险")
    risk_description: str = Field(description="风险详细描述")
    legal_basis: Optional[str] = Field(default=None, description="法律依据")
    suggestions: List[str] = Field(default_factory=list, description="修改建议")
    score: Optional[int] = Field(default=None, description="对该条款的评价（0到100）分")

    class Config:
        json_schema_extra = {
            "example": {
                "clause_no": "第3条",
                "clause_content": "甲方有权随时解除合同",
                "risk_level": "HIGH",
                "risk_type": "法律风险",
                "risk_description": "该条款赋予甲方单方解除权，违反合同法公平原则",
                "legal_basis": "《合同法》第39条",
                "suggestions": ["建议增加解除条件限制", "建议增加提前通知期限"],
                "score": 90
            }
        }


class ComplianceResult(BaseModel):
    """
    合规检查结果模型

    表示条款是否符合法律法规要求。
    """
    clause_no: str = Field(description="条款编号")
    clause_content: str = Field(description="条款内容")
    is_compliant: bool = Field(description="是否合规")
    violated_laws: List[str] = Field(default_factory=list, description="违反的法律法规")
    violation_details: Optional[str] = Field(default=None, description="违规详情")
    recommendations: List[str] = Field(default_factory=list, description="合规建议")
    score: Optional[int] = Field(default=None, description="对该条款的评价（0到100）分")

    class Config:
        json_schema_extra = {
            "example": {
                "clause_no": "第5条",
                "clause_content": "违约金为合同金额的50%",
                "is_compliant": False,
                "violated_laws": ["《民法典》第585条"],
                "violation_details": "违约金过高，可能被法院调整",
                "recommendations": ["建议将违约金调整为不超过实际损失的30%"],
                "score": 65
            }
        }


class ContractSummary(BaseModel):
    """
    合同摘要模型

    表示合同的整体摘要信息。
    """
    contract_type: str = Field(description="合同类型")
    parties: List[str] = Field(description="合同双方")
    key_terms: List[str] = Field(description="关键条款摘要")
    overall_assessment: str = Field(description="整体评估")
    risk_count: Dict[RiskLevel, int] = Field(description="各级风险数量统计")
    main_concerns: List[str] = Field(default_factory=list, description="主要关注点")

    class Config:
        json_schema_extra = {
            "example": {
                "contract_type": "销售合同",
                "parties": ["甲方公司", "乙方公司"],
                "key_terms": ["付款方式为分期付款", "交付期限为30天"],
                "overall_assessment": "合同整体风险较低，但付款条款需要关注",
                "risk_count": {"HIGH": 0, "MEDIUM": 2, "LOW": 3, "NONE": 0},
                "main_concerns": ["付款期限过短", "违约责任不明确"]
            }
        }


class RiskAnalysisResponse(BaseModel):
    """
    风险分析响应模型

    用于 with_structured_output 的结构化输出。
    """
    risks: List[RiskItem] = Field(
        description="识别的风险项列表"
    )
    summary: str = Field(
        description="风险分析总结"
    )


class ComplianceCheckResponse(BaseModel):
    """
    合规检查响应模型

    用于 with_structured_output 的结构化输出。
    """
    results: List[ComplianceResult] = Field(
        description="各条款的合规检查结果"
    )
    overall_compliant: bool = Field(
        description="整体是否合规"
    )


class ReviewResult(BaseModel):
    """
    完整审查结果模型

    包含单次合同审查的所有结果。
    """
    contract_id: str = Field(description="合同ID")
    review_id: str = Field(description="审查任务ID")
    summary: ContractSummary = Field(description="合同摘要")
    risk_items: List[RiskItem] = Field(default_factory=list, description="风险项列表")
    compliance_results: List[ComplianceResult] = Field(default_factory=list, description="合规检查结果")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "contract_id": "contract_001",
                "review_id": "review_001",
                "summary": {
                    "contract_type": "销售合同",
                    "parties": ["甲方", "乙方"],
                    "key_terms": [],
                    "overall_assessment": "合同整体风险较低",
                    "risk_count": {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NONE": 0},
                    "main_concerns": []
                },
                "risk_items": [],
                "compliance_results": [],
                "metadata": {}
            }
        }
