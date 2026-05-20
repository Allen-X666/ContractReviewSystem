"""
Agent 工具辅助函数 (异步版本)

提供工具函数内部使用的辅助函数，不直接暴露给 Agent。
"""

import asyncio
import json
import logging
import re
from typing import Optional, Dict, Any

import redis.asyncio as aioredis

from 合同审查.app.core.config import settings
from 合同审查.app.core.http_client import async_springboot_get, async_springboot_post, async_springboot_put
from 合同审查.app.utils import get_current_token

logger = logging.getLogger(__name__)

# 异步 Redis 客户端（用于存储待确认的更新状态）
_async_redis_client: Optional[aioredis.Redis] = None


async def _get_async_redis_client() -> Optional[aioredis.Redis]:
    """获取异步 Redis 客户端"""
    global _async_redis_client
    if _async_redis_client is None:
        try:
            _async_redis_client = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )
            # 测试连接
            await _async_redis_client.ping()
            logger.info("异步 Redis 连接成功")
        except Exception as e:
            logger.warning(f"异步 Redis 连接失败: {e}")
            _async_redis_client = None
    return _async_redis_client


def _get_pending_key(token: str) -> str:
    """获取待确认更新的 Redis key"""
    # 使用 token 的哈希值作为 key 的一部分
    import hashlib
    token_hash = hashlib.md5(token.encode()).hexdigest()[:8]
    return f"pending_user_update:{token_hash}"


# 全局变量存储当前请求的 token（用于工具函数）
_current_request_token: Optional[str] = None

# 内存存储（当 Redis 不可用时降级使用）
_pending_user_updates: Dict[str, Dict[str, Any]] = {}
_pending_storage_updates: Dict[str, Dict[str, Any]] = {}


def set_request_token(token: Optional[str]) -> None:
    """设置当前请求的 token（供工具使用）"""
    global _current_request_token
    _current_request_token = token


def get_request_token() -> Optional[str]:
    """获取当前请求的 token"""
    global _current_request_token
    return _current_request_token


def clear_request_token() -> None:
    """清除当前请求的 token"""
    global _current_request_token
    _current_request_token = None


async def set_pending_user_update(token: str, update_info: Optional[Dict[str, Any]]) -> None:
    """设置待确认的用户更新信息（使用 Redis 存储，异步版本）"""
    if not update_info:
        return
    
    redis_client = await _get_async_redis_client()
    if redis_client:
        key = _get_pending_key(token)
        await redis_client.setex(key, 300, json.dumps(update_info))  # 5分钟过期
        logger.info(f"已存储待确认更新到 Redis: {key}")
    else:
        # 降级到内存存储
        _pending_user_updates[token] = update_info
        logger.info(f"已存储待确认更新到内存: {token}")


async def get_pending_user_update(token: str) -> Optional[Dict[str, Any]]:
    """获取待确认的用户更新信息（优先从 Redis 获取，异步版本）"""
    redis_client = await _get_async_redis_client()
    if redis_client:
        key = _get_pending_key(token)
        data = await redis_client.get(key)
        if data:
            logger.info(f"从 Redis 获取待确认更新: {key}")
            return json.loads(data)
    
    # 降级到内存存储
    return _pending_user_updates.get(token)


async def clear_pending_user_update(token: str) -> None:
    """清除待确认的用户更新信息（异步版本）"""
    redis_client = await _get_async_redis_client()
    if redis_client:
        key = _get_pending_key(token)
        await redis_client.delete(key)
        logger.info(f"已清除 Redis 中的待确认更新: {key}")
    
    # 清除内存存储
    if token in _pending_user_updates:
        del _pending_user_updates[token]


def _format_pending_user_update(pending_update: Dict[str, Any]) -> str:
    """格式化待确认的更新信息"""
    field_name = pending_update.get('field_name', '')
    current_value = pending_update.get('current_value', '（空）')
    new_value = pending_update.get('value', '')

    return f"待修改的{field_name}：\n由 **{current_value}** 修改为 **{new_value}**"


def _format_confirmation_request(update_info: Dict[str, Any], current_value: str) -> str:
    """格式化确认请求"""
    field_name = update_info.get('field_name', '')
    new_value = update_info.get('value', '')

    return f'您是否要修改{field_name}，由 **{current_value or "（空）"}** 修改为 **{new_value}**？\n\n请回复"**确认**"执行修改，或回复"**取消**"放弃修改。'


async def _execute_user_update(update_info: Dict[str, Any], token: str) -> str:
    """执行用户更新操作（异步版本）"""

    field = update_info.get("field")
    value = update_info.get("value")
    old_value = update_info.get("old_value")
    field_name = update_info.get("field_name")

    try:
        if field == "password":
            # 修改密码 - POST /auth/change-password
            update_data = {
                "oldPassword": old_value,
                "newPassword": value,
                "confirmPassword": value  # 确认密码与新密码相同
            }

            response = await async_springboot_post(
                "/auth/change-password",
                token=token,
                json_data=update_data
            )
        else:
            # 修改昵称、邮箱、手机号 - PUT /user/profile
            update_data = {}
            if field == "nickName":
                update_data["nickName"] = value
            elif field == "email":
                update_data["email"] = value
            elif field == "phone":
                update_data["phone"] = value

            response = await async_springboot_put(
                "/user/profile",
                token=token,
                json_data=update_data
            )

        # 清除待确认的更新
        await clear_pending_user_update(token)

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                return f"✅ {field_name}修改成功！\n\n新的{field_name}：**{value}**"
            else:
                return f"❌ 修改失败：{result.get('message', '未知错误')}"
        else:
            return f"❌ 修改失败：HTTP {response.status_code}"

    except Exception as e:
        logger.error(f"更新用户信息失败: {e}")
        await clear_pending_user_update(token)
        return f"❌ 更新出错：{str(e)}"


async def _get_current_user_field(field: str, token: str) -> str:
    """获取当前用户的字段值（异步版本）"""
    try:
        response = await async_springboot_get("/user/profile", token=token)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                data = result.get("data", {})
                if field == "nickName":
                    return data.get("nickName", "")
                elif field == "email":
                    return data.get("email", "")
                elif field == "phone":
                    return data.get("phone", "")
                elif field == "password":
                    return "******"  # 密码不显示
    except Exception as e:
        logger.warning(f"获取当前用户信息失败: {e}")

    return ""


def _parse_user_update_intent_v2(message: str) -> Optional[Dict[str, Any]]:
    """
    解析用户更新意图（只支持昵称、邮箱、手机号、密码）
    
    Args:
        message: 用户输入
        
    Returns:
        解析结果，包含 field, field_name, value, old_value
    """
    message = message.strip().lower()

    # 昵称匹配模式（注意：不是用户名）
    nickname_patterns = [
        r'(?:修改|更改|更新|换|改成|设置为).{0,5}?昵称.{0,3}[:：是为]\s*(\S+)',
        r'昵称.{0,3}[:：是为]\s*(\S+)',
    ]

    # 邮箱匹配模式
    email_patterns = [
        r'(?:修改|更改|更新|换|改成|设置为).{0,5}?邮箱.{0,3}[:：是为]\s*([\w.-]+@[\w.-]+\.\w+)',
        r'(?:修改|更改|更新|换|改成|设置为).{0,5}?电子邮件.{0,3}[:：是为]\s*([\w.-]+@[\w.-]+\.\w+)',
        r'邮箱.{0,3}[:：是为]\s*([\w.-]+@[\w.-]+\.\w+)',
        r'([\w.-]+@[\w.-]+\.\w+)',  # 直接提取邮箱格式
    ]

    # 手机号匹配模式
    phone_patterns = [
        r'(?:修改|更改|更新|换|改成|设置为).{0,5}?手机.{0,3}[:：是为]\s*(1\d{10})',
        r'(?:修改|更改|更新|换|改成|设置为).{0,5}?电话.{0,3}[:：是为]\s*(1\d{10})',
        r'(?:修改|更改|更新|换|改成|设置为).{0,5}?手机号.{0,3}[:：是为]\s*(1\d{10})',
        r'手机.{0,3}[:：是为]\s*(1\d{10})',
        r'手机号.{0,3}[:：是为]\s*(1\d{10})',
    ]

    # 密码匹配模式（需要旧密码和新密码）
    password_patterns = [
        r'(?:修改|更改|更新|换|重置).{0,5}?密码.{0,10}旧密码.{0,3}[:：是为]\s*(\S+).{0,10}新密码.{0,3}[:：是为]\s*(\S+)',
        r'(?:修改|更改|更新|换|重置).{0,5}?密码.{0,10}原密码.{0,3}[:：是为]\s*(\S+).{0,10}新密码.{0,3}[:：是为]\s*(\S+)',
        r'密码.{0,10}旧[:：是为]\s*(\S+).{0,10}新[:：是为]\s*(\S+)',
    ]

    # 尝试匹配昵称
    for pattern in nickname_patterns:
        match = re.search(pattern, message)
        if match:
            return {
                "field": "nickName",
                "field_name": "昵称",
                "value": match.group(1).strip(),
                "old_value": None
            }

    # 尝试匹配邮箱
    for pattern in email_patterns:
        match = re.search(pattern, message)
        if match:
            return {
                "field": "email",
                "field_name": "邮箱",
                "value": match.group(1).strip(),
                "old_value": None
            }

    # 尝试匹配手机号
    for pattern in phone_patterns:
        match = re.search(pattern, message)
        if match:
            return {
                "field": "phone",
                "field_name": "手机号",
                "value": match.group(1).strip(),
                "old_value": None
            }

    # 尝试匹配密码
    for pattern in password_patterns:
        match = re.search(pattern, message)
        if match:
            return {
                "field": "password",
                "field_name": "密码",
                "old_value": match.group(1).strip(),
                "value": match.group(2).strip()
            }

    return None


# ==================== 存储路径更新相关函数 ====================

def _get_pending_storage_key(token: str) -> str:
    """获取待确认存储路径更新的 Redis key"""
    import hashlib
    token_hash = hashlib.md5(token.encode()).hexdigest()[:8]
    return f"pending_storage_update:{token_hash}"


async def set_pending_storage_update(token: str, update_info: Optional[Dict[str, Any]]) -> None:
    """设置待确认的存储路径更新信息（异步版本）"""
    if not update_info:
        return
    
    redis_client = await _get_async_redis_client()
    if redis_client:
        key = _get_pending_storage_key(token)
        await redis_client.setex(key, 300, json.dumps(update_info))  # 5分钟过期
        logger.info(f"已存储待确认存储路径更新到 Redis: {key}")
    else:
        # 降级到内存存储
        _pending_storage_updates[token] = update_info
        logger.info(f"已存储待确认存储路径更新到内存: {token}")


async def get_pending_storage_update(token: str) -> Optional[Dict[str, Any]]:
    """获取待确认的存储路径更新信息（异步版本）"""
    redis_client = await _get_async_redis_client()
    if redis_client:
        key = _get_pending_storage_key(token)
        data = await redis_client.get(key)
        if data:
            logger.info(f"从 Redis 获取待确认存储路径更新: {key}")
            return json.loads(data)
    # 降级到内存存储
    return _pending_storage_updates.get(token)


async def clear_pending_storage_update(token: str) -> None:
    """清除待确认的存储路径更新信息（异步版本）"""
    redis_client = await _get_async_redis_client()
    if redis_client:
        key = _get_pending_storage_key(token)
        await redis_client.delete(key)
        logger.info(f"已清除 Redis 中的待确认存储路径更新: {key}")
    # 清除内存存储
    if token in _pending_storage_updates:
        del _pending_storage_updates[token]


async def _get_current_storage_paths(token: str) -> Dict[str, str]:
    """获取当前用户的存储路径配置（异步版本）"""
    try:
        response = await async_springboot_get("/system/config/storage", token=token)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                data = result.get("data", {})
                return {
                    "uploadPath": data.get("uploadPath", ""),
                    "reviewPath": data.get("reviewPath", "")
                }
    except Exception as e:
        logger.warning(f"获取当前存储路径失败: {e}")
    return {"uploadPath": "", "reviewPath": ""}


def _parse_storage_update_intent(message: str) -> Optional[Dict[str, Any]]:
    """
    解析用户存储路径更新意图

    Args:
        message: 用户输入

    Returns:
        解析结果，包含 update_type, upload_path, review_path
        update_type: "upload" | "review" | "both"
    """
    message = message.strip().lower()

    # 上传路径匹配模式
    upload_patterns = [
        r'(?:修改|更改|更新|换|改成|设置).{0,5}?上传.{0,5}?(?:路径|地址|位置).{0,3}[:：是为]\s*(\S+)',
        r'(?:修改|更改|更新|换|改成|设置).{0,5}?上传文件.{0,5}?(?:路径|地址|位置).{0,3}[:：是为]\s*(\S+)',
        r'上传.{0,5}?(?:路径|地址|位置).{0,3}[:：是为]\s*(\S+)',
    ]

    # 审查路径匹配模式
    review_patterns = [
        r'(?:修改|更改|更新|换|改成|设置).{0,5}?(?:审查|生成|报告).{0,5}?(?:路径|地址|位置).{0,3}[:：是为]\s*(\S+)',
        r'(?:修改|更改|更新|换|改成|设置).{0,5}?(?:审查文件|生成文件|报告文件).{0,5}?(?:路径|地址|位置).{0,3}[:：是为]\s*(\S+)',
        r'(?:审查|生成).{0,5}?(?:路径|地址|位置).{0,3}[:：是为]\s*(\S+)',
    ]

    # 同时修改两者的模式
    both_patterns = [
        r'(?:修改|更改|更新|换|改成|设置).{0,5}?(?:存储|保存).{0,5}?(?:路径|地址|位置)',
        r'(?:修改|更改|更新).{0,5}?(?:所有|全部).{0,5}?(?:路径|地址)',
    ]

    result = {
        "update_type": None,
        "upload_path": None,
        "review_path": None
    }

    # 检查是否同时修改两者
    for pattern in both_patterns:
        if re.search(pattern, message):
            result["update_type"] = "both"
            break

    # 尝试匹配上传路径
    for pattern in upload_patterns:
        match = re.search(pattern, message)
        if match:
            result["upload_path"] = match.group(1).strip()
            if result["update_type"] is None:
                result["update_type"] = "upload"
            elif result["update_type"] == "review":
                result["update_type"] = "both"
            break

    # 尝试匹配审查路径
    for pattern in review_patterns:
        match = re.search(pattern, message)
        if match:
            result["review_path"] = match.group(1).strip()
            if result["update_type"] is None:
                result["update_type"] = "review"
            elif result["update_type"] == "upload":
                result["update_type"] = "both"
            break

    if result["update_type"] is None:
        return None

    return result


def _format_storage_confirmation_request(update_info: Dict[str, Any]) -> str:
    """格式化存储路径更新确认请求"""
    update_type = update_info.get("update_type")
    current_upload = update_info.get("current_upload", "（空）")
    current_review = update_info.get("current_review", "（空）")
    new_upload = update_info.get("upload_path", "")
    new_review = update_info.get("review_path", "")

    if update_type == "upload":
        return f'您是否要修改**上传文件路径**？\n\n由 **{current_upload}** 修改为 **{new_upload}**\n\n请回复"**确认**"执行修改，或回复"**取消**"放弃修改。'
    elif update_type == "review":
        return f'您是否要修改**审查文件路径**？\n\n由 **{current_review}** 修改为 **{new_review}**\n\n请回复"**确认**"执行修改，或回复"**取消**"放弃修改。'
    else:  # both
        changes = []
        if new_upload:
            changes.append(f'• 上传文件路径：由 **{current_upload}** 修改为 **{new_upload}**')
        if new_review:
            changes.append(f'• 审查文件路径：由 **{current_review}** 修改为 **{new_review}**')
        return f'您是否要修改以下存储路径？\n\n' + '\n'.join(changes) + '\n\n请回复"**确认**"执行修改，或回复"**取消**"放弃修改。'


async def _execute_storage_update(update_info: Dict[str, Any], token: str) -> str:
    """执行存储路径更新操作（异步版本）"""
    try:
        update_data = {
            "uploadPath": update_info.get("upload_path", ""),
            "reviewPath": update_info.get("review_path", "")
        }

        response = await async_springboot_post(
            "/system/config/storage",
            token=token,
            json_data=update_data
        )

        await clear_pending_storage_update(token)

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                update_type = update_info.get("update_type")
                if update_type == "upload":
                    return f"✅ 上传文件路径修改成功！\n\n新路径：**{update_data['uploadPath']}**"
                elif update_type == "review":
                    return f"✅ 审查文件路径修改成功！\n\n新路径：**{update_data['reviewPath']}**"
                else:
                    return f"✅ 存储路径修改成功！\n\n• 上传文件路径：**{update_data['uploadPath']}**\n• 审查文件路径：**{update_data['reviewPath']}**"
            else:
                return f"❌ 修改失败：{result.get('message', '未知错误')}"
        else:
            return f"❌ 修改失败：HTTP {response.status_code}"

    except Exception as e:
        logger.error(f"更新存储路径失败: {e}")
        await clear_pending_storage_update(token)
        return f"❌ 更新出错：{str(e)}"


def _validate_user_field_v2(field: str, value: str, old_value: str = None) -> Dict[str, Any]:
    """
    验证用户字段值（V2版本）
    
    Args:
        field: 字段名
        value: 新值
        old_value: 旧值（密码修改时需要）
        
    Returns:
        验证结果 {"valid": bool, "message": str}
    """
    if field == "nickName":
        if not value or len(value) < 2 or len(value) > 20:
            return {"valid": False, "message": "昵称长度应在2-20个字符之间"}
        if not re.match(r'^[\w\u4e00-\u9fa5]+$', value):
            return {"valid": False, "message": "昵称只能包含字母、数字、下划线和中文"}

    elif field == "email":
        if not re.match(r'^[\w.-]+@[\w.-]+\.\w+$', value):
            return {"valid": False, "message": "邮箱格式不正确"}

    elif field == "phone":
        if not re.match(r'^1\d{10}$', value):
            return {"valid": False, "message": "手机号格式不正确，应为11位数字"}

    elif field == "password":
        if not old_value:
            return {"valid": False, "message": "修改密码需要提供旧密码"}
        if not value or len(value) < 6:
            return {"valid": False, "message": "新密码长度至少为6位"}

    return {"valid": True, "message": "验证通过"}


def _validate_user_field(field: str, value: str, old_value: str = None) -> Dict[str, Any]:
    """
    验证用户字段值
    
    Args:
        field: 字段名
        value: 新值
        old_value: 旧值（密码修改时需要）
        
    Returns:
        验证结果 {"valid": bool, "message": str}
    """
    if field == "username":
        if not value or len(value) < 3 or len(value) > 20:
            return {"valid": False, "message": "用户名长度应在3-20个字符之间"}
        if not re.match(r'^[\w\u4e00-\u9fa5]+$', value):
            return {"valid": False, "message": "用户名只能包含字母、数字、下划线和中文"}

    elif field == "email":
        if not re.match(r'^[\w.-]+@[\w.-]+\.\w+$', value):
            return {"valid": False, "message": "邮箱格式不正确"}

    elif field == "phone":
        if not re.match(r'^1\d{10}$', value):
            return {"valid": False, "message": "手机号格式不正确，应为11位数字"}

    elif field == "password":
        if not old_value:
            return {"valid": False, "message": "修改密码需要提供旧密码"}
        if not value or len(value) < 6:
            return {"valid": False, "message": "新密码长度至少为6位"}

    return {"valid": True, "message": "验证通过"}


def _parse_user_update_intent(message: str) -> Optional[Dict[str, Any]]:
    """
    解析用户更新意图
    
    Args:
        message: 用户输入
        
    Returns:
        解析结果，包含 field, field_name, value, old_value
    """
    message = message.strip().lower()

    # 用户名匹配模式
    username_patterns = [
        r'(?:修改|更改|更新|换|改成|设置为).{0,5}?用户名.{0,3}[:：是为]\s*(\S+)',
        r'用户名.{0,3}[:：是为]\s*(\S+)',
    ]

    # 邮箱匹配模式
    email_patterns = [
        r'(?:修改|更改|更新|换|改成|设置为).{0,5}?邮箱.{0,3}[:：是为]\s*([\w.-]+@[\w.-]+\.\w+)',
        r'(?:修改|更改|更新|换|改成|设置为).{0,5}?电子邮件.{0,3}[:：是为]\s*([\w.-]+@[\w.-]+\.\w+)',
        r'邮箱.{0,3}[:：是为]\s*([\w.-]+@[\w.-]+\.\w+)',
        r'([\w.-]+@[\w.-]+\.\w+)',  # 直接提取邮箱格式
    ]

    # 手机号匹配模式
    phone_patterns = [
        r'(?:修改|更改|更新|换|改成|设置为).{0,5}?手机.{0,3}[:：是为]\s*(1\d{10})',
        r'(?:修改|更改|更新|换|改成|设置为).{0,5}?电话.{0,3}[:：是为]\s*(1\d{10})',
        r'(?:修改|更改|更新|换|改成|设置为).{0,5}?手机号.{0,3}[:：是为]\s*(1\d{10})',
        r'手机.{0,3}[:：是为]\s*(1\d{10})',
        r'手机号.{0,3}[:：是为]\s*(1\d{10})',
    ]

    # 密码匹配模式（需要旧密码和新密码）
    password_patterns = [
        r'(?:修改|更改|更新|换|重置).{0,5}?密码.{0,10}旧密码.{0,3}[:：是为]\s*(\S+).{0,10}新密码.{0,3}[:：是为]\s*(\S+)',
        r'(?:修改|更改|更新|换|重置).{0,5}?密码.{0,10}原密码.{0,3}[:：是为]\s*(\S+).{0,10}新密码.{0,3}[:：是为]\s*(\S+)',
        r'密码.{0,10}旧[:：是为]\s*(\S+).{0,10}新[:：是为]\s*(\S+)',
    ]

    # 尝试匹配用户名
    for pattern in username_patterns:
        match = re.search(pattern, message)
        if match:
            return {
                "field": "username",
                "field_name": "用户名",
                "value": match.group(1).strip(),
                "old_value": None
            }

    # 尝试匹配邮箱
    for pattern in email_patterns:
        match = re.search(pattern, message)
        if match:
            return {
                "field": "email",
                "field_name": "邮箱",
                "value": match.group(1).strip(),
                "old_value": None
            }

    # 尝试匹配手机号
    for pattern in phone_patterns:
        match = re.search(pattern, message)
        if match:
            return {
                "field": "phone",
                "field_name": "手机号",
                "value": match.group(1).strip(),
                "old_value": None
            }

    # 尝试匹配密码
    for pattern in password_patterns:
        match = re.search(pattern, message)
        if match:
            return {
                "field": "password",
                "field_name": "密码",
                "old_value": match.group(1).strip(),
                "value": match.group(2).strip()
            }

    return None
