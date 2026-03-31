"""
AI 生成服务
"""
import json
import re
import requests
from typing import List, Dict, Any
from config import AI_MODEL_CONFIG


def generate_test_cases(
    requirement_text: str,
    model: str,
    api_key: str,
    normal_case_count: int = 3,
    abnormal_case_count: int = 2,
    test_types: List[str] = None
) -> List[Dict[str, Any]]:
    """
    生成测试用例
    
    Args:
        requirement_text: 需求文本
        model: 模型名称 (qwen/example/openai)
        api_key: API密钥
        normal_case_count: 正常用例数量
        abnormal_case_count: 异常用例数量
        test_types: 测试类型列表
    
    Returns:
        测试用例列表
    """
    if test_types is None:
        test_types = ["功能测试"]
    
    # 示例数据模式
    if model == "example":
        return _generate_example_cases(requirement_text, normal_case_count, abnormal_case_count, test_types)
    
    # 通义千问
    if model == "qwen":
        return _generate_qwen_cases(
            requirement_text, api_key, 
            normal_case_count, abnormal_case_count, test_types
        )
    
    # OpenAI
    if model == "openai":
        return _generate_openai_cases(
            requirement_text, api_key,
            normal_case_count, abnormal_case_count, test_types
        )
    
    raise ValueError(f"不支持的模型: {model}")


def _generate_example_cases(requirement_text: str, normal_count: int, abnormal_count: int, test_types: List[str]) -> List[Dict]:
    """生成示例用例数据"""
    cases = []
    case_id = 1
    
    for test_type in test_types:
        # 正常用例
        for i in range(normal_count):
            cases.append({
                "case_id": f"TC{case_id:03d}",
                "module": "示例模块",
                "case_name": f"{test_type}_正常用例_{i+1}",
                "precondition": "系统正常运行，用户已登录",
                "steps": f"1. 进入功能页面\n2. 执行正常操作步骤{i+1}\n3. 验证结果",
                "expected_result": "操作成功，显示正确结果",
                "priority": "P1",
                "case_type": test_type,
                "status": "pending"  # 默认为待执行
            })
            case_id += 1
        
        # 异常用例
        for i in range(abnormal_count):
            cases.append({
                "case_id": f"TC{case_id:03d}",
                "module": "示例模块",
                "case_name": f"{test_type}_异常用例_{i+1}",
                "precondition": "系统正常运行",
                "steps": f"1. 进入功能页面\n2. 执行异常操作步骤{i+1}\n3. 验证错误处理",
                "expected_result": "系统正确处理异常，显示友好错误提示",
                "priority": "P2",
                "case_type": test_type,
                "status": "pending"  # 默认为待执行
            })
            case_id += 1
    
    return cases


def _generate_qwen_cases(requirement_text: str, api_key: str, normal_count: int, abnormal_count: int, test_types: List[str]) -> List[Dict]:
    """调用通义千问生成用例"""
    if not api_key:
        raise ValueError("未配置通义千问 API 密钥")
    
    config = AI_MODEL_CONFIG["qwen"]
    max_cases = config["max_cases_per_request"]
    total_requested = (normal_count + abnormal_count) * len(test_types)
    
    all_cases = []
    generated_count = 0
    
    # 分批生成
    while generated_count < total_requested:
        batch_size = min(max_cases, total_requested - generated_count)
        batch_cases = _call_qwen_api(
            requirement_text, api_key, 
            normal_count, abnormal_count, test_types,
            batch_size, generated_count
        )
        all_cases.extend(batch_cases)
        generated_count += len(batch_cases)
        
        if len(batch_cases) == 0:
            break
    
    return all_cases


def _call_qwen_api(
    requirement_text: str, api_key: str,
    normal_count: int, abnormal_count: int,
    test_types: List[str], batch_size: int, offset: int
) -> List[Dict]:
    """调用通义千问 API"""
    
    test_types_str = ", ".join(test_types)
    
    prompt = f"""你是一位资深的 Web3 钱包 App 测试专家，精通区块链钱包的功能测试、安全测试和用户体验测试。

请根据以下需求，生成高质量的功能测试用例。

## 需求描述
{requirement_text}

## 生成要求
1. 测试类型：{test_types_str}
2. 正常用例数量：{normal_count} 条
3. 异常用例数量：{abnormal_count} 条
4. 用例编号从 TC{offset+1:03d} 开始

## 输出格式
必须以 JSON 数组格式返回，每个用例包含以下字段：
- case_id: 用例编号（如 TC001）
- module: 功能模块（从需求中识别）
- case_name: 用例名称（简洁明了）
- precondition: 前置条件
- steps: 测试步骤（分步骤描述）
- expected_result: 预期结果
- priority: 优先级（P0/P1/P2）
- case_type: 测试类型（{test_types_str}）

请只返回 JSON 数组，不要包含其他说明文字。"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "qwen-plus",
        "input": {
            "messages": [
                {"role": "system", "content": "你是一位专业的 Web3 钱包 App 测试工程师，擅长生成详细的测试用例。"},
                {"role": "user", "content": prompt}
            ]
        },
        "parameters": {
            "result_format": "message",
            "max_tokens": 6000,
            "temperature": 0.7
        }
    }
    
    try:
        response = requests.post(
            AI_MODEL_CONFIG["qwen"]["base_url"],
            headers=headers,
            json=data,
            timeout=120
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["output"]["choices"][0]["message"]["content"]
        
        # 解析 JSON
        return _parse_ai_response(content)
        
    except Exception as e:
        raise Exception(f"AI 调用失败: {str(e)}")


def _generate_openai_cases(requirement_text: str, api_key: str, normal_count: int, abnormal_count: int, test_types: List[str]) -> List[Dict]:
    """调用 OpenAI 生成用例"""
    # 简化实现，实际项目中补充
    return _generate_example_cases(requirement_text, normal_count, abnormal_count, test_types)


def _parse_ai_response(content: str) -> List[Dict]:
    """解析 AI 返回的 JSON"""
    try:
        # 尝试直接解析
        return json.loads(content)
    except json.JSONDecodeError:
        # 尝试提取 JSON 代码块
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # 尝试提取方括号内容
        bracket_match = re.search(r'\[[\s\S]*\]', content)
        if bracket_match:
            try:
                return json.loads(bracket_match.group(0))
            except:
                pass
        
        raise ValueError("无法解析 AI 返回的内容")
