"""
导出服务
"""
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from config import EXPORT_DIR


def export_to_excel(test_cases: List[Dict[str, Any]], filename: str = None) -> Path:
    """
    导出测试用例到 Excel
    
    Args:
        test_cases: 测试用例列表
        filename: 文件名（可选）
    
    Returns:
        导出文件路径
    """
    if filename is None:
        filename = f"test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    file_path = EXPORT_DIR / filename
    
    # 准备数据
    data = []
    for case in test_cases:
        data.append({
            "用例编号": case.get("case_id", ""),
            "功能模块": case.get("module", ""),
            "用例名称": case.get("case_name", ""),
            "前置条件": case.get("precondition", ""),
            "测试步骤": case.get("steps", ""),
            "预期结果": case.get("expected_result", ""),
            "优先级": case.get("priority", ""),
            "测试类型": case.get("case_type", "")
        })
    
    # 创建 DataFrame 并导出
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False, engine='openpyxl')
    
    return file_path


def export_to_json(test_cases: List[Dict[str, Any]], filename: str = None) -> Path:
    """导出为 JSON"""
    if filename is None:
        filename = f"test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    file_path = EXPORT_DIR / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(test_cases, f, ensure_ascii=False, indent=2)
    
    return file_path


def export_to_csv(test_cases: List[Dict[str, Any]], filename: str = None) -> Path:
    """导出为 CSV"""
    if filename is None:
        filename = f"test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    file_path = EXPORT_DIR / filename
    
    data = []
    for case in test_cases:
        data.append({
            "用例编号": case.get("case_id", ""),
            "功能模块": case.get("module", ""),
            "用例名称": case.get("case_name", ""),
            "前置条件": case.get("precondition", ""),
            "测试步骤": case.get("steps", ""),
            "预期结果": case.get("expected_result", ""),
            "优先级": case.get("priority", ""),
            "测试类型": case.get("case_type", "")
        })
    
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    
    return file_path
