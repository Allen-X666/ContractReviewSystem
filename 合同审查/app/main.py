import os

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from 合同审查.app.api.v1.router import api_v1_router
from 合同审查.app.core.config import settings
from 合同审查.app.core.database import get_db_health
from 合同审查.app.services.warmup_service import get_warmup_service

# 配置 HuggingFace 环境变量（使用 settings 配置）
os.environ["HF_ENDPOINT"] = settings.HF_ENDPOINT
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1" if settings.HF_HUB_DISABLE_SYMLINKS_WARNING else "0"
os.environ["HUGGINGFACE_HUB_CACHE"] = settings.HF_HUB_CACHE
os.environ["TRANSFORMERS_CACHE"] = settings.HF_HUB_CACHE


def setup_logging():
    """配置日志输出到控制台"""
    # 创建日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 清除现有的处理器
    root_logger.handlers = []

    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # 设置特定模块的日志级别
    logging.getLogger("合同审查").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    return root_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    在应用启动时执行预热，在关闭时清理资源
    """
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("应用启动中...")
    logger.info("=" * 50)

    # 启动后台预热任务
    warmup_service = get_warmup_service()
    asyncio.create_task(warmup_service.warmup())
    logger.info("服务预热任务已在后台启动")

    yield  # 应用运行期间

    # 应用关闭时清理资源
    logger.info("=" * 50)
    logger.info("应用关闭中...")
    logger.info("=" * 50)


def create_application() -> FastAPI:
    """创建FastAPI应用实例"""

    # 设置日志
    setup_logging()

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.APP_DEBUG,
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        lifespan=lifespan,  # 使用 lifespan 管理应用生命周期
    )

    # 配置CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册API路由
    application.include_router(api_v1_router, prefix=settings.API_PREFIX)

    return application


app = create_application()


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to Contract Review AI Service",
        "version": settings.APP_VERSION,
        "docs_url": f"{settings.API_PREFIX}/docs",
    }


@app.get("/health")
async def health_check():
    """
    基础健康检查接口

    返回服务基本状态，不检查依赖服务
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/ready")
async def readiness_check():
    """
    就绪检查接口

    检查服务是否已完成预热，可以接收流量。
    负载均衡器应使用此接口判断服务是否就绪。

    Returns:
        - 200: 服务已就绪
        - 503: 服务未就绪（正在预热或预热失败）
    """
    from fastapi.responses import JSONResponse

    warmup_service = get_warmup_service()
    readiness = warmup_service.readiness

    # 获取数据库健康状态
    db_health = get_db_health()

    response_data = {
        "ready": readiness.ready and db_health["connected"],
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "warmup": warmup_service.get_readiness_report(),
        "database": db_health
    }

    # 如果未就绪，返回 503
    if not response_data["ready"]:
        return JSONResponse(
            status_code=503,
            content=response_data
        )

    return response_data


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8001)
