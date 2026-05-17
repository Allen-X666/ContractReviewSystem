"""
应用配置文件

包含所有环境变量和配置项
"""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """应用配置类"""

    # 基础路径
    BASE_DIR = Path(__file__).parent
    APP_DIR = BASE_DIR / "app"
    DATA_DIR = BASE_DIR / "data"
    UPLOAD_DIR = DATA_DIR / "uploads"
    VECTOR_DB_DIR = DATA_DIR / "vector_db"

    # 确保目录存在
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

    # FastAPI 配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # CORS 配置
    ALLOW_ORIGINS: list = ["*"]  # 生产环境应设置为具体域名
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: list = ["*"]
    ALLOW_HEADERS: list = ["*"]

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".txt", ".docx", ".doc"}

    # RAG 配置
    RAG_EMBEDDING_TYPE: str = os.getenv("RAG_EMBEDDING_TYPE", "dashscope")
    RAG_EMBEDDING_MODEL: str = os.getenv("RAG_EMBEDDING_MODEL", "qwen3-vl-rerank")
    RAG_VECTOR_STORE: str = os.getenv("RAG_VECTOR_STORE", "chroma")
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "1500"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))

    # LLM 配置
    LLM_TYPE: str = os.getenv("LLM_TYPE", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))

    # OpenAI 配置
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL")

    # DashScope 配置
    DASHSCOPE_API_KEY: Optional[str] = os.getenv("DASHSCOPE_API_KEY")

    # Ollama 配置
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama2")

    # 会话配置
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 秒
    MAX_HISTORY_MESSAGES: int = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))

    # 合同审查配置
    CONTRACT_REVIEW_POINTS: list = [
        "合同主体是否明确合法",
        "合同标的描述是否清晰",
        "价款及支付方式条款",
        "违约责任条款",
        "争议解决条款",
        "合同生效及终止条件",
        "保密条款",
        "知识产权条款",
        "不可抗力条款",
        "其他特殊条款",
    ]


settings = Settings()
