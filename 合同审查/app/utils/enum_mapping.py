"""
枚举映射工具

提供中文到枚举值的映射转换功能。
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


# 风险类型映射：中文 -> 英文枚举值
RISK_TYPE_MAPPING = {
    # 中文 -> 枚举值
    "法律风险": "legal_risk",
    "执行风险": "legal_risk",
    "合规风险": "legal_risk",
    "条款无效": "invalid_clause",
    "无效条款": "invalid_clause",
    "条款缺失": "missing_clause",
    "缺失条款": "missing_clause",
    "条款不合理": "unreasonable_clause",
    "不合理条款": "unreasonable_clause",
    "商业风险": "legal_risk",
    "无明显风险": "none",
    "无风险": "none",
    # 英文 -> 枚举值（已经是枚举值的直接返回）
    "legal_risk": "legal_risk",
    "invalid_clause": "invalid_clause",
    "missing_clause": "missing_clause",
    "unreasonable_clause": "unreasonable_clause",
    "none": "none",
}

# 风险等级映射：中文/大写 -> 小写枚举值
RISK_LEVEL_MAPPING = {
    # 中文 -> 枚举值
    "高风险": "high",
    "中风险": "medium",
    "低风险": "low",
    "无风险": "none",
    "高": "high",
    "中": "medium",
    "低": "low",
    "无": "none",
    # 大写英文 -> 小写枚举值
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
    "NONE": "none",
    # 已经是小写的直接返回
    "high": "high",
    "medium": "medium",
    "low": "low",
    "none": "none",
}


def map_risk_type(chinese_type: str) -> str:
    """
    将中文风险类型映射为英文枚举值

    Args:
        chinese_type: 中文风险类型，如"法律风险"

    Returns:
        str: 英文枚举值，如"legal_risk"
    """
    if not chinese_type:
        return "legal_risk"  # 默认值

    # 清理输入
    chinese_type = chinese_type.strip()

    # 查找映射
    mapped = RISK_TYPE_MAPPING.get(chinese_type)
    if mapped:
        return mapped

    # 尝试模糊匹配
    for cn, en in RISK_TYPE_MAPPING.items():
        if cn in chinese_type or chinese_type in cn:
            return en

    # 默认返回 legal_risk
    logger.warning(f"未知的风险类型: {chinese_type}，使用默认值 legal_risk")
    return "legal_risk"


def map_risk_level(level: str) -> str:
    """
    将风险等级映射为小写枚举值

    Args:
        level: 风险等级，如"HIGH"、"高风险"、"high"

    Returns:
        str: 小写枚举值，如"high"
    """
    if not level:
        return "medium"  # 默认值

    # 清理输入
    level = level.strip().upper()

    # 查找映射
    mapped = RISK_LEVEL_MAPPING.get(level)
    if mapped:
        return mapped

    # 尝试模糊匹配
    if "高" in level or "HIGH" in level:
        return "high"
    elif "中" in level or "MEDIUM" in level:
        return "medium"
    elif "低" in level or "LOW" in level:
        return "low"
    elif "无" in level or "NONE" in level:
        return "none"

    # 默认返回 medium
    logger.warning(f"未知的风险等级: {level}，使用默认值 medium")
    return "medium"


def convert_risk_item(risk_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    转换风险项中的枚举字段

    Args:
        risk_item: 原始风险项字典

    Returns:
        Dict[str, Any]: 转换后的风险项字典
    """
    if not isinstance(risk_item, dict):
        return risk_item

    converted = risk_item.copy()

    # 转换风险类型
    if "risk_type" in converted:
        converted["risk_type"] = map_risk_type(converted["risk_type"])

    # 转换风险等级
    if "risk_level" in converted:
        converted["risk_level"] = map_risk_level(converted["risk_level"])

    return converted


def convert_risk_items(risk_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    批量转换风险项列表

    Args:
        risk_items: 风险项列表

    Returns:
        List[Dict[str, Any]]: 转换后的风险项列表
    """
    if not isinstance(risk_items, list):
        return risk_items

    return [convert_risk_item(item) for item in risk_items if isinstance(item, dict)]


def convert_review_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    转换审查结果中的所有枚举字段

    Args:
        result: 原始审查结果字典

    Returns:
        Dict[str, Any]: 转换后的审查结果字典
    """
    if not isinstance(result, dict):
        return result

    converted = result.copy()

    # 转换风险项列表
    if "risk_items" in converted and isinstance(converted["risk_items"], list):
        converted["risk_items"] = convert_risk_items(converted["risk_items"])

    # 转换单个风险项（如果有）
    if "risk_item" in converted and isinstance(converted["risk_item"], dict):
        converted["risk_item"] = convert_risk_item(converted["risk_item"])

    # 转换风险统计
    if "risk_statistics" in converted and isinstance(converted["risk_statistics"], dict):
        stats = converted["risk_statistics"].copy()
        for key in list(stats.keys()):
            new_key = map_risk_level(key)
            if new_key != key:
                stats[new_key] = stats.pop(key)
        converted["risk_statistics"] = stats

    return converted
