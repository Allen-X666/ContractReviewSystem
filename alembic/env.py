"""
Alembic 环境配置

配置数据库迁移环境，从 FastAPI 的 settings 读取数据库连接信息。
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 导入 FastAPI 的 settings 和 Base
from 合同审查.app.core.config import settings
from 合同审查.app.core.database import Base

# 导入所有模型以确保它们被注册到 Base.metadata
from 合同审查.model.contract import Contract

# Alembic Config 对象
config = context.config

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标 metadata
# 模型需要继承 Base，这样 Alembic 才能检测到表结构变化
target_metadata = Base.metadata

# 从 settings 获取数据库 URL
def get_url():
    """获取数据库连接 URL"""
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    """离线模式运行迁移（生成 SQL 脚本）"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式运行迁移（直接操作数据库）"""
    # 使用从 settings 获取的 URL 创建引擎配置
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
