"""
HTTP 客户端

使用 requests 库与 SpringBoot 后端进行通信
支持同步和异步操作
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Union
from urllib.parse import urljoin

import aiohttp
import requests

from 合同审查.app.core.config import settings

logger = logging.getLogger(__name__)


class SpringBootClient:
    """
    SpringBoot 后端 HTTP 客户端
    
    使用 requests 库发送 HTTP 请求
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            token: JWT Token（不含 Bearer 前缀）
        """
        self.base_url = settings.SPRINGBOOT_BASE_URL
        self.token = token
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # 如果有 token，添加到请求头
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
    
    def _build_url(self, path: str) -> str:
        """构建完整 URL"""
        if path.startswith("http"):
            return path
        # 确保 base_url 以 / 结尾，path 不以 / 开头（除非 path 本身就是 /）
        base = self.base_url.rstrip("/")
        path = path.lstrip("/") if path != "/" else ""
        return f"{base}/{path}" if path else base
    
    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> requests.Response:
        """
        发送 GET 请求
        
        Args:
            path: API 路径
            params: 查询参数
            timeout: 超时时间（秒）
            
        Returns:
            Response 对象
        """
        url = self._build_url(path)
        timeout = timeout or settings.SPRINGBOOT_TIMEOUT
        
        try:
            logger.debug(f"GET {url}, params={params}")
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"GET 请求失败: {url}, error={e}")
            raise
    
    def post(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict, str]] = None,
        timeout: Optional[float] = None
    ) -> requests.Response:
        """
        发送 POST 请求
        
        Args:
            path: API 路径
            json_data: JSON 数据
            data: 表单数据
            timeout: 超时时间（秒）
            
        Returns:
            Response 对象
        """
        url = self._build_url(path)
        timeout = timeout or settings.SPRINGBOOT_TIMEOUT
        
        try:
            logger.debug(f"POST {url}, json={json_data}")
            response = self.session.post(
                url,
                json=json_data,
                data=data,
                timeout=timeout
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"POST 请求失败: {url}, error={e}")
            raise
    
    def close(self) -> None:
        """关闭会话"""
        self.session.close()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
        return False


# 便捷函数

def springboot_get(
    path: str,
    token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None
) -> requests.Response:
    """
    发送 GET 请求（便捷函数）
    
    Args:
        path: API 路径
        token: JWT Token
        params: 查询参数
        timeout: 超时时间
        
    Returns:
        Response 对象
        
    Example:
        >>> response = springboot_get("/contract/list", token="xxx")
        >>> data = response.json()
    """
    with SpringBootClient(token=token) as client:
        return client.get(path, params=params, timeout=timeout)


def springboot_post(
    path: str,
    token: Optional[str] = None,
    json_data: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict, str]] = None,
    timeout: Optional[float] = None
) -> requests.Response:
    """
    发送 POST 请求（便捷函数）
    
    Args:
        path: API 路径
        token: JWT Token
        json_data: JSON 数据
        data: 表单数据
        timeout: 超时时间
        
    Returns:
        Response 对象
        
    Example:
        >>> response = springboot_post(
        ...     "/review/start",
        ...     token="xxx",
        ...     json_data={"contractId": 123}
        ... )
    """
    with SpringBootClient(token=token) as client:
        return client.post(path, json_data=json_data, data=data, timeout=timeout)


def springboot_put(
    path: str,
    token: Optional[str] = None,
    json_data: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict, str]] = None,
    timeout: Optional[float] = None
) -> requests.Response:
    """
    发送 PUT 请求（便捷函数）

    Args:
        path: API 路径
        token: JWT Token
        json_data: JSON 数据
        data: 表单数据
        timeout: 超时时间

    Returns:
        Response 对象

    Example:
        >>> response = springboot_put(
        ...     "/user/profile",
        ...     token="xxx",
        ...     json_data={"nickName": "新昵称"}
        ... )
    """
    with SpringBootClient(token=token) as client:
        return client.put(path, json_data=json_data, data=data, timeout=timeout)


def springboot_post_multipart(
    path: str,
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None
) -> requests.Response:
    """
    发送 multipart/form-data POST 请求（便捷函数）

    用于上传文件或发送包含文件的表单数据

    Args:
        path: API 路径
        token: JWT Token
        data: 表单字段数据（字典）
        files: 文件数据（字典，格式：{'field_name': ('filename', file_content, 'content_type')})
        timeout: 超时时间

    Returns:
        Response 对象

    Example:
        >>> response = springboot_post_multipart(
        ...     "/review/start",
        ...     token="xxx",
        ...     data={"contractId": 123, "reviewOptions": '{"check": true}'},
        ...     files={"file": ("contract.pdf", open("contract.pdf", "rb"), "application/pdf")}
        ... )
    """
    base_url = settings.SPRINGBOOT_BASE_URL
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    timeout = timeout or settings.SPRINGBOOT_TIMEOUT

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    # 注意：不要设置 Content-Type，requests 会自动设置 multipart boundary

    try:
        logger.debug(f"POST multipart {url}, data={data}, files={files is not None}")
        response = requests.post(
            url,
            data=data,
            files=files,
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"POST multipart 请求失败: {url}, error={e}")
        raise


# ==================== 异步版本函数 ====================

class AsyncSpringBootClient:
    """
    SpringBoot 后端异步 HTTP 客户端

    使用 aiohttp 库发送异步 HTTP 请求
    """

    def __init__(self, token: Optional[str] = None):
        """
        初始化客户端

        Args:
            token: JWT Token（不含 Bearer 前缀）
        """
        self.base_url = settings.SPRINGBOOT_BASE_URL
        self.token = token
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        self.session = aiohttp.ClientSession(headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
        return False

    def _build_url(self, path: str) -> str:
        """构建完整 URL"""
        if path.startswith("http"):
            return path
        base = self.base_url.rstrip("/")
        path = path.lstrip("/") if path != "/" else ""
        return f"{base}/{path}" if path else base

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> aiohttp.ClientResponse:
        """
        发送异步 GET 请求

        Args:
            path: API 路径
            params: 查询参数
            timeout: 超时时间（秒）

        Returns:
            ClientResponse 对象
        """
        url = self._build_url(path)
        timeout = aiohttp.ClientTimeout(total=timeout or settings.SPRINGBOOT_TIMEOUT)

        try:
            logger.debug(f"Async GET {url}, params={params}")
            async with self.session.get(url, params=params, timeout=timeout) as response:
                response.raise_for_status()
                return response
        except aiohttp.ClientError as e:
            logger.error(f"Async GET 请求失败: {url}, error={e}")
            raise

    async def post(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict, str]] = None,
        timeout: Optional[float] = None
    ) -> aiohttp.ClientResponse:
        """
        发送异步 POST 请求

        Args:
            path: API 路径
            json_data: JSON 数据
            data: 表单数据
            timeout: 超时时间（秒）

        Returns:
            ClientResponse 对象
        """
        url = self._build_url(path)
        timeout = aiohttp.ClientTimeout(total=timeout or settings.SPRINGBOOT_TIMEOUT)

        try:
            logger.debug(f"Async POST {url}, json={json_data}")
            async with self.session.post(
                url,
                json=json_data,
                data=data,
                timeout=timeout
            ) as response:
                response.raise_for_status()
                return response
        except aiohttp.ClientError as e:
            logger.error(f"Async POST 请求失败: {url}, error={e}")
            raise

    async def put(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict, str]] = None,
        timeout: Optional[float] = None
    ) -> aiohttp.ClientResponse:
        """
        发送异步 PUT 请求

        Args:
            path: API 路径
            json_data: JSON 数据
            data: 表单数据
            timeout: 超时时间（秒）

        Returns:
            ClientResponse 对象
        """
        url = self._build_url(path)
        timeout = aiohttp.ClientTimeout(total=timeout or settings.SPRINGBOOT_TIMEOUT)

        try:
            logger.debug(f"Async PUT {url}, json={json_data}")
            async with self.session.put(
                url,
                json=json_data,
                data=data,
                timeout=timeout
            ) as response:
                response.raise_for_status()
                return response
        except aiohttp.ClientError as e:
            logger.error(f"Async PUT 请求失败: {url}, error={e}")
            raise


# 异步便捷函数

async def async_springboot_get(
    path: str,
    token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None
) -> aiohttp.ClientResponse:
    """
    发送异步 GET 请求（便捷函数）

    Args:
        path: API 路径
        token: JWT Token
        params: 查询参数
        timeout: 超时时间

    Returns:
        ClientResponse 对象

    Example:
        >>> response = await async_springboot_get("/contract/list", token="xxx")
        >>> data = await response.json()
    """
    async with AsyncSpringBootClient(token=token) as client:
        return await client.get(path, params=params, timeout=timeout)


async def async_springboot_post(
    path: str,
    token: Optional[str] = None,
    json_data: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict, str]] = None,
    timeout: Optional[float] = None
) -> aiohttp.ClientResponse:
    """
    发送异步 POST 请求（便捷函数）

    Args:
        path: API 路径
        token: JWT Token
        json_data: JSON 数据
        data: 表单数据
        timeout: 超时时间

    Returns:
        ClientResponse 对象

    Example:
        >>> response = await async_springboot_post(
        ...     "/review/start",
        ...     token="xxx",
        ...     json_data={"contractId": 123}
        ... )
    """
    async with AsyncSpringBootClient(token=token) as client:
        return await client.post(path, json_data=json_data, data=data, timeout=timeout)


async def async_springboot_put(
    path: str,
    token: Optional[str] = None,
    json_data: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict, str]] = None,
    timeout: Optional[float] = None
) -> aiohttp.ClientResponse:
    """
    发送异步 PUT 请求（便捷函数）

    Args:
        path: API 路径
        token: JWT Token
        json_data: JSON 数据
        data: 表单数据
        timeout: 超时时间

    Returns:
        ClientResponse 对象

    Example:
        >>> response = await async_springboot_put(
        ...     "/user/profile",
        ...     token="xxx",
        ...     json_data={"nickName": "新昵称"}
        ... )
    """
    async with AsyncSpringBootClient(token=token) as client:
        return await client.put(path, json_data=json_data, data=data, timeout=timeout)
