"""
SQLAlchemy 数据库连接配置

提供数据库引擎、会话管理和基础模型类
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from 合同审查.app.core.config import settings


# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DB_ECHO,
    # 连接参数
    connect_args={
        "charset": settings.MYSQL_CHARSET,
    }
)

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
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False
