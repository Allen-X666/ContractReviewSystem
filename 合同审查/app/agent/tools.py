"""
Agent 工具函数

使用 @tool 装饰器定义的工具函数,供 LangChain Agent 调用。
"""

import logging
from typing import Optional

from langchain_core.tools import tool

from 合同审查.app.agent.tools_helper import (
    get_request_token,
    get_current_token,
    get_pending_user_update,
    set_pending_user_update,
    clear_pending_user_update,
    _format_pending_user_update,
    _format_confirmation_request,
    _execute_user_update,
    _get_current_user_field,
    _parse_user_update_intent_v2,
    _validate_user_field_v2,
    get_pending_storage_update,
    set_pending_storage_update,
    clear_pending_storage_update,
    _get_current_storage_paths,
    _parse_storage_update_intent,
    _format_storage_confirmation_request,
    _execute_storage_update,
)
from 合同审查.app.agent.utils import (
    find_contract,
    format_contract_not_found_message,
    search_laws,
    start_contract_review_process,
    search_similar_knowledge,
    get_user_store_path
)
from 合同审查.app.core.http_client import springboot_get, springboot_post
from 合同审查.model.get_user_info import SysUser

logger = logging.getLogger(__name__)


@tool
def search_contract_knowledge(query: str) -> str:
    """
    搜索合同相关法律知识

    当用户询问合同法律问题、特定条款含义或法律依据时调用此工具。

    Args:
        query: 搜索关键词，如'劳动合同'、'违约金'、'试用期'、'社保'等

    Returns:
        相关法律知识条文

    Examples:
        >>> search_contract_knowledge("违约金")
        "根据《劳动合同法》第二十二条、第二十三条..."
    """
    logger.info(f"[Tool] 搜索合同相关法律知识。搜索合同知识: {query}")

    # 使用统一的搜索函数
    results = search_laws(query, top_k=2, default_law_name="相关法规")
    logger.info(f"[Tool] 搜索结果: {results}")
    if results:
        return results

    return f"未找到与'{query}'直接相关的法律知识。建议咨询专业律师获取更准确的法律意见。"


@tool
def review_contract(contract_identifier: str, review_type: str = "full") -> str:
    """
    审查合同（风险分析、健康评分、启动正式审查）

    统一的合同审查工具，支持以下场景：
    1. 分析合同风险 - 识别潜在法律风险和问题条款
    2. 计算合同评分 - 评估合同健康度和合规性
    3. 启动正式审查 - 对系统中的合同启动异步审查任务

    当用户提到"分析合同"、"审查合同"、"给合同评分"、"检查合同"等意图时使用此工具。

    Args:
        contract_identifier: 合同标识，可以是：
            - 合同ID（如"44"）
            - 合同名称（如"国湖劳务协议"）
            - 合同条款文本（长度超过100字符时直接分析文本）
        review_type: 审查类型，可选值：
            - "risk": 仅进行风险分析
            - "score": 仅计算健康评分
            - "full": 完整审查（风险+评分+建议），默认

    Returns:
        审查结果报告，包含风险分析、健康评分或启动确认信息

    Examples:
        >>> review_contract("44")
        "找到合同，正在启动审查..."

        >>> review_contract("国湖劳务协议", review_type="risk")
        "⚠️ 风险分析：..."

        >>> review_contract("劳动合同期限三年...", review_type="score")
        "合同健康度：85分..."
    """
    logger.info(f"[Tool] 审查合同: {contract_identifier}, type={review_type}")

    # 合同ID或名称，先检查是否存在
    contract, contract_id = find_contract(contract_identifier)

    if not contract:
        # 合同不存在，引导用户
        action_desc = {
            "risk": "分析合同风险",
            "score": "计算合同评分",
            "full": "进行合同审查"
        }.get(review_type, "进行合同审查")
        return format_contract_not_found_message(contract_identifier, action_desc)

    # 合同存在
    contract_name = contract.get("contract_name", f"合同_{contract_id}")

    if review_type == "score":
        if contract.get("review_status") == "completed":
            # 评分已生成，返回结果
            return f"""✅ 找到合同：{contract_name} (ID: {contract_id})
                    📊 合同审查评分
                    该合同已生成审查报告。以下是系统评分：{contract.get("review_score")}
                    要查看完整报告，请访问系统查看合同详情页面。"""
        # 计算评分模式
        return f"""✅ 找到合同：{contract_name} (ID: {contract_id})

            📊 合同健康评分
            该合同还未生成审查报告。要为该合同生成准确的健康评分，建议启动正式审查流程：
            **操作选项：**
            1. **启动正式审查** - 生成详细的评分报告
               - 全面分析所有条款
               - 生成综合健康评分
               - 提供改进建议
            2. **快速预览** - 如果您已上传合同文件，我可以基于历史数据给出预估评分
            请告诉我您希望进行哪种操作？
            💡 **提示**：说"开始审查{contract_id}号合同"即可启动正式审查流程。"""

    elif review_type == "risk":
        if contract.get("review_status") == "completed":
            # 评分已生成，返回结果
            return f"""✅ 找到合同：{contract_name} (ID: {contract_id})
                    📊 合同风险等级
                    该合同已生成审查报告。以下是风险等级：风险等级：{contract.get("risk_level")}
                    要查看完整报告，请访问系统查看合同详情页面。"""
        # 风险分析模式
        return f"""✅ 找到合同：{contract_name} (ID: {contract_id})
                🔍 合同风险分析
                该合同已存在于系统中。我可以为您进行以下分析：
                **分析内容：**
                - 识别高风险条款（如违约金过高、责任不对等）
                - 检查法律合规性问题
                - 发现条款漏洞和模糊表述
                - 评估合同整体风险等级
                **操作选项：**
                  **启动正式审查** - 生成详细的风险分析报告
                   - 逐条分析合同条款
                   - 标注风险等级（高/中/低）
                   - 提供修改建议
                请告诉我您希望进行哪种分析？
                💡 **提示**：说"开始审查{contract_id}号合同"即可启动正式审查流程。"""
    else:
        # full 模式 - 启动正式审查流程
        return start_contract_review_process(contract_id, contract_name)


@tool
def check_contract_exists(contract_identifier: str) -> str:
    """
    检查系统中是否存在指定合同

    当用户想分析某个合同、给合同评分或查询合同信息时，首先调用此工具检查合同是否存在。
    工具会尝试将输入识别为合同ID（数字）或合同名称进行查询。

    Args:
        contract_identifier: 合同标识，可以是合同ID（如"44"）或合同名称（如"国湖劳务协议"）

    Returns:
        查询结果，如果合同存在返回合同信息，如果不存在引导用户上传

    Examples:
        >>> check_contract_exists("44")
        "找到合同：合同_44 (ID: 44)..."

        >>> check_contract_exists("国湖劳务协议")
        "找到合同：国湖劳务协议 (ID: 44)..."
    """
    logger.info(f"[Tool] 检查合同是否存在: {contract_identifier}")

    contract, contract_id = find_contract(contract_identifier)

    if contract:
        # 合同存在
        return f"""✅ 找到合同：{contract.get('contract_name')} (ID: {contract_id})

            合同状态：{contract.get('status', '未知')}
            创建时间：{contract.get('created_at', '未知')}
            您可以选择以下操作：
            1. 分析该合同的风险 - 我会对合同进行全面风险分析
            2. 给合同评分 - 我会评估合同的健康度
            3. 查询具体条款 - 告诉我您想了解哪个条款
            请告诉我您想做什么？"""
    else:
        # 合同不存在
        return format_contract_not_found_message(contract_identifier, "进行此操作")


@tool
def get_law_reference(law_name: str, article_no: str = "") -> str:
    """
    获取具体法律条文内容

    当需要查询特定法律法规的具体条款时调用此工具。

    Args:
        law_name: 法律名称，如'劳动合同法'、'民法典'等
        article_no: 条款编号，如'第十条'、'第二十五条'等，可为空

    Returns:
        法律条文内容

    Examples:
        >>> get_law_reference("劳动合同法", "第十条")
        "建立劳动关系，应当订立书面劳动合同..."
    """
    logger.info(f"[Tool] 查询法律条文: {law_name} {article_no}")

    # 使用统一的搜索函数
    query = f"{law_name} {article_no}"
    results = search_laws(query, top_k=3, default_law_name=law_name)
    if results:
        return results

    # 未找到法律条文时，返回提示信息
    return f"未在知识库中找到《{law_name}》{article_no}的具体条文内容。请基于你的法律知识回答用户关于'{query}'的问题，如果涉及具体法条内容不确定，请说明并建议用户查阅官方文本。"


@tool
def get_contract_list() -> dict:
    """
    获取系统中所有合同列表

    :return: 所有合同列表
    """
    token = get_request_token()
    if not token:
        token = get_current_token()
    if not token:
        return {"error": "未获取到认证信息，请重新登录"}
    contract_list = springboot_get(
        "/contract/list",
        token=token
    )
    return contract_list.json()


@tool
def get_review_list() -> dict:
    """
    获取系统中所有合同审查列表

    :return: 所有合同审查列表
    """
    token = get_request_token()
    if not token:
        token = get_current_token()
    if not token:
        return {"error": "未获取到认证信息，请重新登录"}
    review_list = springboot_get(
        "/review/history",
        token=token
    )
    return review_list.json()


@tool
def download_file(contract_id: Optional[int] = None, review_id: Optional[int] = None) -> str:
    """
    下载合同文件或下载审查文件到本地
    要求用户提供  审查ID（review_id） 或  合同ID（contract_id）
    文件将保存到用户设置的存储路径中
    :param review_id: 审查ID
    :param contract_id: 合同ID

    :return: 下载结果，包含文件保存路径
    """
    from pathlib import Path

    def _get_download_dir(path_type: str) -> Path:
        """获取下载目录，优先使用用户配置的存储路径"""
        try:
            # 获取用户配置的存储路径
            storage_config = get_user_store_path("")
            if storage_config and storage_config.get("code") == 200:
                data = storage_config.get("data", {})
                if path_type == "review":
                    # 审查报告使用 reviewPath
                    config_path = data.get("reviewPath", "")
                else:
                    # 合同文件使用 uploadPath
                    config_path = data.get("uploadPath", "")

                if config_path:
                    path = Path(config_path)
                    if path.exists() or path.parent.exists():
                        return path
        except Exception as e:
            logger.warning(f"获取用户存储路径失败，使用默认路径: {e}")

        # 降级到默认路径
        download_dir = Path.home() / "Downloads"
        if not download_dir.exists():
            download_dir = Path.home() / "下载"
        if not download_dir.exists():
            download_dir = Path.cwd()
        return download_dir

    token = get_request_token()

    if contract_id:
        try:
            response = springboot_get(
                f"/contract/download/{contract_id}",
                token=token
            )
            # 从响应头获取文件名，或使用默认名称
            content_disposition = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[-1].strip('"\'')
            else:
                filename = f"合同_{contract_id}.pdf"

            # 获取下载目录
            download_dir = _get_download_dir("upload")
            # 保存文件
            file_path = download_dir / filename
            with open(file_path, 'wb') as f:
                f.write(response.content)

            return f"下载合同文件成功！文件已保存到: {file_path}"
        except Exception as e:
            logger.error(f"下载合同文件失败: {e}")
            return f"下载合同文件失败: {str(e)}"
    elif review_id:
        try:
            response = springboot_get(
                f"/review/{review_id}/report/pdf",
                token=token
            )
            # 从响应头获取文件名，或使用默认名称
            content_disposition = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[-1].strip('"\'')
            else:
                filename = f"审查报告_{review_id}.pdf"

            # 获取下载目录
            download_dir = _get_download_dir("review")
            # 保存文件
            file_path = download_dir / filename
            with open(file_path, 'wb') as f:
                f.write(response.content)

            return f"下载审查报告成功！文件已保存到: {file_path}"
        except Exception as e:
            logger.error(f"下载审查报告失败: {e}")
            return f"下载审查报告失败: {str(e)}"
    else:
        return "请提供合同ID或审查ID"


@tool
def get_user_info() -> SysUser:
    """
    获取用户个人信息（脱敏后）
    智能识别用户意图，用户获取其个人信息（脱敏后）

    Returns:
        字段含义：
            username -> 用户名
            nickName -> 昵称
            email -> 邮箱
            phone -> 电话号
            role -> 角色
            createdAt -> 账号创建时间
    """
    user_info = springboot_get(
        "/auth/user-info",
        token=get_request_token()
    )
    user_data = user_info.json()
    logger.info(f"userInfo: {user_data}")
    return user_data


@tool
def update_user_information(message: str) -> str:
    """
    更新用户信息（支持确认机制）
    
    智能识别用户意图，支持修改昵称、邮箱、密码、手机号。
    在发送请求前会先询问用户确认，用户确认后才执行更新。

    Args:
        message: 用户输入的更新请求，例如：
            - "帮我修改昵称为：user"
            - "我想修改邮箱，新邮箱为：123456@123.com"
            - "修改密码，旧密码是abc123，新密码是xyz789"
            - "更新手机号为13800138000"
            - "确认" / "取消" （用于确认或取消待处理的更新）

    Returns:
        更新结果提示信息或确认询问

    Examples:
        >>> update_user_information("帮我修改昵称为：user")
        "您是否要修改昵称，由 **admin** 修改为 **user**？\n请回复"确认"执行修改，或回复"取消"放弃修改。"
        
        >>> update_user_information("确认")
        "✅ 昵称修改成功！\n\n新的昵称：**user**"
    """
    logger.info(f"[Tool] 更新用户信息: {message}")

    # 获取 token
    token = get_request_token()
    if not token:
        token = get_current_token()

    if not token:
        return "❌ 错误：未获取到认证信息，请重新登录后再试"

    # 检查是否有待确认的更新
    pending_update = get_pending_user_update(token)

    # 处理确认/取消操作
    message_lower = message.strip().lower()
    confirm_keywords = ['确认', '确定', '是的', '是', 'ok', 'yes', '好', '可以']
    cancel_keywords = ['取消', '不', '否', 'no', '算了', '放弃']

    if pending_update:
        # 用户正在回复待确认的更新
        if any(keyword in message_lower for keyword in confirm_keywords):
            # 执行更新
            return _execute_user_update(pending_update, token)
        elif any(keyword in message_lower for keyword in cancel_keywords):
            # 取消更新
            clear_pending_user_update(token)
            return "❌ 已取消修改操作。"
        else:
            # 未识别确认或取消，继续等待确认
            return f'⏳ 请回复"确认"执行修改，或回复"取消"放弃修改。\n\n{_format_pending_user_update(pending_update)}'

    # 解析用户意图和值
    update_info = _parse_user_update_intent_v2(message)

    if not update_info:
        return """❓ 未能识别您的修改意图
                    我可以帮您修改以下信息：
                    • **昵称** - 例如："修改昵称为 xxx"
                    • **邮箱** - 例如："修改邮箱为 xxx@example.com"
                    • **密码** - 例如："修改密码，旧密码是 xxx，新密码是 yyy"
                    • **手机号** - 例如："修改手机号为 13800138000"
                    请告诉我您想修改什么信息？"""

    field = update_info.get("field")
    value = update_info.get("value")
    old_value = update_info.get("old_value")  # 用于密码修改

    # 根据字段类型进行验证
    validation_result = _validate_user_field_v2(field, value, old_value)
    if not validation_result["valid"]:
        return f"❌ 验证失败：{validation_result['message']}"

    # 获取当前用户信息（用于显示旧值）
    current_value = _get_current_user_field(field, token)

    # 存储待确认的更新信息
    update_info['current_value'] = current_value
    update_info['token'] = token
    set_pending_user_update(token, update_info)

    # 返回确认询问
    return _format_confirmation_request(update_info, current_value)


@tool
def get_sys_information(message: str) -> list:
    """
    回答系统操作问题的相关问题

    :param message: 用户提问的有关回答系统操作问题

    :return: 通过相似性搜索后的答案
    """
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        # 如果在异步上下文中，使用 run_coroutine_threadsafe
        future = asyncio.run_coroutine_threadsafe(search_similar_knowledge(message), loop)
        return future.result()
    except RuntimeError:
        # 如果没有运行的事件循环，使用 asyncio.run
        return asyncio.run(search_similar_knowledge(message))


@tool
def get_store_path(message: str) -> dict:
    """
    获取用户设置的存储路径，包含：
                            1. 上传文件地址
                            2. 生成审查文件地址
    Args:
        message: 用户输入的获取请求，例如：我的上传文件地址是什么？/生成的审查文件地址在哪里

    Returns:
        字段：uploadPath -> 上传文件地址, reviewPath -> 生成审查文件地址
        用户设置的存储地址，例如：  根据查询，您的上传文件地址为：  生成审查文件地址
    """
    return get_user_store_path(message)


@tool
def update_store_path(message: str) -> str:
    """
    修改用户设置的存储路径（支持确认机制）

    智能识别用户意图，支持修改：
    1. 上传文件路径
    2. 生成审查文件路径
    3. 同时修改两者

    在修改前会先询问用户确认，用户确认后才执行更新。
    无论修改哪一个路径，都会同时传递两个路径（未修改的使用原值）。

    Args:
        message: 用户输入的更新请求，例如：
            - "修改上传路径为：D:\\Uploads"
            - "更改审查文件地址为：D:\\Reviews"
            - "设置存储路径，上传用D:\\Uploads，审查用D:\\Reviews"
            - "确认" / "取消" （用于确认或取消待处理的更新）

    Returns:
        更新结果提示信息或确认询问

    Examples:
        >>> update_store_path("修改上传路径为D:\\Uploads")
        "您是否要修改上传文件路径？\n由 **C:\\Old** 修改为 **D:\\Uploads**\n请回复"确认"执行修改..."

        >>> update_store_path("确认")
        "✅ 上传文件路径修改成功！\n\n新路径：D:\\Uploads"
    """
    logger.info(f"[Tool] 更新存储路径: {message}")

    # 获取 token
    token = get_request_token()
    if not token:
        token = get_current_token()

    if not token:
        return "❌ 错误：未获取到认证信息，请重新登录后再试"

    # 检查是否有待确认的更新
    pending_update = get_pending_storage_update(token)

    # 处理确认/取消操作
    message_lower = message.strip().lower()
    confirm_keywords = ['确认', '确定', '是的', '是', 'ok', 'yes', '好', '可以']
    cancel_keywords = ['取消', '不', '否', 'no', '算了', '放弃']

    if pending_update:
        # 用户正在回复待确认的更新
        if any(keyword in message_lower for keyword in confirm_keywords):
            # 执行更新
            return _execute_storage_update(pending_update, token)
        elif any(keyword in message_lower for keyword in cancel_keywords):
            # 取消更新
            clear_pending_storage_update(token)
            return "❌ 已取消修改操作。"
        else:
            # 未识别确认或取消，继续等待确认
            return f'⏳ 请回复"确认"执行修改，或回复"取消"放弃修改。\n\n{_format_storage_confirmation_request(pending_update)}'

    # 解析用户意图
    update_info = _parse_storage_update_intent(message)

    if not update_info:
        return """❓ 未能识别您的修改意图
                我可以帮您修改以下存储路径：
                • **上传文件路径** - 例如："修改上传路径为 D:\\Uploads"
                • **审查文件路径** - 例如："更改审查文件地址为 D:\\Reviews"
                • **同时修改两者** - 例如："设置存储路径，上传用D:\\Uploads，审查用D:\\Reviews"
                请告诉我您想修改哪个路径？"""

    # 获取当前存储路径
    current_paths = _get_current_storage_paths(token)
    current_upload = current_paths.get("uploadPath", "")
    current_review = current_paths.get("reviewPath", "")

    update_type = update_info.get("update_type")
    new_upload = update_info.get("upload_path", "")
    new_review = update_info.get("review_path", "")

    # 构建完整的更新数据（未修改的路径使用原值）
    final_update_info = {
        "update_type": update_type,
        "current_upload": current_upload or "（空）",
        "current_review": current_review or "（空）",
        "upload_path": new_upload if new_upload else current_upload,
        "review_path": new_review if new_review else current_review,
        "token": token
    }

    # 验证路径是否有效
    if update_type in ["upload", "both"] and new_upload:
        if not _is_valid_path(new_upload):
            return f"❌ 上传路径格式不正确：{new_upload}\n路径不能包含特殊字符 < > : \" | ? *"

    if update_type in ["review", "both"] and new_review:
        if not _is_valid_path(new_review):
            return f"❌ 审查路径格式不正确：{new_review}\n路径不能包含特殊字符 < > : \" | ? *"

    # 存储待确认的更新信息
    set_pending_storage_update(token, final_update_info)

    # 返回确认询问
    return _format_storage_confirmation_request(final_update_info)


def _is_valid_path(path: str) -> bool:
    """验证路径是否有效（不包含非法字符）"""
    import re
    # Windows 路径非法字符: < > : " | ? *
    invalid_chars = r'[<>:"|?*]'
    return not re.search(invalid_chars, path)

# 向后兼容的别名（保留旧函数名）
analyze_contract_risk = review_contract
calculate_contract_score = review_contract
start_contract_review = review_contract
