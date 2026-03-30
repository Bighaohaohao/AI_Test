"""
文件处理服务
"""
import os
import shutil
from pathlib import Path
from typing import Tuple, Optional
import docx2txt

from config import UPLOAD_DIR, MAX_FILE_SIZE


ALLOWED_EXTENSIONS = {'.txt', '.doc', '.docx', '.pdf'}


def validate_file(filename: str, file_size: int) -> Tuple[bool, str]:
    """
    验证文件
    
    Returns:
        (是否有效, 错误信息)
    """
    # 检查扩展名
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件格式: {ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}"
    
    # 检查文件大小
    if file_size > MAX_FILE_SIZE:
        return False, f"文件过大，最大支持 {MAX_FILE_SIZE / 1024 / 1024}MB"
    
    return True, ""


def save_upload_file(file_content: bytes, filename: str) -> Path:
    """保存上传的文件"""
    file_path = UPLOAD_DIR / filename
    with open(file_path, 'wb') as f:
        f.write(file_content)
    return file_path


def extract_text_from_file(file_path: Path) -> Tuple[bool, str]:
    """
    从文件中提取文本
    
    Returns:
        (是否成功, 文本内容或错误信息)
    """
    try:
        ext = file_path.suffix.lower()
        
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return True, f.read()
        
        elif ext in ['.doc', '.docx']:
            text = docx2txt.process(str(file_path))
            return True, text
        
        elif ext == '.pdf':
            # 简化实现，实际项目中使用 PyPDF2 或 pdfplumber
            return False, "PDF 解析功能待实现"
        
        else:
            return False, f"不支持的文件格式: {ext}"
            
    except Exception as e:
        return False, f"文件解析失败: {str(e)}"


def clean_old_uploads(max_files: int = 10):
    """清理旧的上传文件"""
    files = sorted(UPLOAD_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
    for old_file in files[max_files:]:
        old_file.unlink(missing_ok=True)
