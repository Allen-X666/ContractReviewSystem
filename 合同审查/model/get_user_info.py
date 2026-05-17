"""
用户信息模型
对应数据库表: sys_user
"""
from typing import Any

from sqlalchemy import Column, BigInteger, String, DateTime, SmallInteger, func
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class SysUser(Base):
    """
    用户表模型
    """
    __tablename__ = 'sys_user'
    __table_args__ = {'comment': '用户表'}

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='用户ID')

    # 用户名
    username = Column(String(50), nullable=False, unique=True, comment='用户名')

    # 昵称
    nick_name = Column(String(50), nullable=True, comment='昵称')

    # 邮箱
    email = Column(String(100), nullable=True, unique=True, comment='邮箱')

    # 手机号
    phone = Column(String(20), nullable=True, unique=True, comment='手机号')

    # 角色: admin/user
    role = Column(String(20), nullable=True, default='user', comment='角色: admin/user')

    # 创建时间
    created_at = Column(DateTime, nullable=True, default=func.current_timestamp(), comment='创建时间')

    def __init__(self, **kw: Any):
        super().__init__()
        self.status = None

    def __repr__(self):
        return f"<SysUser(id={self.id}, username='{self.username}', nick_name='{self.nick_name}')>"

    def to_dict(self):
        """
        转换为字典格式
        """
        return {
            'id': self.id,
            'username': self.username,
            'nickName': self.nick_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'createdAt': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class GetUserInfo:
    """
    用户信息响应类
    用于返回给前端的数据结构
    """

    def __init__(self, username=None, nick_name=None, email=None,
                 phone=None, role=None, created_at=None):
        self.username = username
        self.nick_name = nick_name
        self.email = email
        self.phone = phone
        self.role = role
        self.created_at = created_at

    @property
    def nickName(self):
        """兼容前端驼峰命名"""
        return self.nick_name

    @property
    def createdAt(self):
        """兼容前端驼峰命名，格式化时间"""
        if self.created_at:
            if isinstance(self.created_at, datetime):
                return self.created_at.strftime('%Y-%m-%d %H:%M:%S')
            return self.created_at
        return None

    def to_dict(self):
        """
        转换为字典格式，兼容前端字段命名
        """
        return {
            'username': self.username,
            'nickName': self.nick_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'createdAt': self.createdAt
        }

    @classmethod
    def from_model(cls, user: SysUser):
        """
        从数据库模型创建响应对象
        """
        if not user:
            return None
        return cls(
            username=user.username,
            nick_name=user.nick_name,
            email=user.email,
            phone=user.phone,
            role=user.role,
            created_at=user.created_at
        )
