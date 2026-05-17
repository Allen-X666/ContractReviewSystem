import logging
import os

from fastapi import APIRouter, UploadFile, File, Form, Request

from 合同审查.app.schemas.models import (
    Result,
)
from 合同审查.app.services.law_upload_service import law_upload_service

router = APIRouter()
logger = logging.getLogger(__name__)

# 启动上传服务
law_upload_service.start()


@router.post("/upload")
async def upload_law_document(
    request: Request,
    file: UploadFile = File(..., description="法律文档文件"),
    document_type: str = Form(..., description="文档类型"),
    effective_date: str = Form(None, description="生效日期"),
    description: str = Form(None, description="文档说明"),
):
    """
    上传法律文档（异步处理）

    上传后会立即返回任务ID，实际处理在后台进行。
    使用 /upload/{task_id}/status 接口查询处理进度。
    """
    # 从请求头中获取 Authorization
    authorization = request.headers.get("Authorization")
    logger.info(f"收到法律文档上传请求，文件名: {file.filename}, authorization: {authorization}")
    
    # TODO: 可以在这里添加 authorization 验证逻辑
    
    try:
        # ========== 1. 验证文件 ==========
        allowed_extensions = {".pdf", ".doc", ".docx", ".md"}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return Result(code=400, message=f"不支持的文件格式，仅支持: {', '.join(allowed_extensions)}")

        # 验证文件大小（50MB）
        file_content = await file.read()
        if len(file_content) > 50 * 1024 * 1024:
            return Result(code=400, message="文件大小超过限制（50MB）")

        # ========== 2. 创建异步任务 ==========
        task_id = law_upload_service.create_task(
            file_name=file.filename,
            file_content=file_content,
            file_ext=file_ext,
            document_type=document_type,
            effective_date=effective_date,
            description=description,
        )

        logger.info(f"法律文档上传任务已创建: {task_id}")

        return Result(
            code=200,
            message="法律文档上传任务已创建，正在后台处理",
            data={
                "task_id": task_id,
                "file_name": file.filename,
                "document_type": document_type,
                "status": "pending",
                "message": "任务已创建，正在等待处理",
            }
        )

    except Exception as e:
        logger.error(f"创建上传任务失败: {str(e)}", exc_info=True)
        return Result(code=500, message=f"创建上传任务失败: {str(e)}")


@router.get("/upload/{task_id}/status")
async def get_upload_status(task_id: str):
    """获取上传任务状态"""
    try:
        task = law_upload_service.get_task(task_id)
        if not task:
            return Result(code=404, message="任务不存在")

        return Result(
            code=200,
            message="获取任务状态成功",
            data=task.to_dict()
        )

    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}", exc_info=True)
        return Result(code=500, message=f"获取任务状态失败: {str(e)}")


@router.get("/upload/tasks")
async def list_upload_tasks():
    """获取所有上传任务列表"""
    try:
        tasks = []
        with law_upload_service.tasks_lock:
            for task in law_upload_service.tasks.values():
                tasks.append(task.to_dict())

        # 按创建时间倒序排序
        tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return Result(
            code=200,
            message="获取任务列表成功",
            data={
                "total": len(tasks),
                "tasks": tasks
            }
        )

    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}", exc_info=True)
        return Result(code=500, message=f"获取任务列表失败: {str(e)}")
#
#
# @router.get("/documents")
# async def list_law_documents(
#     document_type: str = None,
#     page: int = 1,
#     page_size: int = 10,
# ):
#     """获取法律文档列表"""
#     # 过滤文档
#     filtered_docs = law_documents_db
#     if document_type:
#         filtered_docs = [doc for doc in filtered_docs if doc.document_type == document_type]
#
#     # 按上传时间倒序排序
#     sorted_docs = sorted(filtered_docs, key=lambda x: x.upload_time, reverse=True)
#
#     # 分页
#     total = len(sorted_docs)
#     start_idx = (page - 1) * page_size
#     end_idx = start_idx + page_size
#     page_docs = sorted_docs[start_idx:end_idx]
#
#     return Result(
#         data={
#             "total": total,
#             "page": page,
#             "page_size": page_size,
#             "documents": page_docs,
#         }
#     )
#
#
# @router.get("/documents/{doc_id}")
# async def get_law_document(doc_id: int):
#     """获取法律文档详情"""
#     for doc in law_documents_db:
#         if doc.id == doc_id:
#             return Result(data=doc)
#     return Result(code=404, message="文档不存在")
#
#
# @router.get("/documents/{doc_id}/download")
# async def download_law_document(doc_id: int):
#     """下载法律文档"""
#     for doc in law_documents_db:
#         if doc.id == doc_id:
#             if not os.path.exists(doc.file_path):
#                 return Result(code=404, message="文件不存在")
#             return FileResponse(
#                 path=doc.file_path,
#                 filename=doc.name,
#                 media_type="application/octet-stream",
#             )
#     return Result(code=404, message="文档不存在")
#
#
# @router.delete("/documents/{doc_id}")
# async def delete_law_document(doc_id: int):
#     """删除法律文档"""
#     for i, doc in enumerate(law_documents_db):
#         if doc.id == doc_id:
#             # 删除文件
#             if os.path.exists(doc.file_path):
#                 os.remove(doc.file_path)
#             # 删除记录
#             law_documents_db.pop(i)
#             return Result(message="文档删除成功")
#     return Result(code=404, message="文档不存在")
#
#
# @router.post("/search")
# async def search_laws(request: LawSearchRequest):
#     """搜索法条"""
#     result = LawSearchResult(
#         category_id="contract",
#         category_name="合同法",
#         laws=[],
#     )
#     return Result(data={"total": 50, "results": [result]})
#
#
# @router.get("/{law_id}")
# async def get_law_detail(law_id: int):
#     """获取法条详情"""
#     from datetime import date, datetime
#
#     law = LawRegulationDetail(
#         id=law_id,
#         law_no="主席令15届第45号",
#         name="中华人民共和国民法典",
#         category=LawCategory.CONTRACT,
#         issuer="全国人民代表大会",
#         publish_date=date(2020, 5, 28),
#         effective_date=date(2021, 1, 1),
#         status="有效",
#         description="民法典合同编相关规定",
#         content="法规全文...",
#         article_count=526,
#         is_new=True,
#         articles=[],
#         created_at=datetime.now(),
#     )
#     return Result(data=law)
#
#
# @router.get("/categories")
# async def get_law_categories():
#     """获取法条分类列表"""
#     categories: List[LawCategoryInfo] = [
#         LawCategoryInfo(id="contract", name="合同法", count=150),
#         LawCategoryInfo(id="labor", name="劳动法", count=80),
#         LawCategoryInfo(id="intellectual_property", name="知识产权", count=60),
#         LawCategoryInfo(id="company", name="公司法", count=120),
#         LawCategoryInfo(id="civil", name="民法", count=200),
#         LawCategoryInfo(id="criminal", name="刑法", count=50),
#     ]
#     return Result(data=categories)
#
#
# @router.post("/match")
# async def match_laws(clause_content: str, contract_type: str = "purchase", top_k: int = 5):
#     """智能匹配法条"""
#     matches: List[LawMatchResult] = [
#         LawMatchResult(
#             law_id=101,
#             law_name="中华人民共和国民法典",
#             article_no="第509条",
#             content="当事人应当按照约定全面履行自己的义务...",
#             relevance_score=0.95,
#         ),
#         LawMatchResult(
#             law_id=101,
#             law_name="中华人民共和国民法典",
#             article_no="第577条",
#             content="当事人一方不履行合同义务或者履行合同义务不符合约定的...",
#             relevance_score=0.88,
#         ),
#     ]
#     return Result(data=LawMatchResponse(matches=matches))
