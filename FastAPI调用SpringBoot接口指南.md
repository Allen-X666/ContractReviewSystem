# FastAPI 调用 SpringBoot 接口指南

## 1. 项目架构概述

### 1.1 服务配置信息

| 服务 | 基础URL | API前缀 | 完整地址 |
|------|---------|---------|----------|
| SpringBoot | `http://localhost:8080` | `/api` | `http://localhost:8080/api` |
| FastAPI | `http://localhost:8001` | `/api/v1` | `http://localhost:8001/api/v1` |

### 1.2 统一响应格式

SpringBoot 所有接口返回统一响应体 `Result<T>`：

```json
{
  "code": 200,           // 状态码，200表示成功
  "message": "操作成功",  // 提示信息
  "data": { ... },       // 响应数据（泛型）
  "total": null,         // 分页总数（可选）
  "timestamp": 1740123456789  // 时间戳
}
```

## 2. 接口清单

### 2.1 用户认证接口 (AuthController)

| 接口 | 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|------|
| 用户注册 | POST | `/api/auth/register` | 否 | 用户注册 |
| 用户登录 | POST | `/api/auth/login` | 否 | 用户登录，返回Token |
| 获取图形验证码 | GET | `/api/auth/captcha` | 否 | source参数标识来源 |
| 发送验证码 | POST | `/api/auth/send-code` | 否 | 发送邮箱验证码 |
| 退出登录 | POST | `/api/auth/logout` | 是 | 使Token失效 |
| 获取用户信息 | GET | `/api/auth/user-info` | 是 | 获取当前登录用户信息 |
| 修改密码 | POST | `/api/auth/change-password` | 是 | 修改当前用户密码 |
| 刷新Token | POST | `/api/auth/refresh-token` | 是 | 刷新访问Token |
| 重置密码 | POST | `/api/auth/reset-password` | 否 | 忘记密码重置 |

### 2.2 用户接口 (UserController)

| 接口 | 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|------|
| 更新用户信息 | PUT | `/api/user/profile` | 是 | 更新用户资料 |
| 上传头像 | PUT | `/api/user/avatar` | 是 | 上传用户头像文件 |
| 获取通知设置 | GET | `/api/user/notification-settings` | 是 | 获取用户通知偏好 |
| 更新通知设置 | PUT | `/api/user/notification-settings` | 是 | 更新用户通知偏好 |

### 2.3 合同接口 (ContractController)

| 接口 | 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|------|
| 上传合同 | POST | `/api/contract/upload` | 是 | 上传单个合同文件 |
| 批量上传合同 | POST | `/api/contract/batch-upload` | 是 | 批量上传合同文件 |
| 获取合同列表 | GET | `/api/contract/list` | 是 | 分页获取合同列表 |
| 删除合同 | DELETE | `/api/contract/{id}` | 是 | 删除指定合同 |
| 批量删除合同 | DELETE | `/api/contract/batch` | 是 | 批量删除合同 |
| 获取合同统计数据 | GET | `/api/contract/stats` | 是 | 获取合同统计信息 |
| 获取合同预览信息 | GET | `/api/contract/preview/{contractId}` | 是 | 获取合同预览数据 |
| 获取合同文件 | GET | `/api/contract/file/{contractId}` | 是 | 获取合同文件用于预览 |
| 下载合同文件 | GET | `/api/contract/download/{contractId}` | 是 | 下载合同文件 |

### 2.4 合同审查接口 (ReviewController)

| 接口 | 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|------|
| 发起合同审查 | POST | `/api/review/start` | 是 | multipart/form-data格式 |
| 获取审查进度 | GET | `/api/review/{reviewId}/progress` | 是 | SSE流式推送 |
| 获取审查结果 | GET | `/api/review/{reviewId}/result` | 是 | 获取审查结果 |
| 获取风险列表 | GET | `/api/review/{reviewId}/risks` | 是 | 分页获取风险项 |
| 重新审查 | POST | `/api/review/{reviewId}/re-review` | 是 | 重新发起审查 |
| 取消审查 | POST | `/api/review/{reviewId}/cancel` | 是 | 取消进行中的审查 |
| 合同审核历史统计 | GET | `/api/review/history/stats` | 是 | 获取历史统计 |
| 获取审查历史列表 | GET | `/api/review/history` | 是 | 分页获取历史记录 |
| 删除审查历史 | DELETE | `/api/review/{reviewId}` | 是 | 删除历史记录 |

### 2.5 智能客服接口 (ChatBotController)

| 接口 | 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|------|
| 发送消息 | POST | `/api/chatbot/messages` | 是 | SSE流式输出 |
| 获取对话列表 | GET | `/api/chatbot/conversations` | 是 | 获取所有对话 |
| 获取对话详情 | GET | `/api/chatbot/conversations/{id}` | 是 | 获取指定对话详情 |
| 重命名对话 | PUT | `/api/chatbot/conversations/{id}/name` | 是 | 修改对话名称 |
| 删除对话 | DELETE | `/api/chatbot/conversations/{id}` | 是 | 删除指定对话 |
| 导出为EXCEL | GET | `/api/chatbot/conversations/{id}/export` | 是 | 导出对话记录 |

### 2.6 知识管理接口 (KnowledgeController)

| 接口 | 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|------|
| 获取知识库统计数据 | GET | `/api/knowledge/stats` | 否 | 获取知识库统计 |
| 获取法条分类列表 | GET | `/api/knowledge/laws/categories` | 否 | 获取法条分类 |
| 搜索法条 | GET | `/api/knowledge/laws/search` | 否 | 按关键词搜索法条 |
| 获取法条详情 | GET | `/api/knowledge/laws/{lawId}` | 否 | 获取法条详细信息 |

### 2.7 系统管理接口 (AdminController)

| 接口 | 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|------|
| 上传法律文档 | POST | `/api/admin/law/upload` | 是 | multipart/form-data |
| 获取法律列表 | GET | `/api/admin/law/list` | 是 | 获取所有法律文档 |
| 删除文档 | DELETE | `/api/admin/law/{id}` | 是 | 删除法律文档 |
| 获取法律文档文件 | GET | `/api/admin/law/{id}/file` | 是 | 获取文档文件 |

## 3. FastAPI 调用示例

### 3.1 基础配置

```python
import httpx
from typing import Optional, Dict, Any

# SpringBoot 服务配置
SPRINGBOOT_BASE_URL = "http://localhost:8080/api"
DEFAULT_TIMEOUT = 30.0  # 秒

# 创建异步HTTP客户端
async def get_http_client() -> httpx.AsyncClient:
    """获取HTTP客户端实例"""
    return httpx.AsyncClient(
        base_url=SPRINGBOOT_BASE_URL,
        timeout=DEFAULT_TIMEOUT,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    )
```

### 3.2 认证相关调用

#### 3.2.1 用户登录

```python
import httpx
from typing import Optional, Dict, Any

async def login(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    用户登录，获取JWT Token
    
    Args:
        username: 用户名/邮箱
        password: 密码
        
    Returns:
        登录成功返回包含token的字典，失败返回None
        
    Example Response:
        {
            "code": 200,
            "message": "登录成功",
            "data": {
                "token": "eyJhbGciOiJIUzI1NiIs...",
                "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
                "expiresIn": 3600,
                "user": {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com"
                }
            }
        }
    """
    async with httpx.AsyncClient(base_url="http://localhost:8080/api") as client:
        response = await client.post(
            "/auth/login",
            json={
                "username": username,
                "password": password
            }
        )
        result = response.json()
        if result.get("code") == 200:
            return result.get("data")
        return None
```

#### 3.2.2 获取用户信息

```python
async def get_user_info(token: str) -> Optional[Dict[str, Any]]:
    """
    获取当前登录用户信息
    
    Args:
        token: JWT Token (Bearer token)
        
    Returns:
        用户信息字典
    """
    async with httpx.AsyncClient(base_url="http://localhost:8080/api") as client:
        response = await client.get(
            "/auth/user-info",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        result = response.json()
        if result.get("code") == 200:
            return result.get("data")
        return None
```

### 3.3 合同相关调用

#### 3.3.1 上传合同

```python
from pathlib import Path

async def upload_contract(token: str, file_path: Path) -> Optional[Dict[str, Any]]:
    """
    上传合同文件
    
    Args:
        token: JWT Token
        file_path: 合同文件路径
        
    Returns:
        上传结果，包含合同ID等信息
    """
    async with httpx.AsyncClient(base_url="http://localhost:8080/api") as client:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/pdf")}
            response = await client.post(
                "/contract/upload",
                headers={"Authorization": f"Bearer {token}"},
                files=files
            )
        result = response.json()
        if result.get("code") == 200:
            return result.get("data")
        return None
```

#### 3.3.2 获取合同列表

```python
async def get_contract_list(
    token: str, 
    page: int = 1, 
    page_size: int = 10
) -> Optional[Dict[str, Any]]:
    """
    获取合同列表
    
    Args:
        token: JWT Token
        page: 页码，默认1
        page_size: 每页大小，默认10
        
    Returns:
        合同列表数据
    """
    async with httpx.AsyncClient(base_url="http://localhost:8080/api") as client:
        response = await client.get(
            "/contract/list",
            headers={"Authorization": f"Bearer {token}"},
            params={"page": page, "pageSize": page_size}
        )
        result = response.json()
        if result.get("code") == 200:
            return {
                "list": result.get("data"),
                "total": result.get("total")
            }
        return None
```

### 3.4 审查相关调用

#### 3.4.1 发起合同审查

```python
async def start_review(
    token: str,
    contract_id: int,
    file_path: Path,
    review_options: Optional[Dict[str, bool]] = None
) -> Optional[Dict[str, Any]]:
    """
    发起合同审查
    
    Args:
        token: JWT Token
        contract_id: 合同ID
        file_path: 合同文件路径
        review_options: 审查选项，如 {"checkLegalRisk": true, "checkTerms": true}
        
    Returns:
        审查任务信息，包含reviewId
    """
    import json
    
    if review_options is None:
        review_options = {
            "checkLegalRisk": True,
            "checkTerms": True,
            "checkCompliance": True,
            "checkCompleteness": True
        }
    
    async with httpx.AsyncClient(
        base_url="http://localhost:8080/api",
        timeout=120.0  # 审查接口超时时间较长
    ) as client:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/pdf")}
            data = {
                "contractId": str(contract_id),
                "reviewOptions": json.dumps(review_options)
            }
            response = await client.post(
                "/review/start",
                headers={"Authorization": f"Bearer {token}"},
                files=files,
                data=data
            )
        result = response.json()
        if result.get("code") == 200:
            return result.get("data")
        return None
```

#### 3.4.2 获取审查进度 (SSE)

```python
import asyncio
from typing import AsyncGenerator

async def get_review_progress_sse(
    token: str,
    review_id: int
) -> AsyncGenerator[str, None]:
    """
    获取审查进度（SSE流式）
    
    Args:
        token: JWT Token
        review_id: 审查任务ID
        
    Yields:
        SSE事件数据字符串
    """
    async with httpx.AsyncClient(base_url="http://localhost:8080/api") as client:
        async with client.stream(
            "GET",
            f"/review/{review_id}/progress",
            headers={"Authorization": f"Bearer {token}",
                    "Accept": "text/event-stream"},
            timeout=None  # SSE长连接
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    yield line[5:].strip()
```

#### 3.4.3 获取审查结果

```python
async def get_review_result(token: str, review_id: int) -> Optional[Dict[str, Any]]:
    """
    获取审查结果
    
    Args:
        token: JWT Token
        review_id: 审查任务ID
        
    Returns:
        审查结果详情
    """
    async with httpx.AsyncClient(base_url="http://localhost:8080/api") as client:
        response = await client.get(
            f"/review/{review_id}/result",
            headers={"Authorization": f"Bearer {token}"}
        )
        result = response.json()
        if result.get("code") == 200:
            return result.get("data")
        return None
```

### 3.5 智能客服相关调用

#### 3.5.1 发送消息 (SSE流式)

```python
async def send_chat_message_sse(
    token: str,
    message: str,
    conversation_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    发送消息到智能客服（SSE流式输出）
    
    Args:
        token: JWT Token
        message: 用户消息内容
        conversation_id: 对话ID（可选，首次对话可不传）
        
    Yields:
        AI回复的流式内容
    """
    async with httpx.AsyncClient(base_url="http://localhost:8080/api") as client:
        # 构建请求体
        payload = {
            "content": message,
            "conversationId": conversation_id
        }
        
        async with client.stream(
            "POST",
            "/chatbot/messages",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            json=payload,
            timeout=None  # SSE长连接
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = line[5:].strip()
                    yield data
```

#### 3.5.2 获取对话列表

```python
async def get_conversations(token: str) -> Optional[list]:
    """
    获取对话列表
    
    Args:
        token: JWT Token
        
    Returns:
        对话列表
    """
    async with httpx.AsyncClient(base_url="http://localhost:8080/api") as client:
        response = await client.get(
            "/chatbot/conversations",
            headers={"Authorization": f"Bearer {token}"}
        )
        result = response.json()
        if result.get("code") == 200:
            return result.get("data")
        return None
```

### 3.6 知识库相关调用

#### 3.6.1 搜索法条

```python
async def search_laws(
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 100
) -> Optional[list]:
    """
    搜索法条（无需认证）
    
    Args:
        keyword: 搜索关键词
        page: 页码
        page_size: 每页大小
        
    Returns:
        法条搜索结果列表（按分类分组）
    """
    async with httpx.AsyncClient(base_url="http://localhost:8080/api") as client:
        response = await client.get(
            "/knowledge/laws/search",
            params={
                "keyword": keyword,
                "page": page,
                "pageSize": page_size
            }
        )
        result = response.json()
        if result.get("code") == 200:
            return result.get("data")
        return None
```

#### 3.6.2 获取法条详情

```python
async def get_law_detail(law_id: int) -> Optional[Dict[str, Any]]:
    """
    获取法条详情（无需认证）
    
    Args:
        law_id: 法条ID
        
    Returns:
        法条详细信息
    """
    async with httpx.AsyncClient(base_url="http://localhost:8080/api") as client:
        response = await client.get(f"/knowledge/laws/{law_id}")
        result = response.json()
        if result.get("code") == 200:
            return result.get("data")
        return None
```

## 4. 通用工具类封装

```python
import httpx
import json
from typing import Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


@dataclass
class ApiResponse:
    """统一API响应封装"""
    code: int
    message: str
    data: Optional[Any] = None
    total: Optional[int] = None
    timestamp: Optional[int] = None
    
    @property
    def is_success(self) -> bool:
        return self.code == 200


class SpringBootClient:
    """SpringBoot服务客户端"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8080/api",
        timeout: float = 30.0,
        token: Optional[str] = None
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.token = token
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    def _make_auth_header(self, token: Optional[str] = None) -> Dict[str, str]:
        """构建认证头"""
        headers = {}
        auth_token = token or self.token
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers
    
    async def request(
        self,
        method: HttpMethod,
        path: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None,
        token: Optional[str] = None,
        stream: bool = False
    ) -> ApiResponse:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            path: 请求路径
            json_data: JSON请求体
            params: URL参数
            files: 文件上传
            token: 可选的Token（覆盖默认）
            stream: 是否流式响应
            
        Returns:
            ApiResponse对象
        """
        headers = self._make_auth_header(token)
        
        if files:
            # 文件上传时不设置Content-Type，让httpx自动设置multipart
            headers.pop("Content-Type", None)
        
        kwargs = {
            "headers": headers,
            "params": params
        }
        
        if json_data:
            kwargs["json"] = json_data
        if files:
            kwargs["files"] = files
        if stream:
            kwargs["timeout"] = None
        
        if stream:
            return await self._stream_request(method, path, **kwargs)
        
        response = await self._client.request(method.value, path, **kwargs)
        
        try:
            data = response.json()
            return ApiResponse(
                code=data.get("code", response.status_code),
                message=data.get("message", ""),
                data=data.get("data"),
                total=data.get("total"),
                timestamp=data.get("timestamp")
            )
        except json.JSONDecodeError:
            return ApiResponse(
                code=response.status_code,
                message=response.text,
                data=None
            )
    
    async def _stream_request(
        self,
        method: HttpMethod,
        path: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式请求"""
        async with self._client.stream(method.value, path, **kwargs) as response:
            async for line in response.aiter_lines():
                yield line
    
    # ============ 便捷方法 ============
    
    async def get(
        self,
        path: str,
        params: Optional[Dict] = None,
        token: Optional[str] = None
    ) -> ApiResponse:
        """GET请求"""
        return await self.request(HttpMethod.GET, path, params=params, token=token)
    
    async def post(
        self,
        path: str,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        token: Optional[str] = None
    ) -> ApiResponse:
        """POST请求"""
        return await self.request(HttpMethod.POST, path, json_data=json_data, files=files, token=token)
    
    async def put(
        self,
        path: str,
        json_data: Optional[Dict] = None,
        token: Optional[str] = None
    ) -> ApiResponse:
        """PUT请求"""
        return await self.request(HttpMethod.PUT, path, json_data=json_data, token=token)
    
    async def delete(
        self,
        path: str,
        params: Optional[Dict] = None,
        token: Optional[str] = None
    ) -> ApiResponse:
        """DELETE请求"""
        return await self.request(HttpMethod.DELETE, path, params=params, token=token)


# ============ 使用示例 ============

async def example_usage():
    """使用示例"""
    
    # 1. 登录获取Token
    async with SpringBootClient() as client:
        response = await client.post(
            "/auth/login",
            json_data={"username": "admin", "password": "123456"}
        )
        if response.is_success:
            token = response.data.get("token")
            print(f"登录成功，Token: {token}")
    
    # 2. 使用Token调用其他接口
    async with SpringBootClient(token=token) as client:
        # 获取用户信息
        user_info = await client.get("/auth/user-info")
        print(f"用户信息: {user_info.data}")
        
        # 获取合同列表
        contracts = await client.get("/contract/list", params={"page": 1, "pageSize": 10})
        print(f"合同列表: {contracts.data}")
        
        # 搜索法条（无需认证）
        laws = await client.get("/knowledge/laws/search", params={"keyword": "合同"})
        print(f"法条搜索结果: {laws.data}")
```

## 5. 注意事项

### 5.1 认证方式

- 所有需要认证的接口都需要在请求头中携带 `Authorization: Bearer {token}`
- Token通过登录接口获取，有效期1小时（可通过配置调整）
- Token过期后可使用 `refresh-token` 接口刷新

### 5.2 文件上传

- 文件上传使用 `multipart/form-data` 格式
- 单个文件大小限制：50MB
- 批量上传文件总大小限制：100MB
- 支持的合同文件格式：PDF、DOCX、DOC、TXT

### 5.3 SSE流式接口

- 审查进度和智能客服消息接口使用SSE（Server-Sent Events）流式输出
- 需要设置 `Accept: text/event-stream` 请求头
- 建议设置较长的超时时间或不设置超时
- 响应格式：`data: {json数据}\n\n`

### 5.4 错误处理

```python
async def handle_api_error(response: ApiResponse):
    """处理API错误"""
    if not response.is_success:
        if response.code == 401:
            raise Exception("未授权，请重新登录")
        elif response.code == 403:
            raise Exception("无权限访问该资源")
        elif response.code == 404:
            raise Exception("请求的资源不存在")
        elif response.code == 500:
            raise Exception(f"服务器错误: {response.message}")
        else:
            raise Exception(f"请求失败: {response.message} (code: {response.code})")
```

### 5.5 依赖安装

```bash
pip install httpx
```

### 5.6 环境变量配置建议

```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置"""
    # SpringBoot服务配置
    SPRINGBOOT_BASE_URL: str = "http://localhost:8080/api"
    SPRINGBOOT_TIMEOUT: float = 30.0
    
    # FastAPI服务配置
    FASTAPI_HOST: str = "127.0.0.1"
    FASTAPI_PORT: int = 8001
    
    class Config:
        env_file = ".env"

settings = Settings()
```
