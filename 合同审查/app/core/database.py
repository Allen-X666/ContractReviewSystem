"""
SQLAlchemy 数据库连接配置

提供数据库引擎、会话管理和基础模型类
"""

import logging
from typing import Generator, Dict, Any

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from 合同审查.app.core.config import settings

logger = logging.getLogger(__name__)


class DatabasePoolMonitor:
    """数据库连接池监控器"""

    def __init__(self, engine):
        self.engine = engine

    def get_pool_stats(self) -> Dict[str, Any]:
        """
        获取连接池统计信息

        Returns:
            包含连接池状态的字典
        """
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "max_overflow": self.engine.pool._max_overflow,
        }

    def log_pool_stats(self) -> None:
        """记录连接池统计信息到日志"""
        stats = self.get_pool_stats()
        logger.info(
            f"数据库连接池状态: "
            f"size={stats['pool_size']}, "
            f"checked_in={stats['checked_in']}, "
            f"checked_out={stats['checked_out']}, "
            f"overflow={stats['overflow']}"
        )


# 创建数据库引擎（使用 QueuePool 以获得更好的监控能力）
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # 连接前 ping 测试，自动回收失效连接
    echo=settings.DB_ECHO,
    # 连接参数
    connect_args={
        "charset": settings.MYSQL_CHARSET,
    }
)

# 创建连接池监控器
pool_monitor = DatabasePoolMonitor(engine)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 声明性基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖函数

    用于FastAPI的依赖注入系统

    Yields:
        SQLAlchemy Session对象

    Example:
        @router.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_db_async() -> Generator[Session, None, None]:
    """
    异步获取数据库会话的依赖函数

    Yields:
        SQLAlchemy Session对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库

    创建所有定义的表结构
    注意：生产环境建议使用Alembic进行数据库迁移
    """
    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """
    检查数据库连接是否正常

    Returns:
        连接成功返回True，否则返回False
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False


def get_db_health() -> Dict[str, Any]:
    """
    获取数据库健康状态（包含连接池信息）

    Returns:
        数据库健康状态字典
    """
    health = {
        "connected": False,
        "pool_stats": None,
        "error": None
    }

    try:
        # 测试连接
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health["connected"] = True
        health["pool_stats"] = pool_monitor.get_pool_stats()
    except Exception as e:
        health["error"] = str(e)
        logger.error(f"数据库健康检查失败: {e}")

    return health
