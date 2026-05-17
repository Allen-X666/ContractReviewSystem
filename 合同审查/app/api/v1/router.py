from fastapi import APIRouter

from 合同审查.app.api.v1.endpoints import chat_bot, health, laws, review, system_document

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, prefix="/health", tags=["health"])
api_v1_router.include_router(review.router, prefix="/review", tags=["review"])
api_v1_router.include_router(laws.router, prefix="/laws", tags=["laws"])
api_v1_router.include_router(chat_bot.router, prefix="/chatbot", tags=["chat_bot"])
api_v1_router.include_router(system_document.router, prefix="/system-docs", tags=["system_document"])
