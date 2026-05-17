"""
请求上下文管理器

用于在 Agent 工具中传递请求相关的上下文信息（如 Authorization）
使用线程本地存储实现
"""

import threading
from contextlib import contextmanager
from typing import Optional, Any

# 线程本地存储
_thread_local = threading.local()


class RequestContext:
    """
    请求上下文管理
    
    使用线程本地存储在同一线程的不同函数间传递数据
    """
    
    @staticmethod
    def set_auth(token: Optional[str]) -> None:
        """
        设置当前线程的认证令牌
        
        Args:
            token: JWT Token（不含 Bearer 前缀）
        """
        _thread_local.authorization = token
    
    @staticmethod
    def get_auth() -> Optional[str]:
        """
        获取当前线程的认证令牌
        
        Returns:
            JWT Token，如果未设置返回 None
        """
        return getattr(_thread_local, 'authorization', None)
    
    @staticmethod
    def clear_auth() -> None:
        """清除当前线程的认证令牌"""
        if hasattr(_thread_local, 'authorization'):
            delattr(_thread_local, 'authorization')
    
    @staticmethod
    def set(key: str, value: Any) -> None:
        """
        设置自定义上下文值
        
        Args:
            key: 键名
            value: 值
        """
        setattr(_thread_local, key, value)
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """
        获取自定义上下文值
        
        Args:
            key: 键名
            default: 默认值
            
        Returns:
            存储的值，如果不存在返回 default
        """
        return getattr(_thread_local, key, default)


@contextmanager
def auth_context(token: Optional[str]):
    """
    认证上下文管理器
    
    用于在 with 语句块中设置和自动清理认证信息
    
    Args:
        token: JWT Token（不含 Bearer 前缀）
        
    Yields:
        None
        
    Example:
        >>> with auth_context("eyJhbGciOiJIUzI1NiJ9..."):
        ...     result = some_tool()  # 工具内部可以获取到 token
    """
    RequestContext.set_auth(token)
    try:
        yield
    finally:
        RequestContext.clear_auth()


# 便捷函数

def get_current_token() -> Optional[str]:
    """
    获取当前请求的 Token（便捷函数）
    
    Returns:
        当前线程的 JWT Token
    """
    return RequestContext.get_auth()


def set_current_token(token: Optional[str]) -> None:
    """
    设置当前请求的 Token（便捷函数）
    
    Args:
        token: JWT Token
    """
    RequestContext.set_auth(token)


def clear_current_token() -> None:
    """清除当前请求的 Token（便捷函数）"""
    RequestContext.clear_auth()
