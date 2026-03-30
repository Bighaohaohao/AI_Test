"""
配置文件
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据库配置
DATABASE_URL = "sqlite:///./test_cases.db"

# 文件上传配置
UPLOAD_DIR = BASE_DIR / "uploads"
EXPORT_DIR = BASE_DIR / "exports"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# AI模型配置
AI_MODEL_CONFIG = {
    "qwen": {
        "name": "通义千问",
        "max_tokens": 6000,
        "max_cases_per_request": 25,
        "base_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    },
    "example": {
        "name": "示例数据",
        "max_cases_per_request": 25
    },
    "openai": {
        "name": "OpenAI",
        "max_tokens": 4000,
        "max_cases_per_request": 20
    }
}

# 创建目录
UPLOAD_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)
