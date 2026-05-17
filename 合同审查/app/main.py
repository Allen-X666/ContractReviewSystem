import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HUGGINGFACE_HUB_CACHE"] = r"D:\huggingface\cache"
os.environ["TRANSFORMERS_CACHE"] = r"D:\huggingface\cache"

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from 合同审查.app.api.v1.router import api_v1_router
from 合同审查.app.core.config import settings


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
    """健康检查接口"""
    return {"status": "healthy", "service": settings.APP_NAME}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8001)
