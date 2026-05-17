from fastapi import APIRouter
from 合同审查.app.schemas.enums import ReviewStage, ReviewStatus
from 合同审查.app.schemas.models import Result

router = APIRouter()


@router.get("")
async def health_check():
    """服务健康检查"""
    return Result(
        data={
            "status": "healthy",
            "stage": ReviewStage.PARSING,
            "status_enum": ReviewStatus.COMPLETED,
        }
    )
