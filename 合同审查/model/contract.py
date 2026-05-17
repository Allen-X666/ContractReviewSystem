from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Contract(Base):
    __tablename__ = "contract"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='合同ID')
    file_name = Column(String(255), nullable=False, comment='文件名')
    file_path = Column(String(500), nullable=False, comment='文件存储路径')
    file_size = Column(BigInteger, nullable=False, comment='文件大小(字节)')
    file_type = Column(String(50), nullable=False, comment='文件类型: pdf/docx')
    user_id = Column(BigInteger, ForeignKey('sys_user.id', ondelete='CASCADE'), nullable=False, comment='上传用户ID')
    review_status = Column(String(20), default='pending', comment='审查状态: 待审查/审查中/已完成/审查失败/已取消')
    risk_level = Column(String(20), default='', comment='风险等级: 高风险/中风险/低风险')
    review_score = Column(Integer, comment='审查得分(0-100)')
    created_at = Column(DateTime, default=datetime.now, server_default='CURRENT_TIMESTAMP', comment='创建时间')

    def __repr__(self):
        return f"<Contract(id={self.id}, file_name='{self.file_name}', status='{self.review_status}')>"
