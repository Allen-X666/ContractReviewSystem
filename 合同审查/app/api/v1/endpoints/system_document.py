import logging
import os

from fastapi import APIRouter, UploadFile, File, Form, Request

from 合同审查.app.schemas.models import Result
from 合同审查.app.services.system_ops_upload_service import system_ops_upload_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.on_event("startup")
async def startup_event():
    """启动时初始化上传服务"""
    system_ops_upload_service.start()
    logger.info("系统文档上传服务已启动")


@router.on_event("shutdown")
async def shutdown_event():
    """关闭时停止上传服务"""
    system_ops_upload_service.stop()
    logger.info("系统文档上传服务已停止")


@router.post("/upload")
async def upload_system_document(
        request: Request,
        file: UploadFile = File(..., description="系统文档文件"),
        category: str = Form(..., description="文档类型"),
        description: str = Form(..., description="文档说明")
):
    """
    上传系统操作文档
    支持格式: .doc, .docx, .md
    文件大小限制: 50MB
    """
    # 从请求头中获取 Authorization
    authorization = request.headers.get("Authorization")
    logger.info(f"收到系统文档上传请求，文件名: {file.filename}, authorization: {authorization}")
    
    # TODO: 可以在这里添加 authorization 验证逻辑
    
    try:
        allowed_extensions = {".doc", ".docx", ".md"}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return Result(
                code=400,
                message=f"不支持的文件格式，仅支持: {', '.join(allowed_extensions)}"
            )
        file_content = await file.read()
        if len(file_content) > 50 * 1024 * 1024:
            return Result(
                code=400,
                message="文件大小超过限制（50MB）"
            )
        task_id = system_ops_upload_service.create_task(
            file_name=file.filename,
            file_content=file_content,
            file_ext=file_ext,
            category=category,
            description=description,
        )
        logger.info(f"系统文档上传任务已创建: {task_id}, 文件名: {file.filename}")
        return Result(
            code=200,
            message="系统文档上传任务已创建，正在后台处理",
            data={
                "task_id": task_id,
                "file_name": file.filename,
                "category": category,
                "status": "pending",
                "message": "任务已创建，正在等待处理",
            }
        )
    except Exception as e:
        logger.error(f"创建系统文档上传任务失败: {str(e)}", exc_info=True)
        return Result(
            code=500,
            message=f"创建上传任务失败: {str(e)}"
        )
