"""
审查 API 路由
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status, Request
from fastapi.responses import StreamingResponse

from 合同审查.app.schemas.enums import ReviewStatus, ReviewStage, RiskLevel, RiskType
from 合同审查.app.schemas.models import (
    Result,
    ReviewOptions,
    ReviewProgress,
    ReviewResult,
    RiskItem,
    RelatedLaw,
    LocationVO,
)
from 合同审查.app.services import get_review_task_service, ReviewWorker
from 合同审查.app.utils import (
    sanitize_filename,
    validate_file_extension,
    parse_json_options,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# 初始化服务
task_service = get_review_task_service()
review_worker = ReviewWorker(task_service)


@router.post("/start")
async def start_review(
        request: Request,
        contract_id: int = Form(..., description="合同ID", gt=0),
        file: Optional[UploadFile] = File(None, description="合同文件(PDF/DOCX/TXT)"),
        review_options: Optional[str] = Form(None, description="审查选项(JSON)")
) -> Result:
    """
    发起合同审查 - 异步执行

    该接口会立即返回，审查任务在后台异步执行。
    使用返回的 reviewId 查询进度和结果。

    Args:
        contract_id: 合同ID（必须大于0）
        file: 合同文件，支持 pdf/docx/txt 格式
        review_options: 审查选项JSON字符串

    Returns:
        包含 reviewId 的响应结果

    Example:
        ```
        POST /api/v1/review/start
        Form Data:
            contract_id: 123
            file: [合同文件.pdf]
            review_options: {"checkLegalRisk": true}

        Response:
        {
            "code": 200,
            "data": {
                "reviewId": "REVABC123DEF",
                "contractId": 123,
                "status": "processing",
                "message": "审查任务已启动"
            }
        }
        ```
    """
    # 从请求头中获取 Authorization
    authorization = request.headers.get("Authorization")
    logger.info(f"收到审查请求，contract_id: {contract_id}, authorization: {authorization}")
    
    # TODO: 可以在这里添加 authorization 验证逻辑
    
    # 1. 参数验证
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传合同文件"
        )

    # 2. 生成唯一审查ID（使用自增整数）
    review_id = contract_id

    # 3. 解析审查选项
    options = parse_json_options(
        review_options,
        model_class=ReviewOptions,
        default=ReviewOptions
    )
    logger.info(f"创建审查任务 - review_id: {review_id}, contract_id: {contract_id}")

    # 4. 清理文件名并验证
    safe_filename = sanitize_filename(file.filename)
    file_ext = validate_file_extension(safe_filename)

    # 5. 读取文件内容（必须在异步任务启动前读取）
    try:
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件内容为空"
            )
        if len(file_content) > 50 * 1024 * 1024:  # 50MB 限制
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小超过50MB限制"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件读取失败"
        )

    # 6. 创建任务记录
    task_service.create_task(
        review_id=review_id,
        contract_id=contract_id,
        file_name=safe_filename,
        file_type=file_ext,
        review_options=options.model_dump()
    )

    # 7. 启动异步审查任务（不等待完成）
    await review_worker.start_review(
        review_id=review_id,
        contract_id=contract_id,
        file_content=file_content,
        file_name=safe_filename,
        file_type=file_ext,
        review_options=options.model_dump()
    )

    logger.info(f"审查任务已启动: {review_id}")

    # 8. 立即返回
    return Result(
        data={
            "reviewId": review_id,
            "contractId": contract_id,
            "status": ReviewStatus.PROCESSING,
            "message": "审查任务已启动，请使用 reviewId 查询进度"
        }
    )


@router.get("/{review_id}/progress")
async def get_review_progress(
    request: Request,
    review_id: int
) -> Result:
    """
    获取审查进度

    Args:
        review_id: 审查任务ID

    Returns:
        当前进度信息
    """
    # 从请求头中获取 Authorization
    authorization = request.headers.get("Authorization")
    logger.debug(f"获取审查进度，review_id: {review_id}, authorization: {authorization}")
    
    task = task_service.get_task(review_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审查任务不存在"
        )

    # 计算预计剩余时间
    estimated_remaining = None
    if task.status == ReviewStatus.PROCESSING and task.processed_clauses > 0:
        # 简单估算：假设每个条款处理时间相同
        avg_time_per_clause = 0.5  # 秒
        remaining_clauses = task.total_clauses - task.processed_clauses
        estimated_remaining = int(remaining_clauses * avg_time_per_clause)

    progress = ReviewProgress(
        review_id=review_id,
        status=task.status,
        stage=task.stage,
        progress=task.progress,
        message=task.message,
        total_clauses=task.total_clauses,
        processed_clauses=task.processed_clauses,
        estimated_remaining_seconds=estimated_remaining
    )

    return Result(data=progress)


@router.get("/{review_id}/result")
async def get_review_result(
    request: Request,
    review_id: int
) -> Result:
    """
    获取审查结果
    Args:
        review_id: 审查任务ID

    Returns:
        审查结果（仅在状态为 completed 时返回完整结果）
    """
    # 从请求头中获取 Authorization
    authorization = request.headers.get("Authorization")
    logger.debug(f"获取审查结果，review_id: {review_id}, authorization: {authorization}")
    
    task = task_service.get_task(review_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审查任务不存在"
        )

    if task.status == ReviewStatus.PROCESSING:
        return Result(
            code=400,
            message=f"审查进行中，当前进度: {task.progress}%",
            data={
                "status": task.status,
                "progress": task.progress,
                "stage": task.stage
            }
        )

    if task.status == ReviewStatus.FAILED:
        return Result(
            code=500,
            message=f"审查失败: {task.message}",
            data={"status": task.status}
        )

    if task.status == ReviewStatus.CANCELLED:
        return Result(
            code=400,
            message="审查已取消",
            data={"status": task.status}
        )

    # 计算风险统计
    risk_summary = {"high": 0, "medium": 0, "low": 0, "none": 0}
    for item in task.risk_items:
        level = item.get("risk_level", "none")
        if level in risk_summary:
            risk_summary[level] += 1

    # 处理风险项，确保包含必要字段并符合 RiskItem 类型
    processed_risks = []
    for item in task.risk_items:
        # 处理 related_laws，确保是 RelatedLaw 对象列表格式
        raw_related_laws = item.get("related_laws", item.get("relatedLaws", []))
        processed_related_laws = []
        for law in raw_related_laws:
            if isinstance(law, str):
                # 如果是字符串，转换为 RelatedLaw 对象
                processed_related_laws.append(RelatedLaw(
                    law_id=0,
                    law_name="",
                    article_no="",
                    content=law
                ))
            elif isinstance(law, dict):
                # 如果已经是字典，转换为 RelatedLaw 对象
                processed_related_laws.append(RelatedLaw(
                    law_id=law.get("law_id", 0),
                    law_name=law.get("law_name", ""),
                    article_no=law.get("article_no", ""),
                    content=law.get("content", "")
                ))
            else:
                # 其他情况，尝试获取属性
                processed_related_laws.append(RelatedLaw(
                    law_id=getattr(law, 'law_id', 0),
                    law_name=getattr(law, 'law_name', ""),
                    article_no=getattr(law, 'article_no', ""),
                    content=getattr(law, 'content', str(law))
                ))

        # 处理 risk_type，转换为字符串值
        raw_risk_type = item.get("risk_type", "legal_risk")
        if isinstance(raw_risk_type, RiskType):
            risk_type = raw_risk_type.value
        elif isinstance(raw_risk_type, str):
            risk_type = raw_risk_type.lower()
        else:
            risk_type = "legal_risk"

        # 处理 risk_level，转换为字符串值
        raw_risk_level = item.get("risk_level", "medium")
        if isinstance(raw_risk_level, RiskLevel):
            risk_level = raw_risk_level.value
        elif isinstance(raw_risk_level, str):
            risk_level = raw_risk_level.lower()
        else:
            risk_level = "medium"

        # 处理 location (paragraph_index) - 转换为 LocationVO 对象
        location_val = item.get("paragraph_index", item.get("paragraphIndex", 0))
        location_obj = LocationVO(
            paragraph_index=location_val if isinstance(location_val, int) else 0,
            start_offset=0,
            end_offset=0,
            text=item.get("clause_content", item.get("clauseContent", ""))
        )

        # 创建 RiskItem 对象
        processed_item = RiskItem(
            id=item.get("id"),
            risk_type=risk_type,
            level=risk_level,
            clause=item.get("clause_title", item.get("clauseTitle", "未知条款")),
            clause_content=item.get("clause_content", item.get("clauseContent", "")),
            description=item.get("risk_description", item.get("riskDescription", "")),
            suggestion=item.get("suggestion", ""),
            law_references=processed_related_laws,
            location=location_obj
        )
        processed_risks.append(processed_item)

    # 处理 status，转换为字符串值
    if isinstance(task.status, ReviewStatus):
        status_str = task.status.value
    else:
        status_str = str(task.status)

    # 创建 ReviewResult 对象
    overall_score = int(task.average_score) if task.average_score is not None else calculate_score(risk_summary)
    result = ReviewResult(
        review_id=review_id,
        review_no=str(review_id),  # 转换为字符串
        contract_id=task.contract_id,
        status=status_str,
        overall_score=overall_score,
        conclusion=generate_conclusion(risk_summary),
        risk_summary=risk_summary,
        risks=processed_risks
    )
    logger.debug(f"审查结果: {result.model_dump_json()}")
    return Result(data=result)


# @router.post("/{review_id}/re-review")
# async def re_review(review_id: int) -> Result:
#     """
#     重新审查任务
#
#     重置任务状态并重新开始审查流程。
#
#     Args:
#         review_id: 审查任务ID
#
#     Returns:
#         重新审查结果
#     """
#     task = task_service.get_task(review_id)
#
#     if not task:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="审查任务不存在"
#         )
#
#     # 重置任务状态
#     task_service.update_task_status(
#         review_id,
#         status=ReviewStatus.PENDING,
#         stage=ReviewStage.PARSING,
#         progress=0,
#         message="准备重新审查...",
#         processed_clauses=0
#     )
#
#     # 重新启动审查任务
#     try:
#         # 重新读取文件内容（从存储中获取）
#         # 这里简化处理，实际应该从文件存储中读取
#         await review_worker.start_review(
#             review_id=review_id,
#             contract_id=task.contract_id,
#             file_content=b"",  # 需要从存储中读取
#             file_name=task.file_name,
#             file_type=task.file_type,
#             review_options=task.review_options if hasattr(task, 'review_options') else {}
#         )
#
#         return Result(
#             data={
#                 "review_id": review_id,
#                 "contract_id": task.contract_id,
#                 "status": ReviewStatus.PROCESSING,
#                 "message": "重新审查任务已启动"
#             }
#         )
#     except Exception as e:
#         logger.error(f"重新审查失败: {e}")
#         return Result(
#             code=500,
#             message=f"重新审查失败: {str(e)}",
#             data={"review_id": review_id}
#         )
#

@router.post("/{review_id}/cancel")
async def cancel_review(review_id: int) -> Result:
    """
    取消审查任务

    Args:
        review_id: 审查任务ID

    Returns:
        取消结果
    """
    task = task_service.get_task(review_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审查任务不存在"
        )

    if task.status in [ReviewStatus.COMPLETED, ReviewStatus.CANCELLED]:
        return Result(
            code=400,
            message=f"任务已{task.status.value}，无法取消",
            data={"review_id": review_id, "status": task.status}
        )

    if task.status == ReviewStatus.FAILED:
        return Result(
            code=400,
            message="任务已失败，无需取消",
            data={"review_id": review_id, "status": task.status}
        )

    # 执行取消
    success = await review_worker.cancel_review(review_id)

    if success:
        return Result(
            data={
                "review_id": review_id,
                "status": ReviewStatus.CANCELLED,
                "message": "任务已取消"
            }
        )
    else:
        return Result(
            code=500,
            message="取消任务失败",
            data={"review_id": review_id}
        )


def calculate_score(risk_summary: dict) -> int:
    """根据风险统计计算综合评分"""
    base_score = 100
    base_score -= risk_summary.get("high", 0) * 15
    base_score -= risk_summary.get("medium", 0) * 8
    base_score -= risk_summary.get("low", 0) * 3
    return max(0, base_score)


def generate_conclusion(risk_summary: dict) -> str:
    """生成审查结论"""
    high = risk_summary.get("high", 0)
    medium = risk_summary.get("medium", 0)
    low = risk_summary.get("low", 0)

    if high > 0:
        return f"发现 {high} 个高风险项，建议重点关注并修改"
    elif medium > 0:
        return f"发现 {medium} 个中风险项，建议审查确认"
    elif low > 0:
        return f"发现 {low} 个低风险项，整体风险可控"
    else:
        return "未发现明显风险，合同条款基本合规"


@router.get("/{review_id}/progress/stream")
async def stream_review_progress(review_id: int):
    """
    SSE 流式获取审查进度

    用于前端实时推送进度更新，替代轮询。

    Args:
        review_id: 审查任务ID

    Returns:
        SSE 流，每秒推送一次进度更新

    Example:
        ```javascript
        const eventSource = new EventSource('/api/v1/review/REV123/progress/stream');
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log(`进度: ${data.progress}%`);
        };
        ```
    """

    async def event_generator():
        """生成 SSE 事件"""
        while True:
            task = task_service.get_task(review_id)

            if not task:
                # 任务不存在，发送错误并结束
                yield f"event: error\ndata: {json.dumps({'error': '任务不存在'})}\n\n"
                break

            # 构建进度数据
            data = {
                "review_id": review_id,
                "status": task.status.value if isinstance(task.status, ReviewStatus) else task.status,
                "stage": task.stage.value if isinstance(task.stage, ReviewStage) else task.stage,
                "progress": task.progress,
                "message": task.message,
                "total_clauses": task.total_clauses,
                "processed_clauses": task.processed_clauses,
            }

            # 发送数据
            yield f"data: {json.dumps(data)}\n\n"

            # 检查是否完成或失败
            if task.status in [ReviewStatus.COMPLETED, ReviewStatus.FAILED, ReviewStatus.CANCELLED]:
                # 发送结束标记
                yield f"event: complete\ndata: {json.dumps({'status': task.status.value if isinstance(task.status, ReviewStatus) else task.status})}\n\n"
                break

            # 等待1秒后再次检查
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )
