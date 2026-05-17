import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import UploadFile
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

from 合同审查.app.schemas.enums import (
    ContractCategory,
    LawCategory,
    ReviewStage,
    ReviewStatus,
    RiskLevel,
    RiskType,
)

class ModelConfig(BaseModel):
    """基础模型（兼容驼峰命名）"""
    model_config = ConfigDict(
        # 1. 自动驼峰 ↔ 下划线互转（解决你现在的 422 核心问题！）
        alias_generator=to_camel,
        # 2. 允许用字段名或别名传参（Java 传驼峰完全兼容）
        populate_by_name=True,
        # 3. 支持从 ORM 对象（如数据库实体）转 Pydantic
        from_attributes=True,
        # 4. 忽略多余字段，避免前端乱传参数报错
        extra="ignore",
        # 5. 允许空字符串、null 等宽松校验
        str_strip_whitespace=True,
    )


class Result(ModelConfig):
    """统一响应"""

    code: int = Field(200, description="状态码")
    message: str = Field("success", description="提示信息")
    data: Optional[Any] = Field(None, description="响应数据")
    timestamp: int = Field(
        default_factory=lambda: int(time.time() * 1000), description="时间戳"
    )


class ReviewOptions(ModelConfig):
    """审查选项"""

    check_invalid_clause: bool = Field(True, description="检查无效条款")
    check_missing_clause: bool = Field(True, description="检查缺失条款")
    check_unreasonable_clause: bool = Field(True, description="检查不合理条款")
    check_legal_risk: bool = Field(True, description="检查法律风险")
    contract_type: Optional[ContractCategory] = Field(None, description="合同类型")


class StartReviewRequest(ModelConfig):
    """发起审查请求"""

    contract_id: int = Field(..., description="合同ID")
    file: Optional[UploadFile] = Field(None, description="合同文件")
    review_options: ReviewOptions = Field(
        default_factory=ReviewOptions, description="审查选项"
    )


class StartReviewResponse(ModelConfig):
    """发起审查响应"""

    review_id: str = Field(..., description="审查任务ID")
    contract_id: int = Field(..., description="合同ID")
    status: ReviewStatus = Field(..., description="任务状态")
    message: str = Field(..., description="状态消息")


class RelatedLaw(ModelConfig):
    """关联法条"""

    law_id: int = Field(..., description="法规ID")
    law_name: str = Field(..., description="法规名称")
    article_no: str = Field(..., description="条款编号")
    content: str = Field(..., description="条款内容")


class LocationVO(ModelConfig):
    """位置信息（兼容 Java LocationVO）"""

    paragraph_index: int = Field(..., description="段落索引")
    start_offset: int = Field(default=0, description="起始偏移")
    end_offset: int = Field(default=0, description="结束偏移")
    text: str = Field(default="", description="文本内容")


class RiskItem(ModelConfig):
    """风险项（兼容 Java RiskItemVO）"""

    id: Optional[int] = Field(None, description="风险ID")
    risk_type: str = Field(..., description="风险类型")
    level: str = Field(..., description="风险等级")
    clause: str = Field(..., description="条款标题")
    clause_content: str = Field(..., description="条款原文")
    description: str = Field(..., description="风险描述")
    suggestion: str = Field(..., description="修改建议")
    law_references: List[RelatedLaw] = Field(default_factory=list, description="关联法条")
    location: LocationVO = Field(..., description="位置信息")


class ReviewProgress(ModelConfig):
    """审查进度"""

    progress: int = Field(..., ge=0, le=100, description="进度(0-100)")
    stage: ReviewStage = Field(..., description="当前阶段")
    status: ReviewStatus = Field(..., description="状态")
    message: str = Field(..., description="消息")


class ReviewResult(ModelConfig):
    """审查结果（兼容 Java ReviewResultVO）"""

    review_id: int = Field(..., description="审查ID")
    review_no: str = Field(..., description="审查编号")
    contract_id: int = Field(..., description="合同ID")
    status: str = Field(..., description="状态")
    overall_score: int = Field(..., ge=0, le=100, description="总体评分")
    conclusion: str = Field(..., description="审查结论")
    risk_summary: Dict[str, int] = Field(default_factory=dict, description="风险摘要")
    risks: List[RiskItem] = Field(default_factory=list, description="风险列表")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class LawArticle(ModelConfig):
    """法条"""

    id: int = Field(..., description="条款ID")
    article_no: str = Field(..., description="条款编号")
    title: str = Field(..., description="条款标题")
    content: str = Field(..., description="条款内容")


class LawRegulation(ModelConfig):
    """法律法规"""

    id: int = Field(..., description="法规ID")
    law_no: str = Field(..., description="法规编号")
    name: str = Field(..., description="法规名称")
    category: LawCategory = Field(..., description="分类")
    issuer: str = Field(..., description="发布机关")
    publish_date: date = Field(..., description="发布日期")
    effective_date: date = Field(..., description="施行日期")
    status: str = Field(..., description="状态")
    description: str = Field(..., description="法规简介")
    article_count: int = Field(..., description="条款数量")
    is_new: bool = Field(..., description="是否最新")


class LawRegulationDetail(ModelConfig):
    """法规详情"""

    content: str = Field(..., description="法规全文")
    articles: List[LawArticle] = Field(default_factory=list, description="法条列表")
    created_at: datetime = Field(..., description="创建时间")


class LawSearchRequest(ModelConfig):
    """法条搜索请求"""

    keyword: Optional[str] = Field(None, description="关键词")
    category: Optional[LawCategory] = Field(None, description="分类")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(100, ge=1, le=500, description="每页大小")


class LawSearchResult(ModelConfig):
    """法条搜索结果"""

    category_id: str = Field(..., description="分类ID")
    category_name: str = Field(..., description="分类名称")
    laws: List[LawRegulation] = Field(default_factory=list, description="法规列表")


class LawMatchResult(ModelConfig):
    """法条匹配结果"""

    law_id: int = Field(..., description="法规ID")
    law_name: str = Field(..., description="法规名称")
    article_no: str = Field(..., description="条款编号")
    content: str = Field(..., description="条款内容")
    relevance_score: float = Field(..., ge=0, le=1, description="相关度分数")


class LawMatchResponse(ModelConfig):
    """法条匹配响应"""

    matches: List[LawMatchResult] = Field(default_factory=list, description="匹配结果列表")


class ReportOptions(ModelConfig):
    """报告选项"""

    include_cover: bool = Field(True, description="包含封面")
    include_overview: bool = Field(True, description="包含概览")
    include_risk_details: bool = Field(True, description="包含风险详情")
    include_law_reference: bool = Field(True, description="包含法条引用")
    include_suggestions: bool = Field(True, description="包含修改建议")


class GenerateReportRequest(ModelConfig):
    """生成报告请求"""

    review_id: int = Field(..., description="审查ID")
    report_options: ReportOptions = Field(
        default_factory=ReportOptions, description="报告选项"
    )


class Report(ModelConfig):
    """报告"""

    report_id: int = Field(..., description="报告ID")
    report_no: str = Field(..., description="报告编号")
    review_id: int = Field(..., description="审查ID")
    contract_id: int = Field(..., description="合同ID")
    contract_name: str = Field(..., description="合同名称")
    report_title: str = Field(..., description="报告标题")
    overall_score: int = Field(..., description="总体评分")
    risk_summary: Dict[str, int] = Field(default_factory=dict, description="风险摘要")
    conclusion: str = Field(..., description="审查结论")
    risks: List[RiskItem] = Field(default_factory=list, description="风险列表")
    download_url: Optional[str] = Field(None, description="下载链接")
    created_at: datetime = Field(..., description="创建时间")


class LawCategoryInfo(ModelConfig): 
    """法条分类信息"""

    id: str = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    count: int = Field(..., description="法规数量")


class LawDocumentUpload(ModelConfig):
    """法律文档上传请求"""

    document_type: str = Field(..., description="文档类型：法律法规/司法解释/行政法规")
    effective_date: Optional[datetime] = Field(None, description="生效日期")
    description: Optional[str] = Field(None, description="文档说明")


class LawDocument(ModelConfig):
    """法律文档信息"""

    id: int = Field(..., description="文档ID")
    name: str = Field(..., description="文档名称")
    file_path: str = Field(..., description="文件路径")
    document_type: str = Field(..., description="文档类型")
    effective_date: Optional[datetime] = Field(None, description="生效日期")
    description: Optional[str] = Field(None, description="文档说明")
    file_size: int = Field(..., description="文件大小（字节）")
    upload_time: datetime = Field(..., description="上传时间")
    status: str = Field("active", description="状态：active/invalid")
