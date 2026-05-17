from enum import Enum


class ReviewStatus(str, Enum):
    """审查状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReviewStage(str, Enum):
    """审查阶段"""
    PARSING = "parsing"
    RETRIEVING = "retrieving"
    ANALYZING = "analyzing"
    GENERATING = "generating"


class RiskLevel(str, Enum):
    """风险等级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class RiskType(str, Enum):
    """风险类型"""
    INVALID_CLAUSE = "invalid_clause"
    MISSING_CLAUSE = "missing_clause"
    UNREASONABLE_CLAUSE = "unreasonable_clause"
    LEGAL_RISK = "legal_risk"


class LawCategory(str, Enum):
    """法条分类"""
    CONTRACT = "contract"
    LABOR = "labor"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    COMPANY = "company"
    CIVIL = "civil"
    CRIMINAL = "criminal"


class ContractCategory(str, Enum):
    """合同分类"""
    PURCHASE = "purchase"
    SERVICE = "service"
    LABOR = "labor"
    LEASE = "lease"
    CONFIDENTIALITY = "confidentiality"
    COOPERATION = "cooperation"
