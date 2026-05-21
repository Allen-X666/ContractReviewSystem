import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings

# 预加载HF_TOKEN和HF_ENDPOINT环境变量（确保在Settings实例化前设置）
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                if key in ("HF_TOKEN", "HF_ENDPOINT") and key not in os.environ:
                    os.environ[key] = value.strip()


class Settings(BaseSettings):
    """应用配置类"""

    # 应用配置
    APP_NAME: str = "Contract Review AI Service"
    APP_VERSION: str = "1.0.0"
    APP_DEBUG: bool = True

    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8001

    # API配置
    API_PREFIX: str = "/api/v1"
    API_V1_STR: str = "/api/v1"

    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8080", "http://127.0.0.1:8080"]

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ==================== 模型名称配置（集中管理） ====================
    # Embedding模型配置
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_TYPE: str = "huggingface"

    # OpenAI Embedding模型名称
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    # ModelScope Embedding模型名称
    MODELSCOPE_EMBEDDING_MODEL: str = "iic/nlp_gte_sentence-embedding_chinese-small"
    # Ollama Embedding模型名称
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    # LLM模型配置（统一通过DashScope MultiModalConversation.call()调用）
    #   - qwen3-max / qwen-plus / qwen-turbo / qwen-long
    #   - qwen3.5-122b-a10b
    #   - qwen-vl-max / qwen-vl-plus / qwen-vl-max-latest（多模态）
    #   - deepseek-v3 / deepseek-r1
    # LLM模型配置（通过DashScope调用）
    LLM_MODEL_DEFAULT: str = "qwen3.6-flash"
    LLM_MODEL_REVIEW: str = "qwen3.6-flash"
    LLM_TYPE: str = "tongyi"  # 使用DashScope通义千问模型
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
    # Ollama LLM模型名称
    OLLAMA_LLM_MODEL: str = "llama2"

    # Chat模型配置（通过DashScope调用）
    CHAT_MODEL_DEFAULT: str = "qwen3.6-flash"
    CHAT_MODEL_REVIEW: str = "qwen3.6-flash"
    CHAT_TYPE: str = "tongyi"  # 使用DashScope通义千问模型
    CHAT_TEMPERATURE: float = 0.7
    CHAT_MAX_TOKENS: int = 2048
    CHAT_DEBUG: bool = True

    # DeepSeek模型配置（通过DashScope text-generation端点调用）
    DEEPSEEK_MODEL: str = "deepseek-v3"

    # Qwen模型配置
    # 纯文本模型: qwen3.6-flash / qwen3-max / qwen-plus / qwen-turbo
    # 多模态模型: qwen-vl-max / qwen-vl-plus
    # 注：通过DashScope API调用
    QWEN_MODEL: str = "qwen3.6-flash"
    QWEN_PIPELINE_TASK: str = "image-text-to-text"

    # 本地 Qwen/WebWorld-8B 模型配置（通过HuggingFace pipeline加载）
    # 使用方式：设置 LLM_TYPE="local_qwen" 启用本地模型
    LOCAL_QWEN_MODEL: str = "Qwen/WebWorld-8B"  # HuggingFace模型名称
    LOCAL_QWEN_DEVICE: str = "auto"  # 设备: auto, cuda, cpu
    LOCAL_QWEN_TEMPERATURE: float = 0.7
    LOCAL_QWEN_MAX_TOKENS: int = 2048
    LOCAL_QWEN_TOP_P: float = 0.9

    # 通义千问/DashScope配置
    DASHSCOPE_API_KEY: str = Field(default="", validation_alias="DASHSCOPE_API_KEY")
    TONGYI_TEMPERATURE: float = 0.3
    TONGYI_MAX_TOKENS: int = 4096
    TONGYI_TOP_P: float = 0.9

    # HuggingFace配置
    HF_TOKEN: str = ""
    HF_ENDPOINT: str = "https://hf-mirror.com"
    HF_HUB_CACHE: str = r"E:\Professional\合同审查agent\合同审查\huggingface\cache"  # HuggingFace 模型缓存目录
    HF_HUB_DISABLE_SYMLINKS_WARNING: bool = True

    # ==================== Redis Checkpointer 配置 ====================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1
    REDIS_PASSWORD: str = "1115"  # 无密码时留空
    REDIS_KEY__PREFIX: str = "chatRecord:checkpoint"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_CONNECT_TIMEOUT: int = 5
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_HEALTH_CHECK_INTERVAL: int = 30

    # ==================== 对话上下文管理配置 ====================
    # 最大保留的对话消息数量（滑动窗口），超过则截断早期消息
    MAX_HISTORY_MESSAGES: int = 20
    # 是否启用上下文截断
    CONTEXT_TRUNCATION_ENABLED: bool = True

    # ==================== SpringBoot 服务配置 ====================
    SPRINGBOOT_BASE_URL: str = "http://localhost:8080/api"
    SPRINGBOOT_TIMEOUT: float = 30.0  # 秒

    # ==================== 数据库配置 (SQLAlchemy) ====================
    # MySQL连接配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "1115"
    MYSQL_DB: str = "contract_review"
    MYSQL_CHARSET: str = "utf8mb4"

    # SQLAlchemy数据库URL
    @property
    def DATABASE_URL(self) -> str:
        """构建SQLAlchemy数据库连接URL"""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
            f"?charset={self.MYSQL_CHARSET}"
        )

    # 数据库连接池配置
    DB_POOL_SIZE: int = 20          # 连接池大小
    DB_MAX_OVERFLOW: int = 10       # 超出连接池大小时的最大连接数
    DB_POOL_TIMEOUT: int = 30       # 获取连接的超时时间（秒）
    DB_POOL_RECYCLE: int = 3600     # 连接回收时间（秒）
    DB_ECHO: bool = False           # 是否打印SQL语句（调试用）

    # ==================== 混合检索配置 ====================
    # 是否启用混合检索（向量检索 + 关键词检索）
    HYBRID_RETRIEVAL_ENABLED: bool = os.getenv("HYBRID_RETRIEVAL_ENABLED", "true").lower() == "true"
    # 向量检索权重（0.0-1.0）
    HYBRID_VECTOR_WEIGHT: float = float(os.getenv("HYBRID_VECTOR_WEIGHT", "0.7"))
    # 关键词检索权重（0.0-1.0）
    HYBRID_KEYWORD_WEIGHT: float = float(os.getenv("HYBRID_KEYWORD_WEIGHT", "0.3"))
    # 混合检索召回数量（重排前）
    HYBRID_RECALL_TOP_K: int = int(os.getenv("HYBRID_RECALL_TOP_K", "10"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# 设置HuggingFace环境变量
if settings.HF_TOKEN:
    os.environ["HF_TOKEN"] = settings.HF_TOKEN
if settings.HF_ENDPOINT:
    os.environ["HF_ENDPOINT"] = settings.HF_ENDPOINT
if settings.HF_HUB_CACHE:
    os.environ["HUGGINGFACE_HUB_CACHE"] = settings.HF_HUB_CACHE
    os.environ["TRANSFORMERS_CACHE"] = settings.HF_HUB_CACHE
if settings.HF_HUB_DISABLE_SYMLINKS_WARNING:
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
