"""
文件上传路由
"""
import uuid
from fastapi import APIRouter, File, UploadFile, Form
from pathlib import Path

from services.file_service import validate_file, save_upload_file, extract_text_from_file, clean_old_uploads
from config import UPLOAD_DIR

router = APIRouter(prefix="/api", tags=["文件上传"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    normal_case_count: int = Form(3),
    abnormal_case_count: int = Form(2),
    test_types: str = Form("[\"功能测试\"]")
):
    """上传并处理需求文档"""
    try:
        # 验证文件
        content = await file.read()
        is_valid, error_msg = validate_file(file.filename, len(content))
        if not is_valid:
            return {"success": False, "error": error_msg}
        
        # 保存文件
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = save_upload_file(content, unique_filename)
        
        # 提取文本
        success, result = extract_text_from_file(file_path)
        if not success:
            return {"success": False, "error": result}
        
        # 清理旧文件
        clean_old_uploads()
        
        # 截取预览内容
        preview = result[:500] + "..." if len(result) > 500 else result
        
        return {
            "success": True,
            "filename": file.filename,
            "content": preview,
            "full_content": result,
            "normal_case_count": normal_case_count,
            "abnormal_case_count": abnormal_case_count,
            "test_types": test_types
        }
        
    except Exception as e:
        return {"success": False, "error": f"文件处理失败: {str(e)}"}


@router.post("/direct_input")
async def direct_input(
    requirement_text: str = Form(...),
    normal_case_count: int = Form(3),
    abnormal_case_count: int = Form(2),
    test_types: str = Form("[\"功能测试\"]")
):
    """直接输入需求文本"""
    try:
        if not requirement_text.strip():
            return {"success": False, "error": "需求内容不能为空"}
        
        # 截取预览内容
        preview = requirement_text[:500] + "..." if len(requirement_text) > 500 else requirement_text
        
        return {
            "success": True,
            "content": preview,
            "full_content": requirement_text,
            "normal_case_count": normal_case_count,
            "abnormal_case_count": abnormal_case_count,
            "test_types": test_types
        }
        
    except Exception as e:
        return {"success": False, "error": f"处理失败: {str(e)}"}
