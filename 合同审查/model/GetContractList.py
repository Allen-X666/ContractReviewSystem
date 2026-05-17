from sqlalchemy import Column, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


def GetContractList(Base):
    __tablename__ = "contract"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='合同ID')
    file_name = Column(String(255), nullable=False, comment='文件名')
    file_size = Column(BigInteger, nullable=False, comment='文件大小(字节)')
    file_type = Column(String(50), nullable=False, comment='文件类型: pdf/docx')
    created_at = Column(DateTime, default=datetime.now, server_default='CURRENT_TIMESTAMP', comment='创建时间')

    def __repr__(self):
        return f"<Contract(id={self.id}, file_name='{self.file_name}', status='{self.review_status}')>"
