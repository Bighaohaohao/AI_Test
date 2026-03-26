"""
AI测试用例生成工具 - 简化稳定版
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import json
import os
import tempfile
import docx2txt
import pandas as pd
from datetime import datetime
import dashscope
import re

app = FastAPI()

# 挂载静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 确保exports目录存在
os.makedirs("exports", exist_ok=True)

# API密钥配置
CONFIG_FILE = "api_keys_config.json"

def load_api_keys():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_api_keys(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api_config.html", response_class=HTMLResponse)
async def read_api_config(request: Request):
    return templates.TemplateResponse("api_config.html", {"request": request})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """处理文件上传"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # 提取文本
        text = docx2txt.process(tmp_path) if file.filename.endswith('.docx') else open(tmp_path, 'r', encoding='utf-8').read()
        os.unlink(tmp_path)
        
        return {"success": True, "content": text[:1000], "full_content": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/direct_input")
async def direct_input(
    requirement_text: str = Form(...),
    normal_case_count: int = Form(10),
    abnormal_case_count: int = Form(5),
    test_types: str = Form("[\"功能测试\"]")
):
    """处理直接文本输入"""
    return {
        "success": True, 
        "content": requirement_text[:1000], 
        "full_content": requirement_text,
        "normal_case_count": normal_case_count,
        "abnormal_case_count": abnormal_case_count,
        "test_types": test_types
    }

def parse_ai_response(ai_response: str, test_types: list) -> list:
    """解析AI响应，提取测试用例"""
    print(f"AI响应长度: {len(ai_response)}")
    print(f"期望的测试类型: {test_types}")
    
    # 清理markdown标记
    cleaned = ai_response.strip()
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    # 尝试直接解析整个响应
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            print(f"成功解析JSON数组，包含 {len(data)} 个用例")
            # 验证每个用例
            valid = []
            for i, item in enumerate(data):
                if isinstance(item, dict) and all(k in item for k in ['module', 'case_id', 'case_name', 'case_type']):
                    case_type = item.get('case_type')
                    print(f"用例{i+1}: case_type='{case_type}', 期望类型={test_types}")
                    if case_type in test_types:
                        valid.append(item)
                        print(f"  ✓ 通过过滤")
                    else:
                        print(f"  ✗ 类型不匹配，跳过")
                else:
                    print(f"用例{i+1}: 缺少必要字段，跳过")
            print(f"过滤后剩余 {len(valid)} 个有效用例")
            return valid
    except Exception as e:
        print(f"直接解析失败: {e}")
    
    # 尝试提取JSON数组
    try:
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            data = json.loads(match.group())
            if isinstance(data, list):
                print(f"通过正则提取到 {len(data)} 个用例")
                valid = []
                for item in data:
                    if isinstance(item, dict) and all(k in item for k in ['module', 'case_id', 'case_name', 'case_type']):
                        if item.get('case_type') in test_types:
                            valid.append(item)
                return valid
    except Exception as e:
        print(f"正则提取失败: {e}")
    
    print("未能提取到任何有效用例")
    return []

@app.post("/generate")
async def generate(
    requirement_text: str = Form(...),
    model_type: str = Form(...),
    api_key: str = Form(None),
    normal_case_count: int = Form(10),
    abnormal_case_count: int = Form(5),
    test_types: str = Form("[\"功能测试\"]")
):
    """生成测试用例"""
    try:
        test_types_list = json.loads(test_types)
        target_count = normal_case_count + abnormal_case_count
        
        # 从配置文件获取当前模型的限制
        config = load_api_keys()
        model_config = config.get(model_type, {})
        max_cases = model_config.get('max_cases_per_request', 25)
        max_tokens = model_config.get('max_tokens', 4000)
        
        # 限制单次生成数量，避免超出token限制
        if target_count > max_cases:
            print(f"警告：请求生成{target_count}条用例，超出模型限制，调整为{max_cases}条")
            target_count = max_cases
        
        # 处理示例模型 - 直接返回模拟数据
        if model_type == 'example':
            # 生成示例测试用例
            cases = []
            for i in range(1, target_count + 1):
                cases.append({
                    "module": "示例模块",
                    "case_id": f"TC{i:03d}",
                    "case_name": f"示例测试用例{i}",
                    "precondition": "示例前置条件",
                    "steps": "1. 执行步骤1 2. 执行步骤2 3. 执行步骤3",
                    "expected_result": "示例预期结果",
                    "priority": "P1",
                    "case_type": test_types_list[0] if test_types_list else "功能测试"
                })
            return {
                "success": True,
                "test_cases": cases,
                "model_used": "example"
            }
        
        # 获取API密钥
        actual_key = model_config.get('api_key')
        
        if not actual_key:
            raise HTTPException(status_code=400, detail="未配置API密钥")
        
        dashscope.api_key = actual_key
        
        # 构建提示词
        prompt = f"""你是一位Web3钱包App方向的资深高级测试工程师，拥有丰富的区块链钱包、数字资产管理、DApp交互等测试经验。请根据以下需求生成{target_count}个专业的测试用例。

【需求描述】
{requirement_text[:1500]}

【生成要求】
1. 生成数量：{target_count}个测试用例
2. 测试类型：{', '.join(test_types_list)}
3. 优先级规范：P0(高)、P1(中)、P2(低)
4. case_type必须是以下之一：{', '.join(test_types_list)}
5. 请从Web3钱包App的专业角度出发，考虑区块链特性、数字资产安全、私钥管理、助记词、交易签名、Gas费、多链支持、DApp浏览器等典型场景

【格式要求 - 严格遵守】
1. 直接返回JSON数组，不要添加markdown代码块标记(```json)
2. 不要添加任何解释性文字
3. 确保JSON格式完整有效，以[开头，以]结尾
4. 每个用例必须包含以下字段：module, case_id, case_name, precondition, steps, expected_result, priority, case_type
5. 控制每个字段的长度，确保整体响应不超过4000个token
6. steps和expected_result字段请精简描述，控制在100字以内

【输出示例】
[
  {{
    "module": "钱包创建",
    "case_id": "TC001",
    "case_name": "创建新钱包生成助记词",
    "precondition": "App首次安装，无现有钱包",
    "steps": "1. 打开App 2. 点击创建新钱包 3. 备份助记词 4. 验证助记词",
    "expected_result": "成功创建钱包，显示钱包地址，助记词备份完成",
    "priority": "P0",
    "case_type": "{test_types_list[0]}"
  }}
]"""
        
        # 调用AI
        response = dashscope.Generation.call(
            model='qwen-plus',
            prompt=prompt,
            max_tokens=max_tokens
        )
        
        if response.status_code == 200:
            ai_text = response.output.text
            print(f"AI响应: {ai_text[:500]}")
            
            # 解析测试用例
            cases = parse_ai_response(ai_text, test_types_list)
            
            # 重新编号
            for i, case in enumerate(cases, 1):
                case['case_id'] = f"TC{i:03d}"
            
            return {
                "success": True,
                "test_cases": cases,
                "model_used": model_type
            }
        else:
            raise HTTPException(status_code=500, detail=f"AI调用失败: {response.status_code}")
            
    except Exception as e:
        print(f"生成错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def export_to_excel(cases: list, filename: str) -> str:
    """导出到Excel"""
    df = pd.DataFrame(cases)
    columns = ['module', 'case_id', 'case_name', 'precondition', 'steps', 'expected_result', 'priority', 'case_type']
    existing = [c for c in columns if c in df.columns]
    df = df[existing]
    
    mapping = {
        'module': '功能模块',
        'case_id': '用例编号', 
        'case_name': '用例名称',
        'precondition': '前置条件',
        'steps': '测试步骤',
        'expected_result': '预期结果',
        'priority': '优先级',
        'case_type': '用例类型'
    }
    df.rename(columns={k: v for k, v in mapping.items() if k in df.columns}, inplace=True)
    
    filepath = f"exports/{filename}"
    df.to_excel(filepath, index=False)
    return filepath

@app.post("/export")
async def export(test_cases_json: str = Form(...)):
    """导出测试用例"""
    try:
        cases = json.loads(test_cases_json)
        filename = f"test_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = export_to_excel(cases, filename)
        return FileResponse(filepath, filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/models")
async def get_supported_models():
    """获取支持的AI模型列表"""
    return {
        "qwen": "通义千问 (Qwen)",
        "openai": "OpenAI GPT",
        "example": "示例模型 (Mock)"
    }

@app.get("/api/config/api-keys")
async def get_api_keys():
    """获取API密钥状态和模型配置"""
    config = load_api_keys()
    result = {}
    for model, data in config.items():
        api_key = data.get("api_key", "")
        result[model] = {
            "configured": bool(api_key),
            "has_key": bool(api_key),
            "masked_key": "*" * 8 + api_key[-4:] if api_key else "",
            "max_cases_per_request": data.get("max_cases_per_request", 25),
            "max_tokens": data.get("max_tokens", 4000)
        }
    return result

@app.post("/api/config/api-keys/{model_name}")
async def save_api_key(model_name: str, api_key: str = Form(...)):
    """保存API密钥"""
    try:
        config = load_api_keys()
        if model_name not in config:
            config[model_name] = {}
        config[model_name]["api_key"] = api_key
        save_api_keys(config)
        return {"success": True, "message": f"{model_name} 的API密钥已保存"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/config/api-keys/{model_name}")
async def delete_api_key(model_name: str):
    """删除API密钥"""
    try:
        config = load_api_keys()
        if model_name in config and "api_key" in config[model_name]:
            del config[model_name]["api_key"]
            save_api_keys(config)
        return {"success": True, "message": f"{model_name} 的API密钥已移除"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)