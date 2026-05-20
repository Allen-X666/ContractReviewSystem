"""
核心模块

包含配置、数据库连接、HTTP客户端等核心功能
"""

from 合同审查.app.core.config import settings, Settings
from 合同审查.app.core.database import (
    engine,
    SessionLocal,
    Base,
    get_db,
    get_db_async,
    init_db,
    check_db_connection,
    get_db_health,
    pool_monitor,
    DatabasePoolMonitor,
)
from 合同审查.app.core.fallback import (
    get_llm_fallback_manager,
    get_rag_fallback_manager,
    LLMFallbackManager,
    RAGFallbackManager,
    FallbackStrategy,
    FallbackResult,
    with_llm_fallback,
)

__all__ = [
    # 配置
    "settings",
    "Settings",
    # 数据库
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "get_db_async",
    "init_db",
    "check_db_connection",
    "get_db_health",
    "pool_monitor",
    "DatabasePoolMonitor",
    # 降级与熔断
    "get_llm_fallback_manager",
    "get_rag_fallback_manager",
    "LLMFallbackManager",
    "RAGFallbackManager",
    "FallbackStrategy",
    "FallbackResult",
    "with_llm_fallback",
    # HTTP客户端
    "get_http_client",
    "http_client_context",
    "SpringBootHttpClient",
    "springboot_get",
    "springboot_post",
]
