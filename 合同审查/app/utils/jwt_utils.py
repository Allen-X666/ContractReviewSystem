"""
JWT Token 提取和解析工具

用于从Authorization头中提取和解析JWT Token
"""

import base64
import json
from typing import Optional, Dict, Any
from datetime import datetime


def extract_token_from_header(authorization: Optional[str]) -> Optional[str]:
    """
    从Authorization头中提取Token

    Args:
        authorization: Authorization头值，格式如 "Bearer eyJhbGci..."

    Returns:
        提取的Token字符串，如果不存在则返回None

    Example:
        >>> token = extract_token_from_header("Bearer eyJhbGciOiJIUzI1NiJ9...")
        >>> print(token)
        eyJhbGciOiJIUzI1NiJ9...
    """
    if not authorization:
        return None

    # 去除首尾空格
    authorization = authorization.strip()

    # 检查是否以Bearer开头
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()

    return None


def decode_jwt_payload(token: str) -> Optional[Dict[str, Any]]:
    """
    解码JWT Token的Payload部分（不验证签名）

    Args:
        token: JWT Token字符串

    Returns:
        解码后的Payload字典，如果解码失败则返回None

    Example:
        >>> payload = decode_jwt_payload("eyJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOjks...")
        >>> print(payload)
        {'userId': 9, 'role': 'ADMIN', 'username': 'admin', 'exp': 1778922538}
    """
    if not token:
        return None

    try:
        # JWT格式: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            return None

        payload_base64 = parts[1]

        # 处理Base64填充
        padding_needed = 4 - len(payload_base64) % 4
        if padding_needed != 4:
            payload_base64 += "=" * padding_needed

        # 解码Payload
        payload_bytes = base64.urlsafe_b64decode(payload_base64)
        payload_json = payload_bytes.decode("utf-8")
        payload = json.loads(payload_json)

        # 将role的值转换为小写
        if "role" in payload and isinstance(payload["role"], str):
            payload["role"] = payload["role"].lower()

        return payload
    except Exception:
        return None


def parse_token(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    从Authorization头中提取并解析JWT Token

    Args:
        authorization: Authorization头值

    Returns:
        解析后的Token信息字典，包含token字符串和payload

    Example:
        >>> result = parse_token("Bearer eyJhbGciOiJIUzI1NiJ9...")
        >>> print(result)
        {
            'token': 'eyJhbGciOiJIUzI1NiJ9...',
            'payload': {'userId': 9, 'role': 'ADMIN', 'username': 'admin', 'exp': 1778922538},
            'user_id': 9,
            'username': 'admin',
            'role': 'ADMIN',
            'exp': 1778922538,
            'is_expired': False
        }
    """
    token = extract_token_from_header(authorization)
    if not token:
        return None

    payload = decode_jwt_payload(token)
    if not payload:
        return None

    # 检查是否过期
    exp = payload.get("exp")
    is_expired = False
    if exp:
        try:
            exp_timestamp = int(exp)
            is_expired = datetime.now().timestamp() > exp_timestamp
        except (ValueError, TypeError):
            pass

    return {
        "token": token,
        "payload": payload,
        "user_id": payload.get("userId"),
        "username": payload.get("username"),
        "role": payload.get("role"),
        "exp": payload.get("exp"),
        "is_expired": is_expired
    }


def get_user_id_from_token(authorization: Optional[str]) -> Optional[int]:
    """
    从Authorization头中提取用户ID

    Args:
        authorization: Authorization头值

    Returns:
        用户ID，如果提取失败则返回None
    """
    result = parse_token(authorization)
    if result and not result.get("is_expired"):
        return result.get("user_id")
    return None


def get_username_from_token(authorization: Optional[str]) -> Optional[str]:
    """
    从Authorization头中提取用户名

    Args:
        authorization: Authorization头值

    Returns:
        用户名，如果提取失败则返回None
    """
    result = parse_token(authorization)
    if result and not result.get("is_expired"):
        return result.get("username")
    return None


def get_role_from_token(authorization: Optional[str]) -> Optional[str]:
    """
    从Authorization头中提取用户角色

    Args:
        authorization: Authorization头值

    Returns:
        用户角色，如果提取失败则返回None
    """
    result = parse_token(authorization)
    if result and not result.get("is_expired"):
        role = result.get("role")
        return role.lower() if role else None
    return None
