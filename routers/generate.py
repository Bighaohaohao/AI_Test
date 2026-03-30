"""
AI 生成路由
"""
import json
import os
from fastapi import APIRouter, Form
from typing import List

from services.ai_service import generate_test_cases
from services.export_service import export_to_excel
from config import EXPORT_DIR, BASE_DIR

router = APIRouter(prefix="/api", tags=["AI生成"])

# API 密钥存储（实际项目中应使用更安全的方式）
api_keys = {}

# 加载配置文件
def load_api_keys():
    """从配置文件加载 API 密钥"""
    config_path = BASE_DIR / "api_keys_config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for model, settings in config.items():
                    if isinstance(settings, dict) and settings.get('api_key'):
                        api_keys[model] = settings['api_key']
                print(f"已从配置文件加载 {len(api_keys)} 个 API 密钥")
        except Exception as e:
            print(f"加载 API 密钥配置文件失败: {e}")

# 启动时加载
load_api_keys()


@router.post("/generate")
async def generate_cases(
    requirement_text: str = Form(...),
    api_key: str = Form(None),
    model: str = Form("qwen"),
    normal_case_count: int = Form(3),
    abnormal_case_count: int = Form(2),
    test_types: str = Form("[\"功能测试\"]")
):
    """生成测试用例"""
    try:
        # 解析测试类型
        test_types_list = json.loads(test_types)
        
        # 获取 API 密钥
        if model == "example":
            api_key = None
        elif not api_key:
            api_key = api_keys.get(model)
            if not api_key:
                return {"success": False, "error": f"未配置 {model} 的 API 密钥"}
        
        # 生成用例
        test_cases = generate_test_cases(
            requirement_text=requirement_text,
            model=model,
            api_key=api_key,
            normal_case_count=normal_case_count,
            abnormal_case_count=abnormal_case_count,
            test_types=test_types_list
        )
        
        return {
            "success": True,
            "test_cases": test_cases,
            "total": len(test_cases)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/export")
async def export_cases(
    test_cases: str = Form(...),
    format: str = Form("excel")
):
    """导出测试用例"""
    try:
        cases = json.loads(test_cases)
        
        if format == "excel":
            file_path = export_to_excel(cases)
            return {
                "success": True,
                "filename": file_path.name,
                "download_url": f"/exports/{file_path.name}"
            }
        else:
            return {"success": False, "error": "不支持的导出格式"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api-keys/status")
async def get_api_key_status():
    """获取 API 密钥配置状态"""
    return {
        "qwen": bool(api_keys.get("qwen")),
        "openai": bool(api_keys.get("openai")),
        "example": True
    }


@router.post("/api-keys/save")
async def save_api_key(
    model: str = Form(...),
    api_key: str = Form(...)
):
    """保存 API 密钥"""
    try:
        api_keys[model] = api_key
        return {"success": True, "message": f"{model} API 密钥已保存"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# 兼容旧版 API 路径
@router.get("/config/models")
async def get_config_models():
    """获取模型配置列表"""
    return {
        "qwen": "通义千问",
        "openai": "OpenAI",
        "example": "示例数据"
    }


@router.get("/config/api-keys")
async def get_config_api_keys():
    """获取 API 密钥列表（脱敏）"""
    return {
        "qwen": {
            "has_key": bool(api_keys.get("qwen")),
            "masked_key": api_keys.get("qwen", "")[:8] + "****" if api_keys.get("qwen") else ""
        },
        "openai": {
            "has_key": bool(api_keys.get("openai")),
            "masked_key": api_keys.get("openai", "")[:8] + "****" if api_keys.get("openai") else ""
        },
        "example": {
            "has_key": True,
            "masked_key": "无需密钥"
        }
    }


@router.put("/config/api-keys/{model_name}")
async def update_config_api_key(model_name: str, api_key: str = Form(...)):
    """更新 API 密钥"""
    try:
        api_keys[model_name] = api_key
        return {"success": True, "message": f"{model_name} API 密钥已更新"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/config/api-keys/{model_name}")
async def delete_config_api_key(model_name: str):
    """删除 API 密钥"""
    try:
        if model_name in api_keys:
            del api_keys[model_name]
        return {"success": True, "message": f"{model_name} API 密钥已删除"}
    except Exception as e:
        return {"success": False, "error": str(e)}
