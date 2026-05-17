"""
Agent 工具辅助函数

提供工具函数内部使用的辅助函数，不直接暴露给 Agent。
"""
import json
import logging
from typing import Dict, Any, Optional, Tuple

from redis import Redis
from sqlalchemy import true

from 合同审查.app.core.config import settings
from 合同审查.app.core.database import SessionLocal
from 合同审查.app.core.http_client import springboot_post, springboot_get, springboot_post_multipart
from 合同审查.app.rag import get_system_retriever
from 合同审查.app.rag.retriever import get_law_retriever
from 合同审查.app.services.contract_service import ContractService
from 合同审查.app.utils.context import get_current_token
from 合同审查.app.agent.tools_helper import get_request_token

logger = logging.getLogger(__name__)


def _create_contract_service_with_redis() -> ContractService:
    """
    创建带有 Redis 缓存的 ContractService 实例

    Returns:
        ContractService 实例（带 Redis 缓存）
    """
    try:
        # 创建同步 Redis 客户端
        redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True,  # 返回字符串而不是字节
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        # 测试连接
        redis_client.ping()
        logger.info(f"ContractService Redis 连接成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        return ContractService(redis_client=redis_client)
    except Exception as e:
        logger.warning(f"ContractService Redis 连接失败，将使用无缓存模式: {e}")
        return ContractService(redis_client=None)


# 创建带 Redis 缓存的 ContractService 实例
contract_service = _create_contract_service_with_redis()


def find_contract(contract_identifier: str, token: Optional[str] = None) -> Tuple[
    Optional[Dict[str, Any]], Optional[int]]:
    """
    根据合同标识查找合同

    尝试将输入识别为合同ID（数字）或合同名称进行查询。
    优先使用传入的token，否则从上下文获取。

    Args:
        contract_identifier: 合同标识，可以是合同ID或合同名称
        token: JWT Token，为None时从上下文获取

    Returns:
        Tuple[合同信息字典, 合同ID]，如果未找到返回 (None, None)
    """
    # 获取token
    if token is None:
        token = get_current_token()

    if not token:
        logger.warning("find_contract: 未获取到认证token")
        return None, None

    contract = None
    contract_id = None
    db = SessionLocal()

    try:
        # 尝试解析为合同ID（纯数字）
        if contract_identifier.isdigit():
            contract_id = int(contract_identifier)
            contract = contract_service.get_contract_by_id(contract_id=contract_id, db=db)
        else:
            contract = contract_service.get_contract_by_name(contract_name=contract_identifier, db=db)
            if contract and isinstance(contract, dict):
                contract_id = contract.get('id')
    except Exception as e:
        logger.error(f"查找合同失败: {e}")
        return None, None
    finally:
        db.close()

    return contract, contract_id


def format_contract_not_found_message(identifier: str, action: str = "操作") -> str:
    """
    格式化合同未找到的提示信息

    Args:
        identifier: 合同标识
        action: 用户想要执行的操作描述

    Returns:
        格式化的提示信息
    """
    return f"""❌ 未找到合同：{identifier}

            系统中没有找到该合同。如果您想{action}，可以选择：

            1. **上传合同文件** - 如果您有合同文件（PDF/DOCX/TXT格式），请先上传合同
            2. **提供合同文本** - 直接粘贴合同的条款文本，我可以直接分析
            3. **检查输入** - 请确认合同ID或名称是否正确

            请告诉我您想怎么做？"""


def search_laws(query: str, top_k: int = 3, default_law_name: str = "相关法规") -> str:
    """
    搜索法律条文

    Args:
        query: 搜索查询
        top_k: 返回结果数量
        default_law_name: 默认法律名称

    Returns:
        格式化的搜索结果，如果未找到返回空字符串
    """
    try:
        retriever = get_law_retriever()
        if retriever:
            results = retriever.retrieve(query, top_k=top_k)
            if results:
                return "\n\n".join([
                    f"【{r.metadata.get('law_name', default_law_name)} - {r.clause_no}】\n{r.clause_content}"
                    for r in results
                ])
    except Exception as e:
        logger.warning(f"RAG 检索失败: {e}")

    return ""


def start_contract_review_process(contract_id: int, contract_name: str, token: Optional[str] = None) -> str:
    """
    启动合同审查流程
    调用 SpringBoot 后端接口启动异步审查任务

    Args:
        contract_id: 合同ID
        contract_name: 合同名称
        token: JWT Token，为None时从上下文获取

    Returns:
        审查启动结果信息
    """
    logger.info(f"[Tool] 启动合同审查流程: {contract_id}, {contract_name}")
    if token is None:
        token = get_current_token()
    if not token:
        return "❌ 错误：未获取到认证信息，请重新登录后再试"
    review_options = {
        "checkInvalidClause": True,
        "checkMissingClause": True,
        "checkUnreasonableClause": True,
        "checkLegalRisk": True
    }
    try:
        data = {
            "contractId": str(contract_id),
            "reviewOptions": json.dumps(review_options)
        }

        # 调用接口获取合同文件
        logger.info(f"[Tool] 获取合同文件: contractId={contract_id}")
        file_response = springboot_get(
            f"/contract/file/{contract_id}",
            token=token
        )
        file_response.raise_for_status()

        # 从响应头获取文件名
        content_disposition = file_response.headers.get('Content-Disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[-1].strip('"\'')
        else:
            filename = f"contract_{contract_id}.pdf"

        # 获取文件内容类型
        content_type = file_response.headers.get('Content-Type', 'application/pdf')

        # 封装为 Multipart 格式
        files = {
            "file": (filename, file_response.content, content_type)
        }

        logger.info(f"[Tool] 发送 multipart 请求，contractId={contract_id}, filename={filename}")

        response = springboot_post_multipart(
            "/review/start",
            token=token,
            data=data,
            files=files
        )
    except Exception as e:
        logger.error(f"启动合同审查失败: {e}")
        return f"❌ 启动合同审查失败：{str(e)}"

    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 200:
            review_id = result.get("data", {}).get("reviewId")
            return f"""✅ 已启动合同审查
                        合同：{contract_name} (ID: {contract_id})
                        审查ID：{review_id}
                        系统正在对合同进行全面审查，包括：
                        • 法律合规性检查
                        • 风险条款识别
                        • 健康度评分
                        • 改进建议生成
                        审查完成后您可以在系统中查看详细报告。
                        💡 提示：您可以说"查看{contract_id}号合同的审查进度"了解审查状态。"""
        else:
            return f"❌ 启动审查失败：{result.get('message', '未知错误')}"
    else:
        return f"❌ 启动审查失败：HTTP {response.status_code}"


def search_similar_knowledge(message) -> list:
    """
    回答系统操作问题的相关问题

    :param message: 用户提问的有关回答系统操作问题

    :return: 通过相似性搜索后的答案
    """
    system_retriever = get_system_retriever()
    system_results = system_retriever.retrieve(message, top_k=3)
    return system_results


def get_user_store_path(message) -> dict:
    """
    获取用户设置的存储路径，包含：
                            1. 上传文件地址
                            2. 生成审查文件地址
    Args:
        message: 用户输入的获取请求

    Returns:
        字段：uploadPath -> 上传文件地址, reviewPath -> 生成审查文件地址
    """
    # 优先使用 request_token（在 Agent 上下文中设置）
    token = get_request_token()
    if not token:
        # 降级使用 context token
        token = get_current_token()

    if not token:
        return {"code": 401, "message": "未获取到认证信息", "data": None}

    try:
        response = springboot_get(
            f"/system/config/storage",
            token=token
        )
        return response.json()
    except Exception as e:
        logger.error(f"获取存储路径失败: {e}")
        return {"code": 500, "message": f"获取失败: {str(e)}", "data": None}