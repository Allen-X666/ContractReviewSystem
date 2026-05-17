"""
合同条款数据结构模块

定义合同审查相关的数据模型。
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ContractClause(BaseModel):
    """
    合同条款模型
    
    用于存储和检索合同中的单个条款信息。
    """
    clause_id: str = Field(description="条款唯一序号")
    clause_no: str = Field(description="合同原文的条款编号")
    clause_content: str = Field(description="条款完整内容，语义闭环")
    
    # 可选字段
    clause_title: Optional[str] = Field(default=None, description="条款标题")
    risk_level: Optional[str] = Field(default=None, description="风险等级：HIGH/MEDIUM/LOW/NONE")
    risk_description: Optional[str] = Field(default=None, description="风险描述")
    suggestions: Optional[List[str]] = Field(default=None, description="修改建议")
    
    class Config:
        json_schema_extra = {
            "example": {
                "clause_id": "clause_001",
                "clause_no": "第一条",
                "clause_content": "甲方应于合同签订后30日内支付首付款。",
                "clause_title": "付款条款",
                "risk_level": "LOW",
            }
        }


class ContractDocument(BaseModel):
    """
    合同文档模型
    
    包含合同的基本信息和条款列表。
    """
    contract_id: str = Field(description="合同唯一标识")
    contract_name: str = Field(description="合同名称")
    contract_type: Optional[str] = Field(default=None, description="合同类型")
    parties: Optional[List[str]] = Field(default=None, description="合同双方")
    
    clauses: List[ContractClause] = Field(default_factory=list, description="合同条款列表")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "contract_id": "contract_001",
                "contract_name": "销售合同",
                "contract_type": "销售合同",
                "parties": ["甲方公司", "乙方公司"],
                "clauses": [],
            }
        }


@dataclass
class ClauseChunk:
    """
    条款块数据结构（用于内部处理）
    
    与 LangChain 兼容的数据结构。
    """
    clause_id: str
    clause_no: str
    clause_content: str
    clause_title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "clause_id": self.clause_id,
            "clause_no": self.clause_no,
            "clause_content": self.clause_content,
            "clause_title": self.clause_title,
            **self.metadata,
        }
    
    def to_text(self) -> str:
        """转换为文本格式"""
        parts = []
        if self.clause_no:
            parts.append(f"【{self.clause_no}】")
        if self.clause_title:
            parts.append(f"{self.clause_title}")
        parts.append(self.clause_content)
        return "\n".join(parts)
    
    @classmethod
    def from_contract_clause(
        cls,
        clause: ContractClause,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> "ClauseChunk":
        """从 ContractClause 创建 ClauseChunk"""
        metadata = extra_metadata or {}
        metadata.update({
            "risk_level": clause.risk_level,
            "risk_description": clause.risk_description,
            "suggestions": clause.suggestions,
        })
        
        return cls(
            clause_id=clause.clause_id,
            clause_no=clause.clause_no,
            clause_content=clause.clause_content,
            clause_title=clause.clause_title,
            metadata={k: v for k, v in metadata.items() if v is not None},
        )


class ContractReviewResult(BaseModel):
    """
    合同审查结果模型
    """
    contract_id: str = Field(description="合同ID")
    overall_score: Optional[int] = Field(default=None, description="总体评分")
    risk_level: Optional[str] = Field(default=None, description="总体风险等级")
    
    clauses: List[ContractClause] = Field(default_factory=list, description="条款审查结果")
    
    summary: Optional[str] = Field(default=None, description="审查总结")
    key_risks: Optional[List[str]] = Field(default=None, description="关键风险点")
    overall_suggestions: Optional[List[str]] = Field(default=None, description="整体建议")
    
    class Config:
        json_schema_extra = {
            "example": {
                "contract_id": "contract_001",
                "overall_score": 85,
                "risk_level": "MEDIUM",
                "clauses": [],
                "summary": "合同整体风险可控，但部分条款需要修改。",
            }
        }
