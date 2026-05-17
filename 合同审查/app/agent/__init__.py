"""
Agent 工具模块

提供合同审查相关的工具函数和提示模板，供 LangChain Agent 使用。
"""

# 类型检查忽略：这些工具函数使用 @tool 装饰器，IDE 可能无法识别
# noinspection PyUnresolvedReferences
from 合同审查.app.agent.tools import (
    # 核心工具
    search_contract_knowledge,
    review_contract,           # 统一的合同审查工具
    check_contract_exists,
    get_law_reference,
    # 新增工具
    get_contract_list,
    get_review_list,
    download_file,
    get_user_info,
    update_user_information,
    get_sys_information,
    get_store_path,            # 获取存储路径设置
    # 向后兼容的别名
    analyze_contract_risk,     # = review_contract
    calculate_contract_score,  # = review_contract
    start_contract_review,     # = review_contract
)

from 合同审查.app.agent.prompts import (
    SYSTEM_PROMPT,
    TOOL_USAGE_GUIDE,
    ERROR_MESSAGES,
    create_chatbot_prompt,
)

__all__ = [
    # 工具函数
    "search_contract_knowledge",
    "review_contract",
    "check_contract_exists",
    "get_law_reference",
    # 新增工具
    "get_contract_list",
    "get_review_list",
    "download_file",
    "get_user_info",
    "update_user_information",
    "get_sys_information",
    "get_store_path",          # 获取存储路径设置
    # 向后兼容
    "analyze_contract_risk",
    "calculate_contract_score",
    "start_contract_review",
    # 提示模板
    "SYSTEM_PROMPT",
    "TOOL_USAGE_GUIDE",
    "ERROR_MESSAGES",
    "create_chatbot_prompt",
]
