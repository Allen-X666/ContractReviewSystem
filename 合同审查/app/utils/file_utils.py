import json
import logging
import unicodedata
from typing import Optional, Set

from fastapi import HTTPException, status

from 合同审查.app.schemas.models import ReviewOptions

logger = logging.getLogger(__name__)

# 支持的文件类型
SUPPORTED_EXTENSIONS: Set[str] = {"pdf", "docx", "txt"}


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，处理编码问题并移除不安全字符
    
    功能：
    - Unicode 规范化（如全角空格、标点转为半角）
    - 移除控制字符
    - 移除路径分隔符和危险字符
    - 限制文件名长度
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的安全文件名
        
    Example:
        >>> sanitize_filename("合同/文件：测试.pdf")
        '合同_文件_测试.pdf'
    """
    if not filename:
        return "unnamed_file"
    
    # 规范化 Unicode 字符（如全角空格转半角）
    filename = unicodedata.normalize('NFKC', filename)
    
    # 移除控制字符
    filename = ''.join(char for char in filename if unicodedata.category(char)[0] != 'C')
    
    # 移除路径分隔符和危险字符
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # 限制文件名长度（保留扩展名）
    max_length = 200
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:max_length - len(ext) - 1] if ext else name[:max_length]
        filename = f"{name}.{ext}" if ext else name
    
    return filename.strip()


def validate_file_extension(filename: str, allowed_extensions: Optional[Set[str]] = None) -> str:
    """
    验证文件扩展名
    
    Args:
        filename: 文件名
        allowed_extensions: 允许的文件扩展名集合，默认使用 SUPPORTED_EXTENSIONS
        
    Returns:
        小写的文件扩展名
        
    Raises:
        HTTPException: 文件名格式错误或文件类型不支持
        
    Example:
        >>> validate_file_extension("contract.pdf")
        'pdf'
        >>> validate_file_extension("contract.doc", {"pdf", "doc"})
        'doc'
    """
    extensions = allowed_extensions or SUPPORTED_EXTENSIONS
    
    if "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名缺少扩展名"
        )
    
    ext = filename.rsplit(".", 1)[-1].lower()
    
    if ext not in extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {ext}，仅支持: {', '.join(sorted(extensions))}"
        )
    
    return ext


def parse_json_options(options_str: Optional[str], model_class=None, default=None):
    """
    解析 JSON 选项字符串
    
    Args:
        options_str: JSON 字符串
        model_class: 可选的 Pydantic 模型类，用于验证
        default: 解析失败时的默认值
        
    Returns:
        解析后的对象或默认值
        
    Example:
        >>> parse_json_options('{"check": true}', ReviewOptions)
        ReviewOptions(check=True)
        >>> parse_json_options(None, default={})
        {}
        >>> parse_json_options('invalid json', default=None)
        None
    """
    if not options_str:
        return default() if callable(default) else default
    
    try:
        options_dict = json.loads(options_str)
        
        if model_class:
            return model_class(**options_dict)
        return options_dict
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON 解析失败: {e}, 使用默认值")
        return default() if callable(default) else default
    except Exception as e:
        logger.warning(f"选项验证失败: {e}, 使用默认值")
        return default() if callable(default) else default
